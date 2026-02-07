from tests.conftest import make_auth_headers


def _planet_ship_totals(fleets, planet_id):
    totals = {}
    for fleet in fleets:
        if fleet.get('start_planet_id') != planet_id:
            continue
        if fleet.get('status') != 'stationed':
            continue
        for ship_type, amount in (fleet.get('ships') or {}).items():
            totals[ship_type] = totals.get(ship_type, 0) + int(amount or 0)
    return totals


class TestFleetRebalanceAPI:
    def test_split_creates_new_stationed_fleet_with_requested_ships(self, client, sample_user, sample_planet):
        headers = make_auth_headers(sample_user.id)

        create_resp = client.post(
            '/api/fleet',
            json={'start_planet_id': sample_planet.id, 'ships': {'small_cargo': 50, 'light_fighter': 20}},
            headers=headers,
        )
        assert create_resp.status_code == 201
        source_fleet_id = create_resp.get_json()['fleet']['id']

        split_resp = client.post(
            f'/api/fleet/{source_fleet_id}/split',
            json={'ships': {'small_cargo': 15, 'light_fighter': 5}},
            headers=headers,
        )
        assert split_resp.status_code == 200
        payload = split_resp.get_json()

        source = payload['source_fleet']
        created = payload['new_fleet']
        assert source['id'] == source_fleet_id
        assert created['id'] != source_fleet_id
        assert created['status'] == 'stationed'
        assert created['mission'] == 'stationed'
        assert created['start_planet_id'] == sample_planet.id
        assert created['ships']['small_cargo'] == 15
        assert created['ships']['light_fighter'] == 5
        assert source['ships']['small_cargo'] == 35
        assert source['ships']['light_fighter'] == 15

    def test_transfer_moves_ships_between_same_planet_stationed_fleets(self, client, sample_user, sample_planet):
        headers = make_auth_headers(sample_user.id)

        source_resp = client.post(
            '/api/fleet',
            json={'start_planet_id': sample_planet.id, 'ships': {'small_cargo': 30, 'light_fighter': 12}},
            headers=headers,
        )
        assert source_resp.status_code == 201
        source_fleet_id = source_resp.get_json()['fleet']['id']

        target_resp = client.post(
            '/api/fleet',
            json={'start_planet_id': sample_planet.id, 'ships': {'small_cargo': 5, 'light_fighter': 1}},
            headers=headers,
        )
        assert target_resp.status_code == 201
        target_fleet_id = target_resp.get_json()['fleet']['id']

        transfer_resp = client.post(
            f'/api/fleet/{source_fleet_id}/transfer',
            json={'target_fleet_id': target_fleet_id, 'ships': {'small_cargo': 7, 'light_fighter': 2}},
            headers=headers,
        )
        assert transfer_resp.status_code == 200
        transfer_data = transfer_resp.get_json()
        assert transfer_data['source_fleet']['ships']['small_cargo'] == 23
        assert transfer_data['source_fleet']['ships']['light_fighter'] == 10
        assert transfer_data['target_fleet']['ships']['small_cargo'] == 12
        assert transfer_data['target_fleet']['ships']['light_fighter'] == 3

    def test_repeated_rebalance_operations_preserve_ship_conservation(self, client, sample_user, sample_planet):
        headers = make_auth_headers(sample_user.id)

        seed_resp = client.post(
            '/api/fleet',
            json={
                'start_planet_id': sample_planet.id,
                'ships': {'small_cargo': 80, 'light_fighter': 40},
            },
            headers=headers,
        )
        assert seed_resp.status_code == 201
        fleet_a_id = seed_resp.get_json()['fleet']['id']

        initial_fleets = client.get('/api/fleet?include_inventory=1', headers=headers).get_json()
        baseline_totals = _planet_ship_totals(initial_fleets, sample_planet.id)

        split_resp = client.post(
            f'/api/fleet/{fleet_a_id}/split',
            json={'ships': {'small_cargo': 30, 'light_fighter': 10}},
            headers=headers,
        )
        assert split_resp.status_code == 200
        fleet_b_id = split_resp.get_json()['new_fleet']['id']

        transfer_one = client.post(
            f'/api/fleet/{fleet_b_id}/transfer',
            json={'target_fleet_id': fleet_a_id, 'ships': {'small_cargo': 5}},
            headers=headers,
        )
        assert transfer_one.status_code == 200

        inventory_fleet = next(
            (f for f in client.get('/api/fleet?include_inventory=1', headers=headers).get_json() if f.get('mission') == 'inventory'),
            None,
        )
        assert inventory_fleet is not None

        transfer_two = client.post(
            f'/api/fleet/{fleet_a_id}/transfer',
            json={'target_fleet_id': inventory_fleet['id'], 'ships': {'small_cargo': 7, 'light_fighter': 4}},
            headers=headers,
        )
        assert transfer_two.status_code == 200

        transfer_three = client.post(
            f'/api/fleet/{inventory_fleet["id"]}/transfer',
            json={'target_fleet_id': fleet_b_id, 'ships': {'small_cargo': 3, 'light_fighter': 1}},
            headers=headers,
        )
        assert transfer_three.status_code == 200

        final_fleets = client.get('/api/fleet?include_inventory=1', headers=headers).get_json()
        final_totals = _planet_ship_totals(final_fleets, sample_planet.id)

        assert final_totals == baseline_totals
