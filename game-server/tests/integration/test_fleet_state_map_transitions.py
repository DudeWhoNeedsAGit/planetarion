from datetime import datetime, timedelta


def _fast_forward_arrival(db_session, fleet, *, seconds_ago=1):
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=seconds_ago)
    db_session.commit()


def _run_tick(app):
    from backend.services.tick import run_tick

    with app.app_context():
        run_tick()

def _disable_production(db_session, planet):
    # Keep tick deterministic for tests that assert exact resource deltas.
    planet.metal_mine = 0
    planet.crystal_mine = 0
    planet.deuterium_synthesizer = 0
    planet.solar_plant = 0
    planet.fusion_reactor = 0
    db_session.commit()


def _create_owned_planet(db_session, user_id, *, x=101, y=201, z=301, name="Owned Target"):
    from backend.models import Planet

    planet = Planet(
        name=name,
        x=x,
        y=y,
        z=z,
        user_id=user_id,
        metal=10000,
        crystal=10000,
        deuterium=10000,
        metal_mine=0,
        crystal_mine=0,
        deuterium_synthesizer=0,
        solar_plant=0,
        fusion_reactor=0,
    )
    db_session.add(planet)
    db_session.commit()
    return planet


def _create_enemy_planet(db_session, *, x=999, y=888, z=777, name="Enemy Planet"):
    from backend.models import User, Planet
    import bcrypt

    password_hash = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    enemy = User(username="enemy", email="enemy@example.com", password_hash=password_hash)
    db_session.add(enemy)
    db_session.commit()

    planet = Planet(
        name=name,
        x=x,
        y=y,
        z=z,
        user_id=enemy.id,
        metal=10000,
        crystal=10000,
        deuterium=10000,
        metal_mine=0,
        crystal_mine=0,
        deuterium_synthesizer=0,
        solar_plant=0,
        fusion_reactor=0,
    )
    db_session.add(planet)
    db_session.commit()
    return enemy, planet


def test_pending_tick_state_is_possible(client, auth_headers, db_session, sample_planet):
    # In testing env, min travel time is 0 by default, so sending can result in an immediate
    # "arrived but not processed" state until a tick runs.
    _disable_production(db_session, sample_planet)

    # Espionage probes aren't stored on Planet; use shipyard which creates/updates a stationed fleet.
    build = client.post(
        "/api/shipyard/build",
        json={"planet_id": sample_planet.id, "ship_type": "espionage_probe", "quantity": 1},
        headers=auth_headers,
    )
    assert build.status_code == 200
    fleet_id = build.get_json()["fleet"]["id"]

    enemy_user, enemy_planet = _create_enemy_planet(db_session)

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "espionage", "target_planet_id": enemy_planet.id},
        headers=auth_headers,
    )
    assert send.status_code == 200

    from backend.models import Fleet

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "traveling"
    # Force the "arrived but not yet processed" state (what the UI calls "pending tick").
    fleet.arrival_time = datetime.utcnow() - timedelta(seconds=1)
    db_session.commit()
    fleet = Fleet.query.get(fleet_id)
    assert fleet.arrival_time <= datetime.utcnow()


def test_transport_flow_unloads_then_returns(app, client, auth_headers, db_session, sample_user, sample_planet):
    _disable_production(db_session, sample_planet)
    target = _create_owned_planet(db_session, sample_user.id, x=111, y=222, z=333, name="Owned B")

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"small_cargo": 1}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    origin_before = (sample_planet.metal, sample_planet.crystal, sample_planet.deuterium)
    target_before = (target.metal, target.crystal, target.deuterium)

    send = client.post(
        "/api/fleet/send",
        json={
            "fleet_id": fleet_id,
            "mission": "transport",
            "target_planet_id": target.id,
            "cargo_metal": 123,
            "cargo_crystal": 45,
            "cargo_deuterium": 6,
        },
        headers=auth_headers,
    )
    assert send.status_code == 200

    # Cargo should be deducted immediately from origin and stored on fleet.
    db_session.refresh(sample_planet)
    assert sample_planet.metal == origin_before[0] - 123
    assert sample_planet.crystal == origin_before[1] - 45
    assert sample_planet.deuterium == origin_before[2] - 6

    from backend.models import Fleet, Planet

    fleet = Fleet.query.get(fleet_id)
    assert fleet.mission == "transport"
    assert fleet.status == "traveling"
    assert fleet.cargo_metal == 123

    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "returning"
    assert fleet.mission == "return"
    assert fleet.cargo_metal == 0

    target = Planet.query.get(target.id)
    assert target.metal == target_before[0] + 123
    assert target.crystal == target_before[1] + 45
    assert target.deuterium == target_before[2] + 6

    # Return arrival: should station at origin and not move any cargo.
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)
    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "stationed"
    assert fleet.target_planet_id == fleet.start_planet_id


