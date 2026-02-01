from datetime import datetime, timedelta


def _ff_arrive(db_session, fleet):
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()


def _tick(app):
    from backend.services.tick import run_tick
    with app.app_context():
        run_tick()


def test_two_player_golden_path_to_capture(app, client, db_session):
    # Create the deterministic scenario.
    import os

    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    res = client.post(
        "/api/admin/scenarios/two-player/reset",
        json={"password": "testpassword123"},
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert res.status_code == 200
    scenario = res.get_json()

    alpha_fleet_id = scenario["fleets"]["alpha_fleet_id"]
    beta_home_id = scenario["planets"]["beta_home"]["id"]
    pirate_camp_id = scenario["planets"]["pirate_camp"]["id"]

    # Login alpha so we can use the API send endpoints.
    login = client.post("/api/auth/login", json={"username": "alpha", "password": "testpassword123"})
    assert login.status_code == 200
    token = login.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1) Attack pirates once (creates combat report, often debris).
    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": alpha_fleet_id, "mission": "attack", "target_planet_id": pirate_camp_id},
        headers=headers,
    )
    assert send.status_code == 200

    from backend.models import Fleet, CombatReport, DebrisField, Planet

    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # process combat + set returning
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "returning"

    # Return arrival
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "stationed"

    assert CombatReport.query.count() >= 1

    # 2) If debris exists at pirate camp, recycle it.
    debris = DebrisField.query.filter_by(planet_id=pirate_camp_id).first()
    if debris:
        before_metal = Planet.query.get(alpha_fleet.start_planet_id).metal
        recycle_send = client.post(
            "/api/fleet/send",
            json={"fleet_id": alpha_fleet_id, "mission": "recycle", "target_planet_id": pirate_camp_id},
            headers=headers,
        )
        assert recycle_send.status_code == 200
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)  # collect -> returning with cargo
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "returning"
        assert (alpha_fleet.cargo_metal or 0) >= 0

        _ff_arrive(db_session, alpha_fleet)
        _tick(app)  # deliver cargo
        after_metal = Planet.query.get(alpha_fleet.start_planet_id).metal
        assert after_metal >= before_metal

    # 3) Spy beta once.
    spy_send = client.post(
        "/api/fleet/send",
        json={"fleet_id": alpha_fleet_id, "mission": "espionage", "target_planet_id": beta_home_id},
        headers=headers,
    )
    assert spy_send.status_code == 200
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # create report + returning
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "returning"
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "stationed"

    # 4) Do two player fights (attack beta) to generate reports.
    for _ in range(2):
        fight = client.post(
            "/api/fleet/send",
            json={"fleet_id": alpha_fleet_id, "mission": "attack", "target_planet_id": beta_home_id},
            headers=headers,
        )
        assert fight.status_code == 200
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "returning"
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "stationed"

    assert CombatReport.query.count() >= 3  # pirate + 2 player fights

    # 5) Force "undefended" capture rule for MVP conquest:
    # remove any defending fleet parked at beta home.
    from backend.models import User
    beta_user = User.query.filter_by(username="beta").first()
    assert beta_user is not None
    defending = (
        Fleet.query.filter(
            Fleet.user_id == beta_user.id,
            Fleet.start_planet_id == beta_home_id,
            Fleet.status.in_(["stationed", "defending"]),
        )
        .order_by(Fleet.id.asc())
        .all()
    )
    for f in defending:
        db_session.delete(f)
    db_session.commit()

    capture = client.post(
        "/api/fleet/send",
        json={"fleet_id": alpha_fleet_id, "mission": "attack", "target_planet_id": beta_home_id},
        headers=headers,
    )
    assert capture.status_code == 200
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # should capture since undefended

    beta_home = Planet.query.get(beta_home_id)
    assert beta_home.user_id == scenario["users"]["alpha"]["id"]

