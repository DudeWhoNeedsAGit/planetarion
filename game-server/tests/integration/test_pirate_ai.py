from datetime import datetime, timedelta


def _create_user(db_session, *, username: str, email: str):
    import bcrypt

    pw = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    from backend.models import User

    u = User(username=username, email=email, password_hash=pw)
    db_session.add(u)
    db_session.commit()
    return u


def test_pirate_ai_spawns_raid_and_logs(app, db_session):
    from backend.models import Fleet, Planet, TickLog, PirateAIState
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_AI_INTERVAL_SECONDS"] = 3600
        app.config["PIRATE_AI_MAX_RAIDS_PER_24H"] = 2
        app.config["PIRATE_AI_COOLDOWN_SECONDS"] = 0
        app.config["PIRATE_AI_SECRET_SALT"] = "test-salt"
        app.config["PIRATE_AI_DIFFICULTY_FACTOR"] = 1.0

        player = _create_user(db_session, username="player1", email="p1@example.com")
        pirates = _create_user(db_session, username="pirates", email="pirates@example.com")

        home = Planet(
            name="Home",
            x=1000,
            y=1000,
            z=42,
            user_id=player.id,
            metal=100_000,
            crystal=50_000,
            deuterium=25_000,
            metal_mine=10,
            crystal_mine=8,
            deuterium_synthesizer=6,
            solar_plant=12,
            is_home_planet=True,
        )
        db_session.add(home)
        db_session.commit()

        # Minimal defender fleet so the attack goes through the Fleet-vs-Fleet pipeline.
        now = datetime.utcnow()
        defender = Fleet(
            user_id=player.id,
            mission="inventory",
            status="stationed",
            start_planet_id=home.id,
            target_planet_id=home.id,
            departure_time=now,
            arrival_time=now,
            eta=0,
            light_fighter=80,
            heavy_fighter=30,
            cruiser=6,
            battleship=2,
        )
        db_session.add(defender)
        db_session.commit()

        run_now = datetime(2026, 2, 6, 19, 0, 0)
        result = PirateAIDirector.run_hourly(now=run_now, force_spawn_for_user_ids={player.id})
        assert result["enabled"] is True
        assert result["spawned"] == 1

        raid = Fleet.query.filter_by(user_id=pirates.id, mission="attack").order_by(Fleet.id.desc()).first()
        assert raid is not None
        assert raid.status == "traveling"
        assert int(raid.eta or 0) > 0

        log = TickLog.query.filter_by(event_type="pirate_raid_spawned", fleet_id=raid.id).first()
        assert log is not None

        state = PirateAIState.query.filter_by(user_id=player.id).first()
        assert state is not None
        assert state.last_action_at is not None
        assert int(state.raids_last_24h or 0) == 1


def test_pirate_raid_resolves_without_capturing_planet(app, db_session):
    from backend.models import CombatReport, DebrisField, Fleet, Planet
    from backend.services.fleet_arrival import FleetArrivalService
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_AI_INTERVAL_SECONDS"] = 3600
        app.config["PIRATE_AI_MAX_RAIDS_PER_24H"] = 2
        app.config["PIRATE_AI_COOLDOWN_SECONDS"] = 0
        app.config["PIRATE_AI_SECRET_SALT"] = "test-salt"
        # Make the raid decisively strong so we reliably generate ship losses -> debris.
        app.config["PIRATE_AI_DIFFICULTY_FACTOR"] = 3.0

        player = _create_user(db_session, username="player2", email="p2@example.com")
        pirates = _create_user(db_session, username="pirates", email="pirates@example.com")

        target = Planet(
            name="Target",
            x=2000,
            y=2000,
            z=42,
            user_id=player.id,
            metal=10_000,
            crystal=5_000,
            deuterium=2_000,
            metal_mine=8,
            crystal_mine=6,
            deuterium_synthesizer=4,
            solar_plant=10,
            is_home_planet=True,
        )
        db_session.add(target)
        db_session.commit()

        now = datetime.utcnow()
        defender = Fleet(
            user_id=player.id,
            mission="inventory",
            status="stationed",
            start_planet_id=target.id,
            target_planet_id=target.id,
            departure_time=now,
            arrival_time=now,
            eta=0,
            light_fighter=40,
            heavy_fighter=15,
            cruiser=3,
            battleship=1,
        )
        db_session.add(defender)
        db_session.commit()

        run_now = datetime(2026, 2, 6, 19, 0, 0)
        PirateAIDirector.run_hourly(now=run_now, force_spawn_for_user_ids={player.id})

        raid = Fleet.query.filter_by(user_id=pirates.id, mission="attack").order_by(Fleet.id.desc()).first()
        assert raid is not None

        # Force arrival.
        raid.arrival_time = datetime.utcnow() - timedelta(seconds=1)
        raid.eta = 0
        db_session.commit()

        FleetArrivalService.process_arrived_fleets()
        db_session.commit()

        report = CombatReport.query.filter_by(attacker_id=pirates.id, defender_id=player.id, planet_id=target.id).first()
        assert report is not None

        debris = DebrisField.query.filter_by(planet_id=target.id).first()
        assert debris is not None
        assert int(debris.metal or 0) + int(debris.crystal or 0) > 0

        # Pirates should not conquer player planets (MVP).
        refreshed = Planet.query.get(target.id)
        assert refreshed.user_id == player.id
