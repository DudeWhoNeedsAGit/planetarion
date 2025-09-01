import pytest
import os
import sys
from datetime import datetime, timedelta
from flask import Flask

from backend.database import db
from backend.models import User, Planet, Fleet, Alliance, TickLog

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

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
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashedpassword'
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
