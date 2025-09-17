"""
Cleanup worker for maintenance tasks.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from sqlalchemy import text
from .celery_app import celery_app
from app.config.database import db_config
from app.config.redis import redis_config

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_old_data(self) -> Dict[str, Any]:
    """
    Clean up old data from the database.
    
    Returns:
        Dict with cleanup results
    """
    try:
        results = {
            "deleted_records": 0,
            "cleaned_tables": [],
            "errors": []
        }
        
        # Define cleanup rules (days to keep data)
        cleanup_rules = {
            "audit_logs": 90,  # Keep audit logs for 90 days
            "user_sessions": 30,  # Keep user sessions for 30 days
            "temporary_files": 7,  # Keep temporary files for 7 days
            "expired_tokens": 1,  # Clean expired tokens daily
        }
        
        with db_config.get_session() as session:
            for table, days_to_keep in cleanup_rules.items():
                try:
                    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                    
                    # Example cleanup queries (adjust based on actual schema)
                    if table == "audit_logs":
                        query = text("""
                            DELETE FROM audit_logs 
                            WHERE created_at < :cutoff_date 
                            AND is_deleted = true
                        """)
                    elif table == "user_sessions":
                        query = text("""
                            DELETE FROM user_sessions 
                            WHERE created_at < :cutoff_date
                            OR expires_at < :now
                        """)
                    elif table == "temporary_files":
                        query = text("""
                            DELETE FROM temporary_files 
                            WHERE created_at < :cutoff_date
                        """)
                    elif table == "expired_tokens":
                        query = text("""
                            DELETE FROM refresh_tokens 
                            WHERE expires_at < :now
                        """)
                    else:
                        continue
                    
                    result = session.execute(
                        query, 
                        {
                            "cutoff_date": cutoff_date,
                            "now": datetime.utcnow()
                        }
                    )
                    
                    deleted_count = result.rowcount
                    results["deleted_records"] += deleted_count
                    results["cleaned_tables"].append({
                        "table": table,
                        "deleted_count": deleted_count
                    })
                    
                    logger.info(f"Cleaned {deleted_count} records from {table}")
                    
                except Exception as e:
                    error_msg = f"Failed to clean {table}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            session.commit()
        
        logger.info(f"Cleanup completed: {results['deleted_records']} total records cleaned")
        return results
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise


@celery_app.task(bind=True)
def cleanup_redis_cache(self) -> Dict[str, Any]:
    """
    Clean up expired Redis cache entries.
    
    Returns:
        Dict with cleanup results
    """
    try:
        redis_client = redis_config.client
        
        # Get cache statistics before cleanup
        info_before = redis_client.info("memory")
        
        # Clean up expired keys (Redis does this automatically, but we can force it)
        # Remove keys with specific patterns that are old
        patterns_to_clean = [
            "cache:temp:*",
            "session:expired:*",
            "rate_limit:old:*"
        ]
        
        total_deleted = 0
        
        for pattern in patterns_to_clean:
            keys = redis_client.keys(pattern)
            if keys:
                deleted = redis_client.delete(*keys)
                total_deleted += deleted
                logger.info(f"Deleted {deleted} keys matching pattern {pattern}")
        
        # Get cache statistics after cleanup
        info_after = redis_client.info("memory")
        
        results = {
            "deleted_keys": total_deleted,
            "memory_before": info_before.get("used_memory", 0),
            "memory_after": info_after.get("used_memory", 0),
            "memory_saved": info_before.get("used_memory", 0) - info_after.get("used_memory", 0)
        }
        
        logger.info(f"Redis cleanup completed: {total_deleted} keys deleted")
        return results
        
    except Exception as e:
        logger.error(f"Redis cleanup task failed: {e}")
        raise


@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """
    Perform system health check.
    
    Returns:
        Dict with health status
    """
    try:
        health_results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check database health
        try:
            db_healthy = db_config.health_check()
            health_results["checks"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection_info": db_config.get_connection_info() if db_healthy else None
            }
        except Exception as e:
            health_results["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_results["status"] = "degraded"
        
        # Check Redis health
        try:
            redis_healthy = redis_config.health_check()
            health_results["checks"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connection_info": redis_config.get_connection_info() if redis_healthy else None
            }
        except Exception as e:
            health_results["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_results["status"] = "degraded"
        
        # Check Celery worker health
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            worker_stats = inspect.stats()
            
            health_results["checks"]["celery"] = {
                "status": "healthy" if active_workers else "unhealthy",
                "active_workers": len(active_workers) if active_workers else 0,
                "worker_stats": worker_stats
            }
            
            if not active_workers:
                health_results["status"] = "degraded"
                
        except Exception as e:
            health_results["checks"]["celery"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_results["status"] = "degraded"
        
        logger.info(f"Health check completed: {health_results['status']}")
        return health_results
        
    except Exception as e:
        logger.error(f"Health check task failed: {e}")
        raise


@celery_app.task(bind=True)
def archive_old_files(self) -> Dict[str, Any]:
    """
    Archive old files to cold storage.
    
    Returns:
        Dict with archival results
    """
    try:
        # TODO: Implement file archival logic
        # This would typically:
        # 1. Find files older than certain threshold
        # 2. Move them to archive storage (S3 Glacier, etc.)
        # 3. Update database records
        # 4. Clean up local storage
        
        results = {
            "archived_files": 0,
            "freed_space": 0,
            "errors": []
        }
        
        logger.info("File archival task completed (not implemented)")
        return results
        
    except Exception as e:
        logger.error(f"File archival task failed: {e}")
        raise


@celery_app.task(bind=True)
def vacuum_database(self) -> Dict[str, Any]:
    """
    Perform database maintenance (VACUUM, ANALYZE).
    
    Returns:
        Dict with maintenance results
    """
    try:
        results = {
            "status": "completed",
            "operations": [],
            "errors": []
        }
        
        with db_config.get_session() as session:
            try:
                # PostgreSQL specific maintenance
                if "postgresql" in str(db_config.engine.url):
                    # Run ANALYZE to update table statistics
                    session.execute(text("ANALYZE;"))
                    results["operations"].append("ANALYZE completed")
                    
                    # Note: VACUUM cannot be run inside a transaction
                    # It would need to be run separately with autocommit
                    
                elif "sqlite" in str(db_config.engine.url):
                    # SQLite specific maintenance
                    session.execute(text("VACUUM;"))
                    session.execute(text("ANALYZE;"))
                    results["operations"].append("VACUUM and ANALYZE completed")
                
                session.commit()
                
            except Exception as e:
                error_msg = f"Database maintenance failed: {str(e)}"
                results["errors"].append(error_msg)
                results["status"] = "failed"
                logger.error(error_msg)
        
        logger.info(f"Database maintenance completed: {results['status']}")
        return results
        
    except Exception as e:
        logger.error(f"Database maintenance task failed: {e}")
        raise
