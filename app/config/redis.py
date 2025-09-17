"""
Redis configuration for caching, sessions, and Celery backend.
"""
from typing import Optional, Dict, Any
import redis
from redis.connection import ConnectionPool
import json
import pickle
import logging
from datetime import timedelta

from .settings import settings

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration and connection management."""
    
    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
    
    @property
    def connection_pool(self) -> ConnectionPool:
        """Get or create Redis connection pool."""
        if self._connection_pool is None:
            self._connection_pool = self._create_connection_pool()
        return self._connection_pool
    
    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._redis_client
    
    def _create_connection_pool(self) -> ConnectionPool:
        """Create Redis connection pool with optimized settings."""
        # Parse Redis URL
        redis_url = settings.redis_url
        
        pool_kwargs = {
            "max_connections": 50,
            "retry_on_timeout": True,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "health_check_interval": 30,
        }
        
        # Add password if configured
        if settings.redis_password:
            pool_kwargs["password"] = settings.redis_password
        
        # Production optimizations
        if settings.is_production:
            pool_kwargs.update({
                "max_connections": 100,
                "socket_connect_timeout": 10,
                "socket_timeout": 10,
            })
        
        pool = ConnectionPool.from_url(redis_url, **pool_kwargs)
        
        logger.info(
            f"Redis connection pool created with max_connections={pool_kwargs['max_connections']}"
        )
        
        return pool
    
    def get_cache_client(self) -> redis.Redis:
        """Get Redis client for caching operations."""
        return self.client
    
    def get_session_client(self) -> redis.Redis:
        """Get Redis client for session storage."""
        # Use different DB for sessions
        return redis.Redis(
            connection_pool=self.connection_pool,
            db=1,
            decode_responses=True
        )
    
    def get_celery_broker_client(self) -> redis.Redis:
        """Get Redis client for Celery broker."""
        # Use different DB for Celery broker
        return redis.Redis(
            connection_pool=self.connection_pool,
            db=2,
            decode_responses=False  # Celery needs binary data
        )
    
    def health_check(self) -> bool:
        """
        Check Redis connectivity and health.
        
        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        try:
            response = self.client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get Redis connection information for monitoring.
        
        Returns:
            Dict[str, Any]: Connection and memory statistics
        """
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis connection info: {e}")
            return {}
    
    def clear_cache(self, pattern: str = "*") -> int:
        """
        Clear cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern to match
            
        Returns:
            int: Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0


