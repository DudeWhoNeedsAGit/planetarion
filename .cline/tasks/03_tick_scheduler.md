# Task 03 – Tick Scheduler

Implement tick system using APScheduler:

- Runs every 5 minutes
- Increments resources on each planet
- Updates fleet movement timers
- When fleet ETA reached, log "combat placeholder"
- Log tick events in TickLog

Provide:
- Service file (`services/tick.py`) with tick logic
- Automatic scheduler start in `app.py`
- Debug endpoint `/api/tick` to trigger manually
