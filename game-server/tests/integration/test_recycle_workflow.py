from datetime import datetime, timedelta

import bcrypt

from backend.models import DebrisField, Fleet, Planet, User


def test_recycle_mission_collects_debris_and_deposits_resources(client, db_session):
    password = "password"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username="recycler_user", email="recycler_user@test.com", password_hash=password_hash)
    db_session.add(user)
    db_session.commit()

    home = Planet(name="Home", x=0, y=0, z=0, user_id=user.id, metal=0, crystal=0, deuterium=0)
    target = Planet(name="Battlefield", x=10, y=0, z=0, user_id=None, metal=0, crystal=0, deuterium=0)
    db_session.add_all([home, target])
    db_session.commit()

    debris = DebrisField(planet_id=target.id, metal=5000, crystal=3000, deuterium=1000)
    db_session.add(debris)
    db_session.commit()

    now = datetime.utcnow()
    fleet = Fleet(
        user_id=user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=home.id,
        target_planet_id=home.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        recycler=10,  # capacity: 10k (split across resources by implementation)
    )
    db_session.add(fleet)
    db_session.commit()

    login = client.post("/api/auth/login", json={"username": "recycler_user", "password": password})
    assert login.status_code == 200
    token = login.get_json()["token"]

    send = client.post(
        "/api/fleet/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"fleet_id": fleet.id, "mission": "recycle", "target_planet_id": target.id},
    )
    assert send.status_code == 200

    db_session.refresh(fleet)
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    fleet.status = "traveling"
    fleet.mission = "recycle"
    db_session.commit()

    tick = client.post("/api/tick")
    assert tick.status_code == 200

    # One tick processes recycle collection and sets the fleet to returning.
    db_session.refresh(fleet)
    assert fleet.status == "returning"
    assert fleet.mission == "return"
    assert (fleet.cargo_metal or 0) > 0

    # Next tick processes return and deposits cargo at origin planet.
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    tick2 = client.post("/api/tick")
    assert tick2.status_code == 200

    db_session.refresh(home)
    # capacity // 2 = 5000 metal + 5000 crystal/deut budget; we cap by debris amounts
    assert home.metal >= 5000
    assert home.crystal >= 3000
    assert home.deuterium >= 1000

    remaining = DebrisField.query.filter_by(planet_id=target.id).first()
    assert remaining is None
