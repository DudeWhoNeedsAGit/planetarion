"""
Admin Routes

Administrative endpoints for system monitoring and maintenance.
Requires authentication and admin privileges.

Endpoints:
- GET /api/admin/fleet-health - Get fleet system health report
- POST /api/admin/fleet/cleanup - Force cleanup stuck fleets
- GET /api/admin/system-status - Get overall system status
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from backend.database import db
from backend.models import User
from backend.services.fleet_travel_guard import FleetTravelGuard
import os
import sqlite3
import time
from pathlib import Path
from datetime import datetime
import bcrypt

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def is_admin(user_id):
    """Check if user has admin privileges"""
    # For now, check if user is e2etestuser (can be expanded later)
    user = User.query.get(user_id)
    return user and user.username == 'e2etestuser'

def _is_dev_or_test_env() -> bool:
    env = (current_app.config.get("FLASK_ENV") or "").lower()
    return env in ("development", "testing")

def _has_dev_admin_token() -> bool:
    token = os.getenv("PLANETARION_DEV_ADMIN_TOKEN", "").strip()
    if not token:
        return False
    presented = (request.headers.get("X-Planetarion-Dev-Token") or "").strip()
    return presented == token

def _require_admin_or_dev_token() -> tuple[bool, tuple[dict, int] | None]:
    # Strong safety: never allow DB snapshot/restore outside dev/test.
    if not _is_dev_or_test_env():
        return False, ({"error": "Not allowed outside development/testing"}, 403)

    # Fast local workflow: allow a shared dev token.
    if _has_dev_admin_token():
        return True, None

    # Fallback: require an admin JWT.
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    if identity is None:
        return False, ({"error": "Admin access required"}, 403)

    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return False, ({"error": "Admin access required"}, 403)

    if not is_admin(user_id):
        return False, ({"error": "Admin access required"}, 403)

    return True, None

def _get_sqlite_db_path() -> str:
    # Only supports sqlite for this fast-reset workflow.
    url = str(db.engine.url)
    if not url.startswith("sqlite:"):
        raise RuntimeError("DB snapshot/restore only supported for sqlite")
    return db.engine.url.database

def _default_snapshot_path(live_path: str) -> str:
    return f"{live_path}.bak"

@admin_bp.route("/db/snapshot", methods=["POST"])
def snapshot_db():
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    payload = request.get_json(silent=True) or {}
    overwrite = bool(payload.get("overwrite", False))

    try:
        live_path = _get_sqlite_db_path()
        snapshot_path = os.getenv("PLANETARION_DB_SNAPSHOT_PATH") or _default_snapshot_path(live_path)

        Path(snapshot_path).parent.mkdir(parents=True, exist_ok=True)

        if os.path.exists(snapshot_path) and not overwrite:
            return jsonify({
                "message": "Snapshot already exists (set overwrite=true to replace)",
                "live_path": live_path,
                "snapshot_path": snapshot_path,
            }), 200

        scheduler = current_app.extensions.get("game_scheduler")
        was_running = bool(getattr(scheduler, "is_running", lambda: False)())
        job_paused = False
        if was_running:
            try:
                scheduler.pause_job("game_tick")
                job_paused = True
            except Exception:
                pass

        start = time.time()
        db.session.remove()
        db.engine.dispose()

        src = sqlite3.connect(live_path)
        try:
            dst = sqlite3.connect(snapshot_path)
            try:
                # Copy live -> snapshot
                src.backup(dst)
                dst.commit()
            finally:
                dst.close()
        finally:
            src.close()

        duration_ms = int((time.time() - start) * 1000)

        if job_paused:
            try:
                scheduler.resume_job("game_tick")
            except Exception:
                pass

        return jsonify({
            "message": "Snapshot created",
            "live_path": live_path,
            "snapshot_path": snapshot_path,
            "duration_ms": duration_ms,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/db/restore", methods=["POST"])
def restore_db():
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    try:
        live_path = _get_sqlite_db_path()
        snapshot_path = os.getenv("PLANETARION_DB_SNAPSHOT_PATH") or _default_snapshot_path(live_path)
        if not os.path.exists(snapshot_path):
            return jsonify({
                "error": "Snapshot not found",
                "snapshot_path": snapshot_path,
            }), 404

        scheduler = current_app.extensions.get("game_scheduler")
        was_running = bool(getattr(scheduler, "is_running", lambda: False)())
        job_paused = False
        if was_running:
            try:
                scheduler.pause_job("game_tick")
                job_paused = True
            except Exception:
                pass

        start = time.time()
        db.session.remove()
        db.engine.dispose()

        src = sqlite3.connect(snapshot_path)
        try:
            dst = sqlite3.connect(live_path)
            try:
                # Copy snapshot -> live
                src.backup(dst)
                dst.commit()
            finally:
                dst.close()
        finally:
            src.close()

        duration_ms = int((time.time() - start) * 1000)

        if job_paused:
            try:
                scheduler.resume_job("game_tick")
            except Exception:
                pass

        return jsonify({
            "message": "Database restored from snapshot",
            "live_path": live_path,
            "snapshot_path": snapshot_path,
            "duration_ms": duration_ms,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/scenarios/two-player/reset", methods=["POST"])
def reset_two_player_scenario():
    """Create a deterministic 2-player + pirates scenario for manual/E2E testing.

    This endpoint is only available in development/testing and requires either:
    - X-Planetarion-Dev-Token matching PLANETARION_DEV_ADMIN_TOKEN, or
    - an admin JWT (currently: username == e2etestuser)
    """
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password") or "testpassword123")
    now = datetime.utcnow()

    try:
        # Clear existing data (reverse dependency order).
        from backend.models import (
            TickLog,
            Fleet,
            Planet,
            Alliance,
            User,
            DebrisField,
            CombatReport,
            EspionageReport,
            Research,
        )

        db.session.query(TickLog).delete()
        db.session.query(CombatReport).delete()
        db.session.query(DebrisField).delete()
        db.session.query(EspionageReport).delete()
        db.session.query(Fleet).delete()
        db.session.query(Planet).delete()
        db.session.query(Alliance).delete()
        db.session.query(Research).delete()
        db.session.query(User).delete()
        db.session.commit()

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        alpha = User(username="alpha", email="alpha@example.com", password_hash=pw_hash, created_at=now, last_login=now)
        beta = User(username="beta", email="beta@example.com", password_hash=pw_hash, created_at=now, last_login=now)
        pirates_pw_hash = bcrypt.hashpw("pirates".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        pirates = User(username="pirates", email="pirates@example.com", password_hash=pirates_pw_hash, created_at=now, last_login=now)

        db.session.add_all([alpha, beta, pirates])
        db.session.flush()

        # Two home planets near each other + one pirate camp nearby.
        alpha_home = Planet(
            name="Alpha Prime",
            x=1000,
            y=1000,
            z=1000,
            user_id=alpha.id,
            is_home_planet=True,
            metal=200_000,
            crystal=150_000,
            deuterium=75_000,
            metal_mine=10,
            crystal_mine=8,
            deuterium_synthesizer=5,
            solar_plant=15,
        )
        beta_home = Planet(
            name="Beta Prime",
            x=1120,
            y=1020,
            z=1005,
            user_id=beta.id,
            is_home_planet=True,
            metal=200_000,
            crystal=150_000,
            deuterium=75_000,
            metal_mine=10,
            crystal_mine=8,
            deuterium_synthesizer=5,
            solar_plant=15,
        )
        pirate_camp = Planet(
            name="Pirate Camp Near Alpha",
            x=1060,
            y=980,
            z=995,
            user_id=pirates.id,
            is_home_planet=False,
            metal=50_000,
            crystal=25_000,
            deuterium=10_000,
            metal_mine=0,
            crystal_mine=0,
            deuterium_synthesizer=0,
            solar_plant=0,
        )

        db.session.add_all([alpha_home, beta_home, pirate_camp])
        db.session.flush()

        # Research baseline (so colonization can be tested later).
        db.session.add_all([
            Research(user_id=alpha.id, colonization_tech=10, astrophysics=0, interstellar_communication=0, research_points=0),
            Research(user_id=beta.id, colonization_tech=10, astrophysics=0, interstellar_communication=0, research_points=0),
        ])

        # Initial fleets for alpha/beta (stationed) and pirate defense.
        alpha_fleet = Fleet(
            user_id=alpha.id,
            mission="stationed",
            status="stationed",
            start_planet_id=alpha_home.id,
            target_planet_id=alpha_home.id,
            departure_time=now,
            arrival_time=now,
            eta=0,
            small_cargo=10,
            large_cargo=5,
            light_fighter=80,
            heavy_fighter=40,
            cruiser=10,
            battleship=5,
            recycler=5,
            espionage_probe=10,
            colony_ship=2,
        )
        beta_fleet = Fleet(
            user_id=beta.id,
            mission="stationed",
            status="stationed",
            start_planet_id=beta_home.id,
            target_planet_id=beta_home.id,
            departure_time=now,
            arrival_time=now,
            eta=0,
            small_cargo=10,
            large_cargo=5,
            light_fighter=80,
            heavy_fighter=40,
            cruiser=10,
            battleship=5,
            recycler=5,
            espionage_probe=10,
            colony_ship=2,
        )
        pirate_defense = Fleet(
            user_id=pirates.id,
            mission="defend",
            status="stationed",
            start_planet_id=pirate_camp.id,
            target_planet_id=pirate_camp.id,
            departure_time=now,
            arrival_time=now,
            eta=0,
            light_fighter=120,
            heavy_fighter=60,
            cruiser=15,
            battleship=5,
        )

        db.session.add_all([alpha_fleet, beta_fleet, pirate_defense])
        db.session.commit()

        return jsonify({
            "message": "two-player scenario reset",
            "password": password,
            "users": {
                "alpha": {"id": alpha.id, "username": alpha.username},
                "beta": {"id": beta.id, "username": beta.username},
                "pirates": {"id": pirates.id, "username": pirates.username},
            },
            "planets": {
                "alpha_home": {"id": alpha_home.id, "name": alpha_home.name, "coords": f"{alpha_home.x}:{alpha_home.y}:{alpha_home.z}"},
                "beta_home": {"id": beta_home.id, "name": beta_home.name, "coords": f"{beta_home.x}:{beta_home.y}:{beta_home.z}"},
                "pirate_camp": {"id": pirate_camp.id, "name": pirate_camp.name, "coords": f"{pirate_camp.x}:{pirate_camp.y}:{pirate_camp.z}"},
            },
            "fleets": {
                "alpha_fleet_id": alpha_fleet.id,
                "beta_fleet_id": beta_fleet.id,
                "pirate_defense_fleet_id": pirate_defense.id,
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/fleet-health', methods=['GET'])
@jwt_required()
def get_fleet_health():
    """Get comprehensive fleet health report"""
    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        health_report = FleetTravelGuard.get_fleet_health_report()
        return jsonify(health_report), 200
    except Exception as e:
        return jsonify({'error': f'Failed to generate health report: {str(e)}'}), 500

@admin_bp.route('/fleet/cleanup', methods=['POST'])
@jwt_required()
def cleanup_stuck_fleets():
    """Administrative endpoint to force cleanup stuck fleets"""
    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        # Get parameters
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)  # Default 24 hours
        target_user_id = data.get('user_id')  # Optional: cleanup specific user

        # Run cleanup
        cleaned_count = FleetTravelGuard.force_cleanup_stuck_fleets(
            user_id=target_user_id,
            max_age_hours=max_age_hours
        )

        return jsonify({
            'message': f'Successfully cleaned up {cleaned_count} stuck fleets',
            'cleaned_count': cleaned_count,
            'max_age_hours': max_age_hours,
            'target_user_id': target_user_id
        }), 200

    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@admin_bp.route('/fleet/validate-coordinates', methods=['POST'])
@jwt_required()
def validate_fleet_coordinates():
    """Validate and fix fleet coordinate issues"""
    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        issues_found = FleetTravelGuard.validate_fleet_coordinates()

        return jsonify({
            'message': f'Validated fleet coordinates, fixed {issues_found} issues',
            'issues_fixed': issues_found
        }), 200

    except Exception as e:
        return jsonify({'error': f'Coordinate validation failed: {str(e)}'}), 500

@admin_bp.route('/system-status', methods=['GET'])
@jwt_required()
def get_system_status():
    """Get overall system status and statistics"""
    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        from backend.services.tick import get_tick_statistics
        from backend.models import Planet, Fleet, User, Alliance

        # Get basic counts
        system_stats = {
            'users': User.query.count(),
            'planets': Planet.query.count(),
            'fleets': Fleet.query.count(),
            'alliances': Alliance.query.count(),
            'timestamp': db.func.now()
        }

        # Get fleet health
        fleet_health = FleetTravelGuard.get_fleet_health_report()

        # Get tick statistics
        tick_stats = get_tick_statistics()

        return jsonify({
            'system_stats': system_stats,
            'fleet_health': fleet_health,
            'tick_stats': tick_stats
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get system status: {str(e)}'}), 500

@admin_bp.route('/fleet/<int:fleet_id>/fix', methods=['POST'])
@jwt_required()
def fix_specific_fleet(fleet_id):
    """Fix a specific stuck fleet"""
    user_id = int(get_jwt_identity())

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        from backend.models import Fleet

        fleet = Fleet.query.get(fleet_id)
        if not fleet:
            return jsonify({'error': 'Fleet not found'}), 404

        # Try to fix the fleet
        from backend.services.fleet_travel_guard import FleetTravelGuard
        current_time = db.func.now()

        if FleetTravelGuard._correct_fleet_state(fleet, current_time):
            db.session.commit()
            return jsonify({
                'message': f'Fleet {fleet_id} fixed successfully',
                'fleet_id': fleet_id,
                'new_status': fleet.status,
                'new_eta': fleet.eta
            }), 200
        else:
            return jsonify({
                'message': f'Fleet {fleet_id} was already in correct state',
                'fleet_id': fleet_id,
                'status': fleet.status,
                'eta': fleet.eta
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to fix fleet: {str(e)}'}), 500
