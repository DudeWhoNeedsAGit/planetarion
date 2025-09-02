# Coding Style Rules

## Style
- **Value:** `structured`

## Rules
- Use clean, modular code with folders for `backend/`, `frontend/`, and `database/`
- Implement SQLAlchemy models: `User`, `Planet`, `Fleet`, `Alliance`, `TickLog`
- Expose REST endpoints with Flask blueprints
- Frontend must fetch data exclusively from backend APIs
- Use Postgres for persistence
- Tick engine must run automatically and be testable via endpoint
- Mark stubs with `TODO` and add placeholder tests
