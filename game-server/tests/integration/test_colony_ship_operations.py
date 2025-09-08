"""
Integration tests for Colony Ship Operations

Tests the complete workflow of sending colony ships to establish new colonies:
- Fleet creation with colony ships
- Planet selection and coordinate validation
- Colony ship sending to nearby planets
- Error handling for invalid operations
"""

import pytest
from datetime import datetime, timedelta
from backend.models import User, Planet, Fleet, Research


class TestColonyShipOperations:
    """Test suite for colony ship operations"""

    def test_send_colony_ship_to_nearby_planet(self, client, db_session):
        """Test sending a colony ship to establish a colony on a nearby planet"""
        # Create test user
        user = User(username='colonizer', email='colonizer@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home World',
            x=100, y=200, z=300,
            user_id=user.id,
            metal=10000, crystal=5000, deuterium=2000,
            metal_mine=10, crystal_mine=8, deuterium_synthesizer=6
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create target planet (unowned, nearby)
        target_planet = Planet(
            name='New Colony Site',
            x=110, y=210, z=310,  # Close to home planet
            user_id=None,  # Unowned
            metal=500, crystal=300, deuterium=100
        )
        db_session.add(target_planet)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,  # Has colony ship
            small_cargo=5,
            light_fighter=10,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'colonizer',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Send colony ship to target planet
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
        assert 'colonizing' in data['fleet']['status']

        # Verify target coordinates match the planet
        status_parts = data['fleet']['status'].split(':')
        assert len(status_parts) == 4  # colonizing:x:y:z
        assert status_parts[1] == str(target_planet.x)
        assert status_parts[2] == str(target_planet.y)
        assert status_parts[3] == str(target_planet.z)

    def test_send_colony_ship_to_coordinates(self, client, db_session):
        """Test sending a colony ship to specific coordinates"""
        # Create test user
        user = User(username='coord_colonizer', email='coord@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home Base',
            x=50, y=60, z=70,
            user_id=user.id,
            metal=8000, crystal=4000, deuterium=1500
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,
            small_cargo=3,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'coord_colonizer',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Send colony ship to specific coordinates
        target_coords = {'x': 75, 'y': 85, 'z': 95}
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': target_coords['x'],
            'target_y': target_coords['y'],
            'target_z': target_coords['z']
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'fleet' in data
        assert data['fleet']['status'] == f"colonizing:{target_coords['x']}:{target_coords['y']}:{target_coords['z']}"

    def test_send_colony_ship_without_colony_ship_fails(self, client, db_session):
        """Test that sending colonization mission without colony ship fails"""
        # Create test user
        user = User(username='no_colony', email='no_colony@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=10, y=20, z=30,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create fleet WITHOUT colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            small_cargo=10,  # No colony ship
            light_fighter=5,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'no_colony',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to send colonization mission
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

    def test_send_colony_ship_to_occupied_coordinates_fails(self, client, db_session):
        """Test that sending colony ship to occupied coordinates fails"""
        # Create test user
        user = User(username='occupied_test', email='occupied@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=0, y=0, z=0,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create occupied target planet
        occupied_planet = Planet(
            name='Occupied',
            x=50, y=60, z=70,
            user_id=user.id  # Already owned
        )
        db_session.add(occupied_planet)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'occupied_test',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to colonize occupied coordinates
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 50,
            'target_y': 60,
            'target_z': 70
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'occupied' in data['error'].lower()

    def test_send_colony_ship_to_occupied_planet_fails(self, client, db_session):
        """Test that sending colony ship to occupied planet fails"""
        # Create test user
        user = User(username='planet_occupied', email='planet_occupied@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=0, y=0, z=0,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create occupied target planet
        occupied_planet = Planet(
            name='Someone Else Colony',
            x=25, y=35, z=45,
            user_id=user.id + 1  # Owned by different user
        )
        db_session.add(occupied_planet)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'planet_occupied',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to colonize occupied planet
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_planet_id': occupied_planet.id
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'already colonized' in data['error'].lower()

    def test_colony_ship_requires_research_level(self, client, db_session):
        """Test that colonization requires appropriate research level"""
        # Create test user
        user = User(username='research_test', email='research@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=0, y=0, z=0,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create research with low colonization level
        research = Research(
            user_id=user.id,
            colonization_tech=1  # Low level
        )
        db_session.add(research)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'research_test',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to colonize distant coordinates (high difficulty)
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 1000,  # Very far
            'target_y': 1000,
            'target_z': 1000
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'research level' in data['error'].lower()

    def test_colony_ship_respects_colony_limits(self, client, db_session):
        """Test that colony ship sending respects colony limits"""
        # Create test user
        user = User(username='colony_limit', email='limit@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=0, y=0, z=0,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create maximum allowed colonies (5)
        for i in range(5):
            colony = Planet(
                name=f'Colony {i+1}',
                x=i*10, y=i*10, z=i*10,
                user_id=user.id
            )
            db_session.add(colony)
        db_session.commit()

        # Create fleet with colony ship
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=user.id,
            mission='stationed',
            start_planet_id=home_planet.id,
            target_planet_id=home_planet.id,
            status='stationed',
            colony_ship=1,
            departure_time=now,
            arrival_time=now
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'colony_limit',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Try to create 6th colony (should fail)
        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 100,
            'target_y': 100,
            'target_z': 100
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'colony limit' in data['error'].lower()

    def test_fleet_travel_info_includes_colony_data(self, client, db_session):
        """Test that fleet travel info includes colony-specific data"""
        # Create test user
        user = User(username='travel_info', email='travel@test.com', password_hash='hashed_password')
        db_session.add(user)
        db_session.commit()

        # Create home planet
        home_planet = Planet(
            name='Home',
            x=0, y=0, z=0,
            user_id=user.id
        )
        db_session.add(home_planet)
        db_session.commit()

        # Create traveling colony fleet
        fleet = Fleet(
            user_id=user.id,
            mission='colonize',
            start_planet_id=home_planet.id,
            target_planet_id=0,
            status='colonizing:50:60:70',
            departure_time=datetime.utcnow() - timedelta(hours=1),
            arrival_time=datetime.utcnow() + timedelta(hours=1),
            eta=3600,
            colony_ship=1,
            small_cargo=2
        )
        db_session.add(fleet)
        db_session.commit()

        # Login user
        login_response = client.post('/api/auth/login', json={
            'username': 'travel_info',
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
        assert fleet_data['mission'] == 'colonize'

        travel_info = fleet_data['travel_info']
        assert travel_info['is_coordinate_based'] == True
        assert travel_info['target_coordinates'] == '50:60:70'
        assert 'fleet_speed' in travel_info
        assert travel_info['fleet_speed'] == 2500  # Colony ship speed
