import pytest
import json
import os
import sys

class TestPlanetEndpoints:
    """Test planet API endpoints"""

    def test_get_planets_empty(self, client):
        """Test getting planets when none exist"""
        response = client.get('/api/planets')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_planets_with_data(self, client, sample_planet):
        """Test getting planets when data exists"""
        response = client.get('/api/planets')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1

        planet_data = data[0]
        assert planet_data['id'] == sample_planet.id
        assert planet_data['name'] == sample_planet.name
        assert planet_data['coordinates'] == f"{sample_planet.x}:{sample_planet.y}:{sample_planet.z}"
        assert 'resources' in planet_data
        assert 'structures' in planet_data
        assert planet_data['resources']['metal'] == sample_planet.metal

    def test_get_planet_by_id_success(self, client, sample_planet):
        """Test getting a specific planet by ID"""
        response = client.get(f'/api/planets/{sample_planet.id}')
        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['id'] == sample_planet.id
        assert data['name'] == sample_planet.name
        assert data['coordinates'] == f"{sample_planet.x}:{sample_planet.y}:{sample_planet.z}"
        assert data['user_id'] == sample_planet.user_id

    def test_get_planet_by_id_not_found(self, client):
        """Test getting a planet that doesn't exist"""
        response = client.get('/api/planets/99999')
        assert response.status_code == 404

    def test_create_planet_success(self, client, sample_user):
        """Test creating a new planet successfully"""
        planet_data = {
            'name': 'New Planet',
            'x': 10,
            'y': 20,
            'z': 30,
            'user_id': sample_user.id
        }

        response = client.post('/api/planets',
                             data=json.dumps(planet_data),
                             content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        assert data['name'] == 'New Planet'
        assert data['coordinates'] == '10:20:30'
        assert data['user_id'] == sample_user.id

    def test_create_planet_missing_fields(self, client):
        """Test creating a planet with missing required fields"""
        incomplete_data = {
            'name': 'Incomplete Planet',
            'x': 1,
            'y': 2
            # Missing z and user_id
        }

        response = client.post('/api/planets',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_planet_invalid_user(self, client):
        """Test creating a planet with non-existent user"""
        planet_data = {
            'name': 'Orphan Planet',
            'x': 100,
            'y': 200,
            'z': 300,
            'user_id': 99999  # Non-existent user
        }

        response = client.post('/api/planets',
                             data=json.dumps(planet_data),
                             content_type='application/json')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_planet_duplicate_coordinates(self, client, sample_planet):
        """Test creating a planet at occupied coordinates"""
        planet_data = {
            'name': 'Duplicate Planet',
            'x': sample_planet.x,  # Same coordinates as sample_planet
            'y': sample_planet.y,
            'z': sample_planet.z,
            'user_id': sample_planet.user_id
        }

        response = client.post('/api/planets',
                             data=json.dumps(planet_data),
                             content_type='application/json')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_planet_invalid_json(self, client):
        """Test creating a planet with invalid JSON"""
        response = client.post('/api/planets',
                             data='invalid json',
                             content_type='application/json')

        assert response.status_code == 400

class TestPlanetIntegration:
    """Test planet-related integration scenarios"""

    def test_create_multiple_planets(self, client, sample_user):
        """Test creating multiple planets for the same user"""
        planets_data = [
            {'name': 'Planet Alpha', 'x': 1, 'y': 1, 'z': 1, 'user_id': sample_user.id},
            {'name': 'Planet Beta', 'x': 2, 'y': 2, 'z': 2, 'user_id': sample_user.id},
            {'name': 'Planet Gamma', 'x': 3, 'y': 3, 'z': 3, 'user_id': sample_user.id}
        ]

        created_planets = []
        for planet_data in planets_data:
            response = client.post('/api/planets',
                                 data=json.dumps(planet_data),
                                 content_type='application/json')
            assert response.status_code == 201
            created_planets.append(json.loads(response.data))

        # Verify all planets were created
        response = client.get('/api/planets')
        data = json.loads(response.data)
        assert len(data) == 3

        # Verify each planet has correct data
        for i, planet in enumerate(created_planets):
            assert planet['name'] == planets_data[i]['name']
            assert planet['coordinates'] == f"{planets_data[i]['x']}:{planets_data[i]['y']}:{planets_data[i]['z']}"

    def test_planet_resource_data_integrity(self, client, sample_planet):
        """Test that planet resource data is correctly returned"""
        # Update planet with specific resource values
        sample_planet.metal = 50000
        sample_planet.crystal = 25000
        sample_planet.deuterium = 10000
        sample_planet.metal_mine = 8
        sample_planet.crystal_mine = 6
        sample_planet.solar_plant = 12

        from backend.database import db
        db.session.commit()

        # Get planet data
        response = client.get(f'/api/planets/{sample_planet.id}')
        data = json.loads(response.data)

        # Verify resource data
        assert data['resources']['metal'] == 50000
        assert data['resources']['crystal'] == 25000
        assert data['resources']['deuterium'] == 10000

        # Verify structure data
        assert data['structures']['metal_mine'] == 8
        assert data['structures']['crystal_mine'] == 6
        assert data['structures']['solar_plant'] == 12

    def test_planet_listing_includes_all_fields(self, client, sample_planet):
        """Test that planet listing includes all necessary fields"""
        response = client.get('/api/planets')
        data = json.loads(response.data)

        assert len(data) == 1
        planet = data[0]

        required_fields = ['id', 'name', 'coordinates', 'user_id', 'resources', 'structures']
        for field in required_fields:
            assert field in planet

        # Check resources sub-fields
        required_resource_fields = ['metal', 'crystal', 'deuterium']
        for field in required_resource_fields:
            assert field in planet['resources']

        # Check structures sub-fields
        required_structure_fields = ['metal_mine', 'crystal_mine', 'deuterium_synthesizer',
                                   'solar_plant', 'fusion_reactor']
        for field in required_structure_fields:
            assert field in planet['structures']

class TestPlanetEdgeCases:
    """Test planet endpoint edge cases"""

    def test_get_planet_negative_id(self, client):
        """Test getting a planet with negative ID"""
        response = client.get('/api/planets/-1')
        assert response.status_code == 404

    def test_get_planet_zero_id(self, client):
        """Test getting a planet with ID 0"""
        response = client.get('/api/planets/0')
        assert response.status_code == 404

    def test_create_planet_extreme_coordinates(self, client, sample_user):
        """Test creating a planet with extreme coordinate values"""
        planet_data = {
            'name': 'Extreme Planet',
            'x': 999999,
            'y': 999999,
            'z': 999999,
            'user_id': sample_user.id
        }

        response = client.post('/api/planets',
                             data=json.dumps(planet_data),
                             content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['coordinates'] == '999999:999999:999999'

    def test_create_planet_zero_coordinates(self, client, sample_user):
        """Test creating a planet at origin coordinates"""
        planet_data = {
            'name': 'Origin Planet',
            'x': 0,
            'y': 0,
            'z': 0,
            'user_id': sample_user.id
        }

        response = client.post('/api/planets',
                             data=json.dumps(planet_data),
                             content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['coordinates'] == '0:0:0'
