import pytest
import os
import requests
from datetime import datetime, timedelta

import sys
import os

# Add the src directory to the path so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.app import create_app
from backend.database import db
from backend.models import User, Planet, Fleet, Alliance, TickLog

@pytest.fixture
def app():
    """Create and configure a test app instance using our new app factory."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Provide a database session for tests."""
    with app.app_context():
        yield db.session
        db.session.rollback()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    import bcrypt
    # Hash the password 'testpassword' with bcrypt
    password_hash = bcrypt.hashpw('testpassword'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=password_hash
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_planet(db_session, sample_user):
    """Create a sample planet for testing."""
    planet = Planet(
        name='Test Planet',
        x=100,
        y=200,
        z=300,
        user_id=sample_user.id,
        metal=10000,
        crystal=5000,
        deuterium=2000,
        # Add ships for fleet testing - sufficient for all test scenarios including max ships test
        small_cargo=2000000,  # Enough for test_create_fleet_max_ships (needs 1M) + buffer
        large_cargo=1000000,  # Enough for test_create_fleet_max_ships (needs 500K) + buffer
        light_fighter=400000, # Enough for test_create_fleet_max_ships (needs 200K) + buffer
        heavy_fighter=200000, # Enough for test_create_fleet_max_ships (needs 100K) + buffer
        cruiser=100000,       # Enough for test_create_fleet_max_ships (needs 50K) + buffer
        battleship=50000,     # Enough for test_create_fleet_max_ships (needs 10K) + buffer
        colony_ship=100       # For colonization tests
    )
    db_session.add(planet)
    db_session.commit()
    return planet

@pytest.fixture
def sample_fleet(db_session, sample_user, sample_planet):
    """Create a sample fleet for testing."""
    now = datetime.utcnow()
    fleet = Fleet(
        user_id=sample_user.id,
        mission='attack',
        start_planet_id=sample_planet.id,
        target_planet_id=sample_planet.id,
        small_cargo=10,
        large_cargo=5,
        light_fighter=20,
        departure_time=now,
        arrival_time=now + timedelta(hours=1),
        eta=3600
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet

@pytest.fixture
def sample_alliance(db_session, sample_user):
    """Create a sample alliance for testing."""
    alliance = Alliance(
        name='Test Alliance',
        description='Test alliance for unit tests',
        leader_id=sample_user.id,
    )
    db_session.add(alliance)
    db_session.commit()
    return alliance

# === PHASE 4: BACKEND-FRONTEND INTERACTION TESTING HELPERS ===

def login_as_test_user(backend_url="http://localhost:5000", username="e2etestuser", password="testpassword123"):
    """Helper function to authenticate and get JWT token for testing"""
    import requests

    login_url = f"{backend_url}/api/auth/login"
    login_data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()

        data = response.json()
        token = data.get('token') or data.get('access_token')

        if not token:
            raise ValueError(f"No token found in login response: {data}")

        return {
            'token': token,
            'user': data.get('user', {}),
            'headers': {'Authorization': f'Bearer {token}'}
        }
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to login as test user: {e}")

def create_colonization_fleet_api(backend_url="http://localhost:5000", auth_headers=None, fleet_data=None):
    """Helper function to create a colonization fleet via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    if fleet_data is None:
        fleet_data = {
            'start_planet_id': 2,  # e2etestuser's home planet
            'target_planet_id': 2,
            'mission': 'stationed',
            'status': 'stationed',
            'colony_ship': 1,
            'light_fighter': 10,
            'cruiser': 5
        }

    fleet_url = f"{backend_url}/api/fleet"
    try:
        response = requests.post(fleet_url, json=fleet_data, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def send_colonization_mission_api(backend_url="http://localhost:5000", auth_headers=None, fleet_id=None, target_planet_id=None):
    """Helper function to send a colonization mission via API"""
    import requests

    if fleet_id is None or target_planet_id is None:
        raise ValueError("fleet_id and target_planet_id are required")

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    mission_data = {
        'fleet_id': fleet_id,
        'target_planet_id': target_planet_id,
        'mission': 'colonize'
    }

    mission_url = f"{backend_url}/api/fleet/send"
    try:
        response = requests.post(mission_url, json=mission_data, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def get_fleets_api(backend_url="http://localhost:5000", auth_headers=None):
    """Helper function to get user's fleets via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    fleet_url = f"{backend_url}/api/fleet"
    try:
        response = requests.get(fleet_url, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def get_planets_api(backend_url="http://localhost:5000", auth_headers=None):
    """Helper function to get user's planets via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    planets_url = f"{backend_url}/api/planets"
    try:
        response = requests.get(planets_url, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

# === PHASE 4 TEST SCENARIOS ===

@pytest.fixture
def phase4_auth_data():
    """Fixture providing authenticated session data for Phase 4 testing"""
    return login_as_test_user()

@pytest.fixture
def phase4_test_fleet(phase4_auth_data):
    """Fixture creating a test colonization fleet for Phase 4 testing"""
    return create_colonization_fleet_api(auth_headers=phase4_auth_data['headers'])

@pytest.fixture
def phase4_fleet_mission(phase4_auth_data, phase4_test_fleet):
    """Fixture sending a colonization mission for Phase 4 testing"""
    # Find an unowned planet for colonization
    planets = get_planets_api(auth_headers=phase4_auth_data['headers'])
    unowned_planet = None

    for planet in planets:
        if planet.get('user_id') is None:  # Unowned planet
            unowned_planet = planet
            break

    if not unowned_planet:
        # Create a test unowned planet if none exists
        unowned_planet = create_test_unowned_planet(db_session=None, x=1000, y=2000, z=3000)
        unowned_planet['id'] = 999  # Mock ID for testing

    return send_colonization_mission_api(
        auth_headers=phase4_auth_data['headers'],
        fleet_id=phase4_test_fleet['id'],
        target_planet_id=unowned_planet['id']
    )

# === PERFORMANCE TESTING FIXTURES ===

@pytest.fixture
def colonization_performance_stress_test(db_session):
    """Create extreme performance test scenario for colonization"""
    return create_performance_test_scenario(
        db_session,
        num_users=50,
        planets_per_user=20
    )
    db_session.add(alliance)
    db_session.commit()
    return alliance

def make_auth_headers(user_id):
    """Helper function to create JWT auth headers for tests."""
    from flask_jwt_extended import create_access_token
    from flask import has_app_context

    # Some unit tests may call helpers outside of an app context. In that case, create
    # a temporary testing app so tokens are always signed with the configured secret.
    if has_app_context():
        token = create_access_token(identity=str(user_id))  # Convert to string
    else:
        temp_app = create_app('testing')
        with temp_app.app_context():
            token = create_access_token(identity=str(user_id))
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers for the sample user."""
    return make_auth_headers(sample_user.id)

@pytest.fixture
def test_user(sample_user):
    """Alias for sample_user to match test naming convention."""
    return sample_user


def create_test_user_with_hashed_password(db_session, username, email, plain_password='password'):
    """Create test user with properly hashed password for integration tests"""
    import bcrypt
    password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, plain_password  # Return both user and plain password for login testing

def create_test_fleet_with_constraints(db_session, user_id, start_planet_id, **kwargs):
    """Create a fleet with all required NOT NULL constraints satisfied"""
    from datetime import datetime

    now = datetime.utcnow()

    # Set defaults for required fields
    fleet_data = {
        'user_id': user_id,
        'start_planet_id': start_planet_id,
        'target_planet_id': kwargs.get('target_planet_id', start_planet_id),  # Required
        'mission': kwargs.get('mission', 'stationed'),
        'status': kwargs.get('status', 'stationed'),
        'departure_time': kwargs.get('departure_time', now),  # Required
        'arrival_time': kwargs.get('arrival_time', now),     # Required
        'eta': kwargs.get('eta', 0),
        **kwargs  # Allow ship counts and other fields
    }

    fleet = Fleet(**fleet_data)
    db_session.add(fleet)
    db_session.commit()
    return fleet

@pytest.fixture
def sample_fleet_proper(db_session, sample_user, sample_planet):
    """Create a properly constrained fleet for testing"""
    return create_test_fleet_with_constraints(
        db_session,
        sample_user.id,
        sample_planet.id,
        small_cargo=10,
        large_cargo=5,
        light_fighter=20,
        mission='attack'
    )


# === COLONIZATION-SPECIFIC TEST HELPERS ===

def create_test_colony_fleet(db_session, user_id, start_planet_id, **kwargs):
    """Create fleet with colony ship for colonization testing"""
    from datetime import datetime

    fleet_data = {
        'user_id': user_id,
        'start_planet_id': start_planet_id,
        'target_planet_id': kwargs.get('target_planet_id', start_planet_id),
        'mission': kwargs.get('mission', 'stationed'),
        'status': kwargs.get('status', 'stationed'),
        'departure_time': kwargs.get('departure_time', datetime.utcnow()),
        'arrival_time': kwargs.get('arrival_time', datetime.utcnow()),
        'colony_ship': kwargs.get('colony_ship', 1),  # Required for colonization
        'light_fighter': kwargs.get('light_fighter', 10),  # Escort ships
        'cruiser': kwargs.get('cruiser', 5),
        'battleship': kwargs.get('battleship', 0),
        'small_cargo': kwargs.get('small_cargo', 0),
        'large_cargo': kwargs.get('large_cargo', 0),
        'recycler': kwargs.get('recycler', 0),
        'bomber': kwargs.get('bomber', 0),
        'destroyer': kwargs.get('destroyer', 0),
        'battlecruiser': kwargs.get('battlecruiser', 0)
    }

    fleet = Fleet(**fleet_data)
    db_session.add(fleet)
    db_session.commit()
    return fleet


def create_test_colony_fleet_with_validation(db_session, user_id, start_planet_id, target_planet_id=None, **kwargs):
    """Create colony fleet with full validation and research requirements"""
    from datetime import datetime
    from backend.config import calculate_fleet_speed, SHIP_SPEEDS

    # Set target planet (default to start if not specified)
    if target_planet_id is None:
        target_planet_id = start_planet_id

    # Get planets for distance calculation
    start_planet = Planet.query.get(start_planet_id)
    target_planet = Planet.query.get(target_planet_id)

    if not start_planet or not target_planet:
        raise ValueError("Invalid start or target planet")

    # Calculate distance and travel time
    from backend.services.fleet_travel import FleetTravelService
    distance = FleetTravelService.calculate_distance(start_planet, target_planet)

    # Fleet composition with validation
    colony_ship = kwargs.get('colony_ship', 1)
    escort_ships = (
        kwargs.get('light_fighter', 10) +
        kwargs.get('heavy_fighter', 0) +
        kwargs.get('cruiser', 5) +
        kwargs.get('battleship', 0)
    )

    # Validate fleet composition
    if colony_ship != 1:
        raise ValueError("Fleet must contain exactly 1 colony ship")
    if escort_ships < 5:
        raise ValueError("Fleet must contain at least 5 escort ships")
    if escort_ships > 50:
        raise ValueError("Fleet cannot contain more than 50 escort ships")

    # Calculate fleet speed (slowest ship rule)
    fleet_composition = {
        'colony_ship': colony_ship,
        'light_fighter': kwargs.get('light_fighter', 10),
        'cruiser': kwargs.get('cruiser', 5),
        'battleship': kwargs.get('battleship', 0)
    }

    # Remove zero-count ships for speed calculation
    fleet_composition = {k: v for k, v in fleet_composition.items() if v > 0}
    slowest_speed = min(SHIP_SPEEDS[ship_type] for ship_type in fleet_composition.keys())

    # Calculate travel time
    travel_time_hours = distance / slowest_speed if slowest_speed > 0 else 0
    departure_time = kwargs.get('departure_time', datetime.utcnow())
    arrival_time = departure_time + timedelta(hours=travel_time_hours)

    # Create fleet with all calculated values
    fleet_data = {
        'user_id': user_id,
        'start_planet_id': start_planet_id,
        'target_planet_id': target_planet_id,
        'mission': kwargs.get('mission', 'colonize'),
        'status': kwargs.get('status', 'traveling'),
        'departure_time': departure_time,
        'arrival_time': arrival_time,
        'eta': int(travel_time_hours * 3600),  # ETA in seconds
        'colony_ship': colony_ship,
        'light_fighter': kwargs.get('light_fighter', 10),
        'heavy_fighter': kwargs.get('heavy_fighter', 0),
        'cruiser': kwargs.get('cruiser', 5),
        'battleship': kwargs.get('battleship', 0),
        'small_cargo': kwargs.get('small_cargo', 0),
        'large_cargo': kwargs.get('large_cargo', 0),
        'recycler': kwargs.get('recycler', 0),
        'bomber': kwargs.get('bomber', 0),
        'destroyer': kwargs.get('destroyer', 0),
        'battlecruiser': kwargs.get('battlecruiser', 0)
    }

    fleet = Fleet(**fleet_data)
    db_session.add(fleet)
    db_session.commit()
    return fleet


def create_test_unowned_planet(db_session, **kwargs):
    """Create unowned planet for colonization testing"""
    planet = Planet(
        name=kwargs.get('name', 'Unowned Planet'),
        x=kwargs.get('x', 100),
        y=kwargs.get('y', 200),
        z=kwargs.get('z', 300),
        user_id=None,  # Unowned
        metal=kwargs.get('metal', 1000),
        crystal=kwargs.get('crystal', 500),
        deuterium=kwargs.get('deuterium', 0),
        small_cargo=kwargs.get('small_cargo', 0),
        large_cargo=kwargs.get('large_cargo', 0),
        light_fighter=kwargs.get('light_fighter', 0),
        heavy_fighter=kwargs.get('heavy_fighter', 0),
        cruiser=kwargs.get('cruiser', 0),
        battleship=kwargs.get('battleship', 0),
        colony_ship=kwargs.get('colony_ship', 0),
        recycler=kwargs.get('recycler', 0),
        solar_plant=kwargs.get('solar_plant', 0),
        metal_mine=kwargs.get('metal_mine', 0),
        crystal_mine=kwargs.get('crystal_mine', 0),
        deuterium_synthesizer=kwargs.get('deuterium_synthesizer', 0)
    )
    db_session.add(planet)
    db_session.commit()
    return planet


def create_test_planet_with_traits(db_session, **kwargs):
    """Create planet with realistic colonization traits and resource deposits"""
    import random
    import math

    # Planet type compatibility data (from specification)
    PLANET_TYPES = {
        'terrestrial': {
            'probability': 0.4,
            'size_range': {'min': 4000, 'max': 12000},
            'temperature_range': {'min': -50, 'max': 50},
            'resources': {'metal': 1.0, 'crystal': 0.8, 'deuterium': 0.3},
            'base_resources': 1000
        },
        'gas_giant': {
            'probability': 0.15,
            'size_range': {'min': 50000, 'max': 150000},
            'temperature_range': {'min': -200, 'max': -100},
            'resources': {'metal': 0.1, 'crystal': 0.05, 'deuterium': 2.0},
            'base_resources': 500
        },
        'ice_world': {
            'probability': 0.2,
            'size_range': {'min': 2000, 'max': 8000},
            'temperature_range': {'min': -250, 'max': -150},
            'resources': {'metal': 0.3, 'crystal': 0.1, 'deuterium': 1.5},
            'base_resources': 800
        },
        'desert': {
            'probability': 0.15,
            'size_range': {'min': 3000, 'max': 10000},
            'temperature_range': {'min': 50, 'max': 150},
            'resources': {'metal': 1.5, 'crystal': 0.5, 'deuterium': 0.1},
            'base_resources': 1200
        },
        'ocean': {
            'probability': 0.08,
            'size_range': {'min': 5000, 'max': 14000},
            'temperature_range': {'min': -10, 'max': 30},
            'resources': {'metal': 0.8, 'crystal': 1.2, 'deuterium': 0.8},
            'base_resources': 1100
        },
        'volcanic': {
            'probability': 0.02,
            'size_range': {'min': 6000, 'max': 18000},
            'temperature_range': {'min': 200, 'max': 800},
            'resources': {'metal': 2.0, 'crystal': 0.3, 'deuterium': 0.2},
            'base_resources': 1500
        }
    }

    # Select planet type based on probabilities or override
    planet_type = kwargs.get('planet_type')
    if not planet_type:
        # Weighted random selection
        rand = random.random()
        cumulative = 0.0
        for p_type, data in PLANET_TYPES.items():
            cumulative += data['probability']
            if rand <= cumulative:
                planet_type = p_type
                break

    if planet_type not in PLANET_TYPES:
        planet_type = 'terrestrial'  # Default fallback

    type_data = PLANET_TYPES[planet_type]

    # Generate planet properties
    size = random.randint(
        type_data['size_range']['min'],
        type_data['size_range']['max']
    )

    temperature = random.randint(
        type_data['temperature_range']['min'],
        type_data['temperature_range']['max']
    )

    # Calculate colonization difficulty based on distance from origin
    x, y, z = kwargs.get('x', 100), kwargs.get('y', 200), kwargs.get('z', 300)
    distance_from_origin = (abs(x) + abs(y) + abs(z)) / 3
    colonization_difficulty = min(5, max(1, math.floor(distance_from_origin / 200)))

    # Generate resource deposits
    base_multipliers = type_data['resources']
    size_multiplier = size / 10000  # Normalize to 10000km baseline

    metal_deposit = int(base_multipliers['metal'] * size_multiplier * random.uniform(0.5, 1.5) * 1000)
    crystal_deposit = int(base_multipliers['crystal'] * size_multiplier * random.uniform(0.5, 1.5) * 1000)
    deuterium_deposit = int(base_multipliers['deuterium'] * size_multiplier * random.uniform(0.5, 1.5) * 1000)

    # Calculate habitability (0-100 scale)
    # Temperature closer to 20°C is more habitable
    temp_penalty = abs(temperature - 20) / 10  # Penalty per 10°C deviation
    habitability = max(0, min(100, 100 - temp_penalty))

    # Planet name generation
    if not kwargs.get('name'):
        adjectives = ['Prime', 'Major', 'Minor', 'Alpha', 'Beta', 'Gamma', 'Delta']
        features = ['Rock', 'Ice', 'Gas', 'Desert', 'Ocean', 'Volcanic', 'Terrestrial']
        name = f"{random.choice(adjectives)} {random.choice(features)} {random.randint(1, 999)}"
    else:
        name = kwargs['name']

    # Create planet with all calculated traits
    planet = Planet(
        name=name,
        x=x,
        y=y,
        z=z,
        user_id=kwargs.get('user_id'),  # Can be owned or unowned
        metal=metal_deposit,
        crystal=crystal_deposit,
        deuterium=deuterium_deposit,
        planet_type=planet_type,
        temperature=temperature,
        size=size,
        habitability=habitability,
        colonization_difficulty=colonization_difficulty,
        # Initialize with basic buildings if owned
        solar_plant=1 if kwargs.get('user_id') else 0,
        metal_mine=1 if kwargs.get('user_id') else 0,
        crystal_mine=1 if kwargs.get('user_id') else 0,
        deuterium_synthesizer=1 if kwargs.get('user_id') else 0
    )

    db_session.add(planet)
    db_session.commit()
    return planet


def setup_test_research_levels(db_session, user_id, **kwargs):
    """Setup research levels for colonization testing"""
    from backend.models import Research

    research = Research(
        user_id=user_id,
        colonization_tech=kwargs.get('colonization_tech', 5),
        energy_tech=kwargs.get('energy_tech', 5),
        laser_tech=kwargs.get('laser_tech', 0),
        ion_tech=kwargs.get('ion_tech', 0),
        hyperspace_tech=kwargs.get('hyperspace_tech', 0),
        plasma_tech=kwargs.get('plasma_tech', 0),
        combustion_drive=kwargs.get('combustion_drive', 0),
        impulse_drive=kwargs.get('impulse_drive', 0),
        hyperspace_drive=kwargs.get('hyperspace_drive', 0),
        espionage_tech=kwargs.get('espionage_tech', 0),
        computer_tech=kwargs.get('computer_tech', 0),
        astrophysics=kwargs.get('astrophysics', 0),
        intergalactic_research_network=kwargs.get('intergalactic_research_network', 0),
        graviton_tech=kwargs.get('graviton_tech', 0),
        weapons_tech=kwargs.get('weapons_tech', 0),
        shielding_tech=kwargs.get('shielding_tech', 0),
        armour_tech=kwargs.get('armour_tech', 0)
    )
    db_session.add(research)
    db_session.commit()
    return research


# === SQLALCHEMY MOCKING HELPERS (Following systemPatterns.md) ===

def create_mock_planet_for_arithmetic(**kwargs):
    """Create real Planet object for arithmetic operations (distance calculations)"""
    planet = Planet(
        name=kwargs.get('name', 'Mock Planet'),
        x=kwargs.get('x', 0),
        y=kwargs.get('y', 0),
        z=kwargs.get('z', 0),
        user_id=kwargs.get('user_id')
    )
    return planet


def create_mock_fleet_for_arithmetic(**kwargs):
    """Create real Fleet object for arithmetic operations (speed calculations)"""
    from datetime import datetime

    # Create fleet with all required fields and proper ship counts
    fleet_data = {
        'user_id': kwargs.get('user_id', 1),
        'start_planet_id': kwargs.get('start_planet_id', 1),
        'target_planet_id': kwargs.get('target_planet_id', 1),
        'mission': kwargs.get('mission', 'stationed'),
        'status': kwargs.get('status', 'stationed'),
        'departure_time': kwargs.get('departure_time', datetime.utcnow()),
        'arrival_time': kwargs.get('arrival_time', datetime.utcnow()),
        'small_cargo': kwargs.get('small_cargo', 0),
        'large_cargo': kwargs.get('large_cargo', 0),
        'light_fighter': kwargs.get('light_fighter', 0),
        'heavy_fighter': kwargs.get('heavy_fighter', 0),
        'cruiser': kwargs.get('cruiser', 0),
        'battleship': kwargs.get('battleship', 0),
        'colony_ship': kwargs.get('colony_ship', 0),
        'recycler': kwargs.get('recycler', 0),
        'espionage_probe': kwargs.get('espionage_probe', 0),
        'bomber': kwargs.get('bomber', 0),
        'destroyer': kwargs.get('destroyer', 0),
        'deathstar': kwargs.get('deathstar', 0),
        'battlecruiser': kwargs.get('battlecruiser', 0)
    }

    fleet = Fleet(**fleet_data)
    return fleet


def create_mock_user_for_auth(**kwargs):
    """Create real User object for authentication testing"""
    import bcrypt
    password_hash = bcrypt.hashpw(
        kwargs.get('plain_password', 'password').encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    user = User(
        username=kwargs.get('username', 'mockuser'),
        email=kwargs.get('email', 'mock@example.com'),
        password_hash=password_hash
    )
    return user, kwargs.get('plain_password', 'password')


# === FIXTURES FOR COLONIZATION TESTING ===

@pytest.fixture
def colony_fleet(db_session, sample_user, sample_planet):
    """Create colony fleet for colonization testing"""
    return create_test_colony_fleet(
        db_session,
        sample_user.id,
        sample_planet.id,
        colony_ship=1,
        light_fighter=10,
        cruiser=5
    )


@pytest.fixture
def unowned_planet(db_session):
    """Create unowned planet for colonization testing"""
    return create_test_unowned_planet(
        db_session,
        x=500,
        y=600,
        z=700,
        name='Target Colony',
        planet_type='terrestrial'
    )


@pytest.fixture
def user_with_research(db_session, sample_user):
    """Create user with colonization research"""
    return setup_test_research_levels(
        db_session,
        sample_user.id,
        colonization_tech=5,
        energy_tech=5
    )


@pytest.fixture
def colonization_scenario(db_session):
    """Create complete colonization test scenario"""
    # Create attacker user
    attacker, attacker_password = create_test_user_with_hashed_password(
        db_session, 'colonizer', 'colonizer@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Home Base',
        x=0, y=0, z=0,
        user_id=attacker.id,
        metal=10000, crystal=5000, deuterium=2000,
        small_cargo=100, large_cargo=50,
        light_fighter=200, cruiser=20
    )
    db_session.add(home_planet)

    # Create target planet
    target_planet = create_test_unowned_planet(
        db_session,
        x=100, y=100, z=100,
        name='New Colony Site'
    )

    # Create research
    research = setup_test_research_levels(
        db_session,
        attacker.id,
        colonization_tech=5
    )

    # Create colony fleet
    fleet = create_test_colony_fleet(
        db_session,
        attacker.id,
        home_planet.id,
        colony_ship=1,
        light_fighter=15,
        cruiser=8
    )

    db_session.commit()

    return {
        'attacker': attacker,
        'attacker_password': attacker_password,
        'home_planet': home_planet,
        'target_planet': target_planet,
        'research': research,
        'fleet': fleet
    }


def create_multi_planet_colonization_scenario(db_session, num_planets=5, **kwargs):
    """Create complex multi-planet colonization scenario for testing"""
    from datetime import datetime, timedelta

    # Create colonizer user
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'multi_colonizer', 'multi@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Home World',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=50000, crystal=30000, deuterium=20000,
        small_cargo=500, large_cargo=200,
        light_fighter=1000, cruiser=200, battleship=50,
        colony_ship=10  # Multiple colony ships available
    )
    db_session.add(home_planet)

    # Create research with high colonization tech
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=kwargs.get('colonization_tech', 5),
        energy_tech=10,
        hyperspace_drive=8
    )

    # Create multiple target planets at different distances
    target_planets = []
    colony_fleets = []

    distances = [200, 400, 600, 800, 1000]  # Different difficulty levels

    for i in range(min(num_planets, len(distances))):
        # Create planet at specific distance with varied traits
        distance = distances[i]
        angle = (i * 72) % 360  # Distribute around origin

        x = int(distance * math.cos(math.radians(angle)))
        y = int(distance * math.sin(math.radians(angle)))
        z = random.randint(-distance//2, distance//2)

        planet_type = random.choice(['terrestrial', 'desert', 'ocean', 'ice_world'])
        target_planet = create_test_planet_with_traits(
            db_session,
            x=x, y=y, z=z,
            planet_type=planet_type,
            user_id=None  # Unowned
        )
        target_planets.append(target_planet)

        # Create colony fleet for this planet
        fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=random.randint(10, 20),
            cruiser=random.randint(5, 15),
            battleship=random.randint(0, 5),
            mission='colonize',
            status='traveling'
        )
        colony_fleets.append(fleet)

    # Create some already-owned planets for conflict testing
    defender, _ = create_test_user_with_hashed_password(
        db_session, 'defender', 'defender@test.com', 'password'
    )

    owned_planets = []
    for i in range(2):
        owned_planet = create_test_planet_with_traits(
            db_session,
            x=random.randint(-300, 300),
            y=random.randint(-300, 300),
            z=random.randint(-300, 300),
            user_id=defender.id,
            planet_type='terrestrial'
        )
        owned_planets.append(owned_planet)

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'target_planets': target_planets,
        'colony_fleets': colony_fleets,
        'research': research,
        'defender': defender,
        'owned_planets': owned_planets
    }


def create_research_progression_scenario(db_session, **kwargs):
    """Create scenario for testing research progression effects on colonization"""
    # Create user with varying research levels
    user, password = create_test_user_with_hashed_password(
        db_session, 'research_test', 'research@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Research Base',
        x=0, y=0, z=0,
        user_id=user.id,
        metal=100000, crystal=50000, deuterium=30000,
        small_cargo=1000, large_cargo=500,
        light_fighter=2000, cruiser=500, battleship=100,
        colony_ship=20
    )
    db_session.add(home_planet)

    # Create research at different levels
    research_levels = [0, 1, 2, 3, 5]  # Different tech levels to test
    research_scenarios = []

    for tech_level in research_levels:
        research = setup_test_research_levels(
            db_session,
            user.id,
            colonization_tech=tech_level,
            energy_tech=max(tech_level, 1),
            hyperspace_drive=tech_level
        )

        # Calculate expected colony limits and bonuses
        expected_colony_limit = [3, 5, 8, 12, 12][tech_level]  # Based on spec
        expected_difficulty_reduction = tech_level * 0.5

        research_scenarios.append({
            'research': research,
            'tech_level': tech_level,
            'expected_colony_limit': expected_colony_limit,
            'expected_difficulty_reduction': expected_difficulty_reduction
        })

    # Create target planets at different distances for difficulty testing
    target_planets = []
    for distance in [100, 300, 500, 700, 900]:
        planet = create_test_planet_with_traits(
            db_session,
            x=distance, y=0, z=0,
            planet_type='terrestrial',
            user_id=None
        )
        target_planets.append({
            'planet': planet,
            'distance': distance,
            'base_difficulty': min(5, max(1, distance // 200))
        })

    db_session.commit()

    return {
        'user': user,
        'user_password': password,
        'home_planet': home_planet,
        'research_scenarios': research_scenarios,
        'target_planets': target_planets
    }


def create_performance_test_scenario(db_session, num_users=10, planets_per_user=5):
    """Create large-scale scenario for performance testing"""
    users = []
    planets = []
    fleets = []

    for i in range(num_users):
        # Create user
        user, _ = create_test_user_with_hashed_password(
            db_session, f'perf_user_{i}', f'perf{i}@test.com', 'password'
        )
        users.append(user)

        # Create home planet
        home_planet = Planet(
            name=f'Home {i}',
            x=i*100, y=i*100, z=i*100,
            user_id=user.id,
            metal=10000, crystal=5000, deuterium=2000,
            small_cargo=100, large_cargo=50,
            light_fighter=200, cruiser=50,
            colony_ship=5
        )
        db_session.add(home_planet)
        planets.append(home_planet)

        # Create additional planets
        for j in range(planets_per_user - 1):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*100 + j*20, y=i*100 + j*20, z=i*100 + j*20,
                user_id=user.id,
                planet_type='terrestrial'
            )
            planets.append(planet)

        # Create research
        setup_test_research_levels(
            db_session,
            user.id,
            colonization_tech=3,
            energy_tech=5
        )

        # Create some fleets
        for k in range(3):
            fleet = create_test_fleet_with_constraints(
                db_session,
                user.id,
                home_planet.id,
                small_cargo=random.randint(10, 50),
                light_fighter=random.randint(20, 100),
                mission='stationed'
            )
            fleets.append(fleet)

    db_session.commit()

    return {
        'users': users,
        'planets': planets,
        'fleets': fleets,
        'total_users': len(users),
        'total_planets': len(planets),
        'total_fleets': len(fleets)
    }


def create_edge_case_colonization_scenario(db_session):
    """Create scenario with edge cases for colonization testing"""
    # Create user at colony limit
    user, password = create_test_user_with_hashed_password(
        db_session, 'edge_case', 'edge@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Edge Case Base',
        x=0, y=0, z=0,
        user_id=user.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=50  # Lots of colony ships
    )
    db_session.add(home_planet)

    # Create research (low tech for difficulty testing)
    research = setup_test_research_levels(
        db_session,
        user.id,
        colonization_tech=1,  # Low tech = high difficulty
        energy_tech=1
    )

    # Create edge case planets
    edge_cases = []

    # 1. Planet at maximum colonization distance
    max_distance_planet = create_test_planet_with_traits(
        db_session,
        x=1000, y=1000, z=1000,  # Very far
        planet_type='volcanic',   # High difficulty
        user_id=None
    )
    edge_cases.append({
        'planet': max_distance_planet,
        'case': 'max_distance',
        'expected_difficulty': 5
    })

    # 2. Planet at minimum colonization distance
    min_distance_planet = create_test_planet_with_traits(
        db_session,
        x=50, y=50, z=50,  # Very close
        planet_type='terrestrial',  # Easy colonization
        user_id=None
    )
    edge_cases.append({
        'planet': min_distance_planet,
        'case': 'min_distance',
        'expected_difficulty': 1
    })

    # 3. Planet with extreme temperature
    extreme_temp_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='ice_world',  # Override to force extreme temp
        user_id=None
    )
    # Manually set extreme temperature
    extreme_temp_planet.temperature = -250
    edge_cases.append({
        'planet': extreme_temp_planet,
        'case': 'extreme_temperature',
        'expected_habitability': 0
    })

    # 4. Planet with rich resources
    rich_planet = create_test_planet_with_traits(
        db_session,
        x=300, y=300, z=300,
        planet_type='volcanic',  # High metal content
        user_id=None
    )
    edge_cases.append({
        'planet': rich_planet,
        'case': 'rich_resources',
        'expected_metal': lambda p: p.metal > 2000
    })

    # 5. Planet at origin (should have minimum difficulty)
    origin_planet = create_test_planet_with_traits(
        db_session,
        x=0, y=0, z=0,
        planet_type='terrestrial',
        user_id=None
    )
    edge_cases.append({
        'planet': origin_planet,
        'case': 'origin_location',
        'expected_difficulty': 1
    })

    db_session.commit()

    return {
        'user': user,
        'user_password': password,
        'home_planet': home_planet,
        'research': research,
        'edge_cases': edge_cases
    }


# === PERFORMANCE TESTING FIXTURES ===

@pytest.fixture
def multi_planet_scenario(db_session):
    """Create multi-planet colonization scenario"""
    return create_multi_planet_colonization_scenario(db_session, num_planets=5)


@pytest.fixture
def research_progression_scenario(db_session):
    """Create research progression testing scenario"""
    return create_research_progression_scenario(db_session)


@pytest.fixture
def performance_test_scenario(db_session):
    """Create large-scale performance testing scenario"""
    return create_performance_test_scenario(db_session, num_users=5, planets_per_user=3)


@pytest.fixture
def edge_case_scenario(db_session):
    """Create edge case testing scenario"""
    return create_edge_case_colonization_scenario(db_session)


# === RESEARCH PROGRESSION TEST FIXTURES ===

@pytest.fixture
def research_progression_basic(db_session):
    """Create basic research progression scenario (tech level 0-1)"""
    return create_research_progression_scenario(db_session)


@pytest.fixture
def research_progression_intermediate(db_session):
    """Create intermediate research progression scenario (tech level 2-3)"""
    scenario = create_research_progression_scenario(db_session)
    # Filter to intermediate levels
    scenario['research_scenarios'] = [
        rs for rs in scenario['research_scenarios']
        if rs['tech_level'] in [2, 3]
    ]
    return scenario


@pytest.fixture
def research_progression_advanced(db_session):
    """Create advanced research progression scenario (tech level 4-5)"""
    scenario = create_research_progression_scenario(db_session)
    # Filter to advanced levels
    scenario['research_scenarios'] = [
        rs for rs in scenario['research_scenarios']
        if rs['tech_level'] >= 4
    ]
    return scenario


@pytest.fixture
def colonization_workflow_complete(db_session):
    """Create complete colonization workflow test scenario"""
    # Create colonizer with high research
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'workflow_test', 'workflow@test.com', 'password'
    )

    # Create home planet with ample resources
    home_planet = Planet(
        name='Workflow Home',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        small_cargo=1000, large_cargo=500,
        light_fighter=2000, cruiser=500, battleship=100,
        colony_ship=20
    )
    db_session.add(home_planet)

    # Create research with maximum colonization tech
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5,
        energy_tech=10,
        hyperspace_drive=8
    )

    # Create target planets at strategic distances
    target_planets = []
    colony_fleets = []

    # Easy colonization (close, good planet)
    easy_planet = create_test_planet_with_traits(
        db_session,
        x=100, y=100, z=100,
        planet_type='terrestrial',
        user_id=None
    )
    target_planets.append({
        'planet': easy_planet,
        'difficulty': 'easy',
        'expected_success': True
    })

    # Medium colonization (moderate distance, mixed planet)
    medium_planet = create_test_planet_with_traits(
        db_session,
        x=400, y=400, z=400,
        planet_type='desert',
        user_id=None
    )
    target_planets.append({
        'planet': medium_planet,
        'difficulty': 'medium',
        'expected_success': True
    })

    # Hard colonization (far, poor planet)
    hard_planet = create_test_planet_with_traits(
        db_session,
        x=800, y=800, z=800,
        planet_type='ice_world',
        user_id=None
    )
    target_planets.append({
        'planet': hard_planet,
        'difficulty': 'hard',
        'expected_success': True
    })

    # Create fleets for each target
    for i, target in enumerate(target_planets):
        fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target['planet'].id,
            colony_ship=1,
            light_fighter=10 + i*5,  # Increasing escort sizes
            cruiser=5 + i*2,
            battleship=i,  # Some with battleships
            mission='colonize',
            status='traveling'
        )
        colony_fleets.append(fleet)

    # Create some defensive fleets for conflict testing
    defender, _ = create_test_user_with_hashed_password(
        db_session, 'defender_workflow', 'defender_workflow@test.com', 'password'
    )

    # Create owned planet that should reject colonization
    owned_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        user_id=defender.id,
        planet_type='terrestrial'
    )

    # Create defensive fleet
    defensive_fleet = create_test_fleet_with_constraints(
        db_session,
        defender.id,
        owned_planet.id,
        light_fighter=50,
        cruiser=20,
        battleship=5,
        mission='defend'
    )

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planets': target_planets,
        'colony_fleets': colony_fleets,
        'defender': defender,
        'owned_planet': owned_planet,
        'defensive_fleet': defensive_fleet
    }


