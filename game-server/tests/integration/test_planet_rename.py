import pytest


def _login(client, username="testuser", password="testpassword"):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.get_json()
    data = res.get_json()
    return data["token"]


def test_planet_can_be_renamed_once(client, sample_planet):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # First rename works.
    res = client.put(
        "/api/planet/rename",
        json={"planet_id": sample_planet.id, "new_name": "New Terra"},
        headers=headers,
    )
    assert res.status_code == 200, res.get_json()
    payload = res.get_json()
    assert payload["planet"]["name"] == "New Terra"

    # Second rename is rejected.
    res2 = client.put(
        "/api/planet/rename",
        json={"planet_id": sample_planet.id, "new_name": "Another Name"},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "already" in (res2.get_json().get("error") or "").lower()


def test_tick_logs_hide_empty_resource_rows_by_default(client, sample_planet):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a rename event (which writes a TickLog with event_type).
    res = client.put(
        "/api/planet/rename",
        json={"planet_id": sample_planet.id, "new_name": "Renamed Once"},
        headers=headers,
    )
    assert res.status_code == 200

    logs_res = client.get("/api/tick/logs?limit=25&offset=0", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.get_json().get("logs", [])
    assert any((l.get("event_type") == "planet_rename") for l in logs)

