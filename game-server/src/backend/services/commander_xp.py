from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.database import db
from backend.models import CommanderXPEvent, User
from backend.services.pirate_factions import is_pirate_user


def xp_to_next_level(level: int) -> int:
    """XP required to go from `level` -> `level + 1`."""
    l = max(1, int(level or 1))
    # Fast early progression, slows down later. Tunable.
    return int(100 * (l ** 1.6))


def level_for_xp(total_xp: int) -> int:
    """Derive commander level from total XP. Level starts at 1."""
    xp = max(0, int(total_xp or 0))
    level = 1
    while True:
        need = xp_to_next_level(level)
        if xp < need:
            return level
        xp -= need
        level += 1


def xp_progress(total_xp: int) -> tuple[int, int]:
    """Return (xp_into_level, xp_to_next)."""
    xp = max(0, int(total_xp or 0))
    level = 1
    while True:
        need = xp_to_next_level(level)
        if xp < need:
            return xp, need
        xp -= need
        level += 1


@dataclass(frozen=True)
class AwardResult:
    applied: bool
    xp_awarded: int
    new_total_xp: int
    new_level: int


class CommanderXPService:
    @staticmethod
    def award_xp(
        *,
        user_id: int,
        xp: int,
        source_type: str,
        source_id: str,
        now: datetime | None = None,
    ) -> AwardResult | None:
        """Idempotently award commander XP and recompute level.

        - Uses `CommanderXPEvent` uniqueness to prevent double-awards.
        - Does not commit; caller controls transaction boundaries.
        """
        if xp is None:
            return None
        amount = int(xp)
        if amount <= 0:
            return None

        user = User.query.get(int(user_id))
        if not user or is_pirate_user(user):
            return None

        st = str(source_type or "").strip().lower()
        sid = str(source_id or "").strip()
        if not st or not sid:
            return None

        existing = CommanderXPEvent.query.filter_by(user_id=user.id, source_type=st, source_id=sid).first()
        if existing:
            return AwardResult(
                applied=False,
                xp_awarded=int(existing.xp_awarded or 0),
                new_total_xp=int(getattr(user, "commander_xp", 0) or 0),
                new_level=int(getattr(user, "commander_level", 1) or 1),
            )

        evt = CommanderXPEvent(
            user_id=user.id,
            source_type=st,
            source_id=sid,
            xp_awarded=amount,
            created_at=now or datetime.utcnow(),
        )
        db.session.add(evt)

        total = int(getattr(user, "commander_xp", 0) or 0) + amount
        user.commander_xp = total
        user.commander_level = level_for_xp(total)

        return AwardResult(
            applied=True,
            xp_awarded=amount,
            new_total_xp=int(user.commander_xp or 0),
            new_level=int(user.commander_level or 1),
        )


def xp_from_resources(metal: int = 0, crystal: int = 0, deuterium: int = 0) -> int:
    total = max(0, int(metal or 0)) + max(0, int(crystal or 0)) + max(0, int(deuterium or 0))
    # MVP: 1 XP per 100 resources collected.
    return int(total // 100)


def xp_from_ship_losses(losses: dict[str, int] | None) -> int:
    """Compute XP from destroyed ship losses using the same simplified costs as debris."""
    if not losses:
        return 0
    ship_costs = {
        "small_cargo": {"metal": 2000, "crystal": 2000},
        "large_cargo": {"metal": 6000, "crystal": 6000},
        "light_fighter": {"metal": 3000, "crystal": 1000},
        "heavy_fighter": {"metal": 6000, "crystal": 4000},
        "cruiser": {"metal": 20000, "crystal": 7000},
        "battleship": {"metal": 45000, "crystal": 15000},
        "colony_ship": {"metal": 10000, "crystal": 20000},
    }
    value = 0
    for ship_type, count in (losses or {}).items():
        n = int(count or 0)
        if n <= 0:
            continue
        cost = ship_costs.get(ship_type)
        if not cost:
            continue
        value += n * (int(cost["metal"]) + int(cost["crystal"]))
    # MVP: 1 XP per 1,000 resources destroyed.
    return int(value // 1000)
