from sqlalchemy import text


def _get_sqlite_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    # row: cid, name, type, notnull, dflt_value, pk
    return {r[1] for r in rows}


def ensure_planet_storage_columns(db_engine) -> None:
    """Add missing Planet storage columns for SQLite DBs.

    This project often uses SQLite without Alembic migrations. Adding new SQLAlchemy
    columns would otherwise break existing databases with "no such column" errors.
    """
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "planets")
        for name, col_type, default in (
            ("metal_storage", "INTEGER", "0"),
            ("crystal_storage", "INTEGER", "0"),
            ("deuterium_tank", "INTEGER", "0"),
        ):
            if name in cols:
                continue
            connection.execute(
                text(f"ALTER TABLE planets ADD COLUMN {name} {col_type} DEFAULT {default}")
            )


def ensure_fleet_cargo_columns(db_engine) -> None:
    """Add missing Fleet cargo columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "fleets")
        for name, col_type, default in (
            ("cargo_metal", "BIGINT", "0"),
            ("cargo_crystal", "BIGINT", "0"),
            ("cargo_deuterium", "BIGINT", "0"),
        ):
            if name in cols:
                continue
            connection.execute(
                text(f"ALTER TABLE fleets ADD COLUMN {name} {col_type} DEFAULT {default}")
            )


def ensure_user_lifecycle_columns(db_engine) -> None:
    """Add missing User lifecycle/protection columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "users")
        for name, col_type, default in (
            ("eliminated_at", "DATETIME", "NULL"),
            ("respawned_at", "DATETIME", "NULL"),
            ("protection_until", "DATETIME", "NULL"),
            ("respawn_count", "INTEGER", "0"),
        ):
            if name in cols:
                continue
            if default == "NULL":
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type}"))
            else:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type} DEFAULT {default}"))
