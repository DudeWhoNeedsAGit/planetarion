import pytest
import json
from tests.conftest import make_auth_headers
from backend.models import Planet, Fleet

class TestShipyardEndpoints:
    """Test shipyard API endpoints"""

    def test_build_ship_success(self, client, sample_user, sample_planet, db_session):
        """Test successful ship building"""
        headers = make_auth_headers(sample_user.id)

        # Ensure planet has enough resources for colony ship
        # Colony ship costs: 10k metal, 20k crystal, 10k deuterium
        sample_planet.metal = 20000
        sample_planet.crystal = 25000
        sample_planet.deuterium = 15000
        db_session.commit()  # Commit the resource changes

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        if response.status_code != 200:
            print(f"Error response: {response.get_data(as_text=True)}")
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'planet_resources' in data
        assert 'fleet' in data

        # Verify resources were deducted
        # Colony ship costs: 10k metal, 20k crystal, 10k deuterium
        assert data['planet_resources']['metal'] == 10000  # 20000 - 10000
        assert data['planet_resources']['crystal'] == 5000  # 25000 - 20000
        assert data['planet_resources']['deuterium'] == 5000  # 15000 - 10000

    def test_build_ship_insufficient_resources(self, client, sample_user, sample_planet):
        """Test building ship with insufficient resources"""
        headers = make_auth_headers(sample_user.id)

        # Set planet to have insufficient resources
        sample_planet.metal = 1000
        sample_planet.crystal = 500
        sample_planet.deuterium = 200

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_build_ship_unowned_planet(self, client, sample_user):
        """Test building ship on planet not owned by user"""
        headers = make_auth_headers(sample_user.id)

        # Create a planet owned by a different user
        from backend.models import User
        from backend.database import db

        other_user = User(username='otheruser', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()

        other_planet = Planet(
            name='Other Planet',
            x=100, y=100, z=100,
            user_id=other_user.id,
            metal=20000, crystal=10000, deuterium=5000
        )
        db.session.add(other_planet)
        db.session.commit()

        build_data = {
            'planet_id': other_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_build_ship_invalid_type(self, client, sample_user, sample_planet):
        """Test building ship with invalid ship type"""
        headers = make_auth_headers(sample_user.id)

        sample_planet.metal = 20000
        sample_planet.crystal = 10000
        sample_planet.deuterium = 5000

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'invalid_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_build_ship_zero_quantity(self, client, sample_user, sample_planet):
        """Test building ship with zero quantity"""
        headers = make_auth_headers(sample_user.id)

        sample_planet.metal = 20000
        sample_planet.crystal = 10000
        sample_planet.deuterium = 5000

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 0
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_build_ship_negative_quantity(self, client, sample_user, sample_planet):
        """Test building ship with negative quantity"""
        headers = make_auth_headers(sample_user.id)

        sample_planet.metal = 20000
        sample_planet.crystal = 10000
        sample_planet.deuterium = 5000

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': -1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_build_ship_missing_fields(self, client, sample_user):
        """Test building ship with missing required fields"""
        headers = make_auth_headers(sample_user.id)

        incomplete_data = {
            'planet_id': 1
            # Missing ship_type and quantity
        }

        response = client.post('/api/shipyard/build',
                             json=incomplete_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_get_ship_costs(self, client):
        """Test getting ship costs (public endpoint)"""
        response = client.get('/api/shipyard/costs')

        assert response.status_code == 200
        data = response.get_json()

        assert 'colony_ship' in data
        assert 'metal' in data['colony_ship']
        assert 'crystal' in data['colony_ship']
        assert 'deuterium' in data['colony_ship']

    def test_build_ship_unauthorized(self, client):
        """Test building ship without JWT token"""
        build_data = {
            'planet_id': 1,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build', json=build_data)

        assert response.status_code == 401

class TestShipyardIntegration:
    """Test shipyard-related integration scenarios"""

    def test_ship_building_workflow(self, client, sample_user, db_session):
        """Test complete ship building workflow"""
        headers = make_auth_headers(sample_user.id)

        # Create a fresh planet with plenty of resources
        planet = Planet(
            name='Rich Planet',
            x=100,
            y=200,
            z=300,
            user_id=sample_user.id,
            metal=100000,
            crystal=100000,
            deuterium=100000
        )
        db_session.add(planet)
        db_session.commit()

        # Build multiple ships
        build_data = {
            'planet_id': planet.id,
            'ship_type': 'colony_ship',
            'quantity': 3
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        if response.status_code != 200:
            pytest.fail(f"Expected 200 but got {response.status_code}. Response: {response.get_data(as_text=True)}")
        assert response.status_code == 200
        data = response.get_json()

        # Verify resources were deducted correctly
        expected_metal_cost = 10000 * 3  # 10k metal per colony ship
        expected_crystal_cost = 20000 * 3  # 20k crystal per colony ship
        expected_deuterium_cost = 10000 * 3  # 10k deuterium per colony ship

        assert data['planet_resources']['metal'] == 100000 - expected_metal_cost
        assert data['planet_resources']['crystal'] == 100000 - expected_crystal_cost
        assert data['planet_resources']['deuterium'] == 100000 - expected_deuterium_cost

        # Verify fleet was created/updated
        assert data['fleet']['colony_ship'] == 3

    def test_ship_building_creates_fleet(self, client, sample_user, sample_planet, db_session):
        """Test that building ships creates a fleet if none exists"""
        headers = make_auth_headers(sample_user.id)

        sample_planet.metal = 20000
        sample_planet.crystal = 20000
        sample_planet.deuterium = 10000
        db_session.commit()  # Commit the resource changes

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify fleet was created
        assert 'fleet' in data
        assert data['fleet']['id'] is not None
        assert data['fleet']['colony_ship'] == 1

    def test_ship_building_updates_existing_fleet(self, client, sample_user, sample_planet, sample_fleet, db_session):
        """Test that building ships updates existing fleet"""
        headers = make_auth_headers(sample_user.id)

        # Ensure fleet is stationed at the planet
        sample_fleet.start_planet_id = sample_planet.id
        sample_fleet.status = 'stationed'
        sample_fleet.colony_ship = 2  # Start with 2 ships

        sample_planet.metal = 20000
        sample_planet.crystal = 20000
        sample_planet.deuterium = 10000
        db_session.commit()  # Commit the resource changes

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify existing fleet was updated
        assert data['fleet']['id'] == sample_fleet.id
        assert data['fleet']['colony_ship'] == 3  # 2 + 1

class TestShipyardEdgeCases:
    """Test shipyard endpoint edge cases"""

    def test_build_ship_max_quantity(self, client, sample_user, sample_planet, db_session):
        """Test building maximum quantity of ships"""
        headers = make_auth_headers(sample_user.id)

        # Set planet with massive resources
        sample_planet.metal = 10000000
        sample_planet.crystal = 20000000
        sample_planet.deuterium = 10000000
        db_session.commit()  # Commit the resource changes

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1000
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['fleet']['colony_ship'] == 1000

    def test_build_ship_exact_resources(self, client, sample_user, sample_planet, db_session):
        """Test building ship with exactly the required resources"""
        headers = make_auth_headers(sample_user.id)

        # Set planet with exactly the required resources
        sample_planet.metal = 10000
        sample_planet.crystal = 20000
        sample_planet.deuterium = 10000
        db_session.commit()  # Commit the resource changes

        build_data = {
            'planet_id': sample_planet.id,
            'ship_type': 'colony_ship',
            'quantity': 1
        }

        response = client.post('/api/shipyard/build',
                             json=build_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify resources are now zero
        assert data['planet_resources']['metal'] == 0
        assert data['planet_resources']['crystal'] == 0
        assert data['planet_resources']['deuterium'] == 0
