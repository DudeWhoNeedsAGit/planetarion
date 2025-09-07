"""
Test the populate API endpoint
"""
import pytest
from backend.models import User, Planet, Fleet, Alliance, TickLog


def test_populate_endpoint(client, app):
    """Test that the populate endpoint creates test data correctly"""

    # Call the populate endpoint with deterministic mode for consistent results
    response = client.post('/populate?deterministic=true')
    assert response.status_code == 200

    data = response.get_json()
    assert 'message' in data
    assert 'users' in data
    assert 'planets' in data
    assert 'fleets' in data
    assert 'alliances' in data
    assert 'tick_logs' in data

    # Verify data was created
    with app.app_context():
        # Check users
        users = User.query.all()
        assert len(users) == data['users']
        assert data['users'] >= 200  # Should have at least 200 users

        # Check that test user exists
        test_user = User.query.filter_by(username='e2etestuser').first()
        assert test_user is not None
        assert test_user.email == 'e2etestuser@example.com'

        # Check planets
        planets = Planet.query.all()
        assert len(planets) == data['planets']
        assert data['planets'] >= 200  # Should have at least 200 planets (1-5 per user)

        # Check fleets
        fleets = Fleet.query.all()
        assert len(fleets) == data['fleets']
        assert data['fleets'] >= 500  # Should have at least 500 fleets

        # Check alliances
        alliances = Alliance.query.all()
        assert len(alliances) == data['alliances']
        assert data['alliances'] >= 20  # Should have at least 20 alliances

        # Check tick logs
        tick_logs = TickLog.query.all()
        assert len(tick_logs) == data['tick_logs']
        assert data['tick_logs'] >= 1000  # Should have at least 1000 tick logs

        # Verify relationships
        for planet in planets[:5]:  # Check first 5 planets
            assert planet.user_id is not None
            user = User.query.get(planet.user_id)
            assert user is not None

        for fleet in fleets[:5]:  # Check first 5 fleets
            assert fleet.user_id is not None
            assert fleet.start_planet_id is not None
            assert fleet.target_planet_id is not None

            user = User.query.get(fleet.user_id)
            start_planet = Planet.query.get(fleet.start_planet_id)
            target_planet = Planet.query.get(fleet.target_planet_id)

            assert user is not None
            assert start_planet is not None
            assert target_planet is not None


def test_populate_endpoint_idempotent(client, app):
    """Test that calling populate multiple times works correctly"""

    # Call populate twice with deterministic mode for identical results
    response1 = client.post('/populate?deterministic=true')
    response2 = client.post('/populate?deterministic=true')

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Both should succeed (data should be cleared and recreated)
    data1 = response1.get_json()
    data2 = response2.get_json()

    # With deterministic mode, results should be identical
    assert data1['users'] == data2['users']
    assert data1['planets'] == data2['planets']
    assert data1['fleets'] == data2['fleets']
    assert data1['alliances'] == data2['alliances']
    assert data1['tick_logs'] == data2['tick_logs']


def test_populate_creates_test_user_for_e2e(client, app):
    """Test that populate creates the specific test user needed for E2E tests"""

    print("\n=== DEBUG: Starting populate test ===")

    # Call the populate endpoint with deterministic mode
    print("DEBUG: Calling /populate endpoint...")
    response = client.post('/populate?deterministic=true')

    print(f"DEBUG: Response status code: {response.status_code}")
    print(f"DEBUG: Response headers: {dict(response.headers)}")

    if response.status_code != 200:
        print(f"DEBUG: Response data: {response.get_data(as_text=True)}")
        # Try to get JSON error details
        try:
            error_data = response.get_json()
            print(f"DEBUG: JSON error response: {error_data}")
        except:
            print("DEBUG: Could not parse JSON error response")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.get_json()
    print(f"DEBUG: Response data: {data}")

    with app.app_context():
        print("DEBUG: Checking database state...")

        # Check total users
        all_users = User.query.all()
        print(f"DEBUG: Total users in database: {len(all_users)}")
        for user in all_users[:3]:  # Show first 3 users
            print(f"DEBUG: User: {user.username} ({user.email})")

        # Verify the E2E test user exists
        test_user = User.query.filter_by(username='e2etestuser').first()
        print(f"DEBUG: Test user found: {test_user is not None}")

        if test_user:
            print(f"DEBUG: Test user details: {test_user.username} ({test_user.email})")
        else:
            print("DEBUG: Test user NOT found!")
            # Show all usernames to debug
            usernames = [u.username for u in all_users]
            print(f"DEBUG: All usernames: {usernames}")

        assert test_user is not None, "E2E test user 'e2etestuser' was not created"
        assert test_user.email == 'e2etestuser@example.com'

        # Verify the test user has planets
        user_planets = Planet.query.filter_by(user_id=test_user.id).all()
        print(f"DEBUG: Test user planets: {len(user_planets)}")

        assert len(user_planets) >= 1, f"Test user should have at least 1 planet, got {len(user_planets)}"

        # Verify the test user can create fleets (has planets to fleet from)
        assert len(user_planets) > 0

        print("DEBUG: Test completed successfully!")
