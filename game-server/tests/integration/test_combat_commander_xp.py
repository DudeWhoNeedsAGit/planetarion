from datetime import datetime, timedelta

import bcrypt

from backend.database import db
from backend.models import CombatReport, Fleet, Planet, User
from backend.services.commander_xp import xp_to_next_level


def _create_user(db_session, username: str, email: str, password: str = "password"):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, password


def _login(client, username: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.get_json()["token"]


def test_combat_awards_commander_xp_and_can_level_up(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "xp_attacker", "xp_attacker@test.com")
    defender, _ = _create_user(db_session, "xp_defender", "xp_defender@test.com")

    attacker_home = Planet(name="Attacker Home", x=11, y=11, z=11, user_id=attacker.id)
    defender_home = Planet(name="Defender Home", x=12, y=12, z=11, user_id=defender.id)
    db_session.add_all([attacker_home, defender_home])
    db_session.commit()

    # Put attacker close to level-up threshold so a single combat should level.
    attacker.commander_xp = max(0, int(xp_to_next_level(1)) - 10)
    attacker.commander_level = 1

    now = datetime.utcnow()
    attacker_fleet = Fleet(
        user_id=attacker.id,
        mission="stationed",
        status="stationed",
        start_planet_id=attacker_home.id,
        target_planet_id=attacker_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=80,
        heavy_fighter=20,
        cruiser=5,
    )
    defender_fleet = Fleet(
        user_id=defender.id,
        mission="defend",
        status="stationed",
        start_planet_id=defender_home.id,
        target_planet_id=defender_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=5,
    )
    db_session.add_all([attacker_fleet, defender_fleet])
    db_session.commit()

    token = _login(client, "xp_attacker", attacker_pw)

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": defender_home.id},
    )
    assert send.status_code == 200

    attacker_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    tick = client.post("/api/tick")
    assert tick.status_code == 200

    db_session.refresh(attacker)
    assert int(attacker.commander_xp or 0) >= int(xp_to_next_level(1))
    assert int(attacker.commander_level or 1) >= 2

    report = (
        CombatReport.query.filter_by(attacker_id=attacker.id, defender_id=defender.id, planet_id=defender_home.id)
        .order_by(CombatReport.id.desc())
        .first()
    )
    assert report is not None


def test_attacking_pirates_is_allowed_even_if_protection_fields_are_set(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pirate_hunter", "pirate_hunter@test.com")
    pirates, _ = _create_user(db_session, "pirates", "pirates@test.com")

    # Simulate protection markers present; this must not block player-vs-pirate attacks.
    attacker.protection_until = datetime.utcnow() + timedelta(hours=2)
    pirates.protection_until = datetime.utcnow() + timedelta(hours=2)

    attacker_home = Planet(name="Hunter Home", x=21, y=21, z=21, user_id=attacker.id)
    pirate_planet = Planet(name="Pirate Camp", x=22, y=22, z=21, user_id=pirates.id)
    db_session.add_all([attacker_home, pirate_planet])
    db_session.commit()

    now = datetime.utcnow()
    attacker_fleet = Fleet(
        user_id=attacker.id,
        mission="stationed",
        status="stationed",
        start_planet_id=attacker_home.id,
        target_planet_id=attacker_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=20,
    )
    pirate_defender = Fleet(
        user_id=pirates.id,
        mission="defend",
        status="stationed",
        start_planet_id=pirate_planet.id,
        target_planet_id=pirate_planet.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=1,
    )
    db_session.add_all([attacker_fleet, pirate_defender])
    db_session.commit()

    token = _login(client, "pirate_hunter", attacker_pw)

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": pirate_planet.id},
    )
    assert send.status_code == 200


def test_pvp_attack_is_blocked_when_target_is_protected(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pvp_attacker", "pvp_attacker@test.com")
    defender, _ = _create_user(db_session, "pvp_defender", "pvp_defender@test.com")
    defender.protection_until = datetime.utcnow() + timedelta(hours=1)

    attacker_home = Planet(name="Attacker Home", x=31, y=31, z=31, user_id=attacker.id)
    defender_home = Planet(name="Defender Home", x=32, y=32, z=31, user_id=defender.id)
    db_session.add_all([attacker_home, defender_home])
    db_session.commit()

    now = datetime.utcnow()
    attacker_fleet = Fleet(
        user_id=attacker.id,
        mission="stationed",
        status="stationed",
        start_planet_id=attacker_home.id,
        target_planet_id=attacker_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=12,
    )
    db_session.add(attacker_fleet)
    db_session.commit()

    token = _login(client, "pvp_attacker", attacker_pw)
    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": defender_home.id},
    )
    assert send.status_code == 400
    assert "protection" in str((send.get_json() or {}).get("error", "")).lower()
