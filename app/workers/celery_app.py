"""
Celery application configuration for background task processing.
"""
from typing import Any, Dict, Optional
from celery import Celery
from celery.signals import task_prerun, task_postrun, worker_ready
import logging

from app.config.settings import settings
from app.config.logging import setup_logging, set_correlation_id

logger = logging.getLogger(__name__)


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.
    
    Returns:
        Celery: Configured Celery application instance
    """
    # Create Celery app
    celery_app = Celery(
        "the_plugs_workers",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend
    )
    
    # Configure Celery
    celery_app.conf.update(
        # Task routing
        task_routes={
            'app.workers.email_worker.*': {'queue': 'email'},
            'app.workers.media_worker.*': {'queue': 'media'},
            'app.workers.analytics_worker.*': {'queue': 'analytics'},
            'app.workers.ai_worker.*': {'queue': 'ai'},
            'app.workers.notification_worker.*': {'queue': 'notifications'},
            'app.workers.cleanup_worker.*': {'queue': 'cleanup'},
        },
        
        # Task execution
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Task result configuration
        result_expires=3600,  # 1 hour
        result_persistent=True,
        
        # Worker configuration
        worker_prefetch_multiplier=1,  # Prevent memory issues
        task_acks_late=True,  # Acknowledge task after completion
        worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
        
        # Task time limits
        task_time_limit=300,  # 5 minutes hard limit
        task_soft_time_limit=240,  # 4 minutes soft limit
        
        # Retry configuration
        task_default_max_retries=3,
        task_default_retry_delay=60,  # 1 minute
        task_retry_backoff=True,
        task_retry_backoff_max=600,  # 10 minutes max
        task_retry_jitter=True,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Beat schedule (for periodic tasks)
        beat_schedule={
            'cleanup-old-data': {
                'task': 'app.workers.cleanup_worker.cleanup_old_data',
                'schedule': 3600.0,  # Every hour
                'options': {'queue': 'cleanup'}
            },
            'process-analytics': {
                'task': 'app.workers.analytics_worker.process_daily_analytics',
                'schedule': 86400.0,  # Daily
                'options': {'queue': 'analytics'}
            },
            'health-check': {
                'task': 'app.workers.cleanup_worker.health_check',
                'schedule': 300.0,  # Every 5 minutes
                'options': {'queue': 'cleanup'}
            },
        },
        
        # Error handling
        task_reject_on_worker_lost=True,
        task_ignore_result=False,
        
        # Development vs Production settings
        **_get_environment_config()
    )
    
    return celery_app


def _get_environment_config() -> Dict[str, Any]:
    """Get environment-specific Celery configuration."""
    if settings.is_production:
        return {
            'broker_connection_retry_on_startup': True,
            'broker_connection_retry': True,
            'broker_connection_max_retries': 10,
            'worker_log_level': 'INFO',
            'worker_hijack_root_logger': False,
        }
    else:
        return {
            'broker_connection_retry_on_startup': True,
            'broker_connection_retry': True,
            'broker_connection_max_retries': 3,
            'worker_log_level': 'DEBUG' if settings.debug else 'INFO',
            'worker_hijack_root_logger': False,
        }


# Create global Celery app instance
celery_app = create_celery_app()


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task class with common functionality."""
    
    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called on task success."""
        logger.info(
            f"Task {self.name} completed successfully",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
                "result": str(retval)[:200] if retval else None
            }
        )
    
    def on_failure(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: dict, 
        einfo: Any
    ) -> None:
        """Called on task failure."""
        logger.error(
            f"Task {self.name} failed",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
                "error": str(exc),
                "traceback": str(einfo)
            },
            exc_info=exc
        )
    
    def on_retry(
        self, 
        exc: Exception, 
        task_id: str, 
        args: tuple, 
        kwargs: dict, 
        einfo: Any
    ) -> None:
        """Called on task retry."""
        logger.warning(
            f"Task {self.name} retrying",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
                "error": str(exc),
                "retry_count": self.request.retries
            }
        )


# Set default task base class
celery_app.Task = BaseTask


# Celery signal handlers
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task prerun signal."""
    # Set correlation ID for logging
    set_correlation_id(task_id)
    
    logger.info(
        f"Starting task {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": args,
            "kwargs": kwargs
        }
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None, 
    task_id=None, 
    task=None, 
    args=None, 
    kwargs=None, 
    retval=None, 
    state=None, 
    **kwds
):
    """Handle task postrun signal."""
    logger.info(
        f"Task {task.name} finished with state {state}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "state": state,
            "args": args,
            "kwargs": kwargs
        }
    )


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info(
        "Celery worker is ready",
        extra={
            "worker_hostname": sender.hostname,
            "worker_pool": type(sender.pool).__name__,
            "worker_concurrency": sender.concurrency
        }
    )


# Utility functions for task management
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status information for a task.
    
    Args:
        task_id: Task ID to check
        
    Returns:
        Dict containing task status information
    """
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "state": result.state,
            "result": result.result,
            "traceback": result.traceback,
            "successful": result.successful(),
            "failed": result.failed(),
            "ready": result.ready(),
        }
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        return {
            "task_id": task_id,
            "state": "UNKNOWN",
            "error": str(e)
        }


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task.
    
    Args:
        task_id: Task ID to cancel
        
    Returns:
        bool: True if task was cancelled, False otherwise
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} cancelled")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        return False


def get_worker_stats() -> Dict[str, Any]:
    """
    Get worker statistics.
    
    Returns:
        Dict containing worker statistics
    """
    try:
        stats = celery_app.control.inspect().stats()
        active_tasks = celery_app.control.inspect().active()
        scheduled_tasks = celery_app.control.inspect().scheduled()
        reserved_tasks = celery_app.control.inspect().reserved()
        
        return {
            "stats": stats,
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
            "reserved_tasks": reserved_tasks,
        }
    except Exception as e:
        logger.error(f"Failed to get worker stats: {e}")
        return {"error": str(e)}


def purge_queue(queue_name: str) -> int:
    """
    Purge all tasks from a queue.
    
    Args:
        queue_name: Name of the queue to purge
        
    Returns:
        int: Number of tasks purged
    """
    try:
        return celery_app.control.purge()
    except Exception as e:
        logger.error(f"Failed to purge queue {queue_name}: {e}")
        return 0


# Auto-discovery of tasks
celery_app.autodiscover_tasks([
    'app.workers.email_worker',
    'app.workers.media_worker',
    'app.workers.analytics_worker',
    'app.workers.ai_worker',
    'app.workers.notification_worker',
    'app.workers.cleanup_worker'
])


# Initialize logging for workers
if not settings.is_testing:
    setup_logging()