def test_deploy_flow_moves_location_and_stays(app, client, auth_headers, db_session, sample_user, sample_planet):
    _disable_production(db_session, sample_planet)
    target = _create_owned_planet(db_session, sample_user.id, x=121, y=221, z=321, name="Owned C")

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"light_fighter": 1}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    origin_before = (sample_planet.metal, sample_planet.crystal, sample_planet.deuterium)
    target_before = (target.metal, target.crystal, target.deuterium)

    send = client.post(
        "/api/fleet/send",
        json={
            "fleet_id": fleet_id,
            "mission": "deploy",
            "target_planet_id": target.id,
            "cargo_metal": 10,
            "cargo_crystal": 20,
            "cargo_deuterium": 30,
        },
        headers=auth_headers,
    )
    assert send.status_code == 200

    db_session.refresh(sample_planet)
    assert sample_planet.metal == origin_before[0] - 10
    assert sample_planet.crystal == origin_before[1] - 20
    assert sample_planet.deuterium == origin_before[2] - 30

    from backend.models import Fleet, Planet

    fleet = Fleet.query.get(fleet_id)
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "stationed"
    assert fleet.mission == "deploy"
    assert fleet.start_planet_id == target.id
    assert fleet.target_planet_id == target.id

    target = Planet.query.get(target.id)
    assert target.metal == target_before[0] + 10
    assert target.crystal == target_before[1] + 20
    assert target.deuterium == target_before[2] + 30


def test_defend_flow_stations_as_defending(app, client, auth_headers, db_session, sample_user, sample_planet):
    _disable_production(db_session, sample_planet)
    target = _create_owned_planet(db_session, sample_user.id, x=131, y=231, z=331, name="Owned D")

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"heavy_fighter": 1}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "defend", "target_planet_id": target.id},
        headers=auth_headers,
    )
    assert send.status_code == 200

    from backend.models import Fleet

    fleet = Fleet.query.get(fleet_id)
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    fleet = Fleet.query.get(fleet_id)
    assert fleet.mission == "defend"
    assert fleet.status == "defending"
    assert fleet.start_planet_id == target.id
    assert fleet.target_planet_id == target.id


def test_attack_flow_returns(app, client, auth_headers, db_session, sample_planet):
    _disable_production(db_session, sample_planet)
    # Ensure an enemy target exists (no defending fleet needed for this assertion).
    enemy_user, enemy_planet = _create_enemy_planet(db_session, x=1001, y=1002, z=1003, name="Enemy 2")

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"light_fighter": 5}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "attack", "target_planet_id": enemy_planet.id},
        headers=auth_headers,
    )
    assert send.status_code == 200

    from backend.models import Fleet

    fleet = Fleet.query.get(fleet_id)
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    fleet = Fleet.query.get(fleet_id)
    assert fleet.mission == "return"
    assert fleet.status == "returning"


