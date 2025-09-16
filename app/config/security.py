"""
Security configuration for JWT authentication and CORS.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, status
import secrets
import hashlib
import hmac

from .settings import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token scheme
security_scheme = HTTPBearer(auto_error=False)


class SecurityConfig:
    """Security configuration and utilities."""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            data: Token payload data
            expires_delta: Optional custom expiration time
            
        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            str: Hex-encoded secure token
        """
        return secrets.token_hex(length)
    
    def generate_api_key(self, user_id: str, prefix: str = "pk") -> str:
        """
        Generate API key for user.
        
        Args:
            user_id: User identifier
            prefix: API key prefix
            
        Returns:
            str: Generated API key
        """
        random_part = self.generate_secure_token(16)
        return f"{prefix}_{user_id}_{random_part}"
    
    def verify_api_key_signature(self, api_key: str, expected_user_id: str) -> bool:
        """
        Verify API key signature.
        
        Args:
            api_key: API key to verify
            expected_user_id: Expected user ID
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            parts = api_key.split("_")
            if len(parts) != 3:
                return False
            
            prefix, user_id, signature = parts
            return user_id == expected_user_id
            
        except Exception:
            return False
    
    def create_hmac_signature(self, data: str, key: Optional[str] = None) -> str:
        """
        Create HMAC signature for data.
        
        Args:
            data: Data to sign
            key: Optional signing key (uses secret_key if not provided)
            
        Returns:
            str: HMAC signature
        """
        signing_key = key or self.secret_key
        return hmac.new(
            signing_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_hmac_signature(
        self, 
        data: str, 
        signature: str, 
        key: Optional[str] = None
    ) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            data: Original data
            signature: Signature to verify
            key: Optional signing key (uses secret_key if not provided)
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        expected_signature = self.create_hmac_signature(data, key)
        return hmac.compare_digest(signature, expected_signature)


class CORSConfig:
    """CORS configuration for FastAPI."""
    
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """
        Get CORS configuration for FastAPI CORSMiddleware.
        
        Returns:
            Dict[str, Any]: CORS configuration parameters
        """
        return {
            "allow_origins": settings.cors_origins,
            "allow_credentials": settings.cors_credentials,
            "allow_methods": settings.cors_methods,
            "allow_headers": settings.cors_headers,
            "expose_headers": ["X-Request-ID", "X-Correlation-ID"],
            "max_age": 86400,  # 24 hours
        }
    
    @staticmethod
    def is_origin_allowed(origin: str) -> bool:
        """
        Check if origin is allowed by CORS policy.
        
        Args:
            origin: Origin to check
            
        Returns:
            bool: True if origin is allowed, False otherwise
        """
        if "*" in settings.cors_origins:
            return True
        
        return origin in settings.cors_origins


class RateLimitConfig:
    """Rate limiting configuration."""
    
    @staticmethod
    def get_rate_limit_key(identifier: str, endpoint: str) -> str:
        """
        Generate rate limit key for Redis.
        
        Args:
            identifier: User/IP identifier
            endpoint: API endpoint
            
        Returns:
            str: Rate limit key
        """
        return f"rate_limit:{identifier}:{endpoint}"
    
    @staticmethod
    def get_default_limits() -> Dict[str, Dict[str, int]]:
        """
        Get default rate limits by endpoint type.
        
        Returns:
            Dict[str, Dict[str, int]]: Rate limit configuration
        """
        if settings.is_production:
            return {
                "auth": {"requests": 5, "window": 60},  # 5 requests per minute
                "api": {"requests": 100, "window": 60},  # 100 requests per minute
                "upload": {"requests": 10, "window": 60},  # 10 uploads per minute
            }
        else:
            return {
                "auth": {"requests": 20, "window": 60},
                "api": {"requests": 1000, "window": 60},
                "upload": {"requests": 50, "window": 60},
            }


# Global security configuration instance
security_config = SecurityConfig()
cors_config = CORSConfig()
rate_limit_config = RateLimitConfig()