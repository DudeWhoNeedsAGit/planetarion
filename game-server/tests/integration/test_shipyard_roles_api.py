def test_shipyard_roles_endpoint_returns_roles(client):
    res = client.get("/api/shipyard/roles")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert "roles" in data
    assert "ships_by_role" in data
    assert isinstance(data["roles"], list)
    assert isinstance(data["ships_by_role"], dict)

    # For each role returned, ensure ships_by_role includes a list.
    for role in data["roles"]:
        assert role in data["ships_by_role"]
        assert isinstance(data["ships_by_role"][role], (list, dict))
