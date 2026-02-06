"""Idle catch-up (offline progression) service.

Design goal (MVP):
- Do NOT replay ticks.
- Instead, award resource and research point gains using a formula based on elapsed time.
- Optionally process "arrived" fleets for this user (single pass).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import current_app

from backend.config import get_planet_storage_caps
from backend.database import db
from backend.models import Planet, Research, TickLog, User
from backend.services.commander_xp import CommanderXPService
from backend.services.fleet_arrival import FleetArrivalService
from backend.services.research_defs import RESEARCH_DEF_BY_KEY
from backend.services.tick import calculate_production_rate


@dataclass
class IdleCatchupResult:
    since: datetime
    until: datetime
    duration_seconds: int
    resources: dict[str, int]
    research_points: int
    events: dict[str, int]


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


def _get_or_create_research(user_id: int) -> Research:
    r = Research.query.filter_by(user_id=user_id).first()
    if not r:
        r = Research(user_id=user_id, research_points=0)
        db.session.add(r)
        db.session.flush()
    return r


def _complete_research_queue_if_due(user: User, now: datetime) -> int:
    """Complete at most one queued research for this user if due. Returns count completed."""
    raw = getattr(user, "research_queue", None)
    if not raw:
        return 0
    try:
        import json

        queue = json.loads(raw)
    except Exception:
        user.research_queue = None
        return 0
    if not isinstance(queue, dict):
        user.research_queue = None
        return 0

    key = queue.get("key")
    target_level = int(queue.get("target_level") or 0)
    completes_at_raw = queue.get("completes_at")
    if not isinstance(completes_at_raw, str):
        return 0
    s = completes_at_raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        completes_at = datetime.fromisoformat(s)
    except Exception:
        return 0

    # Normalize to naive UTC for comparison against naive `now` (UTC).
    if completes_at.tzinfo is not None:
        from datetime import timezone

        completes_at = completes_at.astimezone(timezone.utc).replace(tzinfo=None)

    if completes_at > now:
        return 0

    if not key or key not in RESEARCH_DEF_BY_KEY:
        user.research_queue = None
        return 0

    research = _get_or_create_research(user.id)
    current_level = int(getattr(research, key) or 0)
    if target_level != current_level + 1:
        target_level = current_level + 1
    setattr(research, key, target_level)
    user.research_queue = None

    home = Planet.query.filter_by(user_id=user.id).order_by(Planet.is_home_planet.desc(), Planet.id.asc()).first()
    tick_log = TickLog(
        tick_number=0,
        planet_id=home.id if home else None,
        event_type="research_complete",
        event_description=f"Research completed: {key} → Level {target_level}",
        timestamp=datetime.utcnow(),
    )
    db.session.add(tick_log)
    # Commander XP (idempotent per TickLog row if possible).
    try:
        db.session.flush()
        CommanderXPService.award_xp(
            user_id=int(user.id),
            xp=50 + max(0, int(target_level) - 1) * 25,
            source_type="research_complete",
            source_id=str(getattr(tick_log, "id", None) or f"{key}:{target_level}"),
        )
    except Exception:
        pass
    return 1


def apply_idle_catchup(user_id: int, now: datetime | None = None) -> IdleCatchupResult | None:
    """Apply offline progression for a user and return a summary suitable for UI display."""
    user = User.query.get(user_id)
    if not user or user.username == "pirates":
        return None

    now = now or datetime.utcnow()
    since = getattr(user, "last_seen_at", None) or getattr(user, "last_login", None) or getattr(user, "created_at", None) or now
    if since is None:
        since = now

    # Guard against clock skew (future timestamps).
    if since > now:
        user.last_seen_at = now
        db.session.commit()
        return None

    raw_elapsed = int((now - since).total_seconds())
    # Noise threshold: don't spam tiny "idle gain" summaries.
    min_seconds = int(current_app.config.get("IDLE_CATCHUP_MIN_SECONDS", 120) or 120)
    if raw_elapsed < min_seconds:
        user.last_seen_at = now
        db.session.commit()
        return None

    # Cap catch-up window (4 weeks).
    cap_seconds = int(current_app.config.get("IDLE_CATCHUP_CAP_SECONDS", 60 * 60 * 24 * 7 * 4) or (60 * 60 * 24 * 7 * 4))
    elapsed_seconds = min(raw_elapsed, cap_seconds)
    effective_since = now - timedelta(seconds=elapsed_seconds)

    planets = Planet.query.filter_by(user_id=user_id).all()
    total_metal = total_crystal = total_deut = 0

    elapsed_hours = float(elapsed_seconds) / 3600.0
    for p in planets:
        caps = get_planet_storage_caps(p)
        ratio = _energy_ratio(p)

        metal_per_hour = float(calculate_production_rate(int(p.metal_mine or 0), "metal", p)) * ratio
        crystal_per_hour = float(calculate_production_rate(int(p.crystal_mine or 0), "crystal", p)) * ratio
        deut_per_hour = float(calculate_production_rate(int(p.deuterium_synthesizer or 0), "deuterium", p)) * ratio

        add_metal = int(metal_per_hour * elapsed_hours) if metal_per_hour > 0 else 0
        add_crystal = int(crystal_per_hour * elapsed_hours) if crystal_per_hour > 0 else 0
        add_deut = int(deut_per_hour * elapsed_hours) if deut_per_hour > 0 else 0

        before_m, before_c, before_d = int(p.metal or 0), int(p.crystal or 0), int(p.deuterium or 0)
        if before_m < caps["metal"] and add_metal > 0:
            p.metal = min(caps["metal"], before_m + add_metal)
        if before_c < caps["crystal"] and add_crystal > 0:
            p.crystal = min(caps["crystal"], before_c + add_crystal)
        if before_d < caps["deuterium"] and add_deut > 0:
            p.deuterium = min(caps["deuterium"], before_d + add_deut)

        total_metal += int(p.metal or 0) - before_m
        total_crystal += int(p.crystal or 0) - before_c
        total_deut += int(p.deuterium or 0) - before_d

    # Research point catch-up: award based on research labs and energy ratio (same as tick accrual).
    research = _get_or_create_research(user_id)
    raw_per_hour_per_level = current_app.config.get("RESEARCH_RP_PER_HOUR_PER_LAB_LEVEL", 10)
    try:
        per_hour_per_level = int(raw_per_hour_per_level) if raw_per_hour_per_level is not None else 10
    except (TypeError, ValueError):
        per_hour_per_level = 10

    rp_per_hour = 0.0
    for p in planets:
        lvl = int(getattr(p, "research_lab", 0) or 0)
        if lvl <= 0:
            continue
        rp_per_hour += float(lvl * per_hour_per_level) * _energy_ratio(p)

    rp_gain = int(rp_per_hour * elapsed_hours) if rp_per_hour > 0 else 0
    before_rp = int(research.research_points or 0)
    if rp_gain > 0:
        research.research_points = before_rp + rp_gain

    # Process arrived fleets for this user only (single pass, no tick replay).
    # Count arrived fleets for this user before processing; used for summary only.
    from backend.models import Fleet

    before_arrived = Fleet.query.filter(
        Fleet.user_id == int(user_id),
        Fleet.arrival_time <= now,
        (
            Fleet.status.in_(["traveling", "returning", "defending"])
            | Fleet.status.like("exploring:%")
            | Fleet.status.like("colonizing:%")
        ),
    ).count()
    FleetArrivalService.process_arrived_fleets(user_id=user_id)
    after_arrived = Fleet.query.filter(
        Fleet.user_id == int(user_id),
        Fleet.arrival_time <= now,
        (
            Fleet.status.in_(["traveling", "returning", "defending"])
            | Fleet.status.like("exploring:%")
            | Fleet.status.like("colonizing:%")
        ),
    ).count()
    fleets_resolved = max(0, int(before_arrived) - int(after_arrived))

    # Complete research queue if it is due after we award RP.
    research_completed = _complete_research_queue_if_due(user, now)

    # One summary TickLog (no per-tick spam).
    home = Planet.query.filter_by(user_id=user_id).order_by(Planet.is_home_planet.desc(), Planet.id.asc()).first()
    db.session.add(
        TickLog(
            tick_number=0,
            planet_id=home.id if home else None,
            event_type="idle_catchup",
            event_description=f"Idle catch-up ({elapsed_seconds}s): +{total_metal}M +{total_crystal}C +{total_deut}D, +{rp_gain} RP",
            timestamp=datetime.utcnow(),
        )
    )

    # Update session marker.
    user.last_seen_at = now

    db.session.commit()

    return IdleCatchupResult(
        since=effective_since,
        until=now,
        duration_seconds=elapsed_seconds,
        resources={"metal": total_metal, "crystal": total_crystal, "deuterium": total_deut},
        research_points=rp_gain,
        events={"fleets_resolved": fleets_resolved, "research_completed": research_completed},
    )
