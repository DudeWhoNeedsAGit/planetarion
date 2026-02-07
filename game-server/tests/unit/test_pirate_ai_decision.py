from datetime import datetime, timedelta

import bcrypt

from backend.models import Fleet, PirateAIState, Planet, User
from backend.services.pirate_ai import PirateAIDirector


def _create_user(db_session, username: str, email: str) -> User:
    pw = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    u = User(username=username, email=email, password_hash=pw)
    db_session.add(u)
    db_session.commit()
    return u


def _create_planet(db_session, user_id: int, *, x: int, y: int, z: int, name: str = "Home", home: bool = True) -> Planet:
    p = Planet(
        name=name,
        x=x,
        y=y,
        z=z,
        user_id=user_id,
        metal=50_000,
        crystal=25_000,
        deuterium=10_000,
        metal_mine=10,
        crystal_mine=9,
        deuterium_synthesizer=8,
        solar_plant=12,
        is_home_planet=home,
    )
    db_session.add(p)
    db_session.commit()
    return p


def test_is_eligible_rejects_protected_no_planets_cooldown_and_daily_cap(app, db_session):
    with app.app_context():
        now = datetime.utcnow()
        user = _create_user(db_session, "elig_user", "elig@example.com")
        state = PirateAIState(user_id=user.id, threat_level=0.0, raids_last_24h=0)
        db_session.add(state)
        db_session.commit()

        user.protection_until = now + timedelta(hours=1)
        db_session.commit()
        ok, reason = PirateAIDirector._is_eligible(user=user, state=state, now=now)
        assert ok is False and reason == "protected"

        user.protection_until = None
        db_session.commit()
        ok, reason = PirateAIDirector._is_eligible(user=user, state=state, now=now)
        assert ok is False and reason == "no_planets"

        _create_planet(db_session, user.id, x=10, y=20, z=30)
        state.cooldown_until = now + timedelta(hours=1)
        db_session.commit()
        ok, reason = PirateAIDirector._is_eligible(user=user, state=state, now=now)
        assert ok is False and reason == "cooldown"

        state.cooldown_until = None
        app.config["PIRATE_AI_MAX_RAIDS_PER_24H"] = 2
        state.raids_last_24h = 2
        db_session.commit()
        ok, reason = PirateAIDirector._is_eligible(user=user, state=state, now=now)
        assert ok is False and reason == "daily_cap"


def test_is_peak_hour_boundaries(app):
    with app.app_context():
        assert PirateAIDirector._is_peak_hour(datetime(2026, 2, 7, 18, 0, 0)) is True
        assert PirateAIDirector._is_peak_hour(datetime(2026, 2, 7, 19, 59, 59)) is True
        assert PirateAIDirector._is_peak_hour(datetime(2026, 2, 7, 20, 0, 0)) is False
        assert PirateAIDirector._is_peak_hour(datetime(2026, 2, 7, 17, 59, 59)) is False


def test_rng_for_hour_is_deterministic():
    dt = datetime(2026, 2, 7, 19, 0, 0)
    a = PirateAIDirector._rng_for_hour(user_id=11, hour_key=PirateAIDirector._truncate_to_hour(dt), salt="s")
    b = PirateAIDirector._rng_for_hour(user_id=11, hour_key=PirateAIDirector._truncate_to_hour(dt), salt="s")
    c = PirateAIDirector._rng_for_hour(user_id=11, hour_key=PirateAIDirector._truncate_to_hour(dt + timedelta(hours=1)), salt="s")

    assert a.random() == b.random()
    assert a.random() != c.random()


def test_decide_for_player_respects_probability_clamp_and_peak_power(app, db_session):
    with app.app_context():
        user = _create_user(db_session, "decide_user", "decide@example.com")
        _create_planet(db_session, user.id, x=100, y=200, z=42)
        # Add substantial fleet power so raw probability tends high before clamp.
        now = datetime.utcnow()
        db_session.add(
            Fleet(
                user_id=user.id,
                mission="inventory",
                status="stationed",
                start_planet_id=Planet.query.filter_by(user_id=user.id).first().id,
                target_planet_id=Planet.query.filter_by(user_id=user.id).first().id,
                departure_time=now,
                arrival_time=now,
                eta=0,
                light_fighter=5000,
                cruiser=500,
                battleship=120,
            )
        )
        db_session.commit()

        state = PirateAIState(user_id=user.id, threat_level=100.0, raids_last_24h=0)
        db_session.add(state)
        db_session.commit()

        app.config["PIRATE_AI_SECRET_SALT"] = "decision-test"
        app.config["PIRATE_AI_P_MAX"] = 0.10
        app.config["PIRATE_AI_PEAK_PROB_MULT"] = 2.0
        app.config["PIRATE_AI_DIFFICULTY_FACTOR"] = 1.0
        app.config["PIRATE_AI_PEAK_POWER_MULT"] = 1.5

        peak_now = datetime(2026, 2, 7, 19, 0, 0)
        off_now = datetime(2026, 2, 7, 10, 0, 0)

        peak_decision = PirateAIDirector._decide_for_player(user=user, state=state, now=peak_now)
        off_decision = PirateAIDirector._decide_for_player(user=user, state=state, now=off_now)

        assert peak_decision.probability <= 0.10
        assert off_decision.probability <= 0.10
        assert peak_decision.is_peak is True
        assert off_decision.is_peak is False
        assert peak_decision.pirate_power > off_decision.pirate_power


def test_select_target_planet_avoids_immediate_repeat(db_session):
    user = _create_user(db_session, "target_user", "target@example.com")
    p1 = _create_planet(db_session, user.id, x=1, y=1, z=1, name="A")
    p2 = _create_planet(db_session, user.id, x=2, y=2, z=1, name="B", home=False)
    p1.metal = 2_000_000
    p2.metal = 1_000_000
    db_session.commit()

    target = PirateAIDirector._select_target_planet(player_planets=[p1, p2], last_target_planet_id=p1.id)
    assert target is not None
    assert target.id == p2.id


def test_run_hourly_enforces_cap_and_cooldown(app, db_session):
    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_AI_INTERVAL_SECONDS"] = 3600
        app.config["PIRATE_AI_COOLDOWN_SECONDS"] = 3600
        app.config["PIRATE_AI_MAX_RAIDS_PER_24H"] = 1
        app.config["PIRATE_AI_SECRET_SALT"] = "cap-cooldown-test"

        user = _create_user(db_session, "cap_user", "cap_user@example.com")
        pirates = _create_user(db_session, "pirates", "pirates_cap@example.com")
        _create_planet(db_session, user.id, x=300, y=300, z=9)
        _create_planet(db_session, pirates.id, x=340, y=340, z=9, name="Pirate Camp", home=False)

        t0 = datetime(2026, 2, 7, 19, 0, 0)
        res1 = PirateAIDirector.run_hourly(now=t0, force_spawn_for_user_ids={user.id})
        assert res1["spawned"] == 1

        # Due interval has passed, but cooldown still blocks.
        t1 = t0 + timedelta(hours=1, minutes=1)
        res2 = PirateAIDirector.run_hourly(now=t1, force_spawn_for_user_ids={user.id})
        assert res2["spawned"] == 0

        # Cooldown elapsed, but daily cap still blocks.
        t2 = t0 + timedelta(hours=2, minutes=5)
        res3 = PirateAIDirector.run_hourly(now=t2, force_spawn_for_user_ids={user.id})
        assert res3["spawned"] == 0
