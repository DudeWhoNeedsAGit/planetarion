from __future__ import annotations

from datetime import datetime, timedelta

import os

def _ff_arrive(db_session, fleet):
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()


def _tick(app):
    from backend.services.tick import run_tick

    with app.app_context():
        run_tick()


def _reset_two_player_scenario(client):
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    res = client.post(
        "/api/admin/scenarios/two-player/reset",
        json={"password": "testpassword123"},
        headers={"X-Planetarion-Dev-Token": "test-token"},
    )
    assert res.status_code == 200, res.get_data(as_text=True)
    return res.get_json()


def _login(client, username: str, password: str = "testpassword123") -> dict:
    login = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200, login.get_data(as_text=True)
    token = login.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_table_a_backend_golden_path_arcade_discovery(app, client, db_session):
    """Table A: backend golden-path integration test (deterministic, arcade discovery).

    Covers:
    - pirate raid -> combat report (+ optional debris)
    - recycle debris -> resources credited on return
    - espionage -> report created
    - war arc -> 5 battles total (pirate + 4 vs beta)
    - conquest -> capture beta home when undefended
    """

    scenario = _reset_two_player_scenario(client)

    alpha_fleet_id = scenario["fleets"]["alpha_fleet_id"]
    beta_home_id = scenario["planets"]["beta_home"]["id"]
    pirate_camp_id = scenario["planets"]["pirate_camp"]["id"]
    alpha_id = scenario["users"]["alpha"]["id"]
    beta_id = scenario["users"]["beta"]["id"]

    headers = _login(client, "alpha")

    from backend.models import CombatReport, DebrisField, EspionageReport, Fleet, Planet

    # 1) Pirate raid (creates combat report; may create debris).
    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": alpha_fleet_id, "mission": "attack", "target_planet_id": pirate_camp_id},
        headers=headers,
    )
    assert send.status_code == 200, send.get_data(as_text=True)

    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # combat + set returning
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "returning"

    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # return to stationed
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "stationed"

    assert CombatReport.query.count() >= 1

    # 2) Optional recycle loop if debris exists at pirate camp.
    debris = DebrisField.query.filter_by(planet_id=pirate_camp_id).first()
    if debris:
        origin_planet_id = alpha_fleet.start_planet_id
        before_metal = Planet.query.get(origin_planet_id).metal
        before_crystal = Planet.query.get(origin_planet_id).crystal

        recycle_send = client.post(
            "/api/fleet/send",
            json={"fleet_id": alpha_fleet_id, "mission": "recycle", "target_planet_id": pirate_camp_id},
            headers=headers,
        )
        assert recycle_send.status_code == 200, recycle_send.get_data(as_text=True)

        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)  # collect -> returning with cargo
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "returning"

        _ff_arrive(db_session, alpha_fleet)
        _tick(app)  # deliver cargo
        after_origin = Planet.query.get(origin_planet_id)
        assert after_origin.metal >= before_metal
        assert after_origin.crystal >= before_crystal

    # 3) Espionage (creates report).
    spy_send = client.post(
        "/api/fleet/send",
        json={"fleet_id": alpha_fleet_id, "mission": "espionage", "target_planet_id": beta_home_id},
        headers=headers,
    )
    assert spy_send.status_code == 200, spy_send.get_data(as_text=True)
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # create report + returning
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "returning"
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    assert alpha_fleet.status == "stationed"
    assert EspionageReport.query.count() >= 1

    # 4) War arc: do 4 fights vs beta (combined with pirate raid => 5 battles total).
    for _ in range(4):
        fight = client.post(
            "/api/fleet/send",
            json={"fleet_id": alpha_fleet_id, "mission": "attack", "target_planet_id": beta_home_id},
            headers=headers,
        )
        assert fight.status_code == 200, fight.get_data(as_text=True)
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "returning"
        _ff_arrive(db_session, alpha_fleet)
        _tick(app)
        alpha_fleet = Fleet.query.get(alpha_fleet_id)
        assert alpha_fleet.status == "stationed"

    assert CombatReport.query.count() >= 5

    # 5) Conquest: MVP rule says capture only if undefended.
    # Ensure beta has no stationed/defending fleet at beta home.
    defending = (
        Fleet.query.filter(
            Fleet.user_id == beta_id,
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
    assert capture.status_code == 200, capture.get_data(as_text=True)
    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)  # capture since undefended

    beta_home = Planet.query.get(beta_home_id)
    assert beta_home.user_id == alpha_id

    assert Planet.query.filter_by(user_id=beta_id).count() == 0


def test_table_a_respawn_after_elimination_expected_future(app, client, db_session):
    """Tracks Phase 7 requirement: if user has 0 planets after conquest, they respawn within 1 tick."""

    scenario = _reset_two_player_scenario(client)
    alpha_fleet_id = scenario["fleets"]["alpha_fleet_id"]
    beta_home_id = scenario["planets"]["beta_home"]["id"]
    beta_id = scenario["users"]["beta"]["id"]

    headers = _login(client, "alpha")

    from backend.models import Fleet, Planet

    # Remove beta defending fleets so capture works deterministically.
    defending = (
        Fleet.query.filter(
            Fleet.user_id == beta_id,
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
    assert capture.status_code == 200, capture.get_data(as_text=True)

    alpha_fleet = Fleet.query.get(alpha_fleet_id)
    _ff_arrive(db_session, alpha_fleet)
    _tick(app)

    assert Planet.query.filter_by(user_id=beta_id).count() == 0

    # Phase 7 requirement: on next tick, beta gets a new home planet + protection.
    _tick(app)
    assert Planet.query.filter_by(user_id=beta_id).count() >= 1

    from backend.models import User
    beta = User.query.get(beta_id)
    assert beta is not None
    assert beta.respawned_at is not None
    assert beta.protection_until is not None
