import os


def test_two_player_scenario_reset_endpoint(app):
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    client = app.test_client()

    res = client.post(
        "/api/admin/scenarios/two-player/reset",
        json={"password": "testpassword123"},
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["users"]["alpha"]["username"] == "alpha"
    assert data["users"]["beta"]["username"] == "beta"
    assert data["users"]["pirates"]["username"] == "pirates"

    with app.app_context():
        from backend.models import User, Planet, Fleet

        assert User.query.filter_by(username="alpha").first() is not None
        assert User.query.filter_by(username="beta").first() is not None
        assert User.query.filter_by(username="pirates").first() is not None

        assert Planet.query.count() == 3
        assert Fleet.query.count() == 3

