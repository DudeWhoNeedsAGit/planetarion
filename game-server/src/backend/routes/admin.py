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


def _require_admin_or_dev_token_readonly() -> tuple[bool, tuple[dict, int] | None]:
    """Allow dev token in dev/test, admin JWT everywhere."""
    if _is_dev_or_test_env() and _has_dev_admin_token():
        return True, None

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

def _normalize_scenario_id(raw: str | None) -> str:
    value = (raw or "").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "two-player": "two-player",
        "baseline": "two-player",
        "pirate-pressure": "pirate-pressure",
        "debris-rich": "debris-rich",
        "colonization-race": "colonization-race",
        "returning-fleets-stress": "returning-fleets-stress",
    }
    return aliases.get(value, "")

def _available_scenario_packs() -> list[dict]:
    return [
        {"id": "two-player", "name": "Two Player Baseline"},
        {"id": "pirate-pressure", "name": "Pirate Pressure"},
        {"id": "debris-rich", "name": "Debris Rich"},
        {"id": "colonization-race", "name": "Colonization Race"},
        {"id": "returning-fleets-stress", "name": "Returning Fleets Stress"},
    ]

def _clear_world_state() -> None:
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
        CommanderXPEvent,
        ChatMessage,
        PlanetRenameLog,
        PirateAIState,
    )

    db.session.query(TickLog).delete()
    db.session.query(CombatReport).delete()
    db.session.query(DebrisField).delete()
    db.session.query(EspionageReport).delete()
    db.session.query(CommanderXPEvent).delete()
    db.session.query(ChatMessage).delete()
    db.session.query(PlanetRenameLog).delete()
    db.session.query(Fleet).delete()
    db.session.query(Planet).delete()
    db.session.query(PirateAIState).delete()
    db.session.query(Alliance).delete()
    db.session.query(Research).delete()
    db.session.query(User).delete()
    db.session.commit()

