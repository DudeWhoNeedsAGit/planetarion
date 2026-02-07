from datetime import datetime


def _create_user(db_session, *, username: str, email: str):
    import bcrypt
    from backend.models import User

    pw = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    u = User(username=username, email=email, password_hash=pw)
    db_session.add(u)
    db_session.commit()
    return u


def test_pirate_expansion_spawns_colonizer_and_respects_home_buffer(app, db_session):
    from backend.models import Fleet, Planet, TickLog
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_INTERVAL_SECONDS"] = 60
        app.config["PIRATE_SIM_PLANET_CAP_PER_FACTION"] = 6
        app.config["PIRATE_SIM_PLANET_CAP_PER_Z_SLICE"] = 3
        app.config["PIRATE_SIM_TOTAL_PLANET_CAP"] = 18
        app.config["PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE"] = 300
        app.config["PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO"] = 0.95

        player = _create_user(db_session, username="exp_player", email="exp_player@example.com")
        pirates = _create_user(db_session, username="pirates", email="exp_pirates@example.com")

        player_home = Planet(name="Player Home", x=1000, y=1000, z=7, user_id=player.id, is_home_planet=True)
        pirate_camp = Planet(name="Pirate Camp", x=900, y=900, z=7, user_id=pirates.id, is_home_planet=True)
        blocked_target = Planet(name="Blocked", x=1010, y=1000, z=7, user_id=None)
        valid_target = Planet(name="Valid", x=1900, y=1600, z=7, user_id=None)
        db_session.add_all([player_home, pirate_camp, blocked_target, valid_target])
        db_session.commit()

        source = Fleet(
            user_id=pirates.id,
            mission="defend",
            status="stationed",
            start_planet_id=pirate_camp.id,
            target_planet_id=pirate_camp.id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            colony_ship=2,
            light_fighter=50,
        )
        db_session.add(source)
        db_session.commit()

        now = datetime.utcnow()
        result = PirateAIDirector.run_hourly(now=now)
        assert int(result.get("expansion_spawned") or 0) == 1

        colonizer = (
            Fleet.query.filter_by(user_id=pirates.id, mission="colonize")
            .order_by(Fleet.id.desc())
            .first()
        )
        assert colonizer is not None
        assert colonizer.status.startswith("colonizing:")
        assert colonizer.target_coordinates == f"{valid_target.x}:{valid_target.y}:{valid_target.z}"

        updated_source = Fleet.query.get(source.id)
        assert int(updated_source.colony_ship or 0) == 1

        started_log = TickLog.query.filter_by(event_type="pirate_colonization_started", fleet_id=colonizer.id).first()
        assert started_log is not None


def test_pirate_expansion_respects_per_faction_planet_cap(app, db_session):
    from backend.models import Fleet, Planet
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_INTERVAL_SECONDS"] = 60
        app.config["PIRATE_SIM_PLANET_CAP_PER_FACTION"] = 1
        app.config["PIRATE_SIM_PLANET_CAP_PER_Z_SLICE"] = 3
        app.config["PIRATE_SIM_TOTAL_PLANET_CAP"] = 18
        app.config["PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE"] = 0

        pirates = _create_user(db_session, username="pirates", email="cap_pirates@example.com")

        pirate_planet = Planet(name="Pirate Core", x=400, y=400, z=3, user_id=pirates.id, is_home_planet=True)
        target = Planet(name="Neutral", x=600, y=650, z=3, user_id=None)
        db_session.add_all([pirate_planet, target])
        db_session.commit()

        source = Fleet(
            user_id=pirates.id,
            mission="defend",
            status="stationed",
            start_planet_id=pirate_planet.id,
            target_planet_id=pirate_planet.id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            colony_ship=1,
        )
        db_session.add(source)
        db_session.commit()

        result = PirateAIDirector.run_hourly(now=datetime.utcnow())
        assert int(result.get("expansion_spawned") or 0) == 0
        assert Fleet.query.filter_by(user_id=pirates.id, mission="colonize").count() == 0
