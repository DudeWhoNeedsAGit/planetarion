from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

class GameScheduler:
    """Game tick scheduler service"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def init_app(self, app):
        """Initialize scheduler with Flask app context"""
        # Wrapper function to provide application context
        def run_tick_with_context():
            with app.app_context():
                from .tick import run_tick
                run_tick()

        interval_seconds = app.config.get("TICK_SCHEDULER_INTERVAL_SECONDS", 5) or 0
        try:
            interval_seconds = int(interval_seconds)
        except (TypeError, ValueError):
            interval_seconds = 5

        if interval_seconds <= 0:
            app.logger.info("Tick scheduler disabled (interval_seconds<=0)")
            atexit.register(self.shutdown)
            return

        # Add tick job to run every N seconds
        self.scheduler.add_job(
            func=run_tick_with_context,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id='game_tick',
            name='Game Tick',
            replace_existing=True
        )

        # Register shutdown handler
        atexit.register(self.shutdown)

        app.logger.info(f"Tick scheduler initialized - ticks will run every {interval_seconds} seconds")

    def start(self):
        """Start the scheduler"""
        self.scheduler.start()

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def is_running(self):
        """Check if scheduler is running"""
        return self.scheduler.running

    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()

    def pause_job(self, job_id):
        """Pause a specific job"""
        self.scheduler.pause_job(job_id)

    def resume_job(self, job_id):
        """Resume a specific job"""
        self.scheduler.resume_job(job_id)

    def remove_job(self, job_id):
        """Remove a specific job"""
        self.scheduler.remove_job(job_id)

    def add_custom_job(self, func, trigger, job_id, name=None, **kwargs):
        """Add a custom job to the scheduler"""
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=True,
            **kwargs
        )
