import pytest
from datetime import datetime, timedelta

import bcrypt

from backend.models import Planet, Fleet, TickLog, User


def test_tick_logs_endpoint_returns_user_relevant_logs(client, db_session):
    password = "password"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username="log_user", email="log_user@test.com", password_hash=password_hash)
    db_session.add(user)
    db_session.commit()

    planet = Planet(name="Log Planet", x=1, y=2, z=3, user_id=user.id)
    db_session.add(planet)
    db_session.commit()

    now = datetime.utcnow()
    fleet = Fleet(
        user_id=user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=planet.id,
        target_planet_id=planet.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        light_fighter=1,
    )
    db_session.add(fleet)
    db_session.commit()

    db_session.add(TickLog(
        tick_number=0,
        planet_id=planet.id,
        fleet_id=fleet.id,
        event_type="fleet_sent",
        event_description="Fleet sent for testing",
    ))
    db_session.commit()

    login = client.post("/api/auth/login", json={"username": "log_user", "password": password})
    assert login.status_code == 200
    token = login.get_json()["token"]

    res = client.get("/api/tick/logs?limit=10&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert "logs" in data
    assert len(data["logs"]) >= 1
    assert any(l.get("event_type") == "fleet_sent" for l in data["logs"])

