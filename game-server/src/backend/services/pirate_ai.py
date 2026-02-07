from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from types import SimpleNamespace
import hashlib
import math
import random

from flask import current_app
from sqlalchemy import func

from backend.database import db
from backend.models import (
    Fleet,
    Planet,
    TickLog,
    User,
    PirateAIState,
    PirateAIConfigOverride,
    PirateFactionState,
)
from backend.services.fleet_travel import FleetTravelService
from backend.config import get_forced_travel_time_seconds, get_min_travel_time_seconds
from backend.services.pirate_factions import (
    configured_pirate_usernames,
    is_pirate_user,
    select_primary_pirate_user,
)


@dataclass(frozen=True)
class PirateRaidDecision:
    should_spawn: bool
    probability: float
    is_peak: bool
    player_power: float
    pirate_power: float


class PirateAILiveOps:
    """Runtime-safe Pirate AI config + status helpers for admin operations."""

    CONFIG_SPECS: dict[str, dict] = {
        "PIRATE_AI_ENABLED": {"type": "bool"},
        "PIRATE_AI_INTERVAL_SECONDS": {"type": "int", "min": 1, "max": 86400},
        "PIRATE_AI_MAX_RAIDS_PER_24H": {"type": "int", "min": 0, "max": 48},
        "PIRATE_AI_COOLDOWN_SECONDS": {"type": "int", "min": 0, "max": 172800},
        "PIRATE_AI_PEAK_START_HOUR": {"type": "int", "min": 0, "max": 23},
        "PIRATE_AI_PEAK_END_HOUR": {"type": "int", "min": 0, "max": 24},
        "PIRATE_AI_PEAK_PROB_MULT": {"type": "float", "min": 0.1, "max": 5.0},
        "PIRATE_AI_PEAK_POWER_MULT": {"type": "float", "min": 0.1, "max": 5.0},
        "PIRATE_AI_DIFFICULTY_FACTOR": {"type": "float", "min": 0.1, "max": 5.0},
        "PIRATE_AI_P_MAX": {"type": "float", "min": 0.0, "max": 1.0},
        "PIRATE_FACTION_USERNAMES": {"type": "str"},
        "PIRATE_SIM_ENABLED": {"type": "bool"},
        "PIRATE_SIM_EXPANSION_ENABLED": {"type": "bool"},
        "PIRATE_SIM_EXPANSION_INTERVAL_SECONDS": {"type": "int", "min": 60, "max": 86400},
        "PIRATE_SIM_BUILD_ENABLED": {"type": "bool"},
        "PIRATE_SIM_FLEET_GROWTH_ENABLED": {"type": "bool"},
        "PIRATE_SIM_BUILD_INTERVAL_SECONDS": {"type": "int", "min": 60, "max": 86400},
        "PIRATE_SIM_FLEET_CAP_SCORE": {"type": "int", "min": 100, "max": 1000000},
        "PIRATE_SIM_ATTRITION_PERCENT": {"type": "float", "min": 0.0, "max": 0.5},
        "PIRATE_SIM_SKIRMISH_ENABLED": {"type": "bool"},
        "PIRATE_SIM_SKIRMISH_INTERVAL_SECONDS": {"type": "int", "min": 60, "max": 86400},
        "PIRATE_SIM_PLANET_CAP_PER_FACTION": {"type": "int", "min": 1, "max": 200},
        "PIRATE_SIM_PLANET_CAP_PER_Z_SLICE": {"type": "int", "min": 1, "max": 100},
        "PIRATE_SIM_TOTAL_PLANET_CAP": {"type": "int", "min": 1, "max": 10000},
        "PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO": {"type": "float", "min": 0.0, "max": 1.0},
        "PIRATE_SIM_RESEED_COOLDOWN_SECONDS": {"type": "int", "min": 60, "max": 604800},
        "PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE": {"type": "int", "min": 0, "max": 50000},
    }

    @staticmethod
    def apply_persisted_overrides() -> dict[str, object]:
        """Load persisted overrides from DB into app runtime config."""
        applied: dict[str, object] = {}
        rows = PirateAIConfigOverride.query.all()
        for row in rows:
            spec = PirateAILiveOps.CONFIG_SPECS.get(str(row.config_key))
            if not spec:
                continue
            ok, parsed, _err = PirateAILiveOps._parse_value(row.config_key, row.config_value)
            if not ok:
                continue
            current_app.config[row.config_key] = parsed
            applied[row.config_key] = parsed
        return applied

    @staticmethod
    def get_effective_config() -> dict[str, object]:
        cfg: dict[str, object] = {}
        for key in PirateAILiveOps.CONFIG_SPECS.keys():
            cfg[key] = current_app.config.get(key)
        return cfg

    @staticmethod
    def set_overrides(payload: dict[str, object]) -> tuple[dict[str, object], dict[str, str]]:
        applied: dict[str, object] = {}
        errors: dict[str, str] = {}

        for key, raw in (payload or {}).items():
            if key not in PirateAILiveOps.CONFIG_SPECS:
                errors[str(key)] = "Not allowlisted"
                continue

            ok, parsed, err = PirateAILiveOps._parse_value(key, raw)
            if not ok:
                errors[str(key)] = err or "Invalid value"
                continue

            row = PirateAIConfigOverride.query.filter_by(config_key=key).first()
            if not row:
                row = PirateAIConfigOverride(config_key=key, config_value=str(parsed))
                db.session.add(row)
            else:
                row.config_value = str(parsed)
            current_app.config[key] = parsed
            applied[key] = parsed

        if applied:
            db.session.commit()
        return applied, errors

    @staticmethod
    def build_status_summary(now: datetime | None = None) -> dict:
        now = now or datetime.utcnow()
        enabled = bool(current_app.config.get("PIRATE_AI_ENABLED"))
        users = User.query.all()
        non_pirates = [u for u in users if not is_pirate_user(u)]
        pirate_users = [u for u in users if is_pirate_user(u)]
        pirates = select_primary_pirate_user(users)

        states_by_user_id: dict[int, PirateAIState] = {
            int(s.user_id): s for s in PirateAIState.query.all() if getattr(s, "user_id", None) is not None
        }

        blocked_reasons = {
            "disabled": 0,
            "pirates_user_missing": 0,
            "not_due": 0,
            "protected": 0,
            "no_planets": 0,
            "cooldown": 0,
            "daily_cap": 0,
            "ready": 0,
        }

        if not enabled:
            blocked_reasons["disabled"] = len(non_pirates)
        elif pirates is None:
            blocked_reasons["pirates_user_missing"] = len(non_pirates)
        else:
            for user in non_pirates:
                state = states_by_user_id.get(int(user.id))
                if state and not PirateAIDirector._is_due(state=state, now=now):
                    blocked_reasons["not_due"] += 1
                    continue

                state_for_check = state or SimpleNamespace(
                    raids_last_24h=0,
                    cooldown_until=None,
                    threat_level=0.0,
                    raids_window_start_at=None,
                )
                eligible, reason = PirateAIDirector._is_eligible(user=user, state=state_for_check, now=now)
                if eligible:
                    blocked_reasons["ready"] += 1
                else:
                    blocked_reasons[reason] = int(blocked_reasons.get(reason, 0) or 0) + 1

        last_run_at = db.session.query(func.max(PirateAIState.last_action_at)).scalar()
        last_run_evaluated = 0
        if last_run_at is not None:
            last_run_evaluated = PirateAIState.query.filter_by(last_action_at=last_run_at).count()

        raids_last_24h = TickLog.query.filter(
            TickLog.event_type == "pirate_raid_spawned",
            TickLog.timestamp >= (now - timedelta(hours=24)),
        ).count()
        blocked_sim_reasons = {}
        for row in (
            TickLog.query.filter(
                TickLog.event_type == "pirate_growth_blocked_cap",
                TickLog.timestamp >= (now - timedelta(hours=24)),
            )
            .all()
        ):
            reason = "unknown"
            desc = str(getattr(row, "event_description", "") or "")
            if "reason=" in desc:
                reason = desc.split("reason=", 1)[1].split()[0].strip()
            blocked_sim_reasons[reason] = int(blocked_sim_reasons.get(reason, 0) or 0) + 1

        faction_states = {
            int(s.user_id): s for s in PirateFactionState.query.all() if getattr(s, "user_id", None) is not None
        }
        factions = []
        for pu in sorted(pirate_users, key=lambda u: int(u.id)):
            planets = Planet.query.filter_by(user_id=int(pu.id)).all()
            fleets = Fleet.query.filter_by(user_id=int(pu.id)).all()
            fleet_score = PirateAIDirector._fleet_score(fleets)
            state = faction_states.get(int(pu.id))
            factions.append(
                {
                    "user_id": int(pu.id),
                    "username": pu.username,
                    "planet_count": len(planets),
                    "fleet_score": int(fleet_score),
                    "planet_cap": int(getattr(state, "planet_cap", 0) or 0),
                    "fleet_cap": int(getattr(state, "fleet_cap", 0) or 0),
                    "build_cooldown_until": getattr(state, "build_cooldown_until", None).isoformat() + "Z"
                    if getattr(state, "build_cooldown_until", None)
                    else None,
                    "expansion_cooldown_until": getattr(state, "expansion_cooldown_until", None).isoformat() + "Z"
                    if getattr(state, "expansion_cooldown_until", None)
                    else None,
                    "skirmish_cooldown_until": getattr(state, "skirmish_cooldown_until", None).isoformat() + "Z"
                    if getattr(state, "skirmish_cooldown_until", None)
                    else None,
                }
            )

        return {
            "enabled": enabled,
            "now": now.isoformat() + "Z",
            "last_run_at": last_run_at.isoformat() + "Z" if last_run_at else None,
            "last_run_evaluated": int(last_run_evaluated),
            "raids_spawned_last_24h": int(raids_last_24h),
            "users_total": len(users),
            "users_considered": len(non_pirates),
            "blocked_reasons": blocked_reasons,
            "blocked_sim_reasons_24h": blocked_sim_reasons,
            "factions": factions,
            "config": PirateAILiveOps.get_effective_config(),
        }

    @staticmethod
    def _parse_value(key: str, raw: object) -> tuple[bool, object | None, str | None]:
        spec = PirateAILiveOps.CONFIG_SPECS.get(str(key))
        if not spec:
            return False, None, "Not allowlisted"

        t = spec["type"]
        val: object
        try:
            if t == "bool":
                if isinstance(raw, bool):
                    val = raw
                elif isinstance(raw, str):
                    norm = raw.strip().lower()
                    if norm in ("1", "true", "yes", "on"):
                        val = True
                    elif norm in ("0", "false", "no", "off"):
                        val = False
                    else:
                        return False, None, "Expected boolean"
                else:
                    return False, None, "Expected boolean"
            elif t == "int":
                val = int(raw)
            elif t == "float":
                val = float(raw)
            elif t == "str":
                val = str(raw).strip()
            else:
                return False, None, "Unsupported type"
        except (TypeError, ValueError):
            return False, None, f"Expected {t}"

        if t in ("int", "float"):
            min_v = spec.get("min")
            max_v = spec.get("max")
            if min_v is not None and val < min_v:
                return False, None, f"Must be >= {min_v}"
            if max_v is not None and val > max_v:
                return False, None, f"Must be <= {max_v}"

        return True, val, None


