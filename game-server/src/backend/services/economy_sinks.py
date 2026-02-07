"""Economy sink helpers (fleet upkeep lite)."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable


# Relative upkeep weights by ship class (lightweight pacing pressure).
FLEET_UPKEEP_WEIGHTS = {
    "small_cargo": 1,
    "large_cargo": 1,
    "light_fighter": 1,
    "heavy_fighter": 2,
    "cruiser": 4,
    "battleship": 6,
    "colony_ship": 5,
    "recycler": 2,
    "espionage_probe": 1,
    "bomber": 7,
    "destroyer": 9,
    "deathstar": 20,
    "battlecruiser": 8,
}


def economy_sinks_enabled(config: dict) -> bool:
    return bool(config.get("ECONOMY_SINKS_ENABLED", False))


def fleet_upkeep_deuterium_per_tick(fleet, config: dict) -> int:
    """Return deterministic upkeep cost per tick for a single fleet."""
    if not economy_sinks_enabled(config):
        return 0

    if bool(config.get("FLEET_UPKEEP_EXCLUDE_INVENTORY", True)) and str(getattr(fleet, "mission", "")) == "inventory":
        return 0

    try:
        rate = float(config.get("FLEET_UPKEEP_DEUTERIUM_PER_WEIGHT_PER_TICK", 0.001))
    except (TypeError, ValueError):
        rate = 0.001

    if rate <= 0:
        return 0

    weighted_ships = 0
    for ship_key, weight in FLEET_UPKEEP_WEIGHTS.items():
        count = int(getattr(fleet, ship_key, 0) or 0)
        if count <= 0:
            continue
        weighted_ships += count * weight

    if weighted_ships <= 0:
        return 0

    return max(0, int(math.floor(weighted_ships * rate)))


def fleet_upkeep_deuterium_per_hour(fleet, config: dict) -> int:
    return fleet_upkeep_deuterium_per_tick(fleet, config) * 72


def upkeep_by_start_planet_per_tick(fleets: Iterable, config: dict) -> dict[int, int]:
    """Aggregate upkeep by `start_planet_id` for efficient tick processing."""
    totals = defaultdict(int)
    for fleet in fleets:
        planet_id = getattr(fleet, "start_planet_id", None)
        if planet_id is None:
            continue
        upkeep = fleet_upkeep_deuterium_per_tick(fleet, config)
        if upkeep <= 0:
            continue
        totals[int(planet_id)] += int(upkeep)
    return dict(totals)
