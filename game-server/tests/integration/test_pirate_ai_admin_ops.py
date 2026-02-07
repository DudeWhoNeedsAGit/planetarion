import os


def _seed_user(db_session, *, username: str, email: str):
    import bcrypt
    from backend.models import User

    pw = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=email, password_hash=pw)
    db_session.add(user)
    db_session.commit()
    return user


def test_pirate_ai_status_returns_blocked_reasons(app, db_session):
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    client = app.test_client()

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        _seed_user(db_session, username="player_status", email="player_status@example.com")

    res = client.get(
        "/api/admin/pirate-ai/status",
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert res.status_code == 200
    payload = res.get_json()

    assert payload["enabled"] is True
    assert "blocked_reasons" in payload
    assert payload["blocked_reasons"]["pirates_user_missing"] == 1
    assert "raids_spawned_last_24h" in payload
    assert "last_run_at" in payload


def test_pirate_ai_config_endpoint_allowlists_updates(app, db_session):
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    client = app.test_client()

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = False
        app.config["PIRATE_AI_DIFFICULTY_FACTOR"] = 0.8

    res = client.post(
        "/api/admin/pirate-ai/config",
        json={
            "updates": {
                "PIRATE_AI_ENABLED": True,
                "PIRATE_AI_DIFFICULTY_FACTOR": 1.4,
                "PIRATE_AI_SECRET_SALT": "blocked",
            }
        },
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert res.status_code == 400
    payload = res.get_json()
    assert payload["applied"]["PIRATE_AI_ENABLED"] is True
    assert float(payload["applied"]["PIRATE_AI_DIFFICULTY_FACTOR"]) == 1.4
    assert payload["errors"]["PIRATE_AI_SECRET_SALT"] == "Not allowlisted"

    with app.app_context():
        from backend.models import PirateAIConfigOverride
        from backend.services.pirate_ai import PirateAILiveOps

        # Values persisted for restart-safe behavior.
        enabled_row = PirateAIConfigOverride.query.filter_by(config_key="PIRATE_AI_ENABLED").first()
        diff_row = PirateAIConfigOverride.query.filter_by(config_key="PIRATE_AI_DIFFICULTY_FACTOR").first()
        assert enabled_row is not None
        assert diff_row is not None

        # Simulate restart-style reload from persisted overrides.
        app.config["PIRATE_AI_ENABLED"] = False
        app.config["PIRATE_AI_DIFFICULTY_FACTOR"] = 0.1
        PirateAILiveOps.apply_persisted_overrides()
        assert app.config["PIRATE_AI_ENABLED"] is True
        assert float(app.config["PIRATE_AI_DIFFICULTY_FACTOR"]) == 1.4

    read_res = client.get(
        "/api/admin/pirate-ai/config",
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert read_res.status_code == 200
    read_payload = read_res.get_json()
    assert read_payload["effective"]["PIRATE_AI_ENABLED"] is True
    assert float(read_payload["effective"]["PIRATE_AI_DIFFICULTY_FACTOR"]) == 1.4
