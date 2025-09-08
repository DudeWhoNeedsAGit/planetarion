"""
Integration tests for Combat API endpoints

Tests the combat-related API endpoints including:
- Battle reports retrieval
- Debris field information
- Combat statistics
"""

import pytest
import json
from unittest.mock import patch
from backend.models import User, Planet, Fleet, CombatReport, DebrisField


def test_get_combat_reports_empty(client, db_session):
    """Test getting combat reports when user has none"""
    # Create test user
    user = User(username='testuser', email='test@example.com', password_hash='hash')
    db_session.add(user)
    db_session.commit()

    # Login to get token
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })

    assert response.status_code == 401  # Should fail with wrong password

    # For testing purposes, we'll mock the JWT requirement
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=user.id):
            response = client.get('/api/combat/reports')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'reports' in data
            assert 'total' in data
            assert data['total'] == 0
            assert len(data['reports']) == 0


def test_get_combat_reports_with_data(client, db_session):
    """Test getting combat reports when user has battle history"""
    # Create test users
    attacker = User(username='attacker', email='attacker@example.com', password_hash='hash')
    defender = User(username='defender', email='defender@example.com', password_hash='hash')
    db_session.add(attacker)
    db_session.add(defender)

    # Create planet
    planet = Planet(name='Battle Planet', x=100, y=200, z=300, user_id=defender.id)
    db_session.add(planet)
    db_session.commit()

    # Create combat report
    report = CombatReport(
        attacker_id=attacker.id,
        defender_id=defender.id,
        planet_id=planet.id,
        winner_id=attacker.id,
        rounds=json.dumps([{'round': 1, 'damage': 100}]),
        attacker_losses=json.dumps({'light_fighter': 5}),
        defender_losses=json.dumps({'cruiser': 2}),
        debris_metal=1000,
        debris_crystal=500
    )
    db_session.add(report)
    db_session.commit()

    # Mock JWT for attacker
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=attacker.id):
            response = client.get('/api/combat/reports')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['total'] == 1
            assert len(data['reports']) == 1

            report_data = data['reports'][0]
            assert report_data['id'] == report.id
            assert report_data['attacker']['username'] == 'attacker'
            assert report_data['defender']['username'] == 'defender'
            assert report_data['winner']['username'] == 'attacker'
            assert report_data['debris_metal'] == 1000
            assert report_data['debris_crystal'] == 500


def test_get_combat_report_detail(client, db_session):
    """Test getting detailed combat report by ID"""
    # Create test users and planet
    attacker = User(username='attacker', email='attacker@example.com', password_hash='hash')
    defender = User(username='defender', email='defender@example.com', password_hash='hash')
    db_session.add(attacker)
    db_session.add(defender)

    planet = Planet(name='Battle Planet', x=100, y=200, z=300, user_id=defender.id)
    db_session.add(planet)
    db_session.commit()

    # Create combat report
    report = CombatReport(
        attacker_id=attacker.id,
        defender_id=defender.id,
        planet_id=planet.id,
        winner_id=attacker.id,
        rounds=json.dumps([{'round': 1, 'damage': 100}]),
        attacker_losses=json.dumps({'light_fighter': 5}),
        defender_losses=json.dumps({'cruiser': 2}),
        debris_metal=1000,
        debris_crystal=500
    )
    db_session.add(report)
    db_session.commit()

    # Mock JWT for attacker
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=attacker.id):
            response = client.get(f'/api/combat/reports/{report.id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == report.id
            assert data['attacker']['username'] == 'attacker'
            assert data['defender']['username'] == 'defender'
            assert data['planet']['name'] == 'Battle Planet'
            assert data['winner']['username'] == 'attacker'


def test_get_combat_report_unauthorized(client, db_session):
    """Test that users cannot access reports they're not involved in"""
    # Create test users
    attacker = User(username='attacker', email='attacker@example.com', password_hash='hash')
    defender = User(username='defender', email='defender@example.com', password_hash='hash')
    third_party = User(username='third', email='third@example.com', password_hash='hash')
    db_session.add(attacker)
    db_session.add(defender)
    db_session.add(third_party)

    # Create planet
    planet = Planet(name='Battle Planet', x=100, y=200, z=300, user_id=defender.id)
    db_session.add(planet)
    db_session.commit()

    # Create combat report
    report = CombatReport(
        attacker_id=attacker.id,
        defender_id=defender.id,
        planet_id=planet.id,
        winner_id=attacker.id,
        rounds=json.dumps([{'round': 1, 'damage': 100}]),
        attacker_losses=json.dumps({'light_fighter': 5}),
        defender_losses=json.dumps({'cruiser': 2}),
        debris_metal=1000,
        debris_crystal=500
    )
    db_session.add(report)
    db_session.commit()

    # Mock JWT for third party user
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=third_party.id):
            response = client.get(f'/api/combat/reports/{report.id}')

            assert response.status_code == 403
            data = json.loads(response.data)
            assert 'error' in data


