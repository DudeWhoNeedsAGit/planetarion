import bcrypt

from backend.models import User, Planet, DebrisField, Alliance


def _create_user(db_session, username, email, password):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user


def _login(client, username, password):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    return res.get_json()["token"]


def test_galaxy_nearby_returns_range_limited_system_summaries(client, db_session):
    # Arrange
    user = _create_user(db_session, "galaxy_user", "galaxy_user@test.com", "password")
    enemy = _create_user(db_session, "enemy_user", "enemy_user@test.com", "password")

    home = Planet(name="Home", x=100, y=200, z=300, user_id=user.id)
    enemy_planet = Planet(name="Enemy", x=110, y=200, z=300, user_id=enemy.id)
    unowned = Planet(name="Unowned", x=120, y=200, z=300, user_id=None)
    db_session.add_all([home, enemy_planet, unowned])
    db_session.commit()

    # Debris in enemy system
    db_session.add(DebrisField(planet_id=enemy_planet.id, metal=10, crystal=5, deuterium=0))
    db_session.commit()

    # Mark enemy system as explored
    user.explored_systems = '[{"coordinates":"110:200:300","explored_at":"2026-01-01T00:00:00Z"}]'
    db_session.commit()

    token = _login(client, "galaxy_user", "password")

    # Act
    res = client.get(
        "/api/galaxy/nearby/100/200/300?range=50",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Assert
    assert res.status_code == 200
    data = res.get_json()
    assert "systems" in data
    assert "meta" in data
    assert data["meta"]["range"] == 50

    systems = {s["key"]: s for s in data["systems"]}

    assert "100:200:300" in systems
    assert systems["100:200:300"]["relation"] == "self"
    assert systems["100:200:300"]["explored"] is True

    assert "110:200:300" in systems
    assert systems["110:200:300"]["relation"] == "enemy"
    assert systems["110:200:300"]["explored"] is True
    assert systems["110:200:300"]["flags"]["has_debris"] is True
    assert systems["110:200:300"]["owner_name"] == "enemy_user"

    assert "120:200:300" in systems
    assert systems["120:200:300"]["relation"] == "unowned"
    assert systems["120:200:300"]["owner_id"] is None


def test_galaxy_nearby_marks_alliance_systems_as_ally(client, db_session):
    user = _create_user(db_session, "ally_user", "ally_user@test.com", "password")
    ally = _create_user(db_session, "ally_friend", "ally_friend@test.com", "password")

    alliance = Alliance(name="Alliance", description="test", leader_id=user.id)
    db_session.add(alliance)
    db_session.commit()

    user.alliance_id = alliance.id
    ally.alliance_id = alliance.id
    db_session.commit()

    home = Planet(name="Home", x=0, y=0, z=0, user_id=user.id)
    ally_planet = Planet(name="Ally", x=10, y=0, z=0, user_id=ally.id)
    db_session.add_all([home, ally_planet])
    db_session.commit()

    token = _login(client, "ally_user", "password")
    res = client.get("/api/galaxy/nearby/0/0/0?range=50", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    systems = {s["key"]: s for s in res.get_json()["systems"]}
    assert systems["10:0:0"]["relation"] == "ally"


def test_galaxy_system_planets_respects_fog_of_war(client, db_session):
    user = _create_user(db_session, "fog_user", "fog_user@test.com", "password")
    enemy = _create_user(db_session, "fog_enemy", "fog_enemy@test.com", "password")

    enemy_planet = Planet(name="Enemy", x=500, y=600, z=700, user_id=enemy.id)
    db_session.add(enemy_planet)
    db_session.commit()

    token = _login(client, "fog_user", "password")

    # Not explored => empty list
    res = client.get(
        "/api/galaxy/system/500/600/700",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.get_json() == []

    # Mark explored => planets visible
    user.explored_systems = '[{"coordinates":"500:600:700","explored_at":"2026-01-01T00:00:00Z"}]'
    db_session.commit()

    res2 = client.get(
        "/api/galaxy/system/500/600/700",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    planets = res2.get_json()
    assert isinstance(planets, list)
    assert len(planets) == 1
    assert planets[0]["id"] == enemy_planet.id
