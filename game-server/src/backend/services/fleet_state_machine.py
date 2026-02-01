"""
Fleet State Machine

Centralizes:
- Allowed fleet statuses (including coordinate-encoded statuses)
- Legal transitions for API endpoints and tick/arrival processing
- Helpers to parse/format coordinate-based statuses

Goal: prevent "vibe-coded" drift where different modules invent their own rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from backend.config import get_min_travel_time_seconds
from enum import Enum
from typing import Optional, Tuple


class FleetStatusKind(str, Enum):
    STATIONED = "stationed"
    TRAVELING = "traveling"
    RETURNING = "returning"
    DEFENDING = "defending"
    EXPLORING = "exploring"
    COLONIZING = "colonizing"


class FleetMission(str, Enum):
    STATIONED = "stationed"
    RETURN = "return"
    ATTACK = "attack"
    DEFEND = "defend"
    RECYCLE = "recycle"
    EXPLORE = "explore"
    COLONIZE = "colonize"
    TRANSPORT = "transport"
    DEPLOY = "deploy"
    ESPIONAGE = "espionage"


class FleetStateError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedCoordinateStatus:
    kind: FleetStatusKind
    x: int
    y: int
    z: int


def get_status_kind(status: Optional[str]) -> FleetStatusKind:
    if not status:
        return FleetStatusKind.STATIONED

    if status.startswith("exploring:"):
        return FleetStatusKind.EXPLORING
    if status.startswith("colonizing:"):
        return FleetStatusKind.COLONIZING

    try:
        return FleetStatusKind(status)
    except ValueError as e:
        raise FleetStateError(f"Unknown fleet status: {status}") from e


def parse_coordinate_status(status: str) -> ParsedCoordinateStatus:
    kind = get_status_kind(status)
    if kind not in (FleetStatusKind.EXPLORING, FleetStatusKind.COLONIZING):
        raise FleetStateError(f"Status is not coordinate-based: {status}")

    parts = status.split(":")
    if len(parts) != 4:
        raise FleetStateError(f"Malformed coordinate status: {status}")

    try:
        x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError as e:
        raise FleetStateError(f"Invalid coordinates in status: {status}") from e

    return ParsedCoordinateStatus(kind=kind, x=x, y=y, z=z)


def format_coordinate_status(kind: FleetStatusKind, coords: Tuple[int, int, int]) -> str:
    if kind not in (FleetStatusKind.EXPLORING, FleetStatusKind.COLONIZING):
        raise FleetStateError(f"Only exploring/colonizing may be coordinate-based (got {kind})")
    x, y, z = coords
    return f"{kind.value}:{int(x)}:{int(y)}:{int(z)}"


class FleetStateMachine:
    """
    Fleet status/mission mutations should go through this class.

    Note: This repo currently stores some coordinate-based missions directly in `Fleet.status`.
    This state machine supports that, but encourages also populating `Fleet.target_coordinates`.
    """

    MIN_TRAVEL_TIME_SECONDS = get_min_travel_time_seconds()

    @staticmethod
    def ensure_can_send(fleet, mission: str) -> None:
        status_kind = get_status_kind(getattr(fleet, "status", None))
        if status_kind != FleetStatusKind.STATIONED:
            raise FleetStateError("Fleet is not available for sending")
        if not mission:
            raise FleetStateError("Missing mission")

    @staticmethod
    def ensure_can_recall(fleet) -> None:
        status_kind = get_status_kind(getattr(fleet, "status", None))
        if status_kind in (FleetStatusKind.TRAVELING, FleetStatusKind.RETURNING, FleetStatusKind.EXPLORING, FleetStatusKind.COLONIZING):
            return
        raise FleetStateError("Fleet cannot be recalled")

    @staticmethod
    def set_stationed(fleet, *, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        fleet.status = FleetStatusKind.STATIONED.value
        fleet.mission = FleetMission.STATIONED.value
        # When a fleet is stationary, treat its "target" as its current location.
        # This prevents UI "To: N/A" issues and makes the fleet location unambiguous.
        if getattr(fleet, "start_planet_id", None):
            fleet.target_planet_id = fleet.start_planet_id
        fleet.arrival_time = now
        if not getattr(fleet, "departure_time", None):
            fleet.departure_time = now
        fleet.eta = 0

    @staticmethod
    def set_sent_traveling(
        fleet,
        *,
        mission: str,
        departure_time: datetime,
        arrival_time: datetime,
        eta_seconds: int,
        target_planet_id: Optional[int] = None,
    ) -> None:
        fleet.mission = mission
        if target_planet_id is not None:
            fleet.target_planet_id = target_planet_id
        fleet.status = FleetStatusKind.TRAVELING.value
        fleet.departure_time = departure_time
        fleet.arrival_time = arrival_time
        fleet.eta = int(eta_seconds)

    @staticmethod
    def set_sent_defending(fleet, *, target_planet_id: int) -> None:
        fleet.mission = FleetMission.DEFEND.value
        fleet.target_planet_id = target_planet_id
        fleet.status = FleetStatusKind.DEFENDING.value

    @staticmethod
    def set_sent_exploring(
        fleet,
        *,
        coords: Tuple[int, int, int],
        departure_time: datetime,
        arrival_time: datetime,
        eta_seconds: int,
    ) -> None:
        fleet.mission = FleetMission.EXPLORE.value
        fleet.target_planet_id = 0
        fleet.target_coordinates = f"{coords[0]}:{coords[1]}:{coords[2]}"
        fleet.status = format_coordinate_status(FleetStatusKind.EXPLORING, coords)
        fleet.departure_time = departure_time
        fleet.arrival_time = arrival_time
        fleet.eta = int(eta_seconds)

    @staticmethod
    def set_sent_colonizing(
        fleet,
        *,
        coords: Tuple[int, int, int],
        target_planet_id: int,
        departure_time: datetime,
        arrival_time: datetime,
        eta_seconds: int,
    ) -> None:
        fleet.mission = FleetMission.COLONIZE.value
        fleet.target_planet_id = target_planet_id
        fleet.target_coordinates = f"{coords[0]}:{coords[1]}:{coords[2]}"
        fleet.status = format_coordinate_status(FleetStatusKind.COLONIZING, coords)
        fleet.departure_time = departure_time
        fleet.arrival_time = arrival_time
        fleet.eta = int(eta_seconds)

    @staticmethod
    def set_returning(fleet, *, now: Optional[datetime] = None, return_time_seconds: Optional[float] = None) -> None:
        now = now or datetime.utcnow()
        return_time_seconds = float(return_time_seconds or 0)
        return_time_seconds = max(FleetStateMachine.MIN_TRAVEL_TIME_SECONDS, return_time_seconds)

        fleet.status = FleetStatusKind.RETURNING.value
        fleet.mission = FleetMission.RETURN.value
        fleet.departure_time = now
        fleet.arrival_time = now + timedelta(seconds=return_time_seconds)
        fleet.eta = int(return_time_seconds)
