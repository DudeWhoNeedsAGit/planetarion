"""
Planetarion Configuration

Centralized configuration for the Planetarion game server.
Contains Flask configuration classes, speed settings, and utility functions.
"""

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

    # Use environment variable for database (allows central control)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:////home/yves/repos/planetarion/game-server/instance/test_e2e.db')

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

    # Production database (required) - moved to __init__ to avoid import-time validation
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # Production JWT secret (required)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Production Flask secret (required)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    def __init__(self):
        super().__init__()
        # Validate required production settings
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable is required in production")
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


# ============================================================================
# SPEED CONFIGURATION - Centralized speed settings for the game
# ============================================================================

# Global speed multiplier - adjust this to change overall game speed
SPEED_MULTIPLIER = 1.0

# Base ship speeds (units per hour at normal speed)
SHIP_SPEEDS = {
    'small_cargo': 5000,
    'large_cargo': 7500,
    'light_fighter': 12500,
    'heavy_fighter': 10000,
    'cruiser': 15000,
    'battleship': 10000,
    'colony_ship': 10000,  # Intentionally slow for strategic gameplay
    'recycler': 2000,
    'espionage_probe': 100000,  # Very fast for scouting
    'bomber': 4000,
    'destroyer': 5000,
    'deathstar': 100,
    'battlecruiser': 10000
}

# Fuel consumption rates (deuterium per unit distance)
FUEL_RATES = {
    'small_cargo': 1.0,
    'large_cargo': 1.5,
    'light_fighter': 1.0,
    'heavy_fighter': 2.0,
    'cruiser': 2.0,
    'battleship': 3.0,
    'colony_ship': 3.0,
    'recycler': 2.0,
    'espionage_probe': 1.0,
    'bomber': 3.0,
    'destroyer': 4.0,
    'deathstar': 5.0,
    'battlecruiser': 3.0
}

def get_ship_speed(ship_type):
    """Get the speed for a ship type with global multiplier applied"""
    base_speed = SHIP_SPEEDS.get(ship_type, 5000)
    return base_speed * SPEED_MULTIPLIER

def get_ship_fuel_rate(ship_type):
    """Get the fuel consumption rate for a ship type"""
    return FUEL_RATES.get(ship_type, 1.0)

def get_all_ship_speeds():
    """Get all ship speeds with multiplier applied"""
    return {ship_type: speed * SPEED_MULTIPLIER for ship_type, speed in SHIP_SPEEDS.items()}

def calculate_fleet_speed(fleet):
    """Calculate fleet speed (limited by slowest ship)"""
    if not fleet:
        return 0

    ship_types = ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter',
                 'cruiser', 'battleship', 'colony_ship', 'recycler', 'espionage_probe',
                 'bomber', 'destroyer', 'deathstar', 'battlecruiser']

    slowest_speed = float('inf')

    for ship_type in ship_types:
        if hasattr(fleet, ship_type):
            ship_count = getattr(fleet, ship_type, 0)
            if ship_count > 0:
                ship_speed = get_ship_speed(ship_type)
                slowest_speed = min(slowest_speed, ship_speed)

    return slowest_speed if slowest_speed != float('inf') else get_ship_speed('small_cargo')

def calculate_fuel_consumption(fleet, distance):
    """Calculate total fuel consumption for a fleet traveling a distance"""
    if not fleet or distance <= 0:
        return 0

    total_fuel = 0
    ship_types = ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter',
                 'cruiser', 'battleship', 'colony_ship', 'recycler', 'espionage_probe',
                 'bomber', 'destroyer', 'deathstar', 'battlecruiser']

    for ship_type in ship_types:
        if hasattr(fleet, ship_type):
            ship_count = getattr(fleet, ship_type, 0)
            if ship_count > 0:
                fuel_rate = get_ship_fuel_rate(ship_type)
                total_fuel += ship_count * fuel_rate * distance

    return int(total_fuel)

# Speed categories for reference
SPEED_CATEGORIES = {
    'very_fast': ['espionage_probe'],
    'fast': ['light_fighter', 'cruiser'],
    'medium': ['small_cargo', 'large_cargo', 'heavy_fighter', 'battleship', 'battlecruiser'],
    'slow': ['bomber', 'destroyer', 'recycler'],
    'very_slow': ['colony_ship', 'deathstar']
}

# Configuration validation
def validate_config():
    """Validate that all required ship types are defined"""
    required_ships = ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter',
                     'cruiser', 'battleship', 'colony_ship', 'recycler']

    missing_ships = []
    for ship in required_ships:
        if ship not in SHIP_SPEEDS:
            missing_ships.append(ship)

    if missing_ships:
        raise ValueError(f"Missing speed configuration for ships: {missing_ships}")

    return True

# Validate configuration on import
validate_config()