@pytest.fixture
def colonization_performance_large(db_session):
    """Create large-scale colonization performance test scenario"""
    return create_performance_test_scenario(
        db_session,
        num_users=20,
        planets_per_user=10
    )


@pytest.fixture
def colonization_performance_medium(db_session):
    """Create medium-scale colonization performance test scenario"""
    return create_performance_test_scenario(
        db_session,
        num_users=10,
        planets_per_user=5
    )


@pytest.fixture
def colonization_performance_small(db_session):
    """Create small-scale colonization performance test scenario"""
    return create_performance_test_scenario(
        db_session,
        num_users=5,
        planets_per_user=3
    )


# === COLONIZATION WORKFLOW FIXTURES ===

@pytest.fixture
def colonization_workflow_basic(db_session):
    """Create basic colonization workflow scenario"""
    return create_colonization_workflow_complete(db_session)


@pytest.fixture
def colonization_workflow_with_conflicts(db_session):
    """Create colonization workflow with defensive conflicts"""
    scenario = create_colonization_workflow_complete(db_session)

    # Add more defenders and defensive fleets
    for i in range(3):
        defender, _ = create_test_user_with_hashed_password(
            db_session, f'conflict_defender_{i}', f'conflict{i}@test.com', 'password'
        )

        # Create defended planet
        defended_planet = create_test_planet_with_traits(
            db_session,
            x=random.randint(100, 500),
            y=random.randint(100, 500),
            z=random.randint(100, 500),
            user_id=defender.id,
            planet_type='terrestrial'
        )

        # Create strong defensive fleet
        defensive_fleet = create_test_fleet_with_constraints(
            db_session,
            defender.id,
            defended_planet.id,
            light_fighter=random.randint(100, 200),
            cruiser=random.randint(50, 100),
            battleship=random.randint(10, 30),
            mission='defend'
        )

        scenario[f'conflict_defender_{i}'] = defender
        scenario[f'defended_planet_{i}'] = defended_planet
        scenario[f'defensive_fleet_{i}'] = defensive_fleet

    db_session.commit()
    return scenario


