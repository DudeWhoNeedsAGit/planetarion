"""
Planetarion Configuration

Centralized configuration for the Planetarion game server.
Contains Flask configuration classes, speed settings, and utility functions.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Repo-relative roots (avoid leaking local absolute paths in defaults/docs).
# config.py lives at: game-server/src/backend/config.py
GAME_SERVER_ROOT = Path(__file__).resolve().parents[2]
INSTANCE_DIR = GAME_SERVER_ROOT / "instance"

def _default_sqlite_uri(filename: str) -> str:
    return f"sqlite:////{(INSTANCE_DIR / filename).as_posix()}"

def get_min_travel_time_seconds():
    """Minimum fleet travel time in seconds.

    In testing (Playwright/pytest), we default to 0 so E2E flows don't depend on real-time waiting.
    Override with PLANETARION_MIN_TRAVEL_TIME_SECONDS when needed.
    """
    override = os.getenv('PLANETARION_MIN_TRAVEL_TIME_SECONDS')
    if override is not None and str(override).strip() != '':
        try:
            return max(0, int(override))
        except (TypeError, ValueError):
            pass

    if os.getenv('FLASK_ENV') == 'testing' or os.getenv('PYTEST_CURRENT_TEST'):
        return 0

    return 30


def get_forced_travel_time_seconds():
    """Optional forced travel time override (seconds).

    This is intended for E2E/CI runs where we want deterministic, fast fleet processing
    without waiting for real-time travel.
    """
    raw = os.getenv("PLANETARION_FORCED_TRAVEL_TIME_SECONDS")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return None

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
    # Automatic tick processing (server-side scheduler)
    #
    # Default behavior:
    # - development: scheduler starts automatically (see backend/app.py)
    # - testing: scheduler is OFF unless explicitly enabled via env var (keeps tests deterministic)
    TICK_SCHEDULER_ENABLED = os.getenv("PLANETARION_TICK_SCHEDULER_ENABLED", "").lower() in ("1", "true", "yes", "on")
    try:
        TICK_SCHEDULER_INTERVAL_SECONDS = max(0, int(os.getenv("PLANETARION_TICK_INTERVAL_SECONDS", "5")))
    except (TypeError, ValueError):
        TICK_SCHEDULER_INTERVAL_SECONDS = 5

    # Research MVP tuning
    # Tick scale in this project is accelerated (resources use divisor=72).
    RESEARCH_RP_PER_HOUR_PER_LAB_LEVEL = int(os.getenv("PLANETARION_RESEARCH_RP_PER_HOUR_PER_LAB_LEVEL", "10"))
    # Duration per target level (real-time seconds). Kept low in testing for fast feedback loops.
    try:
        RESEARCH_DURATION_SECONDS_PER_LEVEL = max(0, int(os.getenv("PLANETARION_RESEARCH_DURATION_SECONDS_PER_LEVEL", "60")))
    except (TypeError, ValueError):
        RESEARCH_DURATION_SECONDS_PER_LEVEL = 60

    # Pirate AI (Encounter Director) — disabled by default until tuned.
    PIRATE_AI_ENABLED = os.getenv("PLANETARION_PIRATE_AI_ENABLED", "").lower() in ("1", "true", "yes", "on")
    try:
        PIRATE_AI_INTERVAL_SECONDS = max(1, int(os.getenv("PLANETARION_PIRATE_AI_INTERVAL_SECONDS", "3600")))
    except (TypeError, ValueError):
        PIRATE_AI_INTERVAL_SECONDS = 3600
    try:
        PIRATE_AI_MAX_RAIDS_PER_24H = max(0, int(os.getenv("PLANETARION_PIRATE_AI_MAX_RAIDS_PER_24H", "2")))
    except (TypeError, ValueError):
        PIRATE_AI_MAX_RAIDS_PER_24H = 2
    try:
        PIRATE_AI_COOLDOWN_SECONDS = max(0, int(os.getenv("PLANETARION_PIRATE_AI_COOLDOWN_SECONDS", str(6 * 3600))))
    except (TypeError, ValueError):
        PIRATE_AI_COOLDOWN_SECONDS = 6 * 3600

    try:
        PIRATE_AI_PEAK_START_HOUR = int(os.getenv("PLANETARION_PIRATE_AI_PEAK_START_HOUR", "18"))
    except (TypeError, ValueError):
        PIRATE_AI_PEAK_START_HOUR = 18
    try:
        PIRATE_AI_PEAK_END_HOUR = int(os.getenv("PLANETARION_PIRATE_AI_PEAK_END_HOUR", "20"))
    except (TypeError, ValueError):
        PIRATE_AI_PEAK_END_HOUR = 20

    try:
        PIRATE_AI_PEAK_PROB_MULT = float(os.getenv("PLANETARION_PIRATE_AI_PEAK_PROB_MULT", "1.5"))
    except (TypeError, ValueError):
        PIRATE_AI_PEAK_PROB_MULT = 1.5
    try:
        PIRATE_AI_PEAK_POWER_MULT = float(os.getenv("PLANETARION_PIRATE_AI_PEAK_POWER_MULT", "1.25"))
    except (TypeError, ValueError):
        PIRATE_AI_PEAK_POWER_MULT = 1.25
    try:
        PIRATE_AI_DIFFICULTY_FACTOR = float(os.getenv("PLANETARION_PIRATE_AI_DIFFICULTY_FACTOR", "0.8"))
    except (TypeError, ValueError):
        PIRATE_AI_DIFFICULTY_FACTOR = 0.8

    # Deterministic RNG salt (falls back to SECRET_KEY if unset).
    PIRATE_AI_SECRET_SALT = os.getenv("PLANETARION_PIRATE_AI_SECRET_SALT")
    # Comma-separated NPC pirate faction usernames.
    PIRATE_FACTION_USERNAMES = os.getenv("PLANETARION_PIRATE_FACTION_USERNAMES", "pirates,pirates_red,pirates_black")
    # Pirate simulation (phase 2) - disabled by default for safe rollout.
    PIRATE_SIM_ENABLED = os.getenv("PLANETARION_PIRATE_SIM_ENABLED", "").lower() in ("1", "true", "yes", "on")
    PIRATE_SIM_EXPANSION_ENABLED = os.getenv("PLANETARION_PIRATE_SIM_EXPANSION_ENABLED", "1").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    try:
        PIRATE_SIM_EXPANSION_INTERVAL_SECONDS = max(
            60, int(os.getenv("PLANETARION_PIRATE_SIM_EXPANSION_INTERVAL_SECONDS", "7200"))
        )
    except (TypeError, ValueError):
        PIRATE_SIM_EXPANSION_INTERVAL_SECONDS = 7200
    try:
        PIRATE_SIM_PLANET_CAP_PER_FACTION = max(1, int(os.getenv("PLANETARION_PIRATE_SIM_PLANET_CAP_PER_FACTION", "6")))
    except (TypeError, ValueError):
        PIRATE_SIM_PLANET_CAP_PER_FACTION = 6
    try:
        PIRATE_SIM_PLANET_CAP_PER_Z_SLICE = max(1, int(os.getenv("PLANETARION_PIRATE_SIM_PLANET_CAP_PER_Z_SLICE", "3")))
    except (TypeError, ValueError):
        PIRATE_SIM_PLANET_CAP_PER_Z_SLICE = 3
    try:
        PIRATE_SIM_TOTAL_PLANET_CAP = max(1, int(os.getenv("PLANETARION_PIRATE_SIM_TOTAL_PLANET_CAP", "18")))
    except (TypeError, ValueError):
        PIRATE_SIM_TOTAL_PLANET_CAP = 18
    try:
        PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE = max(
            0, int(os.getenv("PLANETARION_PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE", "1200"))
        )
    except (TypeError, ValueError):
        PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE = 1200

    # Economy sinks (fleet upkeep lite) - disabled by default for safe rollout.
    ECONOMY_SINKS_ENABLED = os.getenv("PLANETARION_ECONOMY_SINKS_ENABLED", "").lower() in ("1", "true", "yes", "on")
    try:
        FLEET_UPKEEP_DEUTERIUM_PER_WEIGHT_PER_TICK = max(
            0.0, float(os.getenv("PLANETARION_FLEET_UPKEEP_DEUTERIUM_PER_WEIGHT_PER_TICK", "0.001"))
        )
    except (TypeError, ValueError):
        FLEET_UPKEEP_DEUTERIUM_PER_WEIGHT_PER_TICK = 0.001
    FLEET_UPKEEP_EXCLUDE_INVENTORY = os.getenv("PLANETARION_FLEET_UPKEEP_EXCLUDE_INVENTORY", "1").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


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
    FLASK_ENV = 'testing'

    # Use environment variable for database (allows central control)
    # IMPORTANT:
    # - `instance/test_e2e.db` is used for manual dev server + Playwright UI runs (make test-env / e2e-ui).
    # - pytest should NOT share that file, otherwise running tests will wipe your manual-play DB.
    # Keep pytest on a separate default DB file, while still allowing overrides via DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', _default_sqlite_uri("test_pytest.db"))

    # Test JWT secret
    JWT_SECRET_KEY = 'test-jwt-secret-key'

    # Disable CSRF in tests
    WTF_CSRF_ENABLED = False

    # Test database
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    # Keep the scheduler off by default in tests unless explicitly enabled
    # (prevents background tick side-effects during pytest runs).
    if not os.getenv("PLANETARION_TICK_SCHEDULER_ENABLED"):
        TICK_SCHEDULER_ENABLED = False

    # Faster research completion in tests/E2E.
    RESEARCH_DURATION_SECONDS_PER_LEVEL = int(os.getenv("PLANETARION_RESEARCH_DURATION_SECONDS_PER_LEVEL", "2"))


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
SPEED_MULTIPLIER = 30.0

# ============================================================================
# ECONOMY / STORAGE
# ============================================================================

# Storage caps are intentionally high because the test dataset starts with large resources.
BASE_STORAGE_CAPACITY = 10_000_000
STORAGE_GROWTH = 1.5


def calculate_storage_capacity(level: int) -> int:
    """Compute storage capacity for a given storage building level."""
    if level is None:
        level = 0
    try:
        level = int(level)
    except (TypeError, ValueError):
        level = 0
    level = max(level, 0)
    return int(BASE_STORAGE_CAPACITY * (STORAGE_GROWTH ** level))


def get_planet_storage_caps(planet) -> dict:
    """Return per-resource storage caps for a planet."""
    metal_level = getattr(planet, "metal_storage", 0) or 0
    crystal_level = getattr(planet, "crystal_storage", 0) or 0
    deut_level = getattr(planet, "deuterium_tank", 0) or 0
    return {
        "metal": calculate_storage_capacity(metal_level),
        "crystal": calculate_storage_capacity(crystal_level),
        "deuterium": calculate_storage_capacity(deut_level),
    }

# Base ship speeds (units per hour at normal speed)
SHIP_SPEEDS = {
    'small_cargo': 5000,
    'large_cargo': 7500,
    'light_fighter': 12500,
    'heavy_fighter': 10000,
    'cruiser': 15000,
    'battleship': 10000,
    'colony_ship': 2500,  # Slow for strategic gameplay
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

# ============================================================================
# COMPREHENSIVE SHIP STATISTICS - Combat, capacity, and role information
# ============================================================================

# Ship combat and capacity statistics
SHIP_STATS = {
    'small_cargo': {
        'firepower': 5,
        'defense': 10,
        'shield': 10,
        'cargo': 5000,
        'fuel': 10,
        'role': 'cargo',
        'description': 'Basic cargo ship for transporting resources'
    },
    'large_cargo': {
        'firepower': 5,
        'defense': 25,
        'shield': 25,
        'cargo': 25000,
        'fuel': 50,
        'role': 'cargo',
        'description': 'Advanced cargo ship with better capacity and defense'
    },
    'light_fighter': {
        'firepower': 50,
        'defense': 10,
        'shield': 10,
        'cargo': 50,
        'fuel': 20,
        'role': 'fighter',
        'description': 'Fast, cheap fighter for basic combat'
    },
    'heavy_fighter': {
        'firepower': 150,
        'defense': 25,
        'shield': 25,
        'cargo': 100,
        'fuel': 75,
        'role': 'fighter',
        'description': 'Heavy fighter with superior firepower'
    },
    'cruiser': {
        'firepower': 400,
        'defense': 50,
        'shield': 50,
        'cargo': 800,
        'fuel': 300,
        'role': 'capital',
        'description': 'Balanced capital ship for fleet operations'
    },
    'battleship': {
        'firepower': 1000,
        'defense': 200,
        'shield': 200,
        'cargo': 1500,
        'fuel': 500,
        'role': 'capital',
        'description': 'Heavy battleship with massive firepower'
    },
    'colony_ship': {
        'firepower': 50,
        'defense': 100,
        'shield': 100,
        'cargo': 7500,
        'fuel': 1000,
        'role': 'special',
        'description': 'Specialized ship for establishing new colonies'
    },
    'recycler': {
        'firepower': 1,
        'defense': 10,
        'shield': 10,
        'cargo': 20000,
        'fuel': 300,
        'role': 'special',
        'description': 'Ship designed to collect debris from battlefields'
    },
    'espionage_probe': {
        'firepower': 0,
        'defense': 1,
        'shield': 1,
        'cargo': 5,
        'fuel': 1,
        'role': 'special',
        'description': 'Fast reconnaissance ship for gathering intelligence'
    },
    'bomber': {
        'firepower': 1000,
        'defense': 75,
        'shield': 50,
        'cargo': 500,
        'fuel': 700,
        'role': 'bomber',
        'description': 'Heavy bomber specialized in destroying planetary defenses'
    },
    'destroyer': {
        'firepower': 1100,
        'defense': 110,
        'shield': 50,
        'cargo': 2000,
        'fuel': 1000,
        'role': 'capital',
        'description': 'Advanced destroyer with rapid fire capabilities'
    },
    'deathstar': {
        'firepower': 200000,
        'defense': 50000,
        'shield': 50000,
        'cargo': 1000000,
        'fuel': 1000,
        'role': 'ultimate',
        'description': 'Ultimate weapon capable of destroying entire planets'
    },
    'battlecruiser': {
        'firepower': 700,
        'defense': 400,
        'shield': 400,
        'cargo': 750,
        'fuel': 250,
        'role': 'capital',
        'description': 'Elite capital ship with exceptional combat capabilities'
    }
}

# ============================================================================
# COMBAT SHIP STATS - Used by CombatEngine (single source of truth)
# ============================================================================

# Note: This is intentionally separate from SHIP_STATS above; SHIP_STATS is a broader
# "game design" view (firepower/defense/shield/cargo/etc). CombatEngine uses a
# hull/shield/weapon model.
COMBAT_SHIP_STATS = {
    'small_cargo': {'hull': 4000, 'shield': 10, 'weapon': 5, 'speed': 5000, 'cargo': 5000, 'fuel': 10},
    'large_cargo': {'hull': 12000, 'shield': 25, 'weapon': 5, 'speed': 7500, 'cargo': 25000, 'fuel': 50},
    'light_fighter': {'hull': 4000, 'shield': 10, 'weapon': 50, 'speed': 12500, 'cargo': 50, 'fuel': 20},
    'heavy_fighter': {'hull': 10000, 'shield': 25, 'weapon': 150, 'speed': 10000, 'cargo': 100, 'fuel': 75},
    'cruiser': {'hull': 27000, 'shield': 50, 'weapon': 400, 'speed': 15000, 'cargo': 800, 'fuel': 300},
    'battleship': {'hull': 60000, 'shield': 200, 'weapon': 1000, 'speed': 10000, 'cargo': 1500, 'fuel': 500},
    'colony_ship': {'hull': 30000, 'shield': 100, 'weapon': 50, 'speed': 2500, 'cargo': 7500, 'fuel': 1000},
}

def get_ship_speed(ship_type):
    """Get the speed for a ship type with global multiplier applied"""
    base_speed = SHIP_SPEEDS.get(ship_type, 5000)
    return base_speed * SPEED_MULTIPLIER

def get_ship_fuel_rate(ship_type):
    """Get the fuel consumption rate for a ship type"""
    return FUEL_RATES.get(ship_type, 1.0)

def get_ship_stats(ship_type):
    """Get comprehensive statistics for a ship type"""
    return SHIP_STATS.get(ship_type, {})

def get_all_ship_stats():
    """Get statistics for all ship types"""
    return SHIP_STATS

def get_ships_by_role(role):
    """Get all ships of a specific role (cargo, fighter, capital, special, etc.)"""
    return {ship_type: stats for ship_type, stats in SHIP_STATS.items() if stats.get('role') == role}

def get_ship_roles():
    """Get all available ship roles"""
    roles = set()
    for stats in SHIP_STATS.values():
        roles.add(stats.get('role', 'unknown'))
    return sorted(list(roles))

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
            try:
                ship_count = int(ship_count)
            except (TypeError, ValueError):
                ship_count = 0
            if ship_count > 0:
                ship_speed = get_ship_speed(ship_type)
                slowest_speed = min(slowest_speed, ship_speed)

    return slowest_speed if slowest_speed != float('inf') else 0

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
            try:
                ship_count = int(ship_count)
            except (TypeError, ValueError):
                ship_count = 0
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
