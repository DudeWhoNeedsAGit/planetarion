import os

import pytest


SCENARIOS = [
    "pirate-pressure",
    "debris-rich",
    "colonization-race",
    "returning-fleets-stress",
]


def _auth_headers():
    os.environ["PLANETARION_DEV_ADMIN_TOKEN"] = "test-token"
    return {"X-Planetarion-Dev-Token": "test-token"}


def _reset(client, scenario: str):
    response = client.post(
        f"/api/admin/scenarios/{scenario}/reset",
        json={"password": "testpassword123"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


def _assert_contract(data, expected_scenario: str):
    assert data["ok"] is True
    assert data["contract_version"] == "scenario-pack.v1"
    assert data["scenario"]["id"] == expected_scenario
    assert data["scenario"]["deterministic"] is True

    entities = data["entities"]
    assert isinstance(entities["users"], list)
    assert isinstance(entities["planets"], list)
    assert isinstance(entities["fleets"], list)
    assert isinstance(entities["debris_fields"], list)

    assert data["counts"]["users"] == len(entities["users"])
    assert data["counts"]["planets"] == len(entities["planets"])
    assert data["counts"]["fleets"] == len(entities["fleets"])
    assert data["counts"]["debris_fields"] == len(entities["debris_fields"])

    user_keys = [entry["key"] for entry in entities["users"]]
    planet_keys = [entry["key"] for entry in entities["planets"]]
    fleet_keys = [entry["key"] for entry in entities["fleets"]]
    assert user_keys == sorted(user_keys)
    assert planet_keys == sorted(planet_keys)
    assert fleet_keys == sorted(fleet_keys)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_named_scenario_pack_reset_contract(client, scenario):
    payload = _reset(client, scenario)
    _assert_contract(payload, scenario)


def test_named_scenario_pack_response_is_deterministic(client):
    first = _reset(client, "debris-rich")
    second = _reset(client, "debris-rich")

    assert first["scenario"] == second["scenario"]
    assert first["counts"] == second["counts"]
    assert first["entities"] == second["entities"]
    assert first["snapshot"] == {
        "write_requested": False,
        "written": False,
    }


def test_legacy_two_player_endpoint_keeps_compatibility_and_contract(client):
    response = client.post(
        "/api/admin/scenarios/two-player/reset",
        json={"password": "testpassword123"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    data = response.get_json()

    _assert_contract(data, "two-player")

    assert data["users"]["alpha"]["username"] == "alpha"
    assert data["users"]["beta"]["username"] == "beta"
    assert data["users"]["pirates"]["username"] == "pirates"
    assert "alpha_fleet_id" in data["fleets"]
    assert "beta_fleet_id" in data["fleets"]
    assert "pirate_defense_fleet_id" in data["fleets"]