@pytest.fixture
def colonization_workflow_research_limited(db_session):
    """Create colonization workflow with research limitations"""
    # Create user with low research
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'limited_research', 'limited@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Limited Research Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=50000, crystal=25000, deuterium=15000,
        small_cargo=200, large_cargo=100,
        light_fighter=500, cruiser=100,
        colony_ship=5
    )
    db_session.add(home_planet)

    # Create research with low colonization tech (should have difficulty penalties)
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=1,  # Low tech = higher difficulty
        energy_tech=2,
        hyperspace_drive=1
    )

    # Create challenging target planets
    target_planets = []
    colony_fleets = []

    # Very far planet (should be very difficult)
    far_planet = create_test_planet_with_traits(
        db_session,
        x=900, y=900, z=900,
        planet_type='ice_world',  # Poor planet type
        user_id=None
    )
    target_planets.append({
        'planet': far_planet,
        'difficulty': 'very_hard',
        'expected_success': True,  # Should still succeed with proper fleet
        'distance': 900
    })

    # Create fleet for the challenging colonization
    fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        far_planet.id,
        colony_ship=1,
        light_fighter=25,  # Large escort for difficult colonization
        cruiser=15,
        battleship=5,
        mission='colonize',
        status='traveling'
    )
    colony_fleets.append(fleet)

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planets': target_planets,
        'colony_fleets': colony_fleets,
        'expected_difficulty_reduction': 0.5,  # Tech level 1 = 0.5 reduction
        'expected_base_difficulty': 5  # Distance 900 = difficulty 5
    }


