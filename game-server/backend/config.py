import os
from pathlib import Path
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


# Project root - single source of truth
PROJECT_ROOT = Path(__file__).parent.parent

# All important paths defined centrally
PATHS = {
    # Core directories
    'project_root': PROJECT_ROOT,
    'src': PROJECT_ROOT / 'src',
    'backend': PROJECT_ROOT / 'src' / 'backend',
    'frontend': PROJECT_ROOT / 'src' / 'frontend',
    'database': PROJECT_ROOT / 'src' / 'database',
    'tests': PROJECT_ROOT / 'src' / 'tests',
    'scripts': PROJECT_ROOT / 'scripts',

    # Frontend build paths
    'frontend_build': PROJECT_ROOT / 'src' / 'frontend' / 'build',
    'frontend_static': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static',
    'frontend_css': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static' / 'css',
    'frontend_js': PROJECT_ROOT / 'src' / 'frontend' / 'build' / 'static' / 'js',

    # Backend paths
    'backend_routes': PROJECT_ROOT / 'src' / 'backend' / 'routes',
    'backend_services': PROJECT_ROOT / 'src' / 'backend' / 'services',
    'backend_templates': PROJECT_ROOT / 'src' / 'backend' / 'templates',

    # Test paths
    'unit_tests': PROJECT_ROOT / 'src' / 'tests' / 'unit',
    'integration_tests': PROJECT_ROOT / 'src' / 'tests' / 'integration',

    # Docker and deployment
    'dockerfiles': PROJECT_ROOT / 'src' / 'backend' / 'Dockerfile',
    'docker_compose': PROJECT_ROOT / 'docker-compose.yml',
}
