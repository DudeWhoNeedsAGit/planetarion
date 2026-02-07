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
from backend.models import Fleet, Planet, TickLog, User, PirateAIState, PirateAIConfigOverride
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

        return {
            "enabled": enabled,
            "now": now.isoformat() + "Z",
            "last_run_at": last_run_at.isoformat() + "Z" if last_run_at else None,
            "last_run_evaluated": int(last_run_evaluated),
            "raids_spawned_last_24h": int(raids_last_24h),
            "users_total": len(users),
            "users_considered": len(non_pirates),
            "blocked_reasons": blocked_reasons,
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

        db.session.commit()
        return {"enabled": True, "evaluated": evaluated, "spawned": spawned}

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
    def _clamp_float(v: float, lo: float, hi: float) -> float:
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = lo
        return max(lo, min(hi, v))
