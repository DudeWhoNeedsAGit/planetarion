import bcrypt
from datetime import datetime, timedelta

from backend.database import db
from backend.models import User, Planet, Fleet, EspionageReport


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


def test_espionage_mission_creates_spy_report_and_returns(client, db_session):
    spy_user, spy_pass = _create_user(db_session, "spy", "spy@test.com", "password")
    target_user, _ = _create_user(db_session, "target", "target@test.com", "password")

    spy_home = Planet(name="Spy Home", x=1, y=2, z=3, user_id=spy_user.id, deuterium=1_000_000)
    target_planet = Planet(name="Target Planet", x=10, y=20, z=30, user_id=target_user.id, metal=123, crystal=456, deuterium=789)
    db_session.add_all([spy_home, target_planet])
    db_session.commit()

    now = datetime.utcnow()
    fleet = Fleet(
        user_id=spy_user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=spy_home.id,
        target_planet_id=spy_home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        espionage_probe=5,
    )
    db_session.add(fleet)
    db_session.commit()

    token = _login(client, "spy", spy_pass)

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": fleet.id, "mission": "espionage", "target_planet_id": target_planet.id},
    )
    assert send.status_code == 200

    # Force arrival and run tick to process.
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    tick = client.post("/api/tick")
    assert tick.status_code == 200

    # Report created
    assert EspionageReport.query.filter_by(user_id=spy_user.id, target_planet_id=target_planet.id).count() == 1

    # Endpoint returns it
    res = client.get("/api/espionage/reports", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data.get("reports", [])) >= 1
    report = data["reports"][0]
    assert report["target_planet_id"] == target_planet.id
    db_session.refresh(target_planet)
    assert report["intel"]["resources"]["metal"] == target_planet.metal