@pytest.fixture
def colonization_workflow_resource_limited(db_session):
    """Create colonization workflow with resource limitations"""
    # Create user with limited resources
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'resource_limited', 'resource@test.com', 'password'
    )

    # Create home planet with limited resources
    home_planet = Planet(
        name='Resource Limited Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=5000, crystal=2000, deuterium=1000,  # Limited resources
        small_cargo=50, large_cargo=20,
        light_fighter=100, cruiser=20,
        colony_ship=2  # Limited colony ships
    )
    db_session.add(home_planet)

    # Create research
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=3,
        energy_tech=5
    )

    # Create nearby planet (easy colonization)
    target_planet = create_test_planet_with_traits(
        db_session,
        x=150, y=150, z=150,
        planet_type='terrestrial',
        user_id=None
    )

    # Create minimal fleet (should still succeed)
    fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=8,  # Minimal escort
        cruiser=3,
        mission='colonize',
        status='traveling'
    )

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planet': target_planet,
        'colony_fleet': fleet,
        'expected_difficulty': 1,  # Close distance = easy
        'resource_limitations': {
            'metal': 5000,
            'crystal': 2000,
            'deuterium': 1000
        }
    }


@pytest.fixture
def colonization_workflow_fleet_variations(db_session):
    """Create colonization workflow with different fleet compositions"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'fleet_variations', 'variations@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Fleet Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        small_cargo=1000, large_cargo=500,
        light_fighter=2000, cruiser=500, battleship=100,
        colony_ship=20
    )
    db_session.add(home_planet)

    # Create research
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=4,
        energy_tech=8
    )

    # Create target planet
    target_planet = create_test_planet_with_traits(
        db_session,
        x=300, y=300, z=300,
        planet_type='desert',
        user_id=None
    )

    # Create fleets with different compositions
    fleet_variations = []

    # 1. Minimal escort fleet
    minimal_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=5,  # Minimum escort
        cruiser=0,
        battleship=0,
        mission='colonize',
        status='stationed'
    )
    fleet_variations.append({
        'fleet': minimal_fleet,
        'composition': 'minimal',
        'escort_count': 5,
        'expected_success': True
    })

    # 2. Balanced fleet
    balanced_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=15,
        cruiser=8,
        battleship=2,
        mission='colonize',
        status='stationed'
    )
    fleet_variations.append({
        'fleet': balanced_fleet,
        'composition': 'balanced',
        'escort_count': 25,
        'expected_success': True
    })

    # 3. Heavy escort fleet
    heavy_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=30,
        cruiser=20,
        battleship=10,
        mission='colonize',
        status='stationed'
    )
    fleet_variations.append({
        'fleet': heavy_fleet,
        'composition': 'heavy',
        'escort_count': 60,
        'expected_success': True
    })

    # 4. Invalid fleet (no colony ship) - should fail
    try:
        invalid_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=0,  # Invalid
            light_fighter=20,
            cruiser=10,
            mission='colonize',
            status='stationed'
        )
        fleet_variations.append({
            'fleet': invalid_fleet,
            'composition': 'invalid_no_colony_ship',
            'expected_success': False
        })
    except ValueError:
        # Expected to fail - add placeholder
        fleet_variations.append({
            'fleet': None,
            'composition': 'invalid_no_colony_ship',
            'expected_success': False,
            'error': 'No colony ship'
        })

    # 5. Invalid fleet (insufficient escort) - should fail
    try:
        invalid_fleet_2 = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=3,  # Insufficient escort
            cruiser=0,
            mission='colonize',
            status='stationed'
        )
        fleet_variations.append({
            'fleet': invalid_fleet_2,
            'composition': 'invalid_insufficient_escort',
            'expected_success': False
        })
    except ValueError:
        # Expected to fail - add placeholder
        fleet_variations.append({
            'fleet': None,
            'composition': 'invalid_insufficient_escort',
            'expected_success': False,
            'error': 'Insufficient escort'
        })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planet': target_planet,
        'fleet_variations': fleet_variations
    }


@pytest.fixture
def colonization_workflow_time_based(db_session):
    """Create colonization workflow with time-based elements"""
    import time
    from datetime import datetime, timedelta

    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'time_based', 'time@test.com', 'password'
    )

    # Create home planet
    home_planet = Planet(
        name='Time Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        small_cargo=1000, large_cargo=500,
        light_fighter=2000, cruiser=500,
        colony_ship=20
    )
    db_session.add(home_planet)

    # Create research
    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5,
        energy_tech=10
    )

    # Create target planet
    target_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='terrestrial',
        user_id=None
    )

    # Create fleet with specific departure time
    departure_time = datetime.utcnow() + timedelta(seconds=5)  # 5 seconds from now
    fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=10,
        cruiser=5,
        mission='colonize',
        status='traveling',
        departure_time=departure_time
    )

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planet': target_planet,
        'colony_fleet': fleet,
        'departure_time': departure_time,
        'expected_travel_time': fleet.arrival_time - departure_time
    }


# === PHASE 4: BACKEND-FRONTEND INTERACTION TESTING HELPERS ===

def login_as_test_user(backend_url="http://localhost:5000", username="e2etestuser", password="testpassword123"):
    """Helper function to authenticate and get JWT token for testing"""
    import requests

    login_url = f"{backend_url}/api/auth/login"
    login_data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()

        data = response.json()
        token = data.get('token') or data.get('access_token')

        if not token:
            raise ValueError(f"No token found in login response: {data}")

        return {
            'token': token,
            'user': data.get('user', {}),
            'headers': {'Authorization': f'Bearer {token}'}
        }
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to login as test user: {e}")

def create_colonization_fleet_api(backend_url="http://localhost:5000", auth_headers=None, fleet_data=None):
    """Helper function to create a colonization fleet via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    if fleet_data is None:
        fleet_data = {
            'start_planet_id': 2,  # e2etestuser's home planet
            'target_planet_id': 2,
            'mission': 'stationed',
            'status': 'stationed',
            'colony_ship': 1,
            'light_fighter': 10,
            'cruiser': 5
        }

    fleet_url = f"{backend_url}/api/fleet"
    try:
        response = requests.post(fleet_url, json=fleet_data, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def send_colonization_mission_api(backend_url="http://localhost:5000", auth_headers=None, fleet_id=None, target_planet_id=None):
    """Helper function to send a colonization mission via API"""
    import requests

    if fleet_id is None or target_planet_id is None:
        raise ValueError("fleet_id and target_planet_id are required")

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    mission_data = {
        'fleet_id': fleet_id,
        'target_planet_id': target_planet_id,
        'mission': 'colonize'
    }

    mission_url = f"{backend_url}/api/fleet/send"
    try:
        response = requests.post(mission_url, json=mission_data, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def get_fleets_api(backend_url="http://localhost:5000", auth_headers=None):
    """Helper function to get user's fleets via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    fleet_url = f"{backend_url}/api/fleet"
    try:
        response = requests.get(fleet_url, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def get_planets_api(backend_url="http://localhost:5000", auth_headers=None):
    """Helper function to get user's planets via API"""
    import requests

    if auth_headers is None:
        auth_data = login_as_test_user(backend_url)
        auth_headers = auth_data['headers']

    planets_url = f"{backend_url}/api/planets"
    try:
        response = requests.get(planets_url, headers=auth_headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

# === PHASE 4 TEST SCENARIOS ===

@pytest.fixture
def phase4_auth_data():
    """Fixture providing authenticated session data for Phase 4 testing"""
    return login_as_test_user()

@pytest.fixture
def phase4_test_fleet(phase4_auth_data):
    """Fixture creating a test colonization fleet for Phase 4 testing"""
    return create_colonization_fleet_api(auth_headers=phase4_auth_data['headers'])

@pytest.fixture
def phase4_fleet_mission(phase4_auth_data, phase4_test_fleet):
    """Fixture sending a colonization mission for Phase 4 testing"""
    # Find an unowned planet for colonization
    planets = get_planets_api(auth_headers=phase4_auth_data['headers'])
    unowned_planet = None

    for planet in planets:
        if planet.get('user_id') is None:  # Unowned planet
            unowned_planet = planet
            break

    if not unowned_planet:
        # Create a test unowned planet if none exists
        unowned_planet = create_test_unowned_planet(db_session=None, x=1000, y=2000, z=3000)
        unowned_planet['id'] = 999  # Mock ID for testing

    return send_colonization_mission_api(
        auth_headers=phase4_auth_data['headers'],
        fleet_id=phase4_test_fleet['id'],
        target_planet_id=unowned_planet['id']
    )

# === PERFORMANCE TESTING FIXTURES ===

@pytest.fixture
def colonization_performance_stress_test(db_session):
    """Create extreme performance test scenario for colonization"""
    return create_performance_test_scenario(
        db_session,
        num_users=50,
        planets_per_user=20
    )


@pytest.fixture
def colonization_performance_concurrent_test(db_session):
    """Create concurrent operations test scenario"""
    # Create multiple users who will perform operations simultaneously
    concurrent_users = []

    for i in range(10):
        user, password = create_test_user_with_hashed_password(
            db_session, f'concurrent_{i}', f'concurrent{i}@test.com', 'password'
        )

        # Each user gets their own planet cluster
        home_planet = Planet(
            name=f'Concurrent Base {i}',
            x=i*1000, y=i*1000, z=i*1000,
            user_id=user.id,
            metal=100000, crystal=50000, deuterium=30000,
            small_cargo=2000, large_cargo=1000,
            light_fighter=10000, cruiser=2000, battleship=500,
            colony_ship=20
        )
        db_session.add(home_planet)

        # Create research
        research = setup_test_research_levels(
            db_session,
            user.id,
            colonization_tech=3,
            energy_tech=5
        )

        # Create target planets in user's region
        target_planets = []
        for j in range(5):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*1000 + j*100, y=i*1000 + j*100, z=i*1000 + j*100,
                planet_type='terrestrial',
                user_id=None
            )
            target_planets.append(planet)

        # Create fleets ready for concurrent operations
        fleets = []
        for k in range(3):
            fleet = create_test_colony_fleet_with_validation(
                db_session,
                user.id,
                home_planet.id,
                target_planets[k].id,
                colony_ship=1,
                light_fighter=20,
                cruiser=10,
                mission='colonize',
                status='stationed'  # Ready to send
            )
            fleets.append(fleet)

        concurrent_users.append({
            'user': user,
            'password': password,
            'home_planet': home_planet,
            'research': research,
            'target_planets': target_planets,
            'fleets': fleets
        })

    db_session.commit()

    return {
        'concurrent_users': concurrent_users,
        'total_concurrent_operations': len(concurrent_users) * 3,  # 3 fleets per user
        'expected_concurrent_colonizations': len(concurrent_users) * 3
    }


@pytest.fixture
def colonization_performance_edge_case_test(db_session):
    """Create performance test with many edge cases"""
    # Create scenario that exercises all edge case code paths
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'edge_perf', 'edge_perf@test.com', 'password'
    )

    home_planet = Planet(
        name='Edge Performance Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=50
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5
    )

    # Create planets that exercise all edge cases
    edge_planets = []

    # Distance edge cases
    distances = [0, 1, 50, 199, 200, 399, 400, 599, 600, 799, 800, 999, 1000, 1001]
    for distance in distances:
        planet = create_test_planet_with_traits(
            db_session,
            x=distance, y=0, z=0,
            planet_type='terrestrial',
            user_id=None
        )
        edge_planets.append({
            'planet': planet,
            'distance': distance,
            'expected_difficulty': min(5, max(1, distance // 200))
        })

    # Planet type edge cases
    planet_types = ['terrestrial', 'gas_giant', 'ice_world', 'desert', 'ocean', 'volcanic']
    for p_type in planet_types:
        planet = create_test_planet_with_traits(
            db_session,
            x=300, y=300, z=300,
            planet_type=p_type,
            user_id=None
        )
        edge_planets.append({
            'planet': planet,
            'type': p_type,
            'expected_resources': 'high' if p_type == 'volcanic' else 'normal'
        })

    # Fleet composition edge cases
    fleet_compositions = [
        {'colony_ship': 1, 'light_fighter': 5},      # Minimum escort
        {'colony_ship': 1, 'light_fighter': 25},     # Normal escort
        {'colony_ship': 1, 'cruiser': 25},           # Different ship types
        {'colony_ship': 1, 'battleship': 10},        # Heavy ships
        {'colony_ship': 1, 'light_fighter': 50},     # Maximum escort
    ]

    edge_fleets = []
    for i, composition in enumerate(fleet_compositions):
        try:
            fleet = create_test_colony_fleet_with_validation(
                db_session,
                colonizer.id,
                home_planet.id,
                edge_planets[i]['planet'].id,
                **composition,
                mission='colonize',
                status='stationed'
            )
            edge_fleets.append({
                'fleet': fleet,
                'composition': composition,
                'expected_success': True
            })
        except ValueError as e:
            edge_fleets.append({
                'fleet': None,
                'composition': composition,
                'expected_success': False,
                'error': str(e)
            })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'edge_planets': edge_planets,
        'edge_fleets': edge_fleets,
        'total_edge_cases': len(edge_planets) + len(edge_fleets)
    }


# === EDGE CASE TEST DATA ===

@pytest.fixture
def colonization_edge_case_distance_limits(db_session):
    """Create edge cases for distance limits"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'distance_edge', 'distance@test.com', 'password'
    )

    home_planet = Planet(
        name='Distance Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5  # Max tech for max range
    )

    # Create planets at various distances
    distance_cases = []

    # Very close (should be easy)
    close_planet = create_test_planet_with_traits(
        db_session,
        x=10, y=10, z=10,
        planet_type='terrestrial',
        user_id=None
    )
    distance_cases.append({
        'planet': close_planet,
        'distance': 17,  # sqrt(10^2 + 10^2 + 10^2)
        'expected_difficulty': 1,
        'expected_success': True
    })

    # At difficulty boundary (199 units)
    boundary_planet = create_test_planet_with_traits(
        db_session,
        x=199, y=0, z=0,
        planet_type='terrestrial',
        user_id=None
    )
    distance_cases.append({
        'planet': boundary_planet,
        'distance': 199,
        'expected_difficulty': 1,  # floor(199/200) = 0 → 1
        'expected_success': True
    })

    # Just over difficulty boundary (201 units)
    over_boundary_planet = create_test_planet_with_traits(
        db_session,
        x=201, y=0, z=0,
        planet_type='terrestrial',
        user_id=None
    )
    distance_cases.append({
        'planet': over_boundary_planet,
        'distance': 201,
        'expected_difficulty': 2,  # floor(201/200) = 1 → 2
        'expected_success': True
    })

    # Very far (should be maximum difficulty)
    far_planet = create_test_planet_with_traits(
        db_session,
        x=1500, y=1500, z=1500,
        planet_type='terrestrial',
        user_id=None
    )
    distance_cases.append({
        'planet': far_planet,
        'distance': 2598,  # sqrt(1500^2 + 1500^2 + 1500^2)
        'expected_difficulty': 5,  # Maximum difficulty
        'expected_success': True
    })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'distance_cases': distance_cases
    }


@pytest.fixture
def colonization_edge_case_fleet_composition(db_session):
    """Create edge cases for fleet composition validation"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'fleet_edge', 'fleet@test.com', 'password'
    )

    home_planet = Planet(
        name='Fleet Composition Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10,
        light_fighter=1000,
        cruiser=500
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5
    )

    target_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='terrestrial',
        user_id=None
    )

    # Test various fleet compositions
    composition_cases = []

    # Valid minimum escort
    try:
        min_escort_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=5,  # Minimum required
            cruiser=0,
            battleship=0,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': min_escort_fleet,
            'composition': {'colony_ship': 1, 'light_fighter': 5},
            'expected_success': True,
            'description': 'Minimum valid escort'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 1, 'light_fighter': 5},
            'expected_success': False,
            'error': str(e),
            'description': 'Minimum valid escort'
        })

    # Valid maximum escort
    try:
        max_escort_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=50,  # Maximum allowed
            cruiser=0,
            battleship=0,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': max_escort_fleet,
            'composition': {'colony_ship': 1, 'light_fighter': 50},
            'expected_success': True,
            'description': 'Maximum valid escort'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 1, 'light_fighter': 50},
            'expected_success': False,
            'error': str(e),
            'description': 'Maximum valid escort'
        })

    # Invalid: No colony ship
    try:
        no_colony_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=0,  # Invalid
            light_fighter=20,
            cruiser=10,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': no_colony_fleet,
            'composition': {'colony_ship': 0, 'light_fighter': 20, 'cruiser': 10},
            'expected_success': False,
            'description': 'No colony ship'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 0, 'light_fighter': 20, 'cruiser': 10},
            'expected_success': False,
            'error': str(e),
            'description': 'No colony ship'
        })

    # Invalid: Too many colony ships
    try:
        multi_colony_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=2,  # Invalid
            light_fighter=20,
            cruiser=10,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': multi_colony_fleet,
            'composition': {'colony_ship': 2, 'light_fighter': 20, 'cruiser': 10},
            'expected_success': False,
            'description': 'Multiple colony ships'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 2, 'light_fighter': 20, 'cruiser': 10},
            'expected_success': False,
            'error': str(e),
            'description': 'Multiple colony ships'
        })

    # Invalid: Insufficient escort
    try:
        insufficient_escort_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=3,  # Insufficient
            cruiser=0,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': insufficient_escort_fleet,
            'composition': {'colony_ship': 1, 'light_fighter': 3},
            'expected_success': False,
            'description': 'Insufficient escort'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 1, 'light_fighter': 3},
            'expected_success': False,
            'error': str(e),
            'description': 'Insufficient escort'
        })

    # Invalid: Over maximum escort
    try:
        over_max_escort_fleet = create_test_colony_fleet_with_validation(
            db_session,
            colonizer.id,
            home_planet.id,
            target_planet.id,
            colony_ship=1,
            light_fighter=60,  # Over maximum
            cruiser=0,
            mission='colonize',
            status='stationed'
        )
        composition_cases.append({
            'fleet': over_max_escort_fleet,
            'composition': {'colony_ship': 1, 'light_fighter': 60},
            'expected_success': False,
            'description': 'Over maximum escort'
        })
    except ValueError as e:
        composition_cases.append({
            'fleet': None,
            'composition': {'colony_ship': 1, 'light_fighter': 60},
            'expected_success': False,
            'error': str(e),
            'description': 'Over maximum escort'
        })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planet': target_planet,
        'composition_cases': composition_cases
    }


