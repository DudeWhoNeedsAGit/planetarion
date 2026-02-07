import pytest
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch
from tests.conftest import make_auth_headers


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
        from backend.models import Planet, User
        from backend.database import db

        enemy = User(
            username='enemyuser',
            email='enemy@example.com',
            password_hash='x',
        )
        db.session.add(enemy)
        db.session.flush()

        target_planet = Planet(
            name='Target Planet',
            x=200, y=200, z=200,
            user_id=enemy.id
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
        # Timestamps should be serialized as UTC with Z suffix so the frontend can compute ETA correctly.
        assert data['fleet']['departure_time'] is None or data['fleet']['departure_time'].endswith('Z')
        assert data['fleet']['arrival_time'] is None or data['fleet']['arrival_time'].endswith('Z')

    def test_send_fleet_forced_nonzero_eta(self, client, sample_fleet):
        """Send should set a non-zero ETA when forced travel time is configured."""
        headers = make_auth_headers(sample_fleet.user_id)

        # Create another planet as target
        from backend.models import Planet, User
        from backend.database import db

        enemy = User(
            username='enemyuser2',
            email='enemy2@example.com',
            password_hash='x',
        )
        db.session.add(enemy)
        db.session.flush()

        target_planet = Planet(
            name='Target Planet 2',
            x=201, y=201, z=201,
            user_id=enemy.id
        )
        db.session.add(target_planet)
        db.session.commit()

        send_data = {
            'fleet_id': sample_fleet.id,
            'target_planet_id': target_planet.id,
            'mission': 'attack'
        }

        with patch('backend.routes.fleet.get_forced_travel_time_seconds', return_value=42):
            response = client.post('/api/fleet/send', json=send_data, headers=headers)

        assert response.status_code == 200
        fleet = response.get_json()['fleet']
        assert fleet['eta'] == 42
        assert fleet['status'] == 'traveling'
        assert fleet['departure_time'].endswith('Z')
        assert fleet['arrival_time'].endswith('Z')

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
        from backend.database import db
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
        from backend.database import db
        db.session.commit()

        response = client.post(f'/api/fleet/recall/{sample_fleet.id}', headers=headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'fleet' in data
        assert data['fleet']['status'] == 'returning'

    def test_recall_fleet_not_found(self, client, sample_user):
        """Test recalling a non-existent fleet"""
        from tests.conftest import make_auth_headers
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/fleet/recall/99999', headers=headers)

        assert response.status_code == 404

    def test_returning_fleet_keeps_start_and_target_planets(self, client, sample_user, sample_planet):
        """Returning fleets should keep start/target stable for UI display (From=start, To=target)."""
        headers = make_auth_headers(sample_user.id)

        from backend.database import db
        from backend.models import Fleet, Planet

        now = datetime.utcnow()
        target_planet = Planet(
            name='Target Planet B',
            x=123,
            y=456,
            z=789,
            user_id=sample_user.id,
        )
        db.session.add(target_planet)
        db.session.flush()

        fleet = Fleet(
            user_id=sample_user.id,
            mission='return',
            status='returning',
            start_planet_id=sample_planet.id,
            target_planet_id=target_planet.id,
            small_cargo=1,
            departure_time=now,
            arrival_time=now + timedelta(seconds=60),
            eta=60,
        )
        db.session.add(fleet)
        db.session.commit()

        response = client.get('/api/fleet', headers=headers)
        assert response.status_code == 200
        fleets = response.get_json()
        returned = next((f for f in fleets if int(f.get('id')) == int(fleet.id)), None)
        assert returned is not None

        assert returned['status'] == 'returning'
        assert returned['start_planet_id'] == sample_planet.id
        assert returned['target_planet_id'] == target_planet.id
        assert returned['start_planet']['id'] == sample_planet.id
        assert returned['target_planet']['id'] == target_planet.id

    def test_dissolve_stationed_fleet_returns_ships_to_inventory(self, client, sample_user, sample_planet):
        """Dissolving a stationed fleet should return ships back into the inventory fleet."""
        headers = make_auth_headers(sample_user.id)

        # Create a small fleet.
        create_payload = {
            'start_planet_id': sample_planet.id,
            'ships': {'small_cargo': 5}
        }
        create_resp = client.post('/api/fleet', json=create_payload, headers=headers)
        assert create_resp.status_code == 201
        created_id = create_resp.get_json()['fleet']['id']

        # Dissolve it.
        dissolve_resp = client.post(f'/api/fleet/{created_id}/dissolve', headers=headers)
        assert dissolve_resp.status_code == 200

        # Inventory fleet should now include the ships again, and the dissolved fleet should be gone.
        fleets = client.get('/api/fleet?include_inventory=1', headers=headers).get_json()
        assert all(f['id'] != created_id for f in fleets)

        inventory = next((f for f in fleets if f.get('mission') == 'inventory'), None)
        assert inventory is not None
        assert inventory['ships']['small_cargo'] >= 5

    def test_dissolve_rejects_traveling_fleet(self, client, sample_fleet):
        headers = make_auth_headers(sample_fleet.user_id)

        # Traveling fleets cannot be dissolved.
        from backend.database import db
        sample_fleet.status = 'traveling'
        db.session.commit()

        resp = client.post(f'/api/fleet/{sample_fleet.id}/dissolve', headers=headers)
        assert resp.status_code == 400

    def test_dissolve_rejects_inventory_fleet(self, client, sample_user, sample_planet):
        headers = make_auth_headers(sample_user.id)

        # Ensure an inventory fleet exists (create_fleet will create it).
        create_payload = {
            'start_planet_id': sample_planet.id,
            'ships': {'small_cargo': 1}
        }
        resp = client.post('/api/fleet', json=create_payload, headers=headers)
        assert resp.status_code == 201

        fleets = client.get('/api/fleet?include_inventory=1', headers=headers).get_json()
        inventory = next((f for f in fleets if f.get('mission') == 'inventory'), None)
        assert inventory is not None

        resp2 = client.post(f"/api/fleet/{inventory['id']}/dissolve", headers=headers)
        assert resp2.status_code == 400
        data = resp2.get_json()
        assert 'error' in data

    def test_recall_fleet_stationed(self, client, sample_fleet):
        """Test recalling a stationed fleet (should fail)"""
        from tests.conftest import make_auth_headers
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
        from tests.conftest import make_auth_headers
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
        from backend.models import Planet
        from backend.database import db
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
        from tests.conftest import make_auth_headers
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
        from tests.conftest import make_auth_headers
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
