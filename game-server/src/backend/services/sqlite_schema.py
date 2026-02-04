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


def ensure_planet_trait_columns(db_engine) -> None:
    """Add missing Planet trait/classification columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "planets")
        for name, col_type, default in (
            ("planet_type", "TEXT", "'terrestrial'"),
            ("temperature", "INTEGER", "20"),
            ("size", "INTEGER", "10000"),
            ("habitability", "REAL", "100.0"),
        ):
            if name in cols:
                continue
            connection.execute(text(f"ALTER TABLE planets ADD COLUMN {name} {col_type} DEFAULT {default}"))


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


def ensure_user_research_queue_columns(db_engine) -> None:
    """Add missing User research queue columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "users")
        # One queue per user stored as JSON string.
        if "research_queue" not in cols:
            connection.execute(text("ALTER TABLE users ADD COLUMN research_queue TEXT"))


def ensure_research_fraction_columns(db_engine) -> None:
    """Add missing Research fractional columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "research")
        if "research_points_fraction" not in cols:
            connection.execute(text("ALTER TABLE research ADD COLUMN research_points_fraction REAL DEFAULT 0.0"))


def ensure_research_tech_columns(db_engine) -> None:
    """Add missing Research tech columns for SQLite DBs (test/gameplay compatibility)."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "research")
        for name, col_type, default in (
            ("energy_tech", "INTEGER", "0"),
            ("laser_tech", "INTEGER", "0"),
            ("ion_tech", "INTEGER", "0"),
            ("hyperspace_tech", "INTEGER", "0"),
            ("plasma_tech", "INTEGER", "0"),
            ("combustion_drive", "INTEGER", "0"),
            ("impulse_drive", "INTEGER", "0"),
            ("hyperspace_drive", "INTEGER", "0"),
            ("espionage_tech", "INTEGER", "0"),
            ("computer_tech", "INTEGER", "0"),
            ("intergalactic_research_network", "INTEGER", "0"),
            ("graviton_tech", "INTEGER", "0"),
            ("weapons_tech", "INTEGER", "0"),
            ("shielding_tech", "INTEGER", "0"),
            ("armour_tech", "INTEGER", "0"),
        ):
            if name in cols:
                continue
            connection.execute(text(f"ALTER TABLE research ADD COLUMN {name} {col_type} DEFAULT {default}"))