@pytest.fixture
def colonization_edge_case_research_levels(db_session):
    """Create edge cases for research level validation"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'research_edge', 'research@test.com', 'password'
    )

    home_planet = Planet(
        name='Research Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10
    )
    db_session.add(home_planet)

    target_planet = create_test_planet_with_traits(
        db_session,
        x=400, y=400, z=400,
        planet_type='terrestrial',
        user_id=None
    )

    # Test different research levels
    research_cases = []

    research_levels = [0, 1, 2, 3, 4, 5, 6]  # Including invalid level 6
    for tech_level in research_levels:
        if tech_level <= 5:  # Valid levels
            research = setup_test_research_levels(
                db_session,
                colonizer.id,
                colonization_tech=tech_level
            )

            # Calculate expected difficulty reduction
            expected_reduction = tech_level * 0.5
            expected_final_difficulty = max(1, 2 - expected_reduction)  # Base difficulty 2

            research_cases.append({
                'research': research,
                'tech_level': tech_level,
                'expected_reduction': expected_reduction,
                'expected_final_difficulty': expected_final_difficulty,
                'is_valid': True
            })
        else:  # Invalid level
            research_cases.append({
                'research': None,
                'tech_level': tech_level,
                'expected_reduction': 0,
                'expected_final_difficulty': 2,  # No reduction
                'is_valid': False,
                'error': 'Invalid research level'
            })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'target_planet': target_planet,
        'research_cases': research_cases,
        'base_difficulty': 2  # Distance 693 = difficulty 2
    }


@pytest.fixture
def colonization_edge_case_planet_ownership(db_session):
    """Create edge cases for planet ownership validation"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'ownership_edge', 'ownership@test.com', 'password'
    )

    home_planet = Planet(
        name='Ownership Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5
    )

    # Create planets with different ownership states
    ownership_cases = []

    # Unowned planet (should succeed)
    unowned_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='terrestrial',
        user_id=None  # Unowned
    )
    ownership_cases.append({
        'planet': unowned_planet,
        'ownership': 'unowned',
        'expected_success': True
    })

    # Self-owned planet (should fail)
    self_owned_planet = create_test_planet_with_traits(
        db_session,
        x=300, y=300, z=300,
        planet_type='terrestrial',
        user_id=colonizer.id  # Self-owned
    )
    ownership_cases.append({
        'planet': self_owned_planet,
        'ownership': 'self_owned',
        'expected_success': False,
        'error': 'Cannot colonize own planet'
    })

    # Other user owned planet (should fail)
    other_user, _ = create_test_user_with_hashed_password(
        db_session, 'other_user', 'other@test.com', 'password'
    )
    other_owned_planet = create_test_planet_with_traits(
        db_session,
        x=400, y=400, z=400,
        planet_type='terrestrial',
        user_id=other_user.id  # Other user owned
    )
    ownership_cases.append({
        'planet': other_owned_planet,
        'ownership': 'other_owned',
        'expected_success': False,
        'error': 'Planet already owned'
    })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'ownership_cases': ownership_cases,
        'other_user': other_user
    }