class CacheManager:
    """High-level cache operations using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_timeout = 3600  # 1 hour
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Any: Cached value or default
        """
        try:
            value = self.redis.get(key)
            if value is None:
                return default
            return json.loads(value)
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return default
    
    def set(
        self, 
        key: str, 
        value: Any, 
        timeout: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Expiration time in seconds
            nx: Set only if key doesn't exist
            
        Returns:
            bool: True if set successfully, False otherwise
        """
        try:
            timeout = timeout or self.default_timeout
            serialized_value = json.dumps(value, default=str)
            return self.redis.setex(key, timeout, serialized_value)
        except (json.JSONEncodeError, redis.RedisError) as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            return bool(self.redis.delete(key))
        except redis.RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        try:
            return bool(self.redis.exists(key))
        except redis.RedisError as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def expire(self, key: str, timeout: int) -> bool:
        """
        Set expiration for existing key.
        
        Args:
            key: Cache key
            timeout: Expiration time in seconds
            
        Returns:
            bool: True if expiration set, False otherwise
        """
        try:
            return bool(self.redis.expire(key, timeout))
        except redis.RedisError as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            Optional[int]: New value or None if error
        """
        try:
            return self.redis.incrby(key, amount)
        except redis.RedisError as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def set_hash(self, key: str, mapping: Dict[str, Any], timeout: Optional[int] = None) -> bool:
        """
        Set hash value in cache.
        
        Args:
            key: Cache key
            mapping: Dictionary to store as hash
            timeout: Expiration time in seconds
            
        Returns:
            bool: True if set successfully, False otherwise
        """
        try:
            # Serialize values in mapping
            serialized_mapping = {
                k: json.dumps(v, default=str) for k, v in mapping.items()
            }
            
            success = self.redis.hset(key, mapping=serialized_mapping)
            
            if timeout:
                self.redis.expire(key, timeout)
            
            return success
        except (json.JSONEncodeError, redis.RedisError) as e:
            logger.error(f"Cache set_hash error for key {key}: {e}")
            return False
    
    def get_hash(self, key: str, field: Optional[str] = None) -> Any:
        """
        Get hash value from cache.
        
        Args:
            key: Cache key
            field: Specific field to get (if None, returns entire hash)
            
        Returns:
            Any: Hash value or field value
        """
        try:
            if field:
                value = self.redis.hget(key, field)
                if value is None:
                    return None
                return json.loads(value)
            else:
                hash_data = self.redis.hgetall(key)
                return {
                    k: json.loads(v) for k, v in hash_data.items()
                }
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Cache get_hash error for key {key}: {e}")
            return None
    
    def add_to_set(self, key: str, *values: Any, timeout: Optional[int] = None) -> int:
        """
        Add values to a set in cache.
        
        Args:
            key: Cache key
            values: Values to add to set
            timeout: Expiration time in seconds
            
        Returns:
            int: Number of elements added
        """
        try:
            serialized_values = [json.dumps(v, default=str) for v in values]
            result = self.redis.sadd(key, *serialized_values)
            
            if timeout:
                self.redis.expire(key, timeout)
            
            return result
        except (json.JSONEncodeError, redis.RedisError) as e:
            logger.error(f"Cache add_to_set error for key {key}: {e}")
            return 0
    
    def get_set_members(self, key: str) -> set:
        """
        Get all members of a set from cache.
        
        Args:
            key: Cache key
            
        Returns:
            set: Set members
        """
        try:
            members = self.redis.smembers(key)
            return {json.loads(member) for member in members}
        except (json.JSONDecodeError, redis.RedisError) as e:
            logger.error(f"Cache get_set_members error for key {key}: {e}")
            return set()


class SessionManager:
    """Session management using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.session_timeout = 86400  # 24 hours
        self.session_prefix = "session:"
    
    def create_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Create new user session.
        
        Args:
            session_id: Unique session identifier
            user_data: User session data
            
        Returns:
            bool: True if session created, False otherwise
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = {
                **user_data,
                "created_at": str(datetime.utcnow()),
                "last_accessed": str(datetime.utcnow())
            }
            
            serialized_data = json.dumps(session_data, default=str)
            return self.redis.setex(session_key, self.session_timeout, serialized_data)
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if not found
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.redis.get(session_key)
            
            if session_data is None:
                return None
            
            data = json.loads(session_data)
            
            # Update last accessed time
            data["last_accessed"] = str(datetime.utcnow())
            self.redis.setex(session_key, self.session_timeout, json.dumps(data, default=str))
            
            return data
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            return bool(self.redis.delete(session_key))
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def extend_session(self, session_id: str, timeout: Optional[int] = None) -> bool:
        """
        Extend session expiration.
        
        Args:
            session_id: Session identifier
            timeout: New timeout in seconds
            
        Returns:
            bool: True if extended, False otherwise
        """
        try:
            session_key = f"{self.session_prefix}{session_id}"
            timeout = timeout or self.session_timeout
            return bool(self.redis.expire(session_key, timeout))
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False


# Global Redis configuration instance
redis_config = RedisConfig()

# Convenience functions for direct access
def get_redis_client() -> redis.Redis:
    """Get Redis client for general use."""
    return redis_config.client

def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    return CacheManager(redis_config.get_cache_client())

def get_session_manager() -> SessionManager:
    """Get session manager instance."""
    return SessionManager(redis_config.get_session_client())
