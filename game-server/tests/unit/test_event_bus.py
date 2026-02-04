from backend.services.event_bus import EventMessage, event_bus


def test_event_bus_publish_and_receive():
    q = event_bus.subscribe(123)
    try:
        msg = EventMessage(event="activity", data={"id": 1, "event_type": "fleet_sent"}, id=1)
        event_bus.publish(123, msg)
        received = q.get(timeout=1)
        assert received.event == "activity"
        assert received.id == 1
        assert received.data["event_type"] == "fleet_sent"
    finally:
        event_bus.unsubscribe(123, q)

