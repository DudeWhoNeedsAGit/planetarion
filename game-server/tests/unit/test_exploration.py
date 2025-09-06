"""
Unit tests for exploration functionality
"""
import pytest
from datetime import datetime, timedelta
from backend.database import db
from backend.models import User, Planet, Fleet
from backend.services.tick import generate_exploration_planets


def test_generate_exploration_planets_new_system(app):
    """Test generating planets in a new unexplored system"""
    with app.app_context():
        # Create test user
        user = User(username="testuser", email="test@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Generate planets in new system
        planets = generate_exploration_planets(100, 200, 300, user.id)

        # Should generate 1-3 planets
        assert 1 <= len(planets) <= 3

        # Check planets are created with correct properties
        for planet in planets:
            assert planet.user_id is None  # Unowned
            assert planet.x != 100 or planet.y != 200 or planet.z != 300  # Offset from center
            assert planet.metal >= 100
            assert planet.crystal >= 50
            assert planet.metal_mine == 0  # No initial structures


def test_generate_exploration_planets_existing_system(app):
    """Test that existing planets are returned for already explored systems"""
    with app.app_context():
        # Create test user
        user = User(username="testuser2", email="test2@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Create existing planet
        existing_planet = Planet(
            name="Existing Planet",
            x=150, y=250, z=350,
            user_id=None
        )
        db.session.add(existing_planet)
        db.session.commit()

        # Try to generate planets in same system
        planets = generate_exploration_planets(150, 250, 350, user.id)

        # Should return existing planet
        assert len(planets) == 1
        assert planets[0].id == existing_planet.id


def test_exploration_fleet_creation(app):
    """Test creating an exploration fleet"""
    with app.app_context():
        # Create test user and planet
        user = User(username="explorer", email="explore@example.com", password_hash="hash")
        planet = Planet(name="Home", x=0, y=0, z=0, user_id=user.id)
        db.session.add(user)
        db.session.add(planet)
        db.session.commit()

        # Create exploration fleet
        fleet = Fleet(
            user_id=user.id,
            mission='explore',
            start_planet_id=planet.id,
            target_planet_id=0,
            status='exploring:10:20:30',
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(fleet)
        db.session.commit()

        # Verify fleet properties
        assert fleet.mission == 'explore'
        assert fleet.status == 'exploring:10:20:30'
        assert fleet.explored_coordinates is None  # Not yet completed


def test_user_explored_systems_tracking(app):
    """Test that user's explored systems are properly tracked"""
    with app.app_context():
        import json

        # Create test user
        user = User(username="explorer2", email="explore2@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Simulate explored systems data
        explored_data = [
            {
                'coordinates': '10:20:30',
                'x': 10, 'y': 20, 'z': 30,
                'planets': 2,
                'explored_at': '2025-09-05T19:00:00'
            }
        ]
        user.explored_systems = json.dumps(explored_data)
        db.session.commit()

        # Verify data is stored correctly
        assert user.explored_systems is not None
        parsed_data = json.loads(user.explored_systems)
        assert len(parsed_data) == 1
        assert parsed_data[0]['coordinates'] == '10:20:30'
        assert parsed_data[0]['planets'] == 2