@pytest.fixture
def colonization_edge_case_resource_deposits(db_session):
    """Create edge cases for resource deposit calculations"""
    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'resource_edge', 'resource@test.com', 'password'
    )

    home_planet = Planet(
        name='Resource Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5
    )

    # Create planets with extreme resource variations
    resource_cases = []

    # Planet with minimum resources
    min_resource_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='gas_giant',  # Low resource multiplier
        user_id=None
    )
    # Manually set minimum resources
    min_resource_planet.metal = 100
    min_resource_planet.crystal = 50
    min_resource_planet.deuterium = 25

    resource_cases.append({
        'planet': min_resource_planet,
        'resource_level': 'minimum',
        'expected_metal': 100,
        'expected_crystal': 50,
        'expected_deuterium': 25
    })

    # Planet with maximum resources
    max_resource_planet = create_test_planet_with_traits(
        db_session,
        x=300, y=300, z=300,
        planet_type='volcanic',  # High resource multiplier
        user_id=None
    )
    # Manually set maximum resources
    max_resource_planet.metal = 10000
    max_resource_planet.crystal = 5000
    max_resource_planet.deuterium = 2500

    resource_cases.append({
        'planet': max_resource_planet,
        'resource_level': 'maximum',
        'expected_metal': 10000,
        'expected_crystal': 5000,
        'expected_deuterium': 2500
    })

    # Planet with zero resources
    zero_resource_planet = create_test_planet_with_traits(
        db_session,
        x=400, y=400, z=400,
        planet_type='terrestrial',
        user_id=None
    )
    # Manually set zero resources
    zero_resource_planet.metal = 0
    zero_resource_planet.crystal = 0
    zero_resource_planet.deuterium = 0

    resource_cases.append({
        'planet': zero_resource_planet,
        'resource_level': 'zero',
        'expected_metal': 0,
        'expected_crystal': 0,
        'expected_deuterium': 0
    })

    # Planet with negative resources (edge case)
    negative_resource_planet = create_test_planet_with_traits(
        db_session,
        x=500, y=500, z=500,
        planet_type='terrestrial',
        user_id=None
    )
    # Manually set negative resources (should be clamped to 0)
    negative_resource_planet.metal = -100
    negative_resource_planet.crystal = -50
    negative_resource_planet.deuterium = -25

    resource_cases.append({
        'planet': negative_resource_planet,
        'resource_level': 'negative',
        'expected_metal': 0,  # Should be clamped
        'expected_crystal': 0,
        'expected_deuterium': 0
    })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'resource_cases': resource_cases
    }


