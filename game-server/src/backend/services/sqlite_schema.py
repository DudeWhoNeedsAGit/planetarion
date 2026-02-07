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


def ensure_user_profile_columns(db_engine) -> None:
    """Add missing User commander/profile columns for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        cols = _get_sqlite_columns(connection, "users")
        for name, col_type, default in (
            ("last_seen_at", "DATETIME", "NULL"),
            ("commander_level", "INTEGER", "1"),
            ("commander_xp", "BIGINT", "0"),
            ("portrait_key", "TEXT", "NULL"),
            ("frame_key", "TEXT", "NULL"),
        ):
            if name in cols:
                continue
            if default == "NULL":
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type}"))
            else:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {col_type} DEFAULT {default}"))


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
            ("recycler_efficiency", "INTEGER", "0"),
        ):
            if name in cols:
                continue
            connection.execute(text(f"ALTER TABLE research ADD COLUMN {name} {col_type} DEFAULT {default}"))


def ensure_commander_xp_event_table(db_engine) -> None:
    """Ensure commander XP event idempotency table exists for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS commander_xp_events (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    source_type VARCHAR(32) NOT NULL,
                    source_id VARCHAR(128) NOT NULL,
                    xp_awarded INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    CONSTRAINT uq_commander_xp_event UNIQUE (user_id, source_type, source_id),
                    FOREIGN KEY(user_id) REFERENCES users (id)
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_commander_xp_event_user_source ON commander_xp_events (user_id, source_type)"
            )
        )


def ensure_pirate_ai_state_table(db_engine) -> None:
    """Ensure per-player Pirate AI state table exists for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pirate_ai_state (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    last_action_at DATETIME,
                    cooldown_until DATETIME,
                    threat_level REAL DEFAULT 0.0,
                    raids_last_24h INTEGER DEFAULT 0,
                    raids_window_start_at DATETIME,
                    last_target_planet_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    FOREIGN KEY(last_target_planet_id) REFERENCES planets (id)
                )
                """
            )
        )
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_pirate_ai_state_user_id ON pirate_ai_state (user_id)"))


def ensure_pirate_ai_config_overrides_table(db_engine) -> None:
    """Ensure Pirate AI live-ops config override table exists for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pirate_ai_config_overrides (
                    id INTEGER PRIMARY KEY,
                    config_key VARCHAR(64) NOT NULL UNIQUE,
                    config_value VARCHAR(128) NOT NULL,
                    updated_at DATETIME,
                    created_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_pirate_ai_config_overrides_config_key ON pirate_ai_config_overrides (config_key)"
            )
        )


def ensure_pirate_faction_state_table(db_engine) -> None:
    """Ensure pirate faction simulation state table exists for SQLite DBs."""
    if db_engine.dialect.name != "sqlite":
        return

    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pirate_faction_state (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    expansion_cooldown_until DATETIME,
                    build_cooldown_until DATETIME,
                    skirmish_cooldown_until DATETIME,
                    expansion_points INTEGER DEFAULT 0,
                    fleet_points INTEGER DEFAULT 0,
                    planet_cap INTEGER DEFAULT 0,
                    fleet_cap INTEGER DEFAULT 0,
                    last_target_faction_user_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    FOREIGN KEY(last_target_faction_user_id) REFERENCES users (id)
                )
                """
            )
        )
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_pirate_faction_state_user_id ON pirate_faction_state (user_id)"))
