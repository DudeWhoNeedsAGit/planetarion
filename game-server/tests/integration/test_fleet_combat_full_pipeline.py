"""
Fleet/Combat/Colonization "Full Pipeline" Integration Tests

These tests avoid mocking the combat engine and the arrival service.
They exercise the actual HTTP endpoints + tick-driven arrival processing.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import bcrypt

from backend.models import CombatReport, DebrisField, Fleet, Planet, Research, TickLog, User


def _create_user(db_session, username: str, password: str = "password") -> tuple[User, str]:
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=f"{username}@test.com", password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, password


def _login_token(client, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    data = res.get_json()
    token = data.get("token") or data.get("access_token")
    assert token
    return token


def _create_planet(db_session, *, name: str, x: int, y: int, z: int, user_id: int | None) -> Planet:
    planet = Planet(name=name, x=x, y=y, z=z, user_id=user_id, metal=10000, crystal=5000, deuterium=2000)
    db_session.add(planet)
    db_session.commit()
    return planet


def _create_fleet(
    db_session,
    *,
    user_id: int,
    start_planet_id: int,
    ships: dict,
    status: str = "stationed",
    mission: str = "stationed",
) -> Fleet:
    now = datetime.utcnow()
    fleet = Fleet(
        user_id=user_id,
        mission=mission,
        status=status,
        start_planet_id=start_planet_id,
        target_planet_id=start_planet_id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        **ships,
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet


def test_attack_combat_victory_captures_planet_and_creates_report(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pipe_attacker_win")
    defender, defender_pw = _create_user(db_session, "pipe_defender_win")

    attacker_planet = _create_planet(db_session, name="A Home", x=0, y=0, z=0, user_id=attacker.id)
    defender_planet = _create_planet(db_session, name="D Colony", x=10, y=0, z=0, user_id=defender.id)

    attacker_fleet = _create_fleet(
        db_session,
        user_id=attacker.id,
        start_planet_id=attacker_planet.id,
        ships={"light_fighter": 150, "cruiser": 50, "battleship": 10, "colony_ship": 1},
    )
    defender_fleet = _create_fleet(
        db_session,
        user_id=defender.id,
        start_planet_id=defender_planet.id,
        ships={"light_fighter": 5},
        status="stationed",
        mission="stationed",
    )

    token = _login_token(client, attacker.username, attacker_pw)

    send_res = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": defender_planet.id},
    )
    assert send_res.status_code == 200
    send_data = send_res.get_json()
    assert send_data["fleet"]["status"] == "traveling"

    # Fast-forward to "arrived" without waiting for wall clock time.
    db_session.refresh(attacker_fleet)
    attacker_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    attacker_fleet.status = "traveling"
    attacker_fleet.mission = "attack"
    db_session.commit()

    tick_res = client.post("/api/tick")
    assert tick_res.status_code == 200

    db_session.refresh(attacker_fleet)
    assert attacker_fleet.status == "returning"
    assert attacker_fleet.mission == "return"
    # In pure pytest runs, min travel time defaults to 0 (see backend.config.get_min_travel_time_seconds).
    assert attacker_fleet.eta >= 0
    # In fast test mode, return can be immediate (arrival_time ~ now).
    assert attacker_fleet.arrival_time >= datetime.utcnow() - timedelta(seconds=2)

    db_session.refresh(defender_planet)
    assert defender_planet.user_id == attacker.id

    report = CombatReport.query.filter_by(
        attacker_id=attacker.id, defender_id=defender.id, planet_id=defender_planet.id
    ).first()
    assert report is not None
    assert report.winner_id == attacker.id

    rounds = json.loads(report.rounds)
    assert isinstance(rounds, list)
    assert len(rounds) >= 1

    attacker_losses = json.loads(report.attacker_losses)
    defender_losses = json.loads(report.defender_losses)
    assert isinstance(attacker_losses, dict)
    assert isinstance(defender_losses, dict)
    assert sum(int(v) for v in defender_losses.values()) >= 1

    debris = DebrisField.query.filter_by(planet_id=defender_planet.id).first()
    assert debris is not None
    assert debris.metal >= 0
    assert debris.crystal >= 0

    tick_log = TickLog.query.filter_by(planet_id=defender_planet.id, event_type="combat").first()
    assert tick_log is not None

    db_session.refresh(defender_fleet)
    defender_remaining = sum(
        int(getattr(defender_fleet, k, 0) or 0)
        for k in [
            "small_cargo",
            "large_cargo",
            "light_fighter",
            "heavy_fighter",
            "cruiser",
            "battleship",
            "colony_ship",
            "recycler",
        ]
    )
    assert defender_remaining == 0


def test_can_build_ships_on_captured_planet(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pipe_attacker_build")
    defender, defender_pw = _create_user(db_session, "pipe_defender_build")

    attacker_planet = _create_planet(db_session, name="A Home", x=0, y=2, z=0, user_id=attacker.id)
    defender_planet = _create_planet(db_session, name="D Colony", x=10, y=2, z=0, user_id=defender.id)

    attacker_fleet = _create_fleet(
        db_session,
        user_id=attacker.id,
        start_planet_id=attacker_planet.id,
        ships={"light_fighter": 150, "cruiser": 50, "battleship": 10},
    )

    token = _login_token(client, attacker.username, attacker_pw)
    headers = {"Authorization": f"Bearer {token}"}

    send_res = client.post(
        "/api/fleet/send",
        headers=headers,
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": defender_planet.id},
    )
    assert send_res.status_code == 200

    # Fast-forward to "arrived".
    db_session.refresh(attacker_fleet)
    attacker_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    attacker_fleet.status = "traveling"
    attacker_fleet.mission = "attack"
    db_session.commit()

    tick_res = client.post("/api/tick")
    assert tick_res.status_code == 200

    db_session.refresh(defender_planet)
    assert defender_planet.user_id == attacker.id

    # The captured planet should appear in /api/planet for the new owner.
    planets_res = client.get("/api/planet", headers=headers)
    assert planets_res.status_code == 200
    owned_ids = {p["id"] for p in planets_res.get_json()}
    assert defender_planet.id in owned_ids

    # Building ships on the captured planet should work and land in its inventory fleet.
    # Use an affordable ship type so this test doesn't depend on specific resource values.
    build_res = client.post(
        "/api/shipyard/build",
        headers=headers,
        json={"planet_id": defender_planet.id, "ship_type": "light_fighter", "quantity": 1},
    )
    assert build_res.status_code == 200, build_res.get_data(as_text=True)

    inventory = Fleet.query.filter_by(
        user_id=attacker.id,
        start_planet_id=defender_planet.id,
        status="stationed",
        mission="inventory",
    ).first()
    assert inventory is not None
    assert inventory.light_fighter >= 1


def test_attack_combat_loss_does_not_capture_planet(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pipe_attacker_lose")
    defender, defender_pw = _create_user(db_session, "pipe_defender_lose")

    attacker_planet = _create_planet(db_session, name="A Home", x=0, y=1, z=0, user_id=attacker.id)
    defender_planet = _create_planet(db_session, name="D Colony", x=10, y=1, z=0, user_id=defender.id)

    attacker_fleet = _create_fleet(
        db_session,
        user_id=attacker.id,
        start_planet_id=attacker_planet.id,
        ships={"light_fighter": 3},
    )
    _create_fleet(
        db_session,
        user_id=defender.id,
        start_planet_id=defender_planet.id,
        ships={"light_fighter": 150, "cruiser": 30, "battleship": 5},
        status="stationed",
        mission="stationed",
    )

    token = _login_token(client, attacker.username, attacker_pw)

    send_res = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": defender_planet.id},
    )
    assert send_res.status_code == 200

    db_session.refresh(attacker_fleet)
    attacker_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    attacker_fleet.status = "traveling"
    attacker_fleet.mission = "attack"
    db_session.commit()

    tick_res = client.post("/api/tick")
    assert tick_res.status_code == 200

    db_session.refresh(defender_planet)
    assert defender_planet.user_id == defender.id

    report = CombatReport.query.filter_by(
        attacker_id=attacker.id, defender_id=defender.id, planet_id=defender_planet.id
    ).first()
    assert report is not None
    assert report.winner_id == defender.id


def test_colonization_send_arrival_claims_planet_and_stations_fleet(client, db_session):
    user, pw = _create_user(db_session, "pipe_colonizer")
    home = _create_planet(db_session, name="Home", x=50, y=50, z=50, user_id=user.id)
    home.deuterium = 200000
    db_session.commit()

    target = _create_planet(db_session, name="Unowned", x=500, y=600, z=700, user_id=None)
    db_session.add(Research(user_id=user.id, colonization_tech=10))
    db_session.commit()

    fleet = _create_fleet(
        db_session,
        user_id=user.id,
        start_planet_id=home.id,
        ships={"colony_ship": 1, "light_fighter": 10},
        status="stationed",
        mission="stationed",
    )

    token = _login_token(client, user.username, pw)
    send_res = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": fleet.id, "mission": "colonize", "target_planet_id": target.id},
    )
    assert send_res.status_code == 200
    send_data = send_res.get_json()
    assert send_data["fleet"]["mission"] == "colonize"
    assert send_data["fleet"]["status"] == "colonizing:500:600:700"

    db_session.refresh(fleet)
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    fleet.status = "colonizing:500:600:700"
    fleet.mission = "colonize"
    fleet.target_coordinates = "500:600:700"
    db_session.commit()

    tick_res = client.post("/api/tick")
    assert tick_res.status_code == 200

    db_session.refresh(target)
    assert target.user_id == user.id
    assert target.colonized_at is not None

    db_session.refresh(fleet)
    assert fleet.status == "stationed"
    assert fleet.mission == "stationed"
