from datetime import datetime, timedelta


def _create_user(db_session, *, username: str, email: str):
    import bcrypt
    from backend.models import User

    pw = bcrypt.hashpw("pw".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    u = User(username=username, email=email, password_hash=pw)
    db_session.add(u)
    db_session.commit()
    return u


def test_growth_cycle_respects_caps(app, db_session):
    from backend.models import Fleet, Planet
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = False
        app.config["PIRATE_SIM_SKIRMISH_ENABLED"] = False
        app.config["PIRATE_SIM_BUILD_ENABLED"] = True
        app.config["PIRATE_SIM_FLEET_GROWTH_ENABLED"] = True
        app.config["PIRATE_SIM_BUILD_INTERVAL_SECONDS"] = 60
        app.config["PIRATE_SIM_FLEET_CAP_SCORE"] = 900

        pirates = _create_user(db_session, username="pirates", email="sim_growth_pirates@example.com")
        planet = Planet(
            name="Pirate Forge",
            x=120,
            y=90,
            z=1,
            user_id=pirates.id,
            is_home_planet=True,
            metal_mine=1,
            crystal_mine=1,
            deuterium_synthesizer=0,
            solar_plant=1,
        )
        db_session.add(planet)
        db_session.commit()

        fleet = Fleet(
            user_id=pirates.id,
            mission="inventory",
            status="stationed",
            start_planet_id=planet.id,
            target_planet_id=planet.id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            colony_ship=1,
            light_fighter=5,
        )
        db_session.add(fleet)
        db_session.commit()

        t0 = datetime.utcnow()
        for i in range(8):
            PirateAIDirector.run_hourly(now=t0 + timedelta(seconds=(i * 65)))
            db_session.commit()

        refreshed = Planet.query.get(planet.id)
        assert int(refreshed.metal_mine or 0) <= 12
        assert int(refreshed.crystal_mine or 0) <= 12
        assert int(refreshed.deuterium_synthesizer or 0) <= 10
        assert int(refreshed.solar_plant or 0) <= 12

        stationed = Fleet.query.filter_by(user_id=pirates.id, start_planet_id=planet.id, status="stationed").all()
        total = {
            "light_fighter": sum(int(getattr(f, "light_fighter", 0) or 0) for f in stationed),
            "heavy_fighter": sum(int(getattr(f, "heavy_fighter", 0) or 0) for f in stationed),
            "cruiser": sum(int(getattr(f, "cruiser", 0) or 0) for f in stationed),
            "battleship": sum(int(getattr(f, "battleship", 0) or 0) for f in stationed),
            "battlecruiser": sum(int(getattr(f, "battlecruiser", 0) or 0) for f in stationed),
            "colony_ship": sum(int(getattr(f, "colony_ship", 0) or 0) for f in stationed),
        }
        assert total["light_fighter"] <= 250
        assert total["heavy_fighter"] <= 120
        assert total["cruiser"] <= 50
        assert total["battleship"] <= 20
        assert total["battlecruiser"] <= 10
        assert total["colony_ship"] <= 3


def test_skirmish_cycle_spawns_attack_and_resolves_to_combat_report_and_debris(app, db_session):
    from backend.models import CombatReport, DebrisField, Fleet, Planet, TickLog
    from backend.services.fleet_arrival import FleetArrivalService
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = False
        app.config["PIRATE_SIM_BUILD_ENABLED"] = False
        app.config["PIRATE_SIM_SKIRMISH_ENABLED"] = True
        app.config["PIRATE_SIM_SKIRMISH_INTERVAL_SECONDS"] = 60

        pirates = _create_user(db_session, username="pirates", email="sim_skirmish_pirates@example.com")
        pirates_red = _create_user(db_session, username="pirates_red", email="sim_skirmish_red@example.com")

        p1 = Planet(name="Skirmish A", x=1000, y=1000, z=4, user_id=pirates.id, is_home_planet=True)
        p2 = Planet(name="Skirmish B", x=1080, y=1020, z=4, user_id=pirates_red.id, is_home_planet=True)
        db_session.add_all([p1, p2])
        db_session.commit()

        f1 = Fleet(
            user_id=pirates.id,
            mission="inventory",
            status="stationed",
            start_planet_id=p1.id,
            target_planet_id=p1.id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            light_fighter=250,
            heavy_fighter=120,
            cruiser=30,
            battleship=10,
        )
        f2 = Fleet(
            user_id=pirates_red.id,
            mission="inventory",
            status="stationed",
            start_planet_id=p2.id,
            target_planet_id=p2.id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            light_fighter=180,
            heavy_fighter=100,
            cruiser=20,
            battleship=8,
        )
        db_session.add_all([f1, f2])
        db_session.commit()

        now = datetime.utcnow()
        PirateAIDirector.run_hourly(now=now)
        db_session.commit()

        skirmish = Fleet.query.filter_by(mission="attack", status="traveling").order_by(Fleet.id.desc()).first()
        assert skirmish is not None

        skirmish.arrival_time = datetime.utcnow() - timedelta(seconds=1)
        skirmish.eta = 0
        db_session.commit()
        FleetArrivalService.process_arrived_fleets()
        db_session.commit()

        report = CombatReport.query.filter(
            CombatReport.attacker_id.in_([pirates.id, pirates_red.id]),
            CombatReport.defender_id.in_([pirates.id, pirates_red.id]),
        ).order_by(CombatReport.id.desc()).first()
        assert report is not None

        debris = DebrisField.query.filter_by(planet_id=report.planet_id).first()
        assert debris is not None
        assert int(debris.metal or 0) + int(debris.crystal or 0) >= 0

        resolved = TickLog.query.filter_by(event_type="pirate_skirmish_resolved").first()
        assert resolved is not None


def test_expansion_halts_when_ownership_ratio_exceeded(app, db_session):
    from backend.models import Fleet, Planet, TickLog
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = True
        app.config["PIRATE_SIM_BUILD_ENABLED"] = False
        app.config["PIRATE_SIM_SKIRMISH_ENABLED"] = False
        app.config["PIRATE_SIM_EXPANSION_INTERVAL_SECONDS"] = 60
        app.config["PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO"] = 0.1

        pirates = _create_user(db_session, username="pirates", email="sim_ratio_pirates@example.com")
        player = _create_user(db_session, username="sim_ratio_player", email="sim_ratio_player@example.com")

        pirate_planets = [
            Planet(name=f"P{i}", x=200 + i * 5, y=200 + i * 5, z=2, user_id=pirates.id, is_home_planet=(i == 0))
            for i in range(3)
        ]
        player_planet = Planet(name="Player Home", x=900, y=900, z=2, user_id=player.id, is_home_planet=True)
        neutral = Planet(name="Neutral", x=500, y=550, z=2, user_id=None)
        db_session.add_all(pirate_planets + [player_planet, neutral])
        db_session.commit()

        source = Fleet(
            user_id=pirates.id,
            mission="defend",
            status="stationed",
            start_planet_id=pirate_planets[0].id,
            target_planet_id=pirate_planets[0].id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            eta=0,
            colony_ship=2,
        )
        db_session.add(source)
        db_session.commit()

        PirateAIDirector.run_hourly(now=datetime.utcnow())
        db_session.commit()

        assert Fleet.query.filter_by(user_id=pirates.id, mission="colonize").count() == 0
        blocked = TickLog.query.filter_by(event_type="pirate_growth_blocked_cap").order_by(TickLog.id.desc()).first()
        assert blocked is not None
        assert "reason=ownership_ratio" in str(blocked.event_description or "")


def test_reseed_restores_faction_with_no_planets(app, db_session):
    from backend.models import Planet, TickLog
    from backend.services.pirate_ai import PirateAIDirector

    with app.app_context():
        app.config["PIRATE_AI_ENABLED"] = True
        app.config["PIRATE_SIM_ENABLED"] = True
        app.config["PIRATE_SIM_EXPANSION_ENABLED"] = False
        app.config["PIRATE_SIM_BUILD_ENABLED"] = False
        app.config["PIRATE_SIM_SKIRMISH_ENABLED"] = False
        app.config["PIRATE_SIM_RESEED_COOLDOWN_SECONDS"] = 60

        _create_user(db_session, username="pirates", email="sim_reseed_primary@example.com")
        wiped = _create_user(db_session, username="pirates_black", email="sim_reseed_black@example.com")

        assert Planet.query.filter_by(user_id=wiped.id).count() == 0
        PirateAIDirector.run_hourly(now=datetime.utcnow())
        db_session.commit()

        assert Planet.query.filter_by(user_id=wiped.id).count() >= 1
        evt = TickLog.query.filter_by(event_type="pirate_faction_reseeded").order_by(TickLog.id.desc()).first()
        assert evt is not None