def test_recycle_flow_collects_and_returns_cargo(app, client, auth_headers, db_session, sample_user, sample_planet):
    from backend.models import DebrisField, Fleet

    _disable_production(db_session, sample_planet)
    sample_planet.metal = 1_000_000
    sample_planet.crystal = 1_000_000
    sample_planet.deuterium = 1_000_000
    db_session.commit()

    # Create an owned target with debris (recycle requires recyclers but doesn't require ownership).
    enemy_user, target = _create_enemy_planet(db_session, x=2001, y=2002, z=2003, name="Enemy Debris")
    debris = DebrisField(planet_id=target.id, metal=1000, crystal=500, deuterium=0)
    db_session.add(debris)
    db_session.commit()

    # Recyclers aren't stored on Planet; use shipyard which creates/updates a stationed fleet.
    build = client.post(
        "/api/shipyard/build",
        json={"planet_id": sample_planet.id, "ship_type": "recycler", "quantity": 2},
        headers=auth_headers,
    )
    assert build.status_code == 200
    fleet_id = build.get_json()["fleet"]["id"]

    origin_before_metal = sample_planet.metal

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "recycle", "target_planet_id": target.id},
        headers=auth_headers,
    )
    assert send.status_code == 200

    fleet = Fleet.query.get(fleet_id)
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "returning"
    assert fleet.mission == "return"
    assert (fleet.cargo_metal or 0) > 0

    collected_metal = fleet.cargo_metal
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    db_session.refresh(sample_planet)
    assert sample_planet.metal == origin_before_metal + collected_metal


def test_espionage_flow_creates_report_and_returns(app, client, auth_headers, db_session, sample_planet):
    from backend.models import Fleet, EspionageReport

    _disable_production(db_session, sample_planet)

    enemy_user, enemy_planet = _create_enemy_planet(db_session, x=3001, y=3002, z=3003, name="Enemy Spy")

    build = client.post(
        "/api/shipyard/build",
        json={"planet_id": sample_planet.id, "ship_type": "espionage_probe", "quantity": 1},
        headers=auth_headers,
    )
    assert build.status_code == 200
    fleet_id = build.get_json()["fleet"]["id"]

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "espionage", "target_planet_id": enemy_planet.id},
        headers=auth_headers,
    )
    assert send.status_code == 200

    fleet = Fleet.query.get(fleet_id)
    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    assert EspionageReport.query.count() >= 1
    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "returning"


def test_explore_flow_returns(app, client, auth_headers, db_session, sample_planet):
    from backend.models import Fleet

    _disable_production(db_session, sample_planet)

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"small_cargo": 1}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    send = client.post(
        "/api/fleet/send",
        json={"fleet_id": fleet_id, "mission": "explore", "target_x": 400, "target_y": 500, "target_z": 600},
        headers=auth_headers,
    )
    assert send.status_code == 200

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status.startswith("exploring:")

    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)
    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "returning"


def test_colonize_flow_claims_planet(app, client, auth_headers, db_session, sample_user, sample_planet):
    from backend.models import Fleet, Planet

    _disable_production(db_session, sample_planet)
    sample_planet.deuterium = 1_000_000
    db_session.commit()

    # Ensure research is sufficient for the chosen target coordinates.
    from backend.models import Research
    research = Research(user_id=sample_user.id, colonization_tech=10, astrophysics=0, interstellar_communication=0, research_points=0)
    db_session.add(research)
    db_session.commit()

    # Create an unowned planet at the target.
    # Keep it close to the origin to avoid fuel issues in tests.
    target = Planet(
        name="Unowned",
        x=101,
        y=201,
        z=301,
        user_id=None,
        metal=0,
        crystal=0,
        deuterium=0,
        metal_mine=0,
        crystal_mine=0,
        deuterium_synthesizer=0,
        solar_plant=0,
        fusion_reactor=0,
    )
    db_session.add(target)
    db_session.commit()

    res = client.post(
        "/api/fleet",
        json={"start_planet_id": sample_planet.id, "ships": {"colony_ship": 1}},
        headers=auth_headers,
    )
    assert res.status_code == 201
    fleet_id = res.get_json()["fleet"]["id"]

    send = client.post(
        "/api/fleet/send",
        json={
            "fleet_id": fleet_id,
            "mission": "colonize",
            "target_planet_id": target.id,
        },
        headers=auth_headers,
    )
    assert send.status_code == 200

    fleet = Fleet.query.get(fleet_id)
    assert fleet.status.startswith("colonizing:")

    _fast_forward_arrival(db_session, fleet)
    _run_tick(app)

    db_session.refresh(target)
    assert target.user_id == sample_user.id
    fleet = Fleet.query.get(fleet_id)
    assert fleet.status == "stationed"
