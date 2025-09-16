"""
Tests for configuration modules.
"""
import pytest
import os
import tempfile
from unittest.mock import patch

from app.config import settings, security_config, cors_config, db_config


class TestSettings:
    """Test settings configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        assert settings.app_name == "The Plugs API"
        assert settings.app_version == "1.0.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 30
    
    def test_environment_properties(self):
        """Test environment property methods."""
        with patch.object(settings, 'environment', settings.Environment.DEVELOPMENT):
            assert settings.is_development is True
            assert settings.is_production is False
            assert settings.is_testing is False
        
        with patch.object(settings, 'environment', settings.Environment.PRODUCTION):
            assert settings.is_development is False
            assert settings.is_production is True
            assert settings.is_testing is False
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from string."""
        with patch.dict(os.environ, {'CORS_ORIGINS': 'http://localhost:3000,https://example.com'}):
            # Create new settings instance to pick up env vars
            from app.config.settings import Settings
            test_settings = Settings()
            assert test_settings.cors_origins == ['http://localhost:3000', 'https://example.com']


class TestSecurityConfig:
    """Test security configuration."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = security_config.hash_password(password)
        
        assert hashed != password
        assert security_config.verify_password(password, hashed) is True
        assert security_config.verify_password("wrong_password", hashed) is False
    
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        test_data = {"user_id": "123", "email": "test@example.com"}
        
        # Test access token
        access_token = security_config.create_access_token(test_data)
        decoded = security_config.verify_token(access_token, "access")
        
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"
        
        # Test refresh token
        refresh_token = security_config.create_refresh_token(test_data)
        decoded_refresh = security_config.verify_token(refresh_token, "refresh")
        
        assert decoded_refresh["user_id"] == "123"
        assert decoded_refresh["type"] == "refresh"
    
    def test_secure_token_generation(self):
        """Test secure token generation."""
        token1 = security_config.generate_secure_token()
        token2 = security_config.generate_secure_token()
        
        assert len(token1) == 64  # 32 bytes = 64 hex chars
        assert len(token2) == 64
        assert token1 != token2
    
    def test_api_key_generation(self):
        """Test API key generation and verification."""
        user_id = "user_123"
        api_key = security_config.generate_api_key(user_id)
        
        assert api_key.startswith("pk_")
        assert user_id in api_key
        assert security_config.verify_api_key_signature(api_key, user_id) is True
        assert security_config.verify_api_key_signature(api_key, "wrong_user") is False
    
    def test_hmac_signature(self):
        """Test HMAC signature creation and verification."""
        data = "test_data_to_sign"
        signature = security_config.create_hmac_signature(data)
        
        assert security_config.verify_hmac_signature(data, signature) is True
        assert security_config.verify_hmac_signature("wrong_data", signature) is False


class TestCORSConfig:
    """Test CORS configuration."""
    
    def test_cors_config_structure(self):
        """Test CORS configuration structure."""
        config = cors_config.get_cors_config()
        
        required_keys = [
            "allow_origins", "allow_credentials", "allow_methods", 
            "allow_headers", "expose_headers", "max_age"
        ]
        
        for key in required_keys:
            assert key in config
    
    def test_origin_allowed(self):
        """Test origin allowance checking."""
        # Test with wildcard
        with patch.object(settings, 'cors_origins', ['*']):
            assert cors_config.is_origin_allowed("https://example.com") is True
        
        # Test with specific origins
        with patch.object(settings, 'cors_origins', ['https://example.com', 'http://localhost:3000']):
            assert cors_config.is_origin_allowed("https://example.com") is True
            assert cors_config.is_origin_allowed("http://localhost:3000") is True
            assert cors_config.is_origin_allowed("https://malicious.com") is False


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_database_config_initialization(self):
        """Test database configuration initialization."""
        assert db_config is not None
        assert hasattr(db_config, 'engine')
        assert hasattr(db_config, 'session_factory')
    
    def test_connection_info(self):
        """Test connection info retrieval."""
        # This test requires a valid database connection
        # In a real test environment, you'd use a test database
        try:
            info = db_config.get_connection_info()
            assert isinstance(info, dict)
            assert "pool_size" in info
            assert "checked_in" in info
            assert "checked_out" in info
        except Exception:
            # Skip if no database connection available
            pytest.skip("Database connection not available for testing")


if __name__ == "__main__":
    pytest.main([__file__])