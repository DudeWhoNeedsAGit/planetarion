from datetime import datetime, timedelta

import pytest

from backend.services.fleet_state_machine import (
    FleetStateMachine,
    FleetStateError,
    FleetStatusKind,
    format_coordinate_status,
    get_status_kind,
    parse_coordinate_status,
)


class DummyFleet:
    def __init__(self):
        self.status = "stationed"
        self.mission = "stationed"
        self.departure_time = datetime.utcnow()
        self.arrival_time = datetime.utcnow()
        self.eta = 0
        self.target_planet_id = 1
        self.target_coordinates = None


def test_get_status_kind_enum():
    assert get_status_kind("stationed") == FleetStatusKind.STATIONED
    assert get_status_kind("traveling") == FleetStatusKind.TRAVELING
    assert get_status_kind("returning") == FleetStatusKind.RETURNING


def test_get_status_kind_coordinate_prefixes():
    assert get_status_kind("exploring:1:2:3") == FleetStatusKind.EXPLORING
    assert get_status_kind("colonizing:4:5:6") == FleetStatusKind.COLONIZING


def test_parse_coordinate_status_roundtrip():
    status = format_coordinate_status(FleetStatusKind.EXPLORING, (10, 20, 30))
    parsed = parse_coordinate_status(status)
    assert parsed.kind == FleetStatusKind.EXPLORING
    assert (parsed.x, parsed.y, parsed.z) == (10, 20, 30)


def test_parse_coordinate_status_rejects_non_coordinate():
    with pytest.raises(FleetStateError):
        parse_coordinate_status("traveling")


def test_ensure_can_send_only_stationed():
    fleet = DummyFleet()
    FleetStateMachine.ensure_can_send(fleet, "attack")

    fleet.status = "traveling"
    with pytest.raises(FleetStateError):
        FleetStateMachine.ensure_can_send(fleet, "attack")


def test_ensure_can_recall_allows_coordinate_statuses():
    fleet = DummyFleet()
    fleet.status = "colonizing:1:2:3"
    FleetStateMachine.ensure_can_recall(fleet)


def test_set_returning_enforces_min_time():
    fleet = DummyFleet()
    now = datetime.utcnow()
    FleetStateMachine.set_returning(fleet, now=now, return_time_seconds=0)
    assert fleet.status == "returning"
    assert fleet.mission == "return"
    assert fleet.eta == FleetStateMachine.MIN_TRAVEL_TIME_SECONDS
    assert fleet.arrival_time >= now + timedelta(seconds=FleetStateMachine.MIN_TRAVEL_TIME_SECONDS)

