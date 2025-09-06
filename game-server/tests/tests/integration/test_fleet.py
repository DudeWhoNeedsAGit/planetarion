import pytest
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch
from src.tests.conftest import make_auth_headers


class TestFleetEndpoints:
    """Test fleet management API endpoints"""

    def test_get_user_fleets_empty(self, client, sample_user):
        """Test getting fleets when user has none"""
        headers = make_auth_headers(sample_user.id)

        response = client.get('/api/fleet', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_fleets_with_data(self, client, sample_fleet):
        """Test getting fleets when user has fleets"""
        headers = make_auth_headers(sample_fleet.user_id)

        response = client.get('/api/fleet', headers=headers)
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

        fleet_data = data[0]
        assert fleet_data['id'] == sample_fleet.id
        assert fleet_data['mission'] == sample_fleet.mission
        assert 'ships' in fleet_data
        assert fleet_data['ships']['small_cargo'] == sample_fleet.small_cargo

    def test_create_fleet_success(self, client, sample_user, sample_planet):
        """Test creating a new fleet successfully"""
        headers = make_auth_headers(sample_user.id)

        fleet_data = {
            'start_planet_id': sample_planet.id,
            'ships': {
                'small_cargo': 5,
                'large_cargo': 3,
                'light_fighter': 10
            }
        }

        response = client.post('/api/fleet',
                             json=fleet_data,
                             headers=headers)

        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        assert 'fleet' in data
        assert data['fleet']['mission'] == 'stationed'
        assert data['fleet']['ships']['small_cargo'] == 5

    def test_create_fleet_missing_fields(self, client, sample_user):
        """Test creating a fleet with missing required fields"""
        headers = make_auth_headers(sample_user.id)

        incomplete_data = {
            'ships': {'small_cargo': 5}
            # Missing start_planet_id
        }

        response = client.post('/api/fleet',
                             json=incomplete_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_create_fleet_invalid_planet(self, client, sample_user):
        """Test creating a fleet on a planet not owned by user"""
        headers = make_auth_headers(sample_user.id)

        fleet_data = {
            'start_planet_id': 99999,  # Non-existent planet
            'ships': {'small_cargo': 5}
        }

        response = client.post('/api/fleet',
                             json=fleet_data,
                             headers=headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_create_fleet_empty_ships(self, client, sample_user, sample_planet):
        """Test creating a fleet with no ships"""
        headers = make_auth_headers(sample_user.id)

        fleet_data = {
            'start_planet_id': sample_planet.id,
            'ships': {}  # Empty ships
        }

        response = client.post('/api/fleet',
                             json=fleet_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_send_fleet_success(self, client, sample_fleet):
        """Test sending a fleet successfully"""
        headers = make_auth_headers(sample_fleet.user_id)

        # Create another planet as target
        from src.backend.models import Planet
        from src.backend.database import db

        target_planet = Planet(
            name='Target Planet',
            x=200, y=200, z=200,
            user_id=sample_fleet.user_id
        )
        db.session.add(target_planet)
        db.session.commit()

        send_data = {
            'fleet_id': sample_fleet.id,
            'target_planet_id': target_planet.id,
            'mission': 'attack'
        }

        response = client.post('/api/fleet/send',
                             json=send_data,
                             headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'fleet' in data
        assert data['fleet']['status'] == 'traveling'
        assert data['fleet']['mission'] == 'attack'

    def test_send_fleet_invalid_fleet(self, client, sample_user):
        """Test sending a non-existent fleet"""
        headers = make_auth_headers(sample_user.id)

        send_data = {
            'fleet_id': 99999,
            'target_planet_id': 1,
            'mission': 'transport'
        }

        response = client.post('/api/fleet/send',
                             json=send_data,
                             headers=headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_send_fleet_already_moving(self, client, sample_fleet):
        """Test sending a fleet that's already moving"""
        headers = make_auth_headers(sample_fleet.user_id)

        # Set fleet to traveling
        sample_fleet.status = 'traveling'
        from src.backend.database import db
        db.session.commit()

        send_data = {
            'fleet_id': sample_fleet.id,
            'target_planet_id': 1,
            'mission': 'attack'
        }

        response = client.post('/api/fleet/send',
                             json=send_data,
                             headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_recall_fleet_success(self, client, sample_fleet):
        """Test recalling a fleet successfully"""
        headers = make_auth_headers(sample_fleet.user_id)

        # Set fleet to traveling
        sample_fleet.status = 'traveling'
        sample_fleet.arrival_time = datetime.utcnow() + timedelta(hours=2)
        from src.backend.database import db
        db.session.commit()

        response = client.post(f'/api/fleet/recall/{sample_fleet.id}', headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'fleet' in data
        assert data['fleet']['status'] == 'returning'

    def test_recall_fleet_not_found(self, client, sample_user):
        """Test recalling a non-existent fleet"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/fleet/recall/99999', headers=headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_recall_fleet_stationed(self, client, sample_fleet):
        """Test recalling a stationed fleet (should fail)"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_fleet.user_id)
        # Fleet is already stationed by default
        response = client.post(f'/api/fleet/recall/{sample_fleet.id}', headers=headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

class TestFleetIntegration:
    """Test fleet-related integration scenarios"""

    def test_fleet_lifecycle(self, client, sample_user, sample_planet):
        """Test complete fleet lifecycle: create -> send -> recall"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_user.id)

        # Create fleet
        fleet_data = {
            'start_planet_id': sample_planet.id,
            'ships': {
                'small_cargo': 10,
                'light_fighter': 5
            }
        }

        # Create
        response = client.post('/api/fleet',
                             json=fleet_data,
                             headers=headers)
        assert response.status_code == 201
        fleet_id = response.get_json()['fleet']['id']

        # Create target planet
        from src.backend.models import Planet
        from src.backend.database import db
        target_planet = Planet(
            name='Target', x=100, y=100, z=100,
            user_id=sample_user.id
        )
        db.session.add(target_planet)
        db.session.commit()

        # Send
        send_data = {
            'fleet_id': fleet_id,
            'target_planet_id': target_planet.id,
            'mission': 'transport'
        }
        response = client.post('/api/fleet/send',
                             json=send_data,
                             headers=headers)
        assert response.status_code == 200

        # Recall
        response = client.post(f'/api/fleet/recall/{fleet_id}', headers=headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['fleet']['status'] == 'returning'

    def test_multiple_fleets_per_user(self, client, sample_user, sample_planet):
        """Test user having multiple fleets"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_user.id)

        # Create multiple fleets
        fleets_data = [
            {'start_planet_id': sample_planet.id, 'ships': {'small_cargo': 5}},
            {'start_planet_id': sample_planet.id, 'ships': {'large_cargo': 3}},
            {'start_planet_id': sample_planet.id, 'ships': {'light_fighter': 8}}
        ]

        for fleet_data in fleets_data:
            response = client.post('/api/fleet',
                                 json=fleet_data,
                                 headers=headers)
            assert response.status_code == 201

        # Get all fleets
        response = client.get('/api/fleet', headers=headers)
        data = response.get_json()
        assert len(data) == 3

class TestFleetEdgeCases:
    """Test fleet endpoint edge cases"""

    def test_send_fleet_same_planet(self, client, sample_fleet):
        """Test sending fleet to same planet (should still work)"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_fleet.user_id)

        send_data = {
            'fleet_id': sample_fleet.id,
            'target_planet_id': sample_fleet.start_planet_id,  # Same planet
            'mission': 'deploy'
        }

        response = client.post('/api/fleet/send',
                             json=send_data,
                             headers=headers)

        # Should work, though travel time might be minimal
        assert response.status_code == 200

    def test_create_fleet_max_ships(self, client, sample_user, sample_planet):
        """Test creating fleet with maximum ship counts"""
        from conftest import make_auth_headers
        headers = make_auth_headers(sample_user.id)

        fleet_data = {
            'start_planet_id': sample_planet.id,
            'ships': {
                'small_cargo': 1000000,
                'large_cargo': 500000,
                'light_fighter': 200000,
                'heavy_fighter': 100000,
                'cruiser': 50000,
                'battleship': 10000
            }
        }

        response = client.post('/api/fleet',
                             json=fleet_data,
                             headers=headers)

        assert response.status_code == 201
        data = response.get_json()
        assert data['fleet']['ships']['small_cargo'] == 1000000

    def test_get_fleets_unauthorized(self, client):
        """Test getting fleets without JWT token"""
        response = client.get('/api/fleet')
        assert response.status_code == 401

    def test_create_fleet_unauthorized(self, client):
        """Test creating fleet without JWT token"""
        response = client.post('/api/fleet', data=json.dumps({}))
        assert response.status_code == 401
