import json
from datetime import datetime

import bcrypt

from backend.database import db
from backend.models import CombatReport, DebrisField, Planet, User
from tests.conftest import make_auth_headers


def _mk_user(db_session, username: str) -> User:
    password_hash = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=f"{username}@test.com", password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user


def _mk_planet(db_session, *, name: str, x: int, y: int, z: int, user_id: int | None) -> Planet:
    planet = Planet(name=name, x=x, y=y, z=z, user_id=user_id, metal=10000, crystal=10000, deuterium=10000)
    db_session.add(planet)
    db_session.commit()
    return planet


def _mk_debris(db_session, *, planet_id: int, metal: int, crystal: int, deuterium: int = 0) -> DebrisField:
    debris = DebrisField(planet_id=planet_id, metal=metal, crystal=crystal, deuterium=deuterium)
    db_session.add(debris)
    db_session.commit()
    return debris


def test_debris_fields_only_visible_when_known(client, db_session):
    user = _mk_user(db_session, "debris_user")
    enemy = _mk_user(db_session, "debris_enemy")

    home = _mk_planet(db_session, name="Home", x=0, y=0, z=0, user_id=user.id)
    fought_planet = _mk_planet(db_session, name="Fought", x=10, y=0, z=0, user_id=enemy.id)
    explored_planet = _mk_planet(db_session, name="Explored", x=99, y=99, z=99, user_id=enemy.id)
    unknown_planet = _mk_planet(db_session, name="Unknown", x=77, y=77, z=77, user_id=enemy.id)

    _mk_debris(db_session, planet_id=fought_planet.id, metal=111, crystal=222, deuterium=333)
    _mk_debris(db_session, planet_id=explored_planet.id, metal=10, crystal=20, deuterium=30)
    _mk_debris(db_session, planet_id=unknown_planet.id, metal=1, crystal=2, deuterium=3)

    # Mark one system as explored for the user.
    user.explored_systems = json.dumps([{"coordinates": f"{explored_planet.x}:{explored_planet.y}:{explored_planet.z}", "explored_at": datetime.utcnow().isoformat()}])
    db_session.commit()

    # Create a combat report involving the user at fought_planet so it's "known".
    report = CombatReport(
        attacker_id=user.id,
        defender_id=enemy.id,
        planet_id=fought_planet.id,
        winner_id=user.id,
        rounds="[]",
        attacker_losses="{}",
        defender_losses="{}",
        debris_metal=111,
        debris_crystal=222,
        debris_deuterium=333,
    )
    db.session.add(report)
    db.session.commit()

    headers = make_auth_headers(user.id)
    res = client.get("/api/combat/debris", headers=headers)
    assert res.status_code == 200
    data = res.get_json()

    planet_ids = {d["planet"]["id"] for d in data["debris_fields"]}
    assert fought_planet.id in planet_ids
    assert explored_planet.id in planet_ids
    assert unknown_planet.id not in planet_ids


def test_debris_detail_requires_visibility(client, db_session):
    user = _mk_user(db_session, "debris_detail_user")
    enemy = _mk_user(db_session, "debris_detail_enemy")

    hidden_planet = _mk_planet(db_session, name="Hidden", x=5, y=5, z=5, user_id=enemy.id)
    _mk_debris(db_session, planet_id=hidden_planet.id, metal=5, crystal=5, deuterium=5)

    headers = make_auth_headers(user.id)
    res = client.get(f"/api/combat/debris/{hidden_planet.id}", headers=headers)
    assert res.status_code == 403

