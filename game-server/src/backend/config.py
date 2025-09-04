import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///instance/test.db')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')

    # Flask configuration
    DEBUG = False
    TESTING = False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

    # CORS configuration
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Scheduler configuration
    SCHEDULER_TIMEZONE = "UTC"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

    # Allow all origins in development
    CORS_ORIGINS = ["*"]

    # Development database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/dev.db')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Test JWT secret
    JWT_SECRET_KEY = 'test-jwt-secret-key'

    # Disable CSRF in tests
    WTF_CSRF_ENABLED = False

    # Test database
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Production CORS origins
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')

    # Production database (required)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required in production")

    # Production JWT secret (required)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Production Flask secret (required)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    def __init__(self):
        super().__init__()
        # Validate required production settings
        if self.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
            raise ValueError("JWT_SECRET_KEY must be set in production")
        if self.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])