def _create_two_player_foundation(password: str, now: datetime) -> dict:
    from backend.models import User, Planet, Fleet, Research

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    alpha = User(username="alpha", email="alpha@example.com", password_hash=pw_hash, created_at=now, last_login=now)
    beta = User(username="beta", email="beta@example.com", password_hash=pw_hash, created_at=now, last_login=now)
    pirates_pw_hash = bcrypt.hashpw("pirates".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    pirates = User(username="pirates", email="pirates@example.com", password_hash=pirates_pw_hash, created_at=now, last_login=now)

    db.session.add_all([alpha, beta, pirates])
    db.session.flush()

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
        z=1000,
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
        z=1000,
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

    db.session.add_all([
        Research(user_id=alpha.id, colonization_tech=10, astrophysics=0, interstellar_communication=0, research_points=0),
        Research(user_id=beta.id, colonization_tech=10, astrophysics=0, interstellar_communication=0, research_points=0),
    ])

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
    pirate_defense_fleet = Fleet(
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

    db.session.add_all([alpha_fleet, beta_fleet, pirate_defense_fleet])
    db.session.flush()

    return {
        "users": {"alpha": alpha, "beta": beta, "pirates": pirates},
        "planets": {"alpha_home": alpha_home, "beta_home": beta_home, "pirate_camp": pirate_camp},
        "fleets": {
            "alpha_fleet": alpha_fleet,
            "beta_fleet": beta_fleet,
            "pirate_defense_fleet": pirate_defense_fleet,
        },
        "debris_fields": {},
    }

def _apply_scenario_pack(scenario_id: str, foundation: dict, now: datetime) -> None:
    from backend.models import Planet, Fleet, DebrisField, Research

    users = foundation["users"]
    planets = foundation["planets"]
    fleets = foundation["fleets"]
    debris_fields = foundation["debris_fields"]

    if scenario_id == "pirate-pressure":
        pirate_camp_beta = Planet(
            name="Pirate Camp Near Beta",
            x=1160,
            y=1060,
            z=1000,
            user_id=users["pirates"].id,
            is_home_planet=False,
            metal=60_000,
            crystal=30_000,
            deuterium=12_000,
        )
        db.session.add(pirate_camp_beta)
        db.session.flush()

        pirate_raider = Fleet(
            user_id=users["pirates"].id,
            mission="attack",
            status="traveling",
            start_planet_id=pirate_camp_beta.id,
            target_planet_id=planets["alpha_home"].id,
            departure_time=now,
            arrival_time=now,
            eta=90,
            light_fighter=180,
            heavy_fighter=90,
            cruiser=24,
            battleship=8,
        )
        fleets["pirate_defense_fleet"].light_fighter = 260
        fleets["pirate_defense_fleet"].heavy_fighter = 140
        fleets["pirate_defense_fleet"].cruiser = 36
        fleets["pirate_defense_fleet"].battleship = 12
        db.session.add(pirate_raider)
        db.session.flush()

        planets["pirate_camp_beta"] = pirate_camp_beta
        fleets["pirate_raider_fleet"] = pirate_raider

    elif scenario_id == "debris-rich":
        debris_alpha_lane = DebrisField(
            planet_id=planets["pirate_camp"].id,
            metal=200_000,
            crystal=120_000,
            deuterium=30_000,
            created_at=now,
        )
        debris_beta_lane = DebrisField(
            planet_id=planets["beta_home"].id,
            metal=140_000,
            crystal=110_000,
            deuterium=20_000,
            created_at=now,
        )
        db.session.add_all([debris_alpha_lane, debris_beta_lane])
        db.session.flush()
        debris_fields["pirate_lane_debris"] = debris_alpha_lane
        debris_fields["beta_lane_debris"] = debris_beta_lane

        fleets["alpha_fleet"].recycler = 20
        fleets["beta_fleet"].recycler = 20

    elif scenario_id == "colonization-race":
        neutral_one = Planet(
            name="Frontier Verge I",
            x=1080,
            y=1005,
            z=1000,
            user_id=None,
            colonization_difficulty=1,
            metal=8_000,
            crystal=5_000,
            deuterium=2_000,
        )
        neutral_two = Planet(
            name="Frontier Verge II",
            x=1090,
            y=1035,
            z=1000,
            user_id=None,
            colonization_difficulty=1,
            metal=8_000,
            crystal=5_000,
            deuterium=2_000,
        )
        db.session.add_all([neutral_one, neutral_two])
        db.session.flush()
        planets["neutral_frontier_one"] = neutral_one
        planets["neutral_frontier_two"] = neutral_two

        fleets["alpha_fleet"].colony_ship = 8
        fleets["beta_fleet"].colony_ship = 8

        alpha_research = Research.query.filter_by(user_id=users["alpha"].id).first()
        beta_research = Research.query.filter_by(user_id=users["beta"].id).first()
        if alpha_research:
            alpha_research.colonization_tech = max(int(alpha_research.colonization_tech or 0), 12)
        if beta_research:
            beta_research.colonization_tech = max(int(beta_research.colonization_tech or 0), 12)

    elif scenario_id == "returning-fleets-stress":
        alpha_returning = Fleet(
            user_id=users["alpha"].id,
            mission="attack",
            status="returning",
            start_planet_id=planets["alpha_home"].id,
            target_planet_id=planets["beta_home"].id,
            departure_time=now,
            arrival_time=now,
            eta=45,
            light_fighter=24,
            heavy_fighter=12,
        )
        alpha_traveling = Fleet(
            user_id=users["alpha"].id,
            mission="espionage",
            status="traveling",
            start_planet_id=planets["alpha_home"].id,
            target_planet_id=planets["pirate_camp"].id,
            departure_time=now,
            arrival_time=now,
            eta=30,
            espionage_probe=16,
        )
        beta_returning = Fleet(
            user_id=users["beta"].id,
            mission="transport",
            status="returning",
            start_planet_id=planets["beta_home"].id,
            target_planet_id=planets["alpha_home"].id,
            departure_time=now,
            arrival_time=now,
            eta=60,
            small_cargo=12,
            large_cargo=4,
            cargo_metal=5_000,
        )
        pirate_returning = Fleet(
            user_id=users["pirates"].id,
            mission="attack",
            status="returning",
            start_planet_id=planets["pirate_camp"].id,
            target_planet_id=planets["alpha_home"].id,
            departure_time=now,
            arrival_time=now,
            eta=75,
            light_fighter=30,
            heavy_fighter=16,
        )
        db.session.add_all([alpha_returning, alpha_traveling, beta_returning, pirate_returning])
        db.session.flush()
        fleets["alpha_returning_attack_fleet"] = alpha_returning
        fleets["alpha_traveling_spy_fleet"] = alpha_traveling
        fleets["beta_returning_transport_fleet"] = beta_returning
        fleets["pirate_returning_raid_fleet"] = pirate_returning

def _serialize_scenario_response(
    *,
    scenario_id: str,
    password: str,
    foundation: dict,
    write_snapshot_requested: bool,
) -> dict:
    users = foundation["users"]
    planets = foundation["planets"]
    fleets = foundation["fleets"]
    debris_fields = foundation["debris_fields"]

    user_key_by_id = {user.id: key for key, user in users.items()}
    planet_key_by_id = {planet.id: key for key, planet in planets.items()}

    users_list = []
    for key, user in sorted(users.items(), key=lambda item: item[0]):
        users_list.append({"key": key, "id": user.id, "username": user.username})

    planets_list = []
    for key, planet in sorted(planets.items(), key=lambda item: item[0]):
        planets_list.append({
            "key": key,
            "id": planet.id,
            "name": planet.name,
            "owner_key": user_key_by_id.get(planet.user_id),
            "coords": f"{planet.x}:{planet.y}:{planet.z}",
        })

    fleets_list = []
    for key, fleet in sorted(fleets.items(), key=lambda item: item[0]):
        fleets_list.append({
            "key": key,
            "id": fleet.id,
            "owner_key": user_key_by_id.get(fleet.user_id),
            "mission": fleet.mission,
            "status": fleet.status,
            "eta": int(fleet.eta or 0),
            "start_planet_key": planet_key_by_id.get(fleet.start_planet_id),
            "target_planet_key": planet_key_by_id.get(fleet.target_planet_id),
        })

    debris_list = []
    for key, debris in sorted(debris_fields.items(), key=lambda item: item[0]):
        debris_list.append({
            "key": key,
            "id": debris.id,
            "planet_key": planet_key_by_id.get(debris.planet_id),
            "metal": int(debris.metal or 0),
            "crystal": int(debris.crystal or 0),
            "deuterium": int(debris.deuterium or 0),
        })

    scenario_name = next((p["name"] for p in _available_scenario_packs() if p["id"] == scenario_id), scenario_id)
    return {
        "ok": True,
        "contract_version": "scenario-pack.v1",
        "message": f"{scenario_name} scenario reset",
        "scenario": {
            "id": scenario_id,
            "name": scenario_name,
            "deterministic": True,
        },
        "credentials": {
            "password": password,
        },
        "snapshot": {
            "write_requested": bool(write_snapshot_requested),
            "written": False,
        },
        "entities": {
            "users": users_list,
            "planets": planets_list,
            "fleets": fleets_list,
            "debris_fields": debris_list,
        },
        "counts": {
            "users": len(users_list),
            "planets": len(planets_list),
            "fleets": len(fleets_list),
            "debris_fields": len(debris_list),
        },
        # Backward-compatible maps used by existing tests/harnesses.
        "users": {key: {"id": user.id, "username": user.username} for key, user in users.items()},
        "planets": {key: {"id": planet.id, "name": planet.name, "coords": f"{planet.x}:{planet.y}:{planet.z}"} for key, planet in planets.items()},
        "fleets": {f"{key}_id": fleet.id for key, fleet in fleets.items()},
    }

def _reset_named_scenario_pack(*, scenario_id: str, password: str, write_snapshot: bool) -> tuple[dict, int]:
    now = datetime.utcnow().replace(microsecond=0)
    _clear_world_state()
    foundation = _create_two_player_foundation(password=password, now=now)
    _apply_scenario_pack(scenario_id=scenario_id, foundation=foundation, now=now)
    db.session.commit()
    payload = _serialize_scenario_response(
        scenario_id=scenario_id,
        password=password,
        foundation=foundation,
        write_snapshot_requested=write_snapshot,
    )
    return payload, 200


@admin_bp.route("/research/seed-points", methods=["POST"])
def seed_research_points():
    """Seed research points for a user (dev/test only).

    Useful for fast E2E flows where RP would otherwise require many ticks.
    """
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    points = payload.get("research_points", payload.get("points", 0))
    try:
        points = int(points)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid points"}), 400

    from backend.models import Research

    if username:
        user = User.query.filter_by(username=username).first()
    else:
        identity = get_jwt_identity()
        try:
            user_id = int(identity) if identity is not None else None
        except (TypeError, ValueError):
            user_id = None
        user = User.query.get(user_id) if user_id else None

    if not user:
        return jsonify({"error": "User not found"}), 404

    research = Research.query.filter_by(user_id=user.id).first()
    if not research:
        research = Research(user_id=user.id, research_points=0)
        db.session.add(research)
        db.session.flush()

    research.research_points = max(0, points)
    if hasattr(research, "research_points_fraction"):
        research.research_points_fraction = 0.0
    db.session.commit()

    return jsonify({"message": "Seeded research points", "user_id": user.id, "research_points": int(research.research_points or 0)}), 200

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

        # After restoring the raw sqlite file, re-ensure schema so newly added columns/tables exist.
        try:
            with current_app.app_context():
                db.create_all()
                from backend.services.sqlite_schema import (
                    ensure_planet_storage_columns,
                    ensure_planet_trait_columns,
                    ensure_fleet_cargo_columns,
                    ensure_user_lifecycle_columns,
                    ensure_user_research_queue_columns,
                    ensure_research_fraction_columns,
                    ensure_research_tech_columns,
                    ensure_commander_xp_event_table,
                    ensure_pirate_ai_state_table,
                    ensure_pirate_ai_config_overrides_table,
                    ensure_pirate_faction_state_table,
                )
                ensure_planet_storage_columns(db.engine)
                ensure_planet_trait_columns(db.engine)
                ensure_fleet_cargo_columns(db.engine)
                ensure_user_lifecycle_columns(db.engine)
                ensure_user_research_queue_columns(db.engine)
                ensure_research_fraction_columns(db.engine)
                ensure_research_tech_columns(db.engine)
                ensure_commander_xp_event_table(db.engine)
                ensure_pirate_ai_state_table(db.engine)
                ensure_pirate_ai_config_overrides_table(db.engine)
                ensure_pirate_faction_state_table(db.engine)
                from backend.services.pirate_ai import PirateAILiveOps
                PirateAILiveOps.apply_persisted_overrides()
        except Exception:
            # Non-fatal: restore should still succeed even if schema ensure fails.
            pass

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
    """Backwards-compatible wrapper for the named scenario-pack reset flow."""
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password") or "testpassword123")
    write_snapshot = bool(payload.get("write_snapshot", False))
    try:
        response, code = _reset_named_scenario_pack(
            scenario_id="two-player",
            password=password,
            write_snapshot=write_snapshot,
        )
        return jsonify(response), code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/scenarios/packs", methods=["GET"])
def list_scenario_packs():
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code
    return jsonify({
        "ok": True,
        "contract_version": "scenario-pack.v1",
        "scenarios": _available_scenario_packs(),
    }), 200

@admin_bp.route("/scenarios/reset", methods=["POST"])
@admin_bp.route("/scenarios/<string:scenario_name>/reset", methods=["POST"])
def reset_named_scenario_pack(scenario_name: str | None = None):
    allowed, err = _require_admin_or_dev_token()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    payload = request.get_json(silent=True) or {}
    requested = scenario_name or payload.get("scenario") or "two-player"
    normalized = _normalize_scenario_id(str(requested))
    if not normalized:
        return jsonify({
            "error": "Unknown scenario pack",
            "requested": requested,
            "available": [item["id"] for item in _available_scenario_packs()],
        }), 400

    password = str(payload.get("password") or "testpassword123")
    write_snapshot = bool(payload.get("write_snapshot", False))
    try:
        response, code = _reset_named_scenario_pack(
            scenario_id=normalized,
            password=password,
            write_snapshot=write_snapshot,
        )
        return jsonify(response), code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/pirate-ai/status", methods=["GET"])
def get_pirate_ai_status():
    allowed, err = _require_admin_or_dev_token_readonly()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    from backend.services.pirate_ai import PirateAILiveOps

    try:
        summary = PirateAILiveOps.build_status_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": f"Failed to build pirate ai status: {str(e)}"}), 500


@admin_bp.route("/pirate-ai/config", methods=["GET"])
def get_pirate_ai_config():
    allowed, err = _require_admin_or_dev_token_readonly()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    from backend.services.pirate_ai import PirateAILiveOps

    return jsonify({
        "allowlist": PirateAILiveOps.CONFIG_SPECS,
        "effective": PirateAILiveOps.get_effective_config(),
    }), 200


@admin_bp.route("/pirate-ai/config", methods=["POST"])
def set_pirate_ai_config():
    allowed, err = _require_admin_or_dev_token_readonly()
    if not allowed:
        payload, code = err
        return jsonify(payload), code

    if not _is_dev_or_test_env():
        return jsonify({"error": "Config mutation not allowed outside development/testing"}), 403

    payload = request.get_json(silent=True) or {}
    updates = payload.get("updates")
    if not isinstance(updates, dict) or not updates:
        return jsonify({"error": "Expected non-empty object at 'updates'"}), 400

    from backend.services.pirate_ai import PirateAILiveOps

    try:
        applied, errors = PirateAILiveOps.set_overrides(updates)
        status = 200 if applied and not errors else 400
        return jsonify({
            "applied": applied,
            "errors": errors,
            "effective": PirateAILiveOps.get_effective_config(),
        }), status
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to apply pirate ai config: {str(e)}"}), 500

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
