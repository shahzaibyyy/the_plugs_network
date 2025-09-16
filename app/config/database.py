"""
Database configuration with connection pooling and session management.
"""
from typing import Generator, Optional
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from .settings import settings

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    @property
    def engine(self) -> Engine:
        """Get or create database engine with connection pooling."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with optimized connection pooling."""
        engine_kwargs = {
            "url": settings.database_url,
            "echo": settings.database_echo,
            "poolclass": QueuePool,
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
            "pool_recycle": settings.database_pool_recycle,
            "pool_pre_ping": True,  # Validate connections before use
        }
        
        # Additional production optimizations
        if settings.is_production:
            engine_kwargs.update({
                "pool_reset_on_return": "commit",
                "connect_args": {
                    "connect_timeout": 10,
                    "application_name": settings.app_name,
                }
            })
        
        engine = create_engine(**engine_kwargs)
        
        # Add connection event listeners
        self._setup_engine_events(engine)
        
        logger.info(
            f"Database engine created with pool_size={settings.database_pool_size}, "
            f"max_overflow={settings.database_max_overflow}"
        )
        
        return engine
    
    def _setup_engine_events(self, engine: Engine) -> None:
        """Setup database engine event listeners for monitoring and optimization."""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for development/testing."""
            if "sqlite" in settings.database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring."""
            if settings.debug:
                logger.debug("Connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin for monitoring."""
            if settings.debug:
                logger.debug("Connection checked in to pool")
    
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with proper lifecycle management.
        
        This method is primarily for internal use. For FastAPI dependency injection,
        use the dependencies in app.core.dependencies instead.
        
        Yields:
            Session: SQLAlchemy database session
        """
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self) -> None:
        """Create all database tables."""
        try:
            # Import BaseModel to ensure metadata is available
            from app.models.base import BaseModel
            BaseModel.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        try:
            # Import BaseModel to ensure metadata is available
            from app.models.base import BaseModel
            BaseModel.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check database connectivity and health.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get database connection information for monitoring.
        
        Returns:
            dict: Connection pool statistics
        """
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }


# Global database configuration instance
db_config = DatabaseConfig()

# Convenience function for direct access (use dependencies for FastAPI)
def get_database_engine() -> Engine:
    """Get database engine instance."""
    return db_config.engine