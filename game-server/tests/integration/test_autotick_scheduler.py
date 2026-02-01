import time


def test_scheduler_runs_ticks(app, db_session, sample_user):
    # Create at least one planet with active mines so ticks always write TickLog entries.
    from backend.models import Planet, TickLog
    from backend.services.scheduler import GameScheduler

    planet = Planet(
        name="AutoTick Planet",
        x=10,
        y=20,
        z=30,
        user_id=sample_user.id,
        metal=0,
        crystal=0,
        deuterium=0,
        metal_mine=1,
        crystal_mine=1,
        deuterium_synthesizer=1,
        solar_plant=10,
    )
    db_session.add(planet)
    db_session.commit()

    before = TickLog.query.count()

    # Run scheduler at a fast interval and verify it produces ticks without manual /api/tick calls.
    app.config["TICK_SCHEDULER_INTERVAL_SECONDS"] = 1
    scheduler = GameScheduler()
    scheduler.init_app(app)
    scheduler.start()
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            if TickLog.query.count() > before:
                break
            time.sleep(0.25)
        assert TickLog.query.count() > before
    finally:
        scheduler.shutdown()

