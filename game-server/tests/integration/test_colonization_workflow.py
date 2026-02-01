"""
Colonization Workflow Integration Tests

Tests the complete colonization process from colony ship creation through colony establishment.
Follows systemPatterns.md for proper SQLAlchemy mocking and test data creation.
"""

import pytest
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.models import User, Planet, Fleet, Research
from backend.services.colonization_service import ColonizationService
from backend.services.fleet_arrival import FleetArrivalService


# Test Data Creation Helpers (following systemPatterns.md)

def create_test_user_with_hashed_password(db_session, username, email, plain_password='password'):
    """Create test user with properly hashed password for integration tests"""
    password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, plain_password


def create_test_planet(db_session, user_id=None, **kwargs):
    """Create planet with proper defaults"""
    planet = Planet(
        name=kwargs.get('name', 'Test Planet'),
        x=kwargs.get('x', 0),
        y=kwargs.get('y', 0),
        z=kwargs.get('z', 0),
        user_id=user_id,
        metal=kwargs.get('metal', 1000),
        crystal=kwargs.get('crystal', 500),
        deuterium=kwargs.get('deuterium', 0)
    )
    db_session.add(planet)
    db_session.commit()
    return planet


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
        deuterium=kwargs.get('deuterium', 0)
    )
    db_session.add(planet)
    db_session.commit()
    return planet


def create_test_colony_fleet(db_session, user_id, start_planet_id, target_planet_id):
    """Create fleet with colony ship for testing"""
    fleet = Fleet(
        user_id=user_id,
        start_planet_id=start_planet_id,
        target_planet_id=target_planet_id,
        mission='colonize',
        status='traveling',
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow() + timedelta(hours=1),
        colony_ship=1,  # Required for colonization
        light_fighter=10,  # Escort ships
        cruiser=5,
        small_cargo=5
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet


def setup_test_research(db_session, user_id, tech_level):
    """Setup research levels for testing"""
    research = Research(
        user_id=user_id,
        colonization_tech=tech_level,
    )
    db_session.add(research)
    db_session.commit()
    return research


# Integration Test Classes

class TestCompleteColonizationWorkflow:
    """Test the complete colonization workflow from fleet creation to colony establishment"""

    def test_colonization_fleet_creation_and_validation(self, client, db_session):
        """Test creating and validating a colonization fleet"""
        # Setup test user
        user, password = create_test_user_with_hashed_password(db_session, 'colonizer', 'colonizer@test.com')
        home_planet = create_test_planet(db_session, user.id, name='Home Planet')
        home_planet.colony_ship = 5
        home_planet.light_fighter = 50
        home_planet.cruiser = 20
        home_planet.small_cargo = 20
        db_session.commit()

        # Login
        login_response = client.post('/api/auth/login', json={
            'username': 'colonizer',
            'password': password
        })
        assert login_response.status_code == 200
        token = login_response.get_json()['token']

        # Create colonization fleet
        fleet_data = {
            'start_planet_id': home_planet.id,
            'ships': {
                'colony_ship': 1,
                'light_fighter': 10,
                'cruiser': 5,
                'small_cargo': 5
            }
        }

        response = client.post('/api/fleet',
            json=fleet_data,
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 201
        fleet_response = response.get_json()['fleet']
        assert fleet_response['ships']['colony_ship'] == 1
        assert fleet_response['ships']['light_fighter'] == 10

    def test_colonization_mission_sending(self, client, db_session):
        """Test sending a colonization fleet to an unowned planet"""
        # Setup
        user, password = create_test_user_with_hashed_password(db_session, 'colonizer2', 'colonizer2@test.com')
        home_planet = create_test_planet(db_session, user.id, name='Home Base')
        target_planet = create_test_unowned_planet(db_session, x=500, y=600, z=700, name='Target Colony')
        home_planet.deuterium = 100000
        db_session.commit()

        setup_test_research(db_session, user.id, tech_level=5)

        # Create fleet
        fleet = create_test_colony_fleet(db_session, user.id, home_planet.id, target_planet.id)
        fleet.status = 'stationed'  # Ready to send
        db_session.commit()

        # Login
        login_response = client.post('/api/auth/login', json={
            'username': 'colonizer2',
            'password': password
        })
        token = login_response.get_json()['token']

        # Send colonization mission
        mission_data = {
            'fleet_id': fleet.id,
            'target_planet_id': target_planet.id,
            'mission': 'colonize'
        }

        response = client.post('/api/fleet/send',
            json=mission_data,
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        mission_response = response.get_json()
        assert mission_response['fleet']['status'] == 'colonizing:500:600:700'
        assert mission_response['fleet']['mission'] == 'colonize'

    def test_colonization_fleet_arrival_processing(self, client, db_session):
        """Test colonization fleet arrival and colony establishment"""
        user, _password = create_test_user_with_hashed_password(db_session, 'colonizer3', 'colonizer3@test.com')
        home_planet = create_test_planet(db_session, user.id, name='Home', deuterium=100000)
        target_planet = create_test_unowned_planet(db_session, x=500, y=600, z=700, name='Target')

        setup_test_research(db_session, user.id, tech_level=5)

        fleet = create_test_colony_fleet(db_session, user.id, home_planet.id, target_planet.id)
        fleet.status = 'colonizing:500:600:700'
        fleet.target_coordinates = '500:600:700'
        fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
        db_session.commit()

        FleetArrivalService.process_arrived_fleets()

        db_session.refresh(target_planet)
        assert target_planet.user_id == user.id
        assert target_planet.colonized_at is not None