class PirateAIDirector:
    """Per-player Pirate Encounter Director (MVP)."""

    SHIP_WEIGHTS: dict[str, float] = {
        "small_cargo": 0.2,
        "large_cargo": 0.4,
        "light_fighter": 1.0,
        "heavy_fighter": 2.0,
        "cruiser": 7.0,
        "battleship": 20.0,
        "colony_ship": 1.0,
        "recycler": 0.1,
        "espionage_probe": 0.0,
        "bomber": 30.0,
        "destroyer": 45.0,
        "deathstar": 500.0,
        "battlecruiser": 25.0,
    }
    PLANET_BUILD_CAPS: dict[str, int] = {
        "metal_mine": 12,
        "crystal_mine": 12,
        "deuterium_synthesizer": 10,
        "solar_plant": 12,
    }
    PLANET_FLEET_CAPS: dict[str, int] = {
        "light_fighter": 250,
        "heavy_fighter": 120,
        "cruiser": 50,
        "battleship": 20,
        "battlecruiser": 10,
        "colony_ship": 3,
    }

    @staticmethod
    def run_hourly(
        now: datetime | None = None,
        *,
        only_user_ids: set[int] | None = None,
        force_spawn_for_user_ids: set[int] | None = None,
    ) -> dict:
        if not current_app.config.get("PIRATE_AI_ENABLED"):
            return {"enabled": False, "evaluated": 0, "spawned": 0}

        now = now or datetime.utcnow()
        only_user_ids = set(only_user_ids or [])
        force_spawn_for_user_ids = set(force_spawn_for_user_ids or [])

        pirate_users = User.query.filter(User.username.in_(configured_pirate_usernames())).all()
        pirates = select_primary_pirate_user(pirate_users)
        if not pirates:
            return {"enabled": True, "evaluated": 0, "spawned": 0, "error": "pirates_user_missing"}

        users = User.query.all()
        evaluated = 0
        spawned = 0
        expansion_spawned = 0
        growth_applied = 0
        skirmish_spawned = 0
        factions_reseeded = 0

        for user in users:
            if is_pirate_user(user):
                continue
            if only_user_ids and int(user.id) not in only_user_ids:
                continue

            state = PirateAIDirector._get_or_create_state(user_id=int(user.id))
            if not PirateAIDirector._is_due(state=state, now=now):
                continue

            evaluated += 1
            PirateAIDirector._reset_raid_window_if_needed(state=state, now=now)
            state.last_action_at = now

            eligible, _reason = PirateAIDirector._is_eligible(user=user, state=state, now=now)
            if not eligible:
                state.threat_level = PirateAIDirector._clamp_float((state.threat_level or 0.0) + 1.0, 0.0, 100.0)
                continue

            player_planets = Planet.query.filter_by(user_id=user.id).all()
            if not player_planets:
                continue

            home = next((p for p in player_planets if getattr(p, "is_home_planet", False)), None) or player_planets[0]
            PirateAIDirector._ensure_pirate_camp_near_player(pirates=pirates, player=user, center_planet=home)

            decision = PirateAIDirector._decide_for_player(user=user, state=state, now=now)
            if not decision.should_spawn and int(user.id) in force_spawn_for_user_ids:
                decision = PirateRaidDecision(
                    should_spawn=True,
                    probability=1.0,
                    is_peak=decision.is_peak,
                    player_power=decision.player_power,
                    pirate_power=decision.pirate_power,
                )

            if not decision.should_spawn:
                state.threat_level = PirateAIDirector._clamp_float((state.threat_level or 0.0) + 5.0, 0.0, 100.0)
                continue

            target = PirateAIDirector._select_target_planet(
                player_planets=player_planets,
                last_target_planet_id=getattr(state, "last_target_planet_id", None),
            )
            if not target:
                continue

            camp = PirateAIDirector._select_pirate_camp(pirates=pirates, target=target)
            if not camp:
                continue

            fleet = PirateAIDirector._spawn_raid_fleet(
                pirates=pirates,
                camp=camp,
                target=target,
                now=now,
                pirate_power=decision.pirate_power,
            )
            spawned += 1

            cooldown_seconds = PirateAIDirector._int_config("PIRATE_AI_COOLDOWN_SECONDS", 6 * 3600, min_value=0)
            state.cooldown_until = now + timedelta(seconds=cooldown_seconds)
            state.raids_last_24h = int(state.raids_last_24h or 0) + 1
            state.last_target_planet_id = int(target.id)
            state.threat_level = PirateAIDirector._clamp_float((state.threat_level or 0.0) - 20.0, 0.0, 100.0)

            db.session.add(
                TickLog(
                    tick_number=0,
                    planet_id=int(target.id),
                    fleet_id=int(fleet.id),
                    event_type="pirate_raid_spawned",
                    event_description=(
                        f"Pirate raid inbound to {target.name} ({target.x}:{target.y}:{target.z}) ETA {int(fleet.eta or 0)}s"
                    ),
                )
            )

        if bool(current_app.config.get("PIRATE_SIM_ENABLED")):
            factions_reseeded = PirateAIDirector._run_reseed_cycle(now=now, pirate_users=pirate_users)
            # refresh pirate users if reseed added camps/factions
            pirate_users = User.query.filter(User.username.in_(configured_pirate_usernames())).all()
            if bool(current_app.config.get("PIRATE_SIM_EXPANSION_ENABLED", True)):
                expansion_spawned = PirateAIDirector._run_expansion_cycle(now=now, pirate_users=pirate_users)
            if bool(current_app.config.get("PIRATE_SIM_BUILD_ENABLED", True)):
                growth_applied = PirateAIDirector._run_growth_cycle(now=now, pirate_users=pirate_users)
            if bool(current_app.config.get("PIRATE_SIM_SKIRMISH_ENABLED", True)):
                skirmish_spawned = PirateAIDirector._run_skirmish_cycle(now=now, pirate_users=pirate_users)

        db.session.commit()
        return {
            "enabled": True,
            "evaluated": evaluated,
            "spawned": spawned,
            "expansion_spawned": expansion_spawned,
            "growth_applied": growth_applied,
            "skirmish_spawned": skirmish_spawned,
            "factions_reseeded": factions_reseeded,
        }

    @staticmethod
    def _run_expansion_cycle(*, now: datetime, pirate_users: list[User]) -> int:
        interval = PirateAIDirector._int_config("PIRATE_SIM_EXPANSION_INTERVAL_SECONDS", 7200, min_value=60)
        if not PirateAIDirector._expansion_due(now=now, interval_seconds=interval):
            return 0

        if not pirate_users:
            return 0

        pirate_ids = [int(u.id) for u in pirate_users if getattr(u, "id", None) is not None]
        if not pirate_ids:
            return 0

        total_cap = PirateAIDirector._int_config("PIRATE_SIM_TOTAL_PLANET_CAP", 18, min_value=1)
        total_pirate_planets = Planet.query.filter(Planet.user_id.in_(pirate_ids)).count()
        total_colonized_planets = Planet.query.filter(Planet.user_id.isnot(None)).count()
        if total_pirate_planets >= total_cap:
            PirateAIDirector._log_growth_blocked(
                reason="total_cap",
                detail=f"Pirate expansion blocked: total cap reached ({total_pirate_planets}/{total_cap})",
            )
            db.session.add(TickLog(tick_number=0, event_type="pirate_expansion_cycle", event_description="blocked:total_cap"))
            return 0
        ratio_cap = float(current_app.config.get("PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO") or 0.20)
        pirate_ratio = (float(total_pirate_planets) / float(total_colonized_planets)) if total_colonized_planets > 0 else 0.0
        if pirate_ratio >= ratio_cap:
            PirateAIDirector._log_growth_blocked(
                reason="ownership_ratio",
                detail=f"Pirate expansion blocked: ownership ratio {pirate_ratio:.3f} >= {ratio_cap:.3f}",
            )
            db.session.add(TickLog(tick_number=0, event_type="pirate_expansion_cycle", event_description="blocked:ownership_ratio"))
            return 0

        planet_cap_per_faction = PirateAIDirector._int_config("PIRATE_SIM_PLANET_CAP_PER_FACTION", 6, min_value=1)
        z_cap = PirateAIDirector._int_config("PIRATE_SIM_PLANET_CAP_PER_Z_SLICE", 3, min_value=1)
        buffer_distance = PirateAIDirector._int_config("PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE", 1200, min_value=0)

        non_pirate_homes = (
            Planet.query.join(User, User.id == Planet.user_id)
            .filter(Planet.is_home_planet.is_(True))
            .all()
        )
        non_pirate_homes = [p for p in non_pirate_homes if not is_pirate_user(getattr(p, "owner", None))]

        spawned = 0
        for pirate_user in sorted(pirate_users, key=lambda u: int(u.id)):
            faction_state = PirateAIDirector._get_or_create_faction_state(user_id=int(pirate_user.id))
            if faction_state.expansion_cooldown_until and faction_state.expansion_cooldown_until > now:
                continue
            faction_planets = Planet.query.filter_by(user_id=int(pirate_user.id)).all()
            if len(faction_planets) >= planet_cap_per_faction:
                continue

            in_flight = Fleet.query.filter(
                Fleet.user_id == int(pirate_user.id),
                Fleet.mission == "colonize",
                Fleet.status.in_(["traveling", "returning"]),
            ).count()
            if in_flight > 0:
                continue

            by_z: dict[int, int] = {}
            for p in faction_planets:
                by_z[int(getattr(p, "z", 0) or 0)] = int(by_z.get(int(getattr(p, "z", 0) or 0), 0) + 1)
            origin = next((p for p in faction_planets if getattr(p, "is_home_planet", False)), None) or (faction_planets[0] if faction_planets else None)
            if origin is None:
                continue
            if int(by_z.get(int(origin.z), 0)) >= z_cap:
                continue

            target = PirateAIDirector._select_expansion_target(
                origin=origin,
                non_pirate_homes=non_pirate_homes,
                home_buffer_distance=buffer_distance,
            )
            if not target:
                continue

            source_fleet = (
                Fleet.query.filter(
                    Fleet.user_id == int(pirate_user.id),
                    Fleet.start_planet_id == int(origin.id),
                    Fleet.status.in_(["stationed", "defending"]),
                    Fleet.colony_ship > 0,
                )
                .order_by(Fleet.id.asc())
                .first()
            )
            if not source_fleet:
                continue

            source_fleet.colony_ship = max(0, int(source_fleet.colony_ship or 0) - 1)

            fleet = Fleet(
                user_id=int(pirate_user.id),
                mission="colonize",
                status=f"colonizing:{int(target.x)}:{int(target.y)}:{int(target.z)}",
                start_planet_id=int(origin.id),
                target_planet_id=int(target.id),
                departure_time=now,
                arrival_time=now,
                eta=0,
                target_coordinates=f"{int(target.x)}:{int(target.y)}:{int(target.z)}",
                colony_ship=1,
            )
            db.session.add(fleet)
            db.session.flush()

            distance = FleetTravelService.calculate_distance(origin, target)
            speed = FleetTravelService.calculate_fleet_speed(fleet)
            travel_time_hours = distance / speed if speed > 0 else 0.0

            min_travel = max(1, int(get_min_travel_time_seconds() or 0))
            travel_time_seconds = max(int(travel_time_hours * 3600), min_travel)
            forced = get_forced_travel_time_seconds()
            if forced is not None:
                travel_time_seconds = max(1, int(forced))

            fleet.departure_time = now
            fleet.arrival_time = now + timedelta(seconds=travel_time_seconds)
            fleet.eta = int(travel_time_seconds)

            spawned += 1
            db.session.add(
                TickLog(
                    tick_number=0,
                    planet_id=int(target.id),
                    fleet_id=int(fleet.id),
                    event_type="pirate_colonization_started",
                    event_description=(
                        f"Pirate colonizer from {origin.name} heading to {target.name} "
                        f"({target.x}:{target.y}:{target.z}) ETA {int(fleet.eta or 0)}s"
                    ),
                )
            )
            expansion_interval = PirateAIDirector._int_config("PIRATE_SIM_EXPANSION_INTERVAL_SECONDS", 7200, min_value=60)
            faction_state.expansion_cooldown_until = now + timedelta(seconds=expansion_interval)
            faction_state.planet_cap = int(planet_cap_per_faction)

        db.session.add(
            TickLog(
                tick_number=0,
                event_type="pirate_expansion_cycle",
                event_description=f"spawned={spawned}",
            )
        )
        return spawned

    @staticmethod
    def _expansion_due(*, now: datetime, interval_seconds: int) -> bool:
        last = (
            db.session.query(func.max(TickLog.timestamp))
            .filter(TickLog.event_type == "pirate_expansion_cycle")
            .scalar()
        )
        if not last:
            return True
        try:
            return (now - last).total_seconds() >= int(interval_seconds)
        except Exception:
            return True

    @staticmethod
    def _select_expansion_target(
        *,
        origin: Planet,
        non_pirate_homes: list[Planet],
        home_buffer_distance: int,
    ) -> Planet | None:
        candidates = (
            Planet.query.filter(
                Planet.user_id.is_(None),
                Planet.z == int(origin.z),
            )
            .all()
        )
        if not candidates:
            return None

        best = None
        best_dist = None
        for p in candidates:
            if home_buffer_distance > 0 and PirateAIDirector._within_home_buffer(p, non_pirate_homes, home_buffer_distance):
                continue
            dist = FleetTravelService.calculate_distance(origin, p)
            if best is None or dist < (best_dist or 0):
                best = p
                best_dist = dist
        return best

    @staticmethod
    def _within_home_buffer(candidate: Planet, homes: list[Planet], buffer_distance: int) -> bool:
        if buffer_distance <= 0:
            return False
        for home in homes:
            if int(getattr(home, "z", 0) or 0) != int(getattr(candidate, "z", 0) or 0):
                continue
            dist = FleetTravelService.calculate_distance(home, candidate)
            if dist <= float(buffer_distance):
                return True
        return False

    @staticmethod
    def _run_growth_cycle(*, now: datetime, pirate_users: list[User]) -> int:
        if not PirateAIDirector._growth_due(now=now):
            return 0

        applied_actions = 0
        for pirate_user in sorted(pirate_users, key=lambda u: int(u.id)):
            state = PirateAIDirector._get_or_create_faction_state(user_id=int(pirate_user.id))
            cooldown = getattr(state, "build_cooldown_until", None)
            if cooldown and cooldown > now:
                continue

            planets = Planet.query.filter_by(user_id=int(pirate_user.id)).all()
            if not planets:
                continue

            # Per-planet one build action per cycle, respecting hard caps.
            for planet in planets:
                if PirateAIDirector._apply_planet_build_step(planet):
                    applied_actions += 1
                    db.session.add(
                        TickLog(
                            tick_number=0,
                            planet_id=int(planet.id),
                            event_type="pirate_build_applied",
                            event_description=(
                                f"Pirate build applied on {planet.name} "
                                f"({planet.x}:{planet.y}:{planet.z})"
                            ),
                        )
                    )

            fleets = Fleet.query.filter_by(user_id=int(pirate_user.id)).all()
            fleet_cap = PirateAIDirector._int_config("PIRATE_SIM_FLEET_CAP_SCORE", 6000, min_value=100)
            fleet_score = PirateAIDirector._fleet_score(fleets)

            if fleet_score > fleet_cap:
                attrition_pct = PirateAIDirector._float_config("PIRATE_SIM_ATTRITION_PERCENT", 0.02, min_value=0.0, max_value=0.5)
                if PirateAIDirector._apply_attrition(user_id=int(pirate_user.id), percent=attrition_pct):
                    applied_actions += 1
                    PirateAIDirector._log_growth_blocked(
                        reason="fleet_cap",
                        detail=f"Faction {pirate_user.username} over fleet cap ({fleet_score}/{fleet_cap}) attrition applied",
                    )
            elif bool(current_app.config.get("PIRATE_SIM_FLEET_GROWTH_ENABLED", True)):
                growth_count = PirateAIDirector._apply_fleet_growth_for_faction(user_id=int(pirate_user.id), planets=planets)
                applied_actions += int(growth_count)

            state.fleet_points = int(PirateAIDirector._fleet_score(Fleet.query.filter_by(user_id=int(pirate_user.id)).all()))
            state.fleet_cap = int(fleet_cap)
            state.planet_cap = int(PirateAIDirector._int_config("PIRATE_SIM_PLANET_CAP_PER_FACTION", 6, min_value=1))
            build_interval = PirateAIDirector._int_config("PIRATE_SIM_BUILD_INTERVAL_SECONDS", 7200, min_value=60)
            state.build_cooldown_until = now + timedelta(seconds=build_interval)

        db.session.add(
            TickLog(
                tick_number=0,
                event_type="pirate_growth_cycle",
                event_description=f"applied={applied_actions}",
            )
        )
        return int(applied_actions)

    @staticmethod
    def _run_skirmish_cycle(*, now: datetime, pirate_users: list[User]) -> int:
        if not PirateAIDirector._skirmish_due(now=now):
            return 0

        spawned = 0
        pirate_users = [u for u in pirate_users if Planet.query.filter_by(user_id=int(u.id)).count() > 0]
        if len(pirate_users) < 2:
            db.session.add(TickLog(tick_number=0, event_type="pirate_skirmish_cycle", event_description="blocked:insufficient_factions"))
            return 0

        for attacker in sorted(pirate_users, key=lambda u: int(u.id)):
            attacker_planets = Planet.query.filter_by(user_id=int(attacker.id)).all()
            if not attacker_planets:
                continue

            attacker_state = PirateAIDirector._get_or_create_faction_state(user_id=int(attacker.id))
            if attacker_state.skirmish_cooldown_until and attacker_state.skirmish_cooldown_until > now:
                continue

            target_user, target_planet = PirateAIDirector._select_skirmish_target(
                attacker=attacker,
                attacker_planets=attacker_planets,
                pirate_users=pirate_users,
                last_target_faction_user_id=getattr(attacker_state, "last_target_faction_user_id", None),
            )
            if not target_user or not target_planet:
                continue

            origin = PirateAIDirector._select_skirmish_origin(attacker_planets)
            source_fleet = PirateAIDirector._select_source_attack_fleet(user_id=int(attacker.id), origin_planet_id=int(origin.id))
            if not source_fleet:
                continue

            ships = PirateAIDirector._extract_attack_ships_from_source(source_fleet)
            if not ships:
                continue

            attack_fleet = Fleet(
                user_id=int(attacker.id),
                mission="attack",
                status="traveling",
                start_planet_id=int(origin.id),
                target_planet_id=int(target_planet.id),
                departure_time=now,
                arrival_time=now,
                eta=0,
                **ships,
            )
            db.session.add(attack_fleet)
            db.session.flush()

            distance = FleetTravelService.calculate_distance(origin, target_planet)
            speed = FleetTravelService.calculate_fleet_speed(attack_fleet)
            travel_time_hours = distance / speed if speed > 0 else 0.0
            min_travel = max(1, int(get_min_travel_time_seconds() or 0))
            travel_time_seconds = max(int(travel_time_hours * 3600), min_travel)
            forced = get_forced_travel_time_seconds()
            if forced is not None:
                travel_time_seconds = max(1, int(forced))
            attack_fleet.arrival_time = now + timedelta(seconds=travel_time_seconds)
            attack_fleet.eta = int(travel_time_seconds)

            attacker_state.last_target_faction_user_id = int(target_user.id)
            cooldown = PirateAIDirector._int_config("PIRATE_SIM_SKIRMISH_INTERVAL_SECONDS", 1200, min_value=60)
            attacker_state.skirmish_cooldown_until = now + timedelta(seconds=cooldown)
            spawned += 1
            db.session.add(
                TickLog(
                    tick_number=0,
                    planet_id=int(target_planet.id),
                    fleet_id=int(attack_fleet.id),
                    event_type="pirate_skirmish_spawned",
                    event_description=(
                        f"Pirate skirmish {attacker.username} -> {target_user.username} "
                        f"at {target_planet.x}:{target_planet.y}:{target_planet.z} ETA {int(attack_fleet.eta or 0)}s"
                    ),
                )
            )

        db.session.add(TickLog(tick_number=0, event_type="pirate_skirmish_cycle", event_description=f"spawned={spawned}"))
        return int(spawned)

    @staticmethod
    def _run_reseed_cycle(*, now: datetime, pirate_users: list[User]) -> int:
        reseeded = 0
        reseed_cd = PirateAIDirector._int_config("PIRATE_SIM_RESEED_COOLDOWN_SECONDS", 86400, min_value=60)
        for pirate_user in pirate_users:
            planets = Planet.query.filter_by(user_id=int(pirate_user.id)).all()
            if planets:
                continue
            state = PirateAIDirector._get_or_create_faction_state(user_id=int(pirate_user.id))
            cooldown = getattr(state, "expansion_cooldown_until", None)
            if cooldown and cooldown > now:
                continue

            x = max(-9000, min(9000, 700 + int(pirate_user.id) * 31))
            y = max(-9000, min(9000, -700 - int(pirate_user.id) * 29))
            z = int(int(pirate_user.id) % 7)
            for _ in range(60):
                if Planet.query.filter_by(x=x, y=y, z=z).first() is None:
                    break
                x += 3
                y -= 2

            camp = Planet(
                name=f"{pirate_user.username} Reseed Camp",
                x=x,
                y=y,
                z=z,
                user_id=int(pirate_user.id),
                is_home_planet=True,
                metal=40_000,
                crystal=20_000,
                deuterium=10_000,
                metal_mine=4,
                crystal_mine=3,
                deuterium_synthesizer=2,
                solar_plant=5,
            )
            db.session.add(camp)
            db.session.flush()
            db.session.add(
                Fleet(
                    user_id=int(pirate_user.id),
                    mission="defend",
                    status="stationed",
                    start_planet_id=int(camp.id),
                    target_planet_id=int(camp.id),
                    departure_time=now,
                    arrival_time=now,
                    eta=0,
                    light_fighter=80,
                    heavy_fighter=30,
                    cruiser=8,
                    battleship=3,
                    colony_ship=1,
                )
            )
            state.expansion_cooldown_until = now + timedelta(seconds=reseed_cd)
            reseeded += 1
            db.session.add(
                TickLog(
                    tick_number=0,
                    planet_id=int(camp.id),
                    event_type="pirate_faction_reseeded",
                    event_description=f"Pirate faction {pirate_user.username} reseeded at {camp.x}:{camp.y}:{camp.z}",
                )
            )
        return int(reseeded)

    @staticmethod
    def _growth_due(*, now: datetime) -> bool:
        interval = PirateAIDirector._int_config("PIRATE_SIM_BUILD_INTERVAL_SECONDS", 7200, min_value=60)
        last = db.session.query(func.max(TickLog.timestamp)).filter(TickLog.event_type == "pirate_growth_cycle").scalar()
        if not last:
            return True
        try:
            return (now - last).total_seconds() >= int(interval)
        except Exception:
            return True

    @staticmethod
    def _skirmish_due(*, now: datetime) -> bool:
        interval = PirateAIDirector._int_config("PIRATE_SIM_SKIRMISH_INTERVAL_SECONDS", 1200, min_value=60)
        last = db.session.query(func.max(TickLog.timestamp)).filter(TickLog.event_type == "pirate_skirmish_cycle").scalar()
        if not last:
            return True
        try:
            return (now - last).total_seconds() >= int(interval)
        except Exception:
            return True

    @staticmethod
    def _apply_planet_build_step(planet: Planet) -> bool:
        if not planet:
            return False
        for key in ("metal_mine", "crystal_mine", "deuterium_synthesizer", "solar_plant"):
            cap = int(PirateAIDirector.PLANET_BUILD_CAPS.get(key, 0))
            current = int(getattr(planet, key, 0) or 0)
            if current < cap:
                setattr(planet, key, current + 1)
                return True
        return False

    @staticmethod
    def _apply_fleet_growth_for_faction(*, user_id: int, planets: list[Planet]) -> int:
        grown = 0
        for planet in planets:
            inv = PirateAIDirector._get_or_create_inventory_fleet(user_id=user_id, planet_id=int(planet.id))
            totals = PirateAIDirector._planet_ship_totals(user_id=user_id, planet_id=int(planet.id))
            for ship in ("light_fighter", "heavy_fighter", "cruiser", "battleship", "battlecruiser", "colony_ship"):
                cap = int(PirateAIDirector.PLANET_FLEET_CAPS.get(ship, 0))
                if int(totals.get(ship, 0) or 0) >= cap:
                    continue
                add_n = 1 if ship != "light_fighter" else 4
                setattr(inv, ship, int(getattr(inv, ship, 0) or 0) + add_n)
                grown += add_n
                break
        return int(grown)

    @staticmethod
    def _apply_attrition(*, user_id: int, percent: float) -> bool:
        changed = False
        percent = PirateAIDirector._clamp_float(percent, 0.0, 0.5)
        fleets = Fleet.query.filter(
            Fleet.user_id == int(user_id),
            Fleet.status.in_(["stationed", "defending"]),
        ).all()
        for fleet in fleets:
            for ship in ("light_fighter", "heavy_fighter", "cruiser", "battleship", "battlecruiser"):
                n = int(getattr(fleet, ship, 0) or 0)
                if n <= 0:
                    continue
                loss = max(1, int(math.ceil(float(n) * percent)))
                setattr(fleet, ship, max(0, n - loss))
                changed = True
        return changed

    @staticmethod
    def _planet_ship_totals(*, user_id: int, planet_id: int) -> dict[str, int]:
        totals = {k: 0 for k in PirateAIDirector.PLANET_FLEET_CAPS.keys()}
        fleets = Fleet.query.filter(
            Fleet.user_id == int(user_id),
            Fleet.start_planet_id == int(planet_id),
            Fleet.status.in_(["stationed", "defending"]),
        ).all()
        for f in fleets:
            for ship in totals.keys():
                totals[ship] += int(getattr(f, ship, 0) or 0)
        return totals

    @staticmethod
    def _get_or_create_inventory_fleet(*, user_id: int, planet_id: int) -> Fleet:
        fleet = (
            Fleet.query.filter_by(
                user_id=int(user_id),
                start_planet_id=int(planet_id),
                status="stationed",
                mission="inventory",
            )
            .order_by(Fleet.id.asc())
            .first()
        )
        if fleet:
            return fleet
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=int(user_id),
            mission="inventory",
            status="stationed",
            start_planet_id=int(planet_id),
            target_planet_id=int(planet_id),
            departure_time=now,
            arrival_time=now,
            eta=0,
        )
        db.session.add(fleet)
        db.session.flush()
        return fleet

    @staticmethod
    def _select_skirmish_target(
        *,
        attacker: User,
        attacker_planets: list[Planet],
        pirate_users: list[User],
        last_target_faction_user_id: int | None,
    ) -> tuple[User | None, Planet | None]:
        if not attacker_planets:
            return None, None
        candidates: list[tuple[float, User, Planet]] = []
        alt_candidates: list[tuple[float, User, Planet]] = []
        for other in pirate_users:
            if int(other.id) == int(attacker.id):
                continue
            other_planets = Planet.query.filter_by(user_id=int(other.id)).all()
            for tp in other_planets:
                origin = min(
                    attacker_planets,
                    key=lambda p: FleetTravelService.calculate_distance(p, tp),
                )
                dist = FleetTravelService.calculate_distance(origin, tp)
                score = dist - float((tp.metal_mine or 0) + (tp.crystal_mine or 0) + (tp.deuterium_synthesizer or 0)) * 12.0
                item = (score, other, tp)
                if last_target_faction_user_id and int(other.id) == int(last_target_faction_user_id):
                    alt_candidates.append(item)
                else:
                    candidates.append(item)
        pool = candidates or alt_candidates
        if not pool:
            return None, None
        pool.sort(key=lambda t: t[0])
        _score, user, planet = pool[0]
        return user, planet

    @staticmethod
    def _select_skirmish_origin(planets: list[Planet]) -> Planet:
        return max(
            planets,
            key=lambda p: float((p.metal_mine or 0) + (p.crystal_mine or 0) + (p.deuterium_synthesizer or 0) + (p.solar_plant or 0)),
        )

    @staticmethod
    def _select_source_attack_fleet(*, user_id: int, origin_planet_id: int) -> Fleet | None:
        return (
            Fleet.query.filter(
                Fleet.user_id == int(user_id),
                Fleet.start_planet_id == int(origin_planet_id),
                Fleet.status.in_(["stationed", "defending"]),
            )
            .order_by(Fleet.id.asc())
            .first()
        )

    @staticmethod
    def _extract_attack_ships_from_source(source_fleet: Fleet) -> dict[str, int]:
        ships: dict[str, int] = {}
        for ship, frac in (
            ("light_fighter", 0.2),
            ("heavy_fighter", 0.2),
            ("cruiser", 0.25),
            ("battleship", 0.25),
            ("battlecruiser", 0.25),
        ):
            n = int(getattr(source_fleet, ship, 0) or 0)
            if n <= 0:
                continue
            send = max(1, int(math.floor(float(n) * frac)))
            send = min(send, n)
            if send <= 0:
                continue
            setattr(source_fleet, ship, max(0, n - send))
            ships[ship] = send
        return ships

    @staticmethod
    def _fleet_score(fleets: list[Fleet]) -> float:
        score = 0.0
        for f in fleets:
            for ship, weight in PirateAIDirector.SHIP_WEIGHTS.items():
                score += float(getattr(f, ship, 0) or 0) * float(weight)
        return float(score)

    @staticmethod
    def _get_or_create_faction_state(*, user_id: int) -> PirateFactionState:
        state = PirateFactionState.query.filter_by(user_id=int(user_id)).first()
        if state:
            return state
        state = PirateFactionState(user_id=int(user_id))
        db.session.add(state)
        db.session.flush()
        return state

    @staticmethod
    def _log_growth_blocked(*, reason: str, detail: str) -> None:
        db.session.add(
            TickLog(
                tick_number=0,
                event_type="pirate_growth_blocked_cap",
                event_description=f"reason={reason} {detail}",
            )
        )

    @staticmethod
    def _get_or_create_state(user_id: int) -> PirateAIState:
        state = PirateAIState.query.filter_by(user_id=int(user_id)).first()
        if state:
            return state
        state = PirateAIState(user_id=int(user_id), threat_level=0.0, raids_last_24h=0)
        db.session.add(state)
        db.session.flush()
        return state

    @staticmethod
    def _is_due(state: PirateAIState, now: datetime) -> bool:
        interval_seconds = PirateAIDirector._int_config("PIRATE_AI_INTERVAL_SECONDS", 3600, min_value=1)
        last = getattr(state, "last_action_at", None)
        if not last:
            return True
        try:
            return (now - last).total_seconds() >= interval_seconds
        except Exception:
            return True

    @staticmethod
    def _reset_raid_window_if_needed(state: PirateAIState, now: datetime) -> None:
        window_start = getattr(state, "raids_window_start_at", None)
        if not window_start:
            state.raids_window_start_at = now
            state.raids_last_24h = 0
            return
        try:
            if (now - window_start) >= timedelta(hours=24):
                state.raids_window_start_at = now
                state.raids_last_24h = 0
        except Exception:
            state.raids_window_start_at = now
            state.raids_last_24h = 0

    @staticmethod
    def _is_eligible(*, user: User, state: PirateAIState, now: datetime) -> tuple[bool, str]:
        try:
            prot = getattr(user, "protection_until", None)
            if prot and prot > now:
                return False, "protected"
        except Exception:
            pass

        planet_count = Planet.query.filter_by(user_id=user.id).count()
        if planet_count <= 0:
            return False, "no_planets"

        cooldown = getattr(state, "cooldown_until", None)
        if cooldown and cooldown > now:
            return False, "cooldown"

        max_raids = PirateAIDirector._int_config("PIRATE_AI_MAX_RAIDS_PER_24H", 2, min_value=0)
        if int(state.raids_last_24h or 0) >= max_raids:
            return False, "daily_cap"

        return True, "ok"

    @staticmethod
    def _decide_for_player(*, user: User, state: PirateAIState, now: datetime) -> PirateRaidDecision:
        salt = str(current_app.config.get("PIRATE_AI_SECRET_SALT") or current_app.config.get("SECRET_KEY") or "pirate-ai")
        hour_key = PirateAIDirector._truncate_to_hour(now)
        rng = PirateAIDirector._rng_for_hour(user_id=int(user.id), hour_key=hour_key, salt=salt)

        player_power = PirateAIDirector._calculate_player_power(user_id=int(user.id))
        threat = float(state.threat_level or 0.0)

        p_base = 0.02
        p_power = min(0.25, (math.log10(player_power + 10.0) / 10.0) if player_power > 0 else 0.0)
        p_threat = min(0.20, threat / 500.0)
        p_max = float(current_app.config.get("PIRATE_AI_P_MAX") or 0.5)
        probability = PirateAIDirector._clamp_float(p_base + p_power + p_threat, 0.0, p_max)

        is_peak = PirateAIDirector._is_peak_hour(now)
        if is_peak:
            probability *= float(current_app.config.get("PIRATE_AI_PEAK_PROB_MULT") or 1.5)
            probability = PirateAIDirector._clamp_float(probability, 0.0, p_max)

        difficulty = float(current_app.config.get("PIRATE_AI_DIFFICULTY_FACTOR") or 0.8)
        pirate_power = max(50.0, player_power * difficulty)
        if is_peak:
            pirate_power *= float(current_app.config.get("PIRATE_AI_PEAK_POWER_MULT") or 1.25)

        should_spawn = rng.random() < probability
        return PirateRaidDecision(
            should_spawn=bool(should_spawn),
            probability=float(probability),
            is_peak=bool(is_peak),
            player_power=float(player_power),
            pirate_power=float(pirate_power),
        )

    @staticmethod
    def _calculate_player_power(*, user_id: int) -> float:
        planets = Planet.query.filter_by(user_id=int(user_id)).all()
        planet_count = len(planets)
        production_score = 0.0
        for p in planets:
            production_score += float(getattr(p, "metal_mine", 0) or 0)
            production_score += float(getattr(p, "crystal_mine", 0) or 0)
            production_score += float(getattr(p, "deuterium_synthesizer", 0) or 0)

        fleets = Fleet.query.filter_by(user_id=int(user_id)).all()
        fleet_score = 0.0
        for f in fleets:
            for ship, weight in PirateAIDirector.SHIP_WEIGHTS.items():
                fleet_score += float(getattr(f, ship, 0) or 0) * float(weight)

        return (planet_count * 50.0) + (production_score * 10.0) + fleet_score

    @staticmethod
    def _select_target_planet(*, player_planets: list[Planet], last_target_planet_id: int | None) -> Planet | None:
        if not player_planets:
            return None

        def score(p: Planet) -> float:
            stored = float((p.metal or 0) + (p.crystal or 0) + (p.deuterium or 0))
            infra = float((p.metal_mine or 0) + (p.crystal_mine or 0) + (p.deuterium_synthesizer or 0) + (p.solar_plant or 0))
            return stored + (infra * 1000.0)

        sorted_planets = sorted(player_planets, key=score, reverse=True)
        for p in sorted_planets:
            if last_target_planet_id and int(p.id) == int(last_target_planet_id):
                continue
            return p
        return sorted_planets[0]

    @staticmethod
    def _select_pirate_camp(*, pirates: User, target: Planet) -> Planet | None:
        pirate_planets = Planet.query.filter_by(user_id=int(pirates.id), z=int(target.z)).all()
        if not pirate_planets:
            return None

        best = None
        best_dist = None
        for p in pirate_planets:
            dist = FleetTravelService.calculate_distance(p, target)
            if best is None or dist < (best_dist or 0):
                best = p
                best_dist = dist
        return best

    @staticmethod
    def _ensure_pirate_camp_near_player(*, pirates: User, player: User, center_planet: Planet) -> None:
        pirate_planets = Planet.query.filter_by(user_id=int(pirates.id), z=int(center_planet.z)).all()
        if pirate_planets:
            for p in pirate_planets:
                if FleetTravelService.calculate_distance(p, center_planet) <= 2500:
                    return

        base_dx = 450 + (int(player.id) * 17) % 400
        base_dy = -450 - (int(player.id) * 11) % 400
        x = int(center_planet.x + base_dx)
        y = int(center_planet.y + base_dy)
        z = int(center_planet.z)

        x = max(-10000, min(10000, x))
        y = max(-10000, min(10000, y))

        for i in range(50):
            if Planet.query.filter_by(x=x, y=y, z=z).first() is None:
                break
            x += 1
            y -= 1

        camp = Planet(
            name=f"Pirate Camp near {center_planet.name}",
            x=x,
            y=y,
            z=z,
            user_id=int(pirates.id),
            metal=50_000,
            crystal=25_000,
            deuterium=10_000,
        )
        db.session.add(camp)
        db.session.flush()

        now = datetime.utcnow()
        db.session.add(
            Fleet(
                user_id=int(pirates.id),
                mission="defend",
                status="stationed",
                start_planet_id=int(camp.id),
                target_planet_id=int(camp.id),
                departure_time=now,
                arrival_time=now,
                eta=0,
                light_fighter=200,
                heavy_fighter=100,
                cruiser=25,
                battleship=10,
            )
        )
        db.session.flush()

    @staticmethod
    def _spawn_raid_fleet(*, pirates: User, camp: Planet, target: Planet, now: datetime, pirate_power: float) -> Fleet:
        ships = PirateAIDirector._pirate_fleet_composition(pirate_power=pirate_power)

        fleet = Fleet(
            user_id=int(pirates.id),
            mission="attack",
            status="traveling",
            start_planet_id=int(camp.id),
            target_planet_id=int(target.id),
            departure_time=now,
            arrival_time=now,
            eta=0,
            **ships,
        )

        db.session.add(fleet)
        db.session.flush()

        distance = FleetTravelService.calculate_distance(camp, target)
        speed = FleetTravelService.calculate_fleet_speed(fleet)
        travel_time_hours = distance / speed if speed > 0 else 0.0

        min_travel = max(1, int(get_min_travel_time_seconds() or 0))
        travel_time_seconds = max(int(travel_time_hours * 3600), min_travel)

        forced = get_forced_travel_time_seconds()
        if forced is not None:
            travel_time_seconds = max(1, int(forced))

        fleet.departure_time = now
        fleet.arrival_time = now + timedelta(seconds=travel_time_seconds)
        fleet.eta = int(travel_time_seconds)
        db.session.flush()
        return fleet

    @staticmethod
    def _pirate_fleet_composition(*, pirate_power: float) -> dict[str, int]:
        scale = max(0.5, float(pirate_power) / 500.0)

        light = int(80 * scale)
        heavy = int(30 * scale)
        cruiser = int(6 * scale)
        battleship = int(2 * scale)
        battlecruiser = int(1 * max(0.0, scale - 2.0))

        light = max(10, min(1500, light))
        heavy = max(0, min(800, heavy))
        cruiser = max(0, min(200, cruiser))
        battleship = max(0, min(80, battleship))
        battlecruiser = max(0, min(40, battlecruiser))

        return {
            "light_fighter": light,
            "heavy_fighter": heavy,
            "cruiser": cruiser,
            "battleship": battleship,
            "battlecruiser": battlecruiser,
        }

    @staticmethod
    def _truncate_to_hour(dt: datetime) -> datetime:
        return dt.replace(minute=0, second=0, microsecond=0)

    @staticmethod
    def _rng_for_hour(*, user_id: int, hour_key: datetime, salt: str) -> random.Random:
        raw = f"{int(user_id)}:{hour_key.isoformat()}:{salt}".encode("utf-8")
        digest = hashlib.sha256(raw).digest()
        seed = int.from_bytes(digest[:8], "big", signed=False)
        return random.Random(seed)

    @staticmethod
    def _is_peak_hour(now: datetime) -> bool:
        start = PirateAIDirector._int_config("PIRATE_AI_PEAK_START_HOUR", 18, min_value=0, max_value=23)
        end = PirateAIDirector._int_config("PIRATE_AI_PEAK_END_HOUR", 20, min_value=0, max_value=24)
        h = int(getattr(now, "hour", 0) or 0)
        if start <= end:
            return start <= h < end
        return h >= start or h < end

    @staticmethod
    def _int_config(name: str, default: int, *, min_value: int | None = None, max_value: int | None = None) -> int:
        raw = current_app.config.get(name, default)
        try:
            val = int(raw)
        except (TypeError, ValueError):
            val = int(default)
        if min_value is not None:
            val = max(min_value, val)
        if max_value is not None:
            val = min(max_value, val)
        return val

    @staticmethod
    def _float_config(name: str, default: float, *, min_value: float | None = None, max_value: float | None = None) -> float:
        raw = current_app.config.get(name, default)
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = float(default)
        if min_value is not None:
            val = max(float(min_value), val)
        if max_value is not None:
            val = min(float(max_value), val)
        return float(val)

    @staticmethod
    def _clamp_float(v: float, lo: float, hi: float) -> float:
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = lo
        return max(lo, min(hi, v))