@pytest.fixture
def colonization_edge_case_timing(db_session):
    """Create edge cases for timing and scheduling"""
    import time
    from datetime import datetime, timedelta

    colonizer, password = create_test_user_with_hashed_password(
        db_session, 'timing_edge', 'timing@test.com', 'password'
    )

    home_planet = Planet(
        name='Timing Test Base',
        x=0, y=0, z=0,
        user_id=colonizer.id,
        metal=100000, crystal=50000, deuterium=30000,
        colony_ship=10
    )
    db_session.add(home_planet)

    research = setup_test_research_levels(
        db_session,
        colonizer.id,
        colonization_tech=5
    )

    target_planet = create_test_planet_with_traits(
        db_session,
        x=200, y=200, z=200,
        planet_type='terrestrial',
        user_id=None
    )

    # Create timing edge cases
    timing_cases = []

    # Immediate departure (now)
    immediate_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=10,
        cruiser=5,
        mission='colonize',
        status='traveling',
        departure_time=datetime.utcnow()
    )
    timing_cases.append({
        'fleet': immediate_fleet,
        'timing': 'immediate',
        'departure_offset': 0,
        'expected_status': 'traveling'
    })

    # Past departure (should have already arrived)
    past_departure = datetime.utcnow() - timedelta(hours=2)
    past_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=10,
        cruiser=5,
        mission='colonize',
        status='stationed',  # Should be completed
        departure_time=past_departure
    )
    timing_cases.append({
        'fleet': past_fleet,
        'timing': 'past',
        'departure_offset': -7200,  # 2 hours ago
        'expected_status': 'stationed'
    })

    # Far future departure
    future_departure = datetime.utcnow() + timedelta(days=30)
    future_fleet = create_test_colony_fleet_with_validation(
        db_session,
        colonizer.id,
        home_planet.id,
        target_planet.id,
        colony_ship=1,
        light_fighter=10,
        cruiser=5,
        mission='colonize',
        status='stationed',  # Not yet departed
        departure_time=future_departure
    )
    timing_cases.append({
        'fleet': future_fleet,
        'timing': 'future',
        'departure_offset': 2592000,  # 30 days
        'expected_status': 'stationed'
    })

    db_session.commit()

    return {
        'colonizer': colonizer,
        'colonizer_password': password,
        'home_planet': home_planet,
        'research': research,
        'target_planet': target_planet,
        'timing_cases': timing_cases,
        'current_time': datetime.utcnow()
    }
