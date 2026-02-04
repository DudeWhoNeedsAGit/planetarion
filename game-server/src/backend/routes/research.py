"""
Research Management Routes (MVP)

Implements:
- Research point balance (stored on Research.research_points)
- One active research project per user (stored as JSON on User.research_queue)
- Start / cancel research
- Tick-driven completion (see backend/services/tick.py)

Notes:
- Research points are accrued during ticks for determinism.
- GET endpoints return computed RP rates (per hour / per tick) for UI display.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.database import db
from backend.models import User, Research, Planet, TickLog

research_bp = Blueprint('research', __name__, url_prefix='/api/research')


RESEARCH_KEYS = ('colonization_tech', 'astrophysics', 'interstellar_communication')


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso_z(raw: str | None) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _get_or_create_research(user_id: int) -> Research:
    research = Research.query.filter_by(user_id=user_id).first()
    if not research:
        research = Research(user_id=user_id, research_points=0)
        db.session.add(research)
        db.session.commit()
    return research


def _energy_ratio(planet: Planet) -> float:
    energy_production = (planet.solar_plant or 0) * 20 + (planet.fusion_reactor or 0) * 50
    energy_consumption = (
        (planet.metal_mine or 0) * 10
        + (planet.crystal_mine or 0) * 10
        + (planet.deuterium_synthesizer or 0) * 20
        + (getattr(planet, "research_lab", 0) or 0) * 15
    )
    if energy_consumption <= 0:
        return 1.0
    return max(0.0, min(1.0, energy_production / energy_consumption))


def calculate_rp_rates(user_id: int) -> dict:
    planets = Planet.query.filter_by(user_id=user_id).all()
    per_level = int(current_app.config.get("RESEARCH_RP_PER_HOUR_PER_LAB_LEVEL", 10) or 10)

    rp_per_hour = 0.0
    for p in planets:
        lvl = int(getattr(p, "research_lab", 0) or 0)
        if lvl <= 0:
            continue
        rp_per_hour += float(lvl * per_level) * _energy_ratio(p)

    # This project uses an accelerated tick time scale (resources divide by 72).
    rp_per_tick = rp_per_hour / 72.0
    return {"rp_per_hour": rp_per_hour, "rp_per_tick": rp_per_tick}


def calculate_research_cost(key: str, target_level: int) -> int:
    if target_level <= 0:
        return 0

    # Legacy formula (covered by existing unit tests):
    #   cost = base * (level ** 1.5)
    base_costs = {
        "colonization_tech": 100,
        "astrophysics": 150,
        "interstellar_communication": 200,
    }
    base = int(base_costs.get(key, 100))
    cost = int(base * (float(target_level) ** 1.5))
    return max(0, int(cost))


def calculate_research_points(user_id: int) -> int:
    """Legacy helper used by unit tests.

    Returns the user's *per-hour* research point generation based on all owned
    planets and their research lab level, scaled by energy efficiency.
    """
    rates = calculate_rp_rates(int(user_id))
    return int(rates.get("rp_per_hour") or 0)


def calculate_research_duration_seconds(key: str, target_level: int) -> int:
    per_level = int(current_app.config.get("RESEARCH_DURATION_SECONDS_PER_LEVEL", 60) or 60)
    return max(0, int(per_level * max(1, target_level)))


def _get_home_planet_id(user_id: int) -> int | None:
    home = Planet.query.filter_by(user_id=user_id).order_by(Planet.is_home_planet.desc(), Planet.id.asc()).first()
    return home.id if home else None


def _load_queue(user: User) -> dict | None:
    raw = getattr(user, "research_queue", None)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _save_queue(user: User, payload: dict | None) -> None:
    user.research_queue = json.dumps(payload) if payload else None


def _serialize_queue(queue: dict | None) -> dict | None:
    if not queue:
        return None
    return {
        "key": queue.get("key"),
        "target_level": queue.get("target_level"),
        "started_at": queue.get("started_at"),
        "completes_at": queue.get("completes_at"),
    }


@research_bp.route("", methods=["GET"])
@jwt_required()
def get_research():
    user_id = int(get_jwt_identity())
    _ = User.query.get_or_404(user_id)
    research = _get_or_create_research(user_id)

    levels = {k: int(getattr(research, k) or 0) for k in RESEARCH_KEYS}
    costs = {k: calculate_research_cost(k, levels[k] + 1) for k in RESEARCH_KEYS}
    durations = {k: calculate_research_duration_seconds(k, levels[k] + 1) for k in RESEARCH_KEYS}
    rates = calculate_rp_rates(user_id)

    user = User.query.get(user_id)
    queue = _serialize_queue(_load_queue(user)) if user else None

    # Backward-compatible response keys:
    return jsonify(
        {
            "research_points": int(research.research_points or 0),
            "levels": levels,
            "next_level_costs": costs,
            "next_level_durations_seconds": durations,
            "rates": rates,
            "queue": queue,
        }
    )


@research_bp.route("/points", methods=["GET"])
@jwt_required()
def get_research_points():
    user_id = int(get_jwt_identity())
    research = _get_or_create_research(user_id)
    return jsonify(
        {
            "research_points": int(research.research_points or 0),
            "last_updated": _to_iso_z(_utcnow()),
        }
    )


@research_bp.route("/start", methods=["POST"])
@jwt_required()
def start_research():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    research = _get_or_create_research(user_id)

    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    if key not in RESEARCH_KEYS:
        return jsonify({"error": "Invalid research key"}), 400

    if _load_queue(user):
        return jsonify({"error": "Research already in progress"}), 400

    current_level = int(getattr(research, key) or 0)
    target_level = current_level + 1
    cost = calculate_research_cost(key, target_level)
    if int(research.research_points or 0) < cost:
        return jsonify({"error": "Insufficient research points", "required": cost, "available": int(research.research_points or 0)}), 400

    research.research_points = int(research.research_points or 0) - cost

    now = _utcnow()
    duration = calculate_research_duration_seconds(key, target_level)
    completes_at = now + timedelta(seconds=duration)

    queue = {
        "key": key,
        "target_level": target_level,
        "started_at": _to_iso_z(now),
        "completes_at": _to_iso_z(completes_at),
    }
    _save_queue(user, queue)

    planet_id = _get_home_planet_id(user_id)
    db.session.add(
        TickLog(
            tick_number=0,
            planet_id=planet_id,
            event_type="research_start",
            event_description=f"Research started: {key} → Level {target_level} (cost {cost} RP)",
            timestamp=datetime.utcnow(),
        )
    )

    db.session.commit()

    return jsonify(
        {
            "message": "Research started",
            "queue": _serialize_queue(queue),
            "research_points_remaining": int(research.research_points or 0),
        }
    )


@research_bp.route("/cancel", methods=["POST"])
@jwt_required()
def cancel_research():
    """Cancel the active research project (MVP: 100% RP refund)."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    research = _get_or_create_research(user_id)

    queue = _load_queue(user)
    if not queue:
        return jsonify({"error": "No research in progress"}), 400

    key = queue.get("key")
    target_level = int(queue.get("target_level") or 0)
    refund = calculate_research_cost(str(key), target_level) if key in RESEARCH_KEYS else 0
    research.research_points = int(research.research_points or 0) + int(refund)
    _save_queue(user, None)

    planet_id = _get_home_planet_id(user_id)
    db.session.add(
        TickLog(
            tick_number=0,
            planet_id=planet_id,
            event_type="research_cancel",
            event_description=f"Research cancelled: {key} → Level {target_level} (refund {refund} RP)",
            timestamp=datetime.utcnow(),
        )
    )

    db.session.commit()

    return jsonify({"message": "Research cancelled", "refund": int(refund), "research_points": int(research.research_points or 0)})


