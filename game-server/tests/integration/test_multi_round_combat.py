import json
from datetime import datetime, timedelta

import bcrypt

from backend.models import CombatReport, Fleet, Planet, User


def test_combat_can_run_multiple_rounds_and_creates_report(client, db_session):
    password = "password"
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    attacker = User(username="mr_attacker", email="mr_attacker@test.com", password_hash=pw_hash)
    defender = User(username="mr_defender", email="mr_defender@test.com", password_hash=pw_hash)
    db_session.add_all([attacker, defender])
    db_session.commit()

    a_home = Planet(name="A Home", x=0, y=10, z=0, user_id=attacker.id)
    d_home = Planet(name="D Home", x=10, y=10, z=0, user_id=defender.id)
    db_session.add_all([a_home, d_home])
    db_session.commit()

    now = datetime.utcnow()
    a_fleet = Fleet(
        user_id=attacker.id,
        mission="stationed",
        status="stationed",
        start_planet_id=a_home.id,
        target_planet_id=a_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        small_cargo=1,  # very low weapon vs shield => often no kills per round
    )
    d_fleet = Fleet(
        user_id=defender.id,
        mission="stationed",
        status="stationed",
        start_planet_id=d_home.id,
        target_planet_id=d_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        small_cargo=1,
    )
    db_session.add_all([a_fleet, d_fleet])
    db_session.commit()

    login = client.post("/api/auth/login", json={"username": "mr_attacker", "password": password})
    assert login.status_code == 200
    token = login.get_json()["token"]

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": a_fleet.id, "mission": "attack", "target_planet_id": d_home.id},
    )
    assert send.status_code == 200

    db_session.refresh(a_fleet)
    a_fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    a_fleet.status = "traveling"
    a_fleet.mission = "attack"
    db_session.commit()

    tick = client.post("/api/tick")
    assert tick.status_code == 200

    report = CombatReport.query.filter_by(attacker_id=attacker.id, defender_id=defender.id, planet_id=d_home.id).first()
    assert report is not None
    rounds = json.loads(report.rounds)
    assert len(rounds) > 1

