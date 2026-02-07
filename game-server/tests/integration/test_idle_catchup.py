import json
from datetime import datetime, timedelta

import bcrypt

from backend.config import get_planet_storage_caps
from backend.models import Fleet, Planet, Research, User


def _register_and_login(client, username: str, email: str, password: str = "pw123456"):
    reg = client.post(
        "/api/auth/register",
        data=json.dumps({"username": username, "email": email, "password": password}),
        content_type="application/json",
    )
    assert reg.status_code == 201

    login = client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    assert login.status_code == 200
    token = login.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_user(db_session, username: str, email: str) -> User:
    password_hash = bcrypt.hashpw("pw123456".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    u = User(username=username, email=email, password_hash=password_hash)
    db_session.add(u)
    db_session.commit()
    return u


def _create_planet(db_session, user_id: int, *, x: int, y: int, z: int, name: str = "P") -> Planet:
    p = Planet(
        name=name,
        x=x,
        y=y,
        z=z,
        user_id=user_id,
        metal=0,
        crystal=0,
        deuterium=0,
        metal_mine=10,
        crystal_mine=10,
        deuterium_synthesizer=10,
        solar_plant=30,
        research_lab=6,
        is_home_planet=True,
    )
    db_session.add(p)
    db_session.commit()
    return p


def test_idle_catchup_caps_duration_and_storage(client, app, db_session):
    headers = _register_and_login(client, "idle_cap_user", "idle_cap@example.com")

    user = db_session.query(User).filter_by(username="idle_cap_user").first()
    assert user is not None
    planet = db_session.query(Planet).filter_by(user_id=user.id).first()
    assert planet is not None

    # Make production high and storages low enough to force cap clamping.
    planet.metal_mine = 18
    planet.crystal_mine = 18
    planet.deuterium_synthesizer = 18
    planet.solar_plant = 40
    planet.metal_storage = 0
    planet.crystal_storage = 0
    planet.deuterium_tank = 0
    user.last_seen_at = datetime.utcnow() - timedelta(days=60)  # > 4 week cap
    db_session.commit()

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    idle = data.get("idle_gains")
    assert idle is not None

    with app.app_context():
        cap_seconds = int(app.config.get("IDLE_CATCHUP_CAP_SECONDS", 60 * 60 * 24 * 7 * 4))
    assert int(idle["duration_seconds"]) == cap_seconds
    assert bool(idle.get("was_capped")) is True
    assert int(idle.get("raw_duration_seconds", 0)) >= int(idle["duration_seconds"])

    db_session.refresh(planet)
    caps = get_planet_storage_caps(planet)
    assert int(planet.metal or 0) <= int(caps["metal"])
    assert int(planet.crystal or 0) <= int(caps["crystal"])
    assert int(planet.deuterium or 0) <= int(caps["deuterium"])


def test_idle_catchup_processes_arrivals_for_authenticated_user_only(client, db_session):
    headers = _register_and_login(client, "idle_fleet_user", "idle_fleet@example.com")
    user = db_session.query(User).filter_by(username="idle_fleet_user").first()
    home = db_session.query(Planet).filter_by(user_id=user.id).first()

    other = _create_user(db_session, "idle_other_user", "idle_other@example.com")
    other_home = _create_planet(db_session, other.id, x=901, y=902, z=903, name="Other Home")

    now = datetime.utcnow()
    mine = Fleet(
        user_id=user.id,
        mission="return",
        status="returning",
        start_planet_id=home.id,
        target_planet_id=home.id,
        departure_time=now - timedelta(hours=2),
        arrival_time=now - timedelta(seconds=1),
        eta=0,
        cargo_metal=100,
    )
    theirs = Fleet(
        user_id=other.id,
        mission="return",
        status="returning",
        start_planet_id=other_home.id,
        target_planet_id=other_home.id,
        departure_time=now - timedelta(hours=2),
        arrival_time=now - timedelta(seconds=1),
        eta=0,
        cargo_metal=100,
    )
    user.last_seen_at = now - timedelta(hours=4)
    db_session.add_all([mine, theirs])
    db_session.commit()

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200

    db_session.refresh(mine)
    db_session.refresh(theirs)
    assert mine.status == "stationed"
    assert theirs.status == "returning"


def test_idle_catchup_completes_due_research_queue_and_awards_rp(client, db_session):
    headers = _register_and_login(client, "idle_research_user", "idle_research@example.com")
    user = db_session.query(User).filter_by(username="idle_research_user").first()
    planet = db_session.query(Planet).filter_by(user_id=user.id).first()
    planet.research_lab = 12
    planet.solar_plant = 40

    research = Research(user_id=user.id, research_points=0, astrophysics=0)
    db_session.add(research)

    user.last_seen_at = datetime.utcnow() - timedelta(hours=12)
    user.research_queue = json.dumps(
        {
            "key": "astrophysics",
            "target_level": 1,
            "completes_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z",
        }
    )
    db_session.commit()

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    idle = data.get("idle_gains")
    assert idle is not None
    assert int(idle["research_points"]) >= 0
    assert int((idle.get("events") or {}).get("research_completed", 0)) == 1

    db_session.refresh(research)
    db_session.refresh(user)
    assert int(research.astrophysics or 0) == 1
    assert user.research_queue is None


def test_idle_catchup_does_not_double_award_on_immediate_repeat(client, db_session):
    headers = _register_and_login(client, "idle_repeat_user", "idle_repeat@example.com")
    user = db_session.query(User).filter_by(username="idle_repeat_user").first()
    planet = db_session.query(Planet).filter_by(user_id=user.id).first()
    user.last_seen_at = datetime.utcnow() - timedelta(hours=6)
    db_session.commit()

    first = client.get("/api/auth/me", headers=headers)
    assert first.status_code == 200
    first_idle = first.get_json().get("idle_gains")
    assert first_idle is not None

    db_session.refresh(planet)
    after_first = (int(planet.metal or 0), int(planet.crystal or 0), int(planet.deuterium or 0))

    second = client.get("/api/auth/me", headers=headers)
    assert second.status_code == 200
    second_idle = second.get_json().get("idle_gains")
    assert second_idle is None

    db_session.refresh(planet)
    after_second = (int(planet.metal or 0), int(planet.crystal or 0), int(planet.deuterium or 0))
    assert after_second == after_first


def test_idle_catchup_handles_future_last_seen_clock_skew(client, db_session):
    headers = _register_and_login(client, "idle_skew_user", "idle_skew@example.com")
    user = db_session.query(User).filter_by(username="idle_skew_user").first()
    user.last_seen_at = datetime.utcnow() + timedelta(hours=6)
    db_session.commit()

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("idle_gains") is None

    refreshed = db_session.query(User).get(user.id)
    assert refreshed.last_seen_at is not None
    assert refreshed.last_seen_at <= datetime.utcnow() + timedelta(seconds=2)
