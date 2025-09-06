import pytest
import json
from src.tests.conftest import make_auth_headers
from src.backend.models import Planet, User
from src.backend.database import db

class TestPlanetUserEndpoints:
    """Test planet user management endpoints"""

    def test_get_user_planets_success(self, client, sample_user, sample_planet):
        """Test getting user's planets successfully"""
        headers = make_auth_headers(sample_user.id)

        response = client.get('/api/planet', headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check first planet structure
        planet_data = data[0]
        assert 'id' in planet_data
        assert 'name' in planet_data
        assert 'coordinates' in planet_data
        assert 'resources' in planet_data
        assert 'structures' in planet_data
        assert 'production_rates' in planet_data

        # Verify coordinates format
        assert ':' in planet_data['coordinates']

        # Verify resources structure
        resources = planet_data['resources']
        assert 'metal' in resources
        assert 'crystal' in resources
        assert 'deuterium' in resources

        # Verify structures
        structures = planet_data['structures']
        assert 'metal_mine' in structures
        assert 'crystal_mine' in structures
        assert 'deuterium_synthesizer' in structures
        assert 'solar_plant' in structures
        assert 'fusion_reactor' in structures

        # Verify production rates
        production = planet_data['production_rates']
        assert 'metal_per_hour' in production
        assert 'crystal_per_hour' in production
        assert 'deuterium_per_hour' in production
        assert 'energy_production' in production
        assert 'energy_consumption' in production

    def test_get_user_planets_multiple_planets(self, client, sample_user, sample_planet):
        """Test getting multiple planets for a user"""
        headers = make_auth_headers(sample_user.id)

        # Create additional planet for the user
        additional_planet = Planet(
            name='Second Planet',
            x=200, y=300, z=400,
            user_id=sample_user.id,
            metal=5000, crystal=3000, deuterium=1000,
            metal_mine=5, crystal_mine=4, deuterium_synthesizer=3,
            solar_plant=6, fusion_reactor=2
        )
        db.session.add(additional_planet)
        db.session.commit()

        response = client.get('/api/planet', headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert len(data) == 2

        # Verify both planets are returned
        planet_names = [planet['name'] for planet in data]
        assert sample_planet.name in planet_names
        assert 'Second Planet' in planet_names

    def test_get_user_planets_unauthorized(self, client):
        """Test getting planets without JWT token"""
        response = client.get('/api/planet')

        assert response.status_code == 401

    def test_get_specific_planet_success(self, client, sample_user, sample_planet):
        """Test getting specific planet details"""
        headers = make_auth_headers(sample_user.id)

        response = client.get(f'/api/planet/{sample_planet.id}', headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert data['id'] == sample_planet.id
        assert data['name'] == sample_planet.name
        assert data['coordinates'] == f"{sample_planet.x}:{sample_planet.y}:{sample_planet.z}"

        # Verify resources match
        assert data['resources']['metal'] == sample_planet.metal
        assert data['resources']['crystal'] == sample_planet.crystal
        assert data['resources']['deuterium'] == sample_planet.deuterium

        # Verify structures match
        assert data['structures']['metal_mine'] == sample_planet.metal_mine
        assert data['structures']['crystal_mine'] == sample_planet.crystal_mine
        assert data['structures']['deuterium_synthesizer'] == sample_planet.deuterium_synthesizer
        assert data['structures']['solar_plant'] == sample_planet.solar_plant
        assert data['structures']['fusion_reactor'] == sample_planet.fusion_reactor

    def test_get_specific_planet_not_found(self, client, sample_user):
        """Test getting non-existent planet"""
        headers = make_auth_headers(sample_user.id)

        response = client.get('/api/planet/99999', headers=headers)

        assert response.status_code == 404

    def test_get_specific_planet_unowned(self, client, sample_user):
        """Test getting planet owned by different user"""
        headers = make_auth_headers(sample_user.id)

        # Create planet owned by different user
        other_user = User(username='otheruser', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()

        other_planet = Planet(
            name='Other Planet',
            x=100, y=100, z=100,
            user_id=other_user.id
        )
        db.session.add(other_planet)
        db.session.commit()

        response = client.get(f'/api/planet/{other_planet.id}', headers=headers)

        assert response.status_code == 404

    def test_get_specific_planet_unauthorized(self, client, sample_planet):
        """Test getting specific planet without JWT"""
        response = client.get(f'/api/planet/{sample_planet.id}')

        assert response.status_code == 401

    def test_update_buildings_success(self, client, sample_user, sample_planet, db_session):
        """Test successful building upgrades"""
        headers = make_auth_headers(sample_user.id)

        # Set planet with enough resources for upgrades
        sample_planet.metal = 10000
        sample_planet.crystal = 5000
        sample_planet.deuterium = 2000
        db_session.commit()

        # Upgrade metal mine from level 1 to level 2
        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 2,
                'crystal_mine': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        assert 'message' in data
        assert 'resources' in data
        assert 'structures' in data

        # Verify buildings were upgraded
        assert data['structures']['metal_mine'] == 2
        assert data['structures']['crystal_mine'] == 2

        # Verify resources were deducted
        assert data['resources']['metal'] < 10000
        assert data['resources']['crystal'] < 5000

    def test_update_buildings_insufficient_resources(self, client, sample_user, sample_planet):
        """Test building upgrades with insufficient resources"""
        headers = make_auth_headers(sample_user.id)

        # Set planet with insufficient resources
        sample_planet.metal = 10
        sample_planet.crystal = 5

        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 5  # Requires significant resources
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Insufficient resources' in data['error']

    def test_update_buildings_invalid_building(self, client, sample_user, sample_planet):
        """Test building upgrades with invalid building type"""
        headers = make_auth_headers(sample_user.id)

        sample_planet.metal = 10000
        sample_planet.crystal = 5000

        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'invalid_building': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Invalid buildings should be ignored, no changes made
        # The response should not contain the invalid building
        assert 'invalid_building' not in data['structures']

    def test_update_buildings_downgrade_not_allowed(self, client, sample_user, sample_planet):
        """Test that downgrading buildings is not allowed"""
        headers = make_auth_headers(sample_user.id)

        # Current metal mine level is 1
        sample_planet.metal = 10000
        sample_planet.crystal = 5000

        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 0  # Try to downgrade
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Level should remain unchanged (downgrades ignored)
        assert data['structures']['metal_mine'] == sample_planet.metal_mine

    def test_update_buildings_unowned_planet(self, client, sample_user):
        """Test building upgrades on unowned planet"""
        headers = make_auth_headers(sample_user.id)

        # Create planet owned by different user
        other_user = User(username='otheruser', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()

        other_planet = Planet(
            name='Other Planet',
            x=100, y=100, z=100,
            user_id=other_user.id,
            metal=10000, crystal=5000, deuterium=2000
        )
        db.session.add(other_planet)
        db.session.commit()

        upgrade_data = {
            'planet_id': other_planet.id,
            'buildings': {
                'metal_mine': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 404

    def test_update_buildings_missing_data(self, client, sample_user):
        """Test building upgrades with missing required data"""
        headers = make_auth_headers(sample_user.id)

        # Missing planet_id
        incomplete_data = {
            'buildings': {
                'metal_mine': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=incomplete_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_update_buildings_unauthorized(self, client, sample_planet):
        """Test building upgrades without JWT"""
        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 2
            }
        }

        response = client.put('/api/planet/buildings', json=upgrade_data)

        assert response.status_code == 401

    def test_production_rates_calculation(self, client, sample_user, sample_planet):
        """Test production rates calculation with different building levels"""
        headers = make_auth_headers(sample_user.id)

        # Set specific building levels
        sample_planet.metal_mine = 5
        sample_planet.crystal_mine = 4
        sample_planet.deuterium_synthesizer = 3
        sample_planet.solar_plant = 6
        sample_planet.fusion_reactor = 2
        db.session.commit()

        response = client.get(f'/api/planet/{sample_planet.id}', headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        production = data['production_rates']

        # Verify production rates are calculated
        assert production['metal_per_hour'] > 0
        assert production['crystal_per_hour'] > 0
        assert production['deuterium_per_hour'] > 0
        assert production['energy_production'] > 0
        assert production['energy_consumption'] > 0

        # Energy production should be greater than consumption for positive production
        assert production['energy_production'] >= production['energy_consumption']

    def test_production_rates_energy_shortage(self, client, sample_user, sample_planet):
        """Test production rates with energy shortage"""
        headers = make_auth_headers(sample_user.id)

        # Set high consumption, low production
        sample_planet.metal_mine = 10
        sample_planet.crystal_mine = 10
        sample_planet.deuterium_synthesizer = 10
        sample_planet.solar_plant = 1  # Very low energy production
        sample_planet.fusion_reactor = 0
        db.session.commit()

        response = client.get(f'/api/planet/{sample_planet.id}', headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        production = data['production_rates']

        # With energy shortage, production should be reduced
        assert production['energy_consumption'] > production['energy_production']

        # Production rates should be lower due to energy penalty
        assert production['metal_per_hour'] >= 0
        assert production['crystal_per_hour'] >= 0
        assert production['deuterium_per_hour'] >= 0

    def test_building_cost_calculation(self, client, sample_user, sample_planet):
        """Test building upgrade cost calculations"""
        headers = make_auth_headers(sample_user.id)

        # Set exact resources needed for level 2 metal mine
        # Level 2 metal mine costs: 60 * 1.5 = 90 metal, 15 * 1.5 = 22.5 crystal
        sample_planet.metal = 90
        sample_planet.crystal = 23
        sample_planet.deuterium = 1000
        db.session.commit()

        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify exact resource deduction
        assert data['resources']['metal'] == 0  # 90 - 90 = 0
        assert data['resources']['crystal'] == 1  # 23 - 22.5 = 1 (rounded down)
        assert data['structures']['metal_mine'] == 2

class TestPlanetUserIntegration:
    """Test planet user integration scenarios"""

    def test_complete_planet_workflow(self, client, sample_user, sample_planet, db_session):
        """Test complete planet management workflow"""
        headers = make_auth_headers(sample_user.id)

        # 1. Get initial planet state
        response = client.get(f'/api/planet/{sample_planet.id}', headers=headers)
        assert response.status_code == 200
        initial_data = response.get_json()

        # 2. Upgrade buildings
        sample_planet.metal = 10000
        sample_planet.crystal = 5000
        sample_planet.deuterium = 2000
        db_session.commit()

        upgrade_data = {
            'planet_id': sample_planet.id,
            'buildings': {
                'metal_mine': 3,
                'solar_plant': 2
            }
        }

        response = client.put('/api/planet/buildings',
                             json=upgrade_data,
                             headers=headers)
        assert response.status_code == 200

        # 3. Verify upgrades were applied
        response = client.get(f'/api/planet/{sample_planet.id}', headers=headers)
        assert response.status_code == 200
        updated_data = response.get_json()

        assert updated_data['structures']['metal_mine'] == 3
        assert updated_data['structures']['solar_plant'] == 2
        assert updated_data['resources']['metal'] < initial_data['resources']['metal']

    def test_multiple_users_isolation(self, client, sample_user, sample_planet):
        """Test that users can only see their own planets"""
        headers = make_auth_headers(sample_user.id)

        # Create another user and planet
        other_user = User(username='otheruser', email='other@test.com', password_hash='hash')
        db.session.add(other_user)
        db.session.commit()

        other_planet = Planet(
            name='Other Planet',
            x=500, y=600, z=700,
            user_id=other_user.id
        )
        db.session.add(other_planet)
        db.session.commit()

        # Get user's planets
        response = client.get('/api/planet', headers=headers)
        assert response.status_code == 200
        data = response.get_json()

        # Should only see sample_user's planets
        planet_ids = [planet['id'] for planet in data]
        assert sample_planet.id in planet_ids
        assert other_planet.id not in planet_ids

        # Try to access other user's planet directly
        response = client.get(f'/api/planet/{other_planet.id}', headers=headers)
        assert response.status_code == 404
