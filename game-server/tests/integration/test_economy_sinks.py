from backend.database import db
from backend.models import Fleet
from backend.services.economy_sinks import fleet_upkeep_deuterium_per_tick
from tests.conftest import make_auth_headers


def _set_sink_config(app, enabled=True, rate=0.02, exclude_inventory=True):
    app.config["ECONOMY_SINKS_ENABLED"] = bool(enabled)
    app.config["FLEET_UPKEEP_DEUTERIUM_PER_WEIGHT_PER_TICK"] = float(rate)
    app.config["FLEET_UPKEEP_EXCLUDE_INVENTORY"] = bool(exclude_inventory)


def test_upkeep_is_config_gated_and_deterministic(app, client, sample_user, sample_planet):
    headers = make_auth_headers(sample_user.id)

    sample_planet.metal_mine = 0
    sample_planet.crystal_mine = 0
    sample_planet.deuterium_synthesizer = 0
    sample_planet.deuterium = 5_000

    fleet = Fleet(
        user_id=sample_user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=sample_planet.id,
        target_planet_id=sample_planet.id,
        departure_time=sample_planet.created_at,
        arrival_time=sample_planet.created_at,
        light_fighter=300,
        cruiser=20,
    )
    db.session.add(fleet)
    db.session.commit()

    _set_sink_config(app, enabled=False, rate=0.02)
    before_disabled = int(sample_planet.deuterium)
    res_disabled = client.post("/api/tick")
    assert res_disabled.status_code == 200
    db.session.refresh(sample_planet)
    assert int(sample_planet.deuterium) == before_disabled

    _set_sink_config(app, enabled=True, rate=0.02)
    expected_upkeep = fleet_upkeep_deuterium_per_tick(fleet, app.config)
    assert expected_upkeep > 0

    before_tick_1 = int(sample_planet.deuterium)
    res_enabled_1 = client.post("/api/tick")
    assert res_enabled_1.status_code == 200
    db.session.refresh(sample_planet)
    assert int(sample_planet.deuterium) == before_tick_1 - expected_upkeep

    before_tick_2 = int(sample_planet.deuterium)
    res_enabled_2 = client.post("/api/tick")
    assert res_enabled_2.status_code == 200
    db.session.refresh(sample_planet)
    assert int(sample_planet.deuterium) == before_tick_2 - expected_upkeep

    planets_res = client.get("/api/planet", headers=headers)
    assert planets_res.status_code == 200
    planet_payload = planets_res.get_json()[0]
    assert planet_payload["production_rates"]["deuterium_upkeep_per_hour"] == expected_upkeep * 72
    assert "net_deuterium_per_hour" in planet_payload["production_rates"]


def test_upkeep_never_underflows_deuterium(app, client, sample_user, sample_planet):
    _set_sink_config(app, enabled=True, rate=0.05)

    sample_planet.metal_mine = 0
    sample_planet.crystal_mine = 0
    sample_planet.deuterium_synthesizer = 0
    sample_planet.deuterium = 3

    fleet = Fleet(
        user_id=sample_user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=sample_planet.id,
        target_planet_id=sample_planet.id,
        departure_time=sample_planet.created_at,
        arrival_time=sample_planet.created_at,
        heavy_fighter=200,
    )
    db.session.add(fleet)
    db.session.commit()

    upkeep = fleet_upkeep_deuterium_per_tick(fleet, app.config)
    assert upkeep > int(sample_planet.deuterium)

    res = client.post("/api/tick")
    assert res.status_code == 200

    db.session.refresh(sample_planet)
    assert int(sample_planet.deuterium) == 0


def test_fleet_payload_includes_upkeep_summary(app, client, sample_user, sample_planet):
    headers = make_auth_headers(sample_user.id)
    _set_sink_config(app, enabled=True, rate=0.02)

    fleet = Fleet(
        user_id=sample_user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=sample_planet.id,
        target_planet_id=sample_planet.id,
        departure_time=sample_planet.created_at,
        arrival_time=sample_planet.created_at,
        light_fighter=120,
    )
    db.session.add(fleet)
    db.session.commit()

    res = client.get("/api/fleet", headers=headers)
    assert res.status_code == 200

    fleets = res.get_json()
    assert len(fleets) >= 1
    payload = fleets[0]
    assert "upkeep" in payload
    assert payload["upkeep"]["enabled"] is True
    assert payload["upkeep"]["deuterium_per_tick"] >= 0
    assert payload["upkeep"]["deuterium_per_hour"] == payload["upkeep"]["deuterium_per_tick"] * 72
