"""
Integration tests for Enhanced Fleet API

Tests the enhanced fleet API endpoints including:
- Travel information in fleet responses
- Planet information retrieval
- Coordinate-based mission handling
- Error handling for invalid requests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from backend.models import User, Planet, Fleet, Research


class TestEnhancedFleetAPI:
    """Test suite for enhanced fleet API functionality"""

    def test_get_fleets_includes_travel_info(self, client, db_session):
        """Test that fleet responses include travel information"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser', email='test@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planets
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        target_planet = Planet(name='Target', x=10, y=0, z=0, user_id=None)
        db_session.add_all([start_planet, target_planet])
        db_session.commit()

        # Create traveling fleet
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            target_planet_id=target_planet.id,
            mission='attack',
            status='traveling',
            departure_time=datetime.utcnow() - timedelta(hours=1),
            arrival_time=datetime.utcnow() + timedelta(hours=1),
            eta=3600,
            small_cargo=5,
            light_fighter=10
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Get fleets
        response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

        fleet_data = data[0]
        assert 'travel_info' in fleet_data
        assert 'start_planet' in fleet_data
        assert 'target_planet' in fleet_data

        # Check travel info structure
        travel_info = fleet_data['travel_info']
        assert 'distance' in travel_info
        assert 'total_duration_hours' in travel_info
        assert 'progress_percentage' in travel_info
        assert 'current_position' in travel_info
        assert 'fleet_speed' in travel_info

        # Check planet info
        start_info = fleet_data['start_planet']
        assert start_info['name'] == 'Start'
        assert start_info['coordinates'] == '0:0:0'

        target_info = fleet_data['target_planet']
        assert target_info['name'] == 'Target'
        assert target_info['coordinates'] == '10:0:0'

    def test_get_fleets_stationed_no_travel_info(self, client, db_session):
        """Test that stationed fleets don't include travel info"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser2', email='test2@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planet
        planet = Planet(name='Home', x=100, y=200, z=300, user_id=user.id)
        db_session.add(planet)
        db_session.commit()

        # Create stationed fleet
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            planet.id,
            mission='stationed',
            status='stationed',
            small_cargo=5
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser2',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Get fleets
        response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

        fleet_data = data[0]
        assert fleet_data['travel_info'] is None  # Stationed fleets have no travel info

    def test_get_fleets_coordinate_based_mission(self, client, db_session):
        """Test fleet responses for coordinate-based missions"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser3', email='test3@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planet
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        db_session.add(start_planet)
        db_session.commit()

        # Create fleet with coordinate-based mission
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            target_planet_id=0,  # Coordinate-based
            mission='colonize',
            status='colonizing:100:200:300',
            departure_time=datetime.utcnow() - timedelta(hours=1),
            arrival_time=datetime.utcnow() + timedelta(hours=1),
            eta=3600,
            colony_ship=1,
            small_cargo=5
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser3',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Get fleets
        response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

        fleet_data = data[0]
        assert 'travel_info' in fleet_data
        assert fleet_data['target_planet'] is None  # No target planet for coordinate missions

        # Check travel info for coordinate-based mission
        travel_info = fleet_data['travel_info']
        assert travel_info['is_coordinate_based'] == True
        assert travel_info['target_coordinates'] == '100:200:300'

    def test_send_fleet_colonization_with_planet_selection(self, client, db_session):
        """Test sending colonization fleet with planet selection"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser4', email='test4@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planets
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        target_planet = Planet(name='Empty Space', x=100, y=200, z=300, user_id=None)
        db_session.add_all([start_planet, target_planet])
        db_session.commit()

        # Create fleet with colony ship
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            mission='stationed',
            status='stationed',
            colony_ship=1,
            small_cargo=5
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser4',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Send colonization fleet with planet selection
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_planet_id': target_planet.id
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'fleet' in data
        assert data['fleet']['status'] == f'colonizing:{target_planet.x}:{target_planet.y}:{target_planet.z}'

    def test_send_fleet_colonization_with_coordinates(self, client, db_session):
        """Test sending colonization fleet with direct coordinates"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser5', email='test5@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planet
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        db_session.add(start_planet)
        db_session.commit()

        # Create fleet with colony ship
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            mission='stationed',
            status='stationed',
            colony_ship=1,
            small_cargo=5
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser5',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Send colonization fleet with coordinates
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 500,
            'target_y': 600,
            'target_z': 700
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'fleet' in data
        assert data['fleet']['status'] == 'colonizing:500:600:700'

    def test_send_fleet_colonization_no_colony_ship(self, client, db_session):
        """Test sending colonization fleet without colony ships"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser6', email='test6@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planet
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        db_session.add(start_planet)
        db_session.commit()

        # Create fleet without colony ship
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            mission='stationed',
            status='stationed',
            small_cargo=5  # No colony ship
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser6',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to send colonization fleet
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 100,
            'target_y': 200,
            'target_z': 300
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'colony ship' in data['error'].lower()

    def test_send_fleet_colonization_occupied_coordinates(self, client, db_session):
        """Test sending colonization fleet to occupied coordinates"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser7', email='test7@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planets
        start_planet = Planet(name='Start', x=0, y=0, z=0, user_id=user.id)
        occupied_planet = Planet(name='Occupied', x=100, y=200, z=300, user_id=user.id)
        db_session.add_all([start_planet, occupied_planet])
        db_session.commit()

        # Create fleet with colony ship
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            start_planet.id,
            mission='stationed',
            status='stationed',
            colony_ship=1
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser7',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to colonize occupied coordinates
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 100,
            'target_y': 200,
            'target_z': 300
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'occupied' in data['error'].lower()

    def test_get_planet_info_function(self, db_session):
        """Test the get_planet_info helper function"""
        # Create test planet
        planet = Planet(name='Test Planet', x=10, y=20, z=30)
        db_session.add(planet)
        db_session.commit()

        # Test with valid planet
        from backend.routes.fleet import get_planet_info
        info = get_planet_info(planet.id, {planet.id: planet})
        assert info['name'] == 'Test Planet'
        assert info['coordinates'] == '10:20:30'

        # Test with invalid planet ID
        info = get_planet_info(999, {})
        assert info['name'] == 'Unknown'
        assert info['coordinates'] == 'N/A'

        # Test with None
        info = get_planet_info(None, {})
        assert info is None

    def test_fleet_response_includes_ship_counts(self, client, db_session):
        """Test that fleet responses include accurate ship counts"""
        # Create test user with proper bcrypt password hash
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username='testuser8', email='test8@example.com', password_hash=password_hash)
        db_session.add(user)
        db_session.commit()

        # Create test planet
        planet = Planet(name='Home', x=0, y=0, z=0, user_id=user.id)
        db_session.add(planet)
        db_session.commit()

        # Create fleet with specific ship counts
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            user.id,
            planet.id,
            mission='stationed',
            status='stationed',
            small_cargo=3,
            large_cargo=2,
            light_fighter=5,
            heavy_fighter=1,
            cruiser=2,
            battleship=1,
            colony_ship=1
        )

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser8',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Get fleets
        response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1

        fleet_data = data[0]
        ships = fleet_data['ships']
        assert ships['small_cargo'] == 3
        assert ships['large_cargo'] == 2
        assert ships['light_fighter'] == 5
        assert ships['heavy_fighter'] == 1
        assert ships['cruiser'] == 2
        assert ships['battleship'] == 1
        assert ships['colony_ship'] == 1
