#!/usr/bin/env python3
"""
Fast database setup for testing - uses backup/restore for speed
"""

import os
import shutil
import subprocess
import sys
import sqlite3
from pathlib import Path

EXPECTED_E2E_USERNAME = os.environ.get("PLANETARION_TEST_USERNAME", "e2etestuser")

def _sqlite_columns(con: sqlite3.Connection, table: str) -> set[str]:
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}

def _ensure_sqlite_columns(db_path: Path) -> None:
    """Ensure newly added columns exist in the SQLite DB file.

    This repo uses SQLite snapshots (.bak). Restoring a snapshot can overwrite schema
    changes that were added by SQLAlchemy models. Keep the snapshot compatible by
    applying small ALTER TABLE migrations here.
    """
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.cursor()

        # users lifecycle/protection
        user_cols = _sqlite_columns(con, "users")
        if "eliminated_at" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN eliminated_at DATETIME")
        if "respawned_at" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN respawned_at DATETIME")
        if "protection_until" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN protection_until DATETIME")
        if "respawn_count" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN respawn_count INTEGER DEFAULT 0")

        # planets storage columns
        planet_cols = _sqlite_columns(con, "planets")
        if "metal_storage" not in planet_cols:
            cur.execute("ALTER TABLE planets ADD COLUMN metal_storage INTEGER DEFAULT 0")
        if "crystal_storage" not in planet_cols:
            cur.execute("ALTER TABLE planets ADD COLUMN crystal_storage INTEGER DEFAULT 0")
        if "deuterium_tank" not in planet_cols:
            cur.execute("ALTER TABLE planets ADD COLUMN deuterium_tank INTEGER DEFAULT 0")

        # fleets cargo columns
        fleet_cols = _sqlite_columns(con, "fleets")
        if "cargo_metal" not in fleet_cols:
            cur.execute("ALTER TABLE fleets ADD COLUMN cargo_metal BIGINT DEFAULT 0")
        if "cargo_crystal" not in fleet_cols:
            cur.execute("ALTER TABLE fleets ADD COLUMN cargo_crystal BIGINT DEFAULT 0")
        if "cargo_deuterium" not in fleet_cols:
            cur.execute("ALTER TABLE fleets ADD COLUMN cargo_deuterium BIGINT DEFAULT 0")

        con.commit()
    finally:
        con.close()

def _backup_looks_valid(backup_file: Path) -> bool:
    """Heuristic check: ensure the backup contains the expected E2E user."""
    try:
        con = sqlite3.connect(str(backup_file))
        cur = con.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (EXPECTED_E2E_USERNAME,))
        return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        try:
            con.close()
        except Exception:
            pass

def setup_test_database():
    """Setup test database using backup/restore for speed"""

    project_root = Path(__file__).parent.parent
    instance_dir = project_root / 'instance'
    instance_dir.mkdir(exist_ok=True)

    db_file = instance_dir / 'test_e2e.db'
    backup_file = instance_dir / 'test_e2e.db.bak'

    print("🗄️ Setting up test database...")

    if backup_file.exists():
        if _backup_looks_valid(backup_file):
            print("📋 Backup found - copying to working database...")
            shutil.copy2(backup_file, db_file)
            # Ensure schema compatibility even if snapshot predates new columns.
            _ensure_sqlite_columns(db_file)
            # Keep the snapshot upgraded too (avoids future overwrites breaking a running backend).
            _ensure_sqlite_columns(backup_file)
            print("✅ Database restored from backup (FAST!)")
            return True
        print("⚠️ Backup found but missing expected E2E user - recreating fresh database...")

    print("📋 No backup found - creating fresh database...")

    # Run population script to create database
    populate_script = project_root / 'scripts' / 'populate_test_data.py'

    env = os.environ.copy()
    env.update({
        'DATABASE_URL': f'sqlite:///{db_file}',
        'BACKEND_URL': 'http://localhost:5000',
        'PYTHONPATH': str(project_root / 'src')
    })

    result = subprocess.run([
        sys.executable, str(populate_script)
    ], env=env, cwd=project_root)

    if result.returncode == 0:
        print("📋 Creating backup for future runs...")
        shutil.copy2(db_file, backup_file)
        print("✅ Database created and backup saved!")
        return True
    else:
        print("❌ Database creation failed!")
        return False

if __name__ == '__main__':
    success = setup_test_database()
    sys.exit(0 if success else 1)