@research_bp.route("/upgrade/<research_type>", methods=["POST"])
@jwt_required()
def upgrade_research_legacy(research_type: str):
    """Legacy endpoint: upgrade immediately (kept for older tests)."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    research = _get_or_create_research(user_id)

    if research_type not in RESEARCH_KEYS:
        return jsonify({"error": "Invalid research type"}), 400

    if _load_queue(user):
        return jsonify({"error": "Research already in progress"}), 400

    current_level = int(getattr(research, research_type) or 0)
    target_level = current_level + 1
    cost = calculate_research_cost(research_type, target_level)
    if int(research.research_points or 0) < cost:
        return jsonify({"error": "Insufficient research points", "required": cost, "available": int(research.research_points or 0)}), 400

    research.research_points = int(research.research_points or 0) - cost
    setattr(research, research_type, target_level)

    planet_id = _get_home_planet_id(user_id)
    db.session.add(
        TickLog(
            tick_number=0,
            planet_id=planet_id,
            event_type="research_complete",
            event_description=f"Research completed: {research_type} → Level {target_level}",
            timestamp=datetime.utcnow(),
        )
    )

    db.session.commit()

    return jsonify(
        {
            "message": f"{research_type} upgraded to level {target_level}",
            "new_level": target_level,
            "research_points_remaining": int(research.research_points or 0),
            "next_upgrade_cost": calculate_research_cost(research_type, target_level + 1),
        }
    )


def get_research_info(research_type):
    """Get information about a research technology"""
    research_info = {
        "colonization_tech": {
            "name": "Colonization Technology",
            "description": "Allows colonization of planets with higher difficulty ratings",
            "benefits": [
                "Unlocks colonization of planets with difficulty up to your research level",
                "Reduces colonization failure chance",
                "Enables faster colony establishment",
            ],
            "max_level": 10,
        },
        "astrophysics": {
            "name": "Astrophysics",
            "description": "Advances understanding of space travel and colonization",
            "benefits": [
                "Reduces fleet travel time",
                "Improves exploration efficiency",
            ],
            "max_level": 15,
        },
        "interstellar_communication": {
            "name": "Interstellar Communication",
            "description": "Enhances communication across vast distances",
            "benefits": [
                "Increases galaxy visibility range",
                "Improves fleet coordination",
            ],
            "max_level": 12,
        },
    }

    return research_info.get(
        research_type,
        {
            "name": "Unknown Research",
            "description": "Research information not available",
            "benefits": [],
            "max_level": 10,
        },
    )


@research_bp.route("/info/<research_type>", methods=["GET"])
@jwt_required()
def get_research_details(research_type):
    info = get_research_info(research_type)
    return jsonify(info)
