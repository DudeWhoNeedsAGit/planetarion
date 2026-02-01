import bcrypt
from datetime import datetime, timedelta

from backend.database import db
from backend.models import User, Planet, Fleet


def _create_user(db_session, username, email, password):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, password


def _login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.get_json()["token"]


def test_pirate_attack_loots_resources(client, db_session):
    attacker, attacker_pw = _create_user(db_session, "pirate_attacker", "attacker@test.com", "password")
    pirates, _ = _create_user(db_session, "pirates", "pirates@test.com", "password")

    attacker_home = Planet(name="Home", x=1, y=1, z=1, user_id=attacker.id, deuterium=1_000_000)
    pirate_planet = Planet(name="Pirate Camp", x=2, y=2, z=2, user_id=pirates.id, metal=1000, crystal=800, deuterium=600)
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
        light_fighter=100,
        cruiser=10,
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
        light_fighter=1,  # trivial defense
    )
    db_session.add_all([attacker_fleet, pirate_defender])
    db_session.commit()

    token = _login(client, "pirate_attacker", attacker_pw)

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": attacker_fleet.id, "mission": "attack", "target_planet_id": pirate_planet.id},
    )
    assert send.status_code == 200

    attacker_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    before = attacker_home.metal, attacker_home.crystal, attacker_home.deuterium
    tick = client.post("/api/tick")
    assert tick.status_code == 200

    db_session.refresh(attacker_home)
    after = attacker_home.metal, attacker_home.crystal, attacker_home.deuterium

    assert after[0] >= before[0]
    assert after[1] >= before[1]
    assert after[2] >= before[2]
    assert after != before