def test_get_debris_fields(client, db_session):
    """Test getting debris fields"""
    # Create test user and planet
    user = User(username='testuser', email='testuser@example.com', password_hash='hash')
    db_session.add(user)

    planet = Planet(name='Debris Planet', x=100, y=200, z=300, user_id=user.id)
    db_session.add(planet)
    db_session.commit()

    # Create debris field
    debris = DebrisField(
        planet_id=planet.id,
        metal=5000,
        crystal=3000,
        deuterium=1000
    )
    db_session.add(debris)
    db_session.commit()

    # Mock JWT
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=user.id):
            response = client.get('/api/combat/debris')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'debris_fields' in data
            assert len(data['debris_fields']) == 1

            debris_data = data['debris_fields'][0]
            assert debris_data['planet']['name'] == 'Debris Planet'
            assert debris_data['resources']['metal'] == 5000
            assert debris_data['resources']['crystal'] == 3000
            assert debris_data['resources']['deuterium'] == 1000


def test_get_planet_debris(client, db_session):
    """Test getting debris field for specific planet"""
    # Create test user and planet
    user = User(username='testuser', email='testuser@example.com', password_hash='hash')
    db_session.add(user)

    planet = Planet(name='Debris Planet', x=100, y=200, z=300, user_id=user.id)
    db_session.add(planet)
    db_session.commit()

    # Create debris field
    debris = DebrisField(
        planet_id=planet.id,
        metal=5000,
        crystal=3000,
        deuterium=1000
    )
    db_session.add(debris)
    db_session.commit()

    # Mock JWT
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=user.id):
            response = client.get(f'/api/combat/debris/{planet.id}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['planet']['name'] == 'Debris Planet'
            assert data['resources']['metal'] == 5000
            assert data['resources']['crystal'] == 3000
            assert data['resources']['deuterium'] == 1000


def test_get_planet_debris_not_found(client, db_session):
    """Test getting debris field for planet with no debris"""
    # Create test user and planet
    user = User(username='testuser', email='testuser@example.com', password_hash='hash')
    db_session.add(user)

    planet = Planet(name='Clean Planet', x=100, y=200, z=300, user_id=user.id)
    db_session.add(planet)
    db_session.commit()

    # Mock JWT
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=user.id):
            response = client.get(f'/api/combat/debris/{planet.id}')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data


def test_get_combat_statistics(client, db_session):
    """Test getting combat statistics for user"""
    # Create test user
    user = User(username='testuser', email='testuser@example.com', password_hash='hash')
    db_session.add(user)
    db_session.commit()

    # Create some fleets with combat stats
    fleet1 = Fleet(
        user_id=user.id,
        mission='stationed',
        start_planet_id=1,
        target_planet_id=1,
        combat_victories=3,
        combat_defeats=1,
        combat_experience=150
    )
    fleet2 = Fleet(
        user_id=user.id,
        mission='stationed',
        start_planet_id=1,
        target_planet_id=1,
        combat_victories=2,
        combat_defeats=0,
        combat_experience=100
    )
    db_session.add(fleet1)
    db_session.add(fleet2)
    db_session.commit()

    # Mock JWT
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=user.id):
            response = client.get('/api/combat/statistics')

            assert response.status_code == 200
            data = json.loads(response.data)

            # Check fleet statistics
            fleet_stats = data['fleet_statistics']
            assert fleet_stats['total_victories'] == 5  # 3 + 2
            assert fleet_stats['total_defeats'] == 1  # 1 + 0
            assert fleet_stats['total_experience'] == 250  # 150 + 100

            # Check battle statistics (would be populated with actual combat reports)
            battle_stats = data['battle_statistics']
            assert 'total_battles' in battle_stats
            assert 'battles_won' in battle_stats
            assert 'battles_lost' in battle_stats
            assert 'win_rate' in battle_stats


def test_combat_reports_pagination(client, db_session):
    """Test combat reports pagination"""
    # Create test users
    attacker = User(username='attacker', email='attacker@example.com', password_hash='hash')
    defender = User(username='defender', email='defender@example.com', password_hash='hash')
    db_session.add(attacker)
    db_session.add(defender)

    # Create planet
    planet = Planet(name='Battle Planet', x=100, y=200, z=300, user_id=defender.id)
    db_session.add(planet)
    db_session.commit()

    # Create multiple combat reports
    reports = []
    for i in range(5):
        report = CombatReport(
            attacker_id=attacker.id,
            defender_id=defender.id,
            planet_id=planet.id,
            winner_id=attacker.id,
            rounds=json.dumps([{'round': 1, 'damage': 100}]),
            attacker_losses=json.dumps({'light_fighter': 5}),
            defender_losses=json.dumps({'cruiser': 2}),
            debris_metal=1000,
            debris_crystal=500
        )
        reports.append(report)
        db_session.add(report)
    db_session.commit()

    # Mock JWT for attacker
    with client.application.test_request_context():
        with patch('flask_jwt_extended.get_jwt_identity', return_value=attacker.id):
            # Test pagination with limit
            response = client.get('/api/combat/reports?limit=2&offset=1')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['reports']) == 2
            assert data['limit'] == 2
            assert data['offset'] == 1
            assert data['total'] == 2  # Only 2 returned due to limit
