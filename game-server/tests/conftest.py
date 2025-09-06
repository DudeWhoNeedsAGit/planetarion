import pytest
import os
from datetime import datetime, timedelta

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
        deuterium=2000
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
        description='A test alliance',
        leader_id=sample_user.id
    )
    db_session.add(alliance)
    db_session.commit()
    return alliance

def make_auth_headers(user_id):
    """Helper function to create JWT auth headers for tests."""
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(user_id))  # Convert to string
    return {"Authorization": f"Bearer {token}"}
