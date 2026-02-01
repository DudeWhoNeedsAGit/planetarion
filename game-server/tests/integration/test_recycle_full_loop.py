from datetime import datetime, timedelta

import bcrypt

from backend.models import DebrisField, Fleet, Planet, User


def test_build_recyclers_send_collect_return_and_deposit(client, db_session):
    password = "password"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username="recycler_builder", email="recycler_builder@test.com", password_hash=password_hash)
    db_session.add(user)
    db_session.commit()

    # Ensure shipyard build has resources to pay recycler costs.
    home = Planet(
        name="Home",
        x=0,
        y=0,
        z=0,
        user_id=user.id,
        metal=200000,
        crystal=200000,
        deuterium=200000,
    )
    target = Planet(name="Battlefield", x=10, y=0, z=0, user_id=None, metal=0, crystal=0, deuterium=0)
    db_session.add_all([home, target])
    db_session.commit()

    debris = DebrisField(planet_id=target.id, metal=5000, crystal=3000, deuterium=1000)
    db_session.add(debris)
    db_session.commit()

    login = client.post("/api/auth/login", json={"username": "recycler_builder", "password": password})
    assert login.status_code == 200
    token = login.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Build recyclers (shipyard creates/updates a stationed fleet at this planet).
    build = client.post(
        "/api/shipyard/build",
        headers=headers,
        json={"planet_id": home.id, "ship_type": "recycler", "quantity": 10},
    )
    assert build.status_code == 200, build.get_json()

    stationed = Fleet.query.filter_by(user_id=user.id, start_planet_id=home.id, status="stationed").first()
    assert stationed is not None
    assert (stationed.recycler or 0) >= 10

    send = client.post(
        "/api/fleet/send",
        headers=headers,
        json={"fleet_id": stationed.id, "mission": "recycle", "target_planet_id": target.id},
    )
    assert send.status_code == 200

    db_session.refresh(stationed)
    stationed.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    stationed.status = "traveling"
    stationed.mission = "recycle"
    db_session.commit()

    # Tick 1: collect debris into cargo and start returning.
    tick1 = client.post("/api/tick")
    assert tick1.status_code == 200
    db_session.refresh(stationed)
    assert stationed.status == "returning"
    assert stationed.mission == "return"
    assert (stationed.cargo_metal or 0) > 0

    # Force return arrival.
    stationed.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()

    # Tick 2: deliver cargo at origin and station fleet.
    tick2 = client.post("/api/tick")
    assert tick2.status_code == 200

    db_session.refresh(home)
    assert home.metal >= 5000
    assert home.crystal >= 3000
    assert home.deuterium >= 1000

    db_session.refresh(stationed)
    assert stationed.status == "stationed"
    assert stationed.mission == "stationed"
    assert (stationed.cargo_metal or 0) == 0
    assert (stationed.cargo_crystal or 0) == 0
    assert (stationed.cargo_deuterium or 0) == 0
