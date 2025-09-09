"""
Comprehensive Integration Tests for Attack → Combat → Colonization Workflow

Tests the complete player vs player workflow including:
- Attack mission execution
- Combat resolution with battle reports
- Debris field creation
- Colonization opportunity detection
- Colonization mission execution
- Ownership transfer and colony initialization

Uses advanced mocking patterns following existing test conventions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from backend.models import User, Planet, Fleet, CombatReport, DebrisField, Research
from backend.services.fleet_travel import FleetTravelService
from backend.services.combat_engine import CombatEngine
from backend.services.fleet_arrival import FleetArrivalService


class TestAttackCombatColonizationWorkflow:
    """Complete attack → combat → colonization workflow integration tests"""

    def setup_method(self, method):
        """Setup test data and mock services for each test"""
        self.attacker = None
        self.defender = None
        self.attacker_planet = None
        self.defender_planet = None
        self.attacker_fleet = None
        self.defender_fleet = None

    def teardown_method(self, method):
        """Clean up test data"""
        pass

    def _setup_test_users_and_planets(self, db_session):
        """Setup realistic test users and planets with proper transaction handling"""
        # Create attacker with proper bcrypt hashing
        import bcrypt
        attacker_password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.attacker = User(
            username='attacker_player',
            email='attacker@test.com',
            password_hash=attacker_password_hash
        )
        db_session.add(self.attacker)

        # Create defender with proper bcrypt hashing
        defender_password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.defender = User(
            username='defender_player',
            email='defender@test.com',
            password_hash=defender_password_hash
        )
        db_session.add(self.defender)

        # ✅ CRITICAL FIX: Commit users first to ensure IDs are generated
        db_session.commit()

        # Create planets with valid user_ids
        self.attacker_planet = Planet(
            name='Attacker Home',
            x=0, y=0, z=0,
            user_id=self.attacker.id,  # ✅ Now guaranteed to be valid
            metal=10000,
            crystal=5000,
            deuterium=2000
        )
        db_session.add(self.attacker_planet)

        self.defender_planet = Planet(
            name='Defender Colony',
            x=10, y=0, z=0,
            user_id=self.defender.id,  # ✅ Now guaranteed to be valid
            metal=8000,
            crystal=4000,
            deuterium=1500
        )
        db_session.add(self.defender_planet)

        # Create research for colonization after users are committed
        attacker_research = Research(
            user_id=self.attacker.id,  # ✅ Now definitely valid
            colonization_tech=5  # Level 5 allows colonization
        )
        db_session.add(attacker_research)

        db_session.commit()

    def _setup_combat_fleets(self, db_session):
        """Setup realistic combat fleets"""
        # Attacker fleet - strong offensive composition
        self.attacker_fleet = Fleet(
            user_id=self.attacker.id,
            mission='stationed',
            start_planet_id=self.attacker_planet.id,
            target_planet_id=self.attacker_planet.id,
            status='stationed',
            small_cargo=10,      # Resource transport
            light_fighter=50,    # Main attack force
            cruiser=20,          # Heavy hitters
            battleship=5,        # Elite units
            colony_ship=1,       # For later colonization
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow()
        )
        db_session.add(self.attacker_fleet)

        # Defender fleet - defensive composition
        self.defender_fleet = Fleet(
            user_id=self.defender.id,
            mission='stationed',
            start_planet_id=self.defender_planet.id,
            target_planet_id=self.defender_planet.id,
            status='stationed',
            light_fighter=30,    # Basic defense
            heavy_fighter=15,    # Medium defense
            cruiser=10,          # Heavy defense
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow()
        )
        db_session.add(self.defender_fleet)

        db_session.commit()

    def _mock_instant_travel(self):
        """Mock instant travel for testing"""
        def mock_travel_info(fleet):
            if hasattr(fleet, 'status') and fleet.status in ['traveling', 'returning']:
                # Mock instant arrival
                return {
                    'distance': 0,
                    'total_duration_hours': 0,
                    'progress_percentage': 100.0,
                    'current_position': '10.0:0.0:0.0',  # Defender planet
                    'fleet_speed': 5000,
                    'is_coordinate_based': False
                }
            return None

        return patch.object(FleetTravelService, 'calculate_travel_info', side_effect=mock_travel_info)

    def _mock_attacker_victory_combat(self):
        """Mock combat engine to return attacker victory"""
        def mock_combat_result(attacker_fleet, defender_fleet, defender_planet=None):
            return {
                'winner': 'attacker',
                'rounds': [
                    {
                        'attacker_fire': 2500,
                        'defender_fire': 1200,
                        'attacker_damage': 800,
                        'defender_damage': 400
                    }
                ],
                'attacker_losses': {
                    'light_fighter': 5,    # Minor losses
                    'cruiser': 1
                },
                'defender_losses': {
                    'light_fighter': 30,   # Total destruction
                    'heavy_fighter': 15,
                    'cruiser': 10
                },
                'debris': {
                    'metal': 2400,         # 30% of destroyed ships
                    'crystal': 1800,
                    'deuterium': 0
                }
            }

        return patch.object(CombatEngine, 'calculate_battle', side_effect=mock_combat_result)

    def _mock_fleet_arrival_processing(self):
        """Mock fleet arrival processing to trigger combat"""
        def mock_process_arrived_fleets():
            # Simulate what happens when fleet arrives
            if self.attacker_fleet and self.attacker_fleet.status == 'traveling':
                # Process attack arrival
                combat_result = CombatEngine.calculate_battle(
                    self.attacker_fleet,
                    self.defender_fleet,
                    self.defender_planet
                )

                # Create battle report
                battle_report = CombatReport(
                    attacker_id=self.attacker.id,
                    defender_id=self.defender.id,
                    planet_id=self.defender_planet.id,
                    winner_id=self.attacker.id,
                    rounds=str(combat_result['rounds']),
                    attacker_losses=str(combat_result['attacker_losses']),
                    defender_losses=str(combat_result['defender_losses']),
                    debris_metal=combat_result['debris']['metal'],
                    debris_crystal=combat_result['debris']['crystal']
                )

                # Create debris field
                debris = DebrisField(
                    planet_id=self.defender_planet.id,
                    metal=combat_result['debris']['metal'],
                    crystal=combat_result['debris']['crystal'],
                    created_at=datetime.utcnow()
                )

                # Update fleet status
                self.attacker_fleet.status = 'stationed'
                self.attacker_fleet.mission = 'stationed'

                # Destroy defender fleet (all ships lost)
                self.defender_fleet.small_cargo = 0
                self.defender_fleet.large_cargo = 0
                self.defender_fleet.light_fighter = 0
                self.defender_fleet.heavy_fighter = 0
                self.defender_fleet.cruiser = 0
                self.defender_fleet.battleship = 0
                self.defender_fleet.colony_ship = 0
                self.defender_fleet.recycler = 0

        return patch.object(FleetArrivalService, 'process_arrived_fleets', side_effect=mock_process_arrived_fleets)

    @patch('backend.services.tick.run_tick')
    def test_successful_attack_colonization_workflow(self, mock_tick, client, db_session):
        """Test complete attack → combat → colonization workflow"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)
        self._setup_combat_fleets(db_session)

        # Setup mocks
        with self._mock_instant_travel() as mock_travel, \
             self._mock_attacker_victory_combat() as mock_combat, \
             self._mock_fleet_arrival_processing() as mock_arrival:

            # === PHASE 1: ATTACK MISSION ===

            # Login as attacker
            login_response = client.post('/api/auth/login', json={
                'username': 'attacker_player',
                'password': 'password'
            })
            assert login_response.status_code == 200
            attacker_token = login_response.get_json()['access_token']

            # Send attack fleet
            attack_response = client.post('/api/fleet/send', headers={
                'Authorization': f'Bearer {attacker_token}'
            }, json={
                'fleet_id': self.attacker_fleet.id,
                'mission': 'attack',
                'target_planet_id': self.defender_planet.id
            })

            assert attack_response.status_code == 200
            attack_data = attack_response.get_json()
            assert 'fleet' in attack_data
            assert attack_data['fleet']['status'] == 'traveling'

            # Update fleet status to traveling
            self.attacker_fleet.status = 'traveling'
            self.attacker_fleet.target_planet_id = self.defender_planet.id
            db_session.commit()

            # === PHASE 2: COMBAT RESOLUTION ===

            # Trigger tick to process arrived fleet
            mock_tick()

            # Verify fleet arrival processing was called
            mock_arrival.assert_called_once()

            # Check battle report was created
            battle_reports = CombatReport.query.filter_by(
                attacker_id=self.attacker.id,
                defender_id=self.defender.id
            ).all()
            assert len(battle_reports) == 1

            report = battle_reports[0]
            assert report.winner_id == self.attacker.id
            assert report.debris_metal == 2400
            assert report.debris_crystal == 1800

            # Check debris field was created
            debris = DebrisField.query.filter_by(planet_id=self.defender_planet.id).first()
            assert debris is not None
            assert debris.metal == 2400
            assert debris.crystal == 1800

            # Check defender fleet was destroyed
            db_session.refresh(self.defender_fleet)
            total_defender_ships = (self.defender_fleet.small_cargo +
                                  self.defender_fleet.large_cargo +
                                  self.defender_fleet.light_fighter +
                                  self.defender_fleet.heavy_fighter +
                                  self.defender_fleet.cruiser +
                                  self.defender_fleet.battleship +
                                  self.defender_fleet.colony_ship +
                                  self.defender_fleet.recycler)
            assert total_defender_ships == 0  # All ships destroyed

            # === PHASE 3: COLONIZATION OPPORTUNITY ===

            # Check planet is now defenseless
            defenseless_response = client.get('/api/combat/colonization-opportunities', headers={
                'Authorization': f'Bearer {attacker_token}'
            })

            assert defenseless_response.status_code == 200
            opportunities = defenseless_response.get_json().get('opportunities', [])
            planet_ids = [opp['planet']['id'] for opp in opportunities]
            assert self.defender_planet.id in planet_ids

            # === PHASE 4: COLONIZATION MISSION ===

            # Send colonization fleet
            colonize_response = client.post('/api/fleet/send', headers={
                'Authorization': f'Bearer {attacker_token}'
            }, json={
                'fleet_id': self.attacker_fleet.id,
                'mission': 'colonize',
                'target_planet_id': self.defender_planet.id
            })

            assert colonize_response.status_code == 200
            colonize_data = colonize_response.get_json()
            assert 'fleet' in colonize_data
            assert 'colonizing' in colonize_data['fleet']['status']

            # Update fleet for colonization
            self.attacker_fleet.status = f'colonizing:{self.defender_planet.x}:{self.defender_planet.y}:{self.defender_planet.z}'
            self.attacker_fleet.target_coordinates = f'{self.defender_planet.x}:{self.defender_planet.y}:{self.defender_planet.z}'
            db_session.commit()

            # Trigger colonization processing (mock arrival)
            mock_tick()

            # Verify ownership transfer
            db_session.refresh(self.defender_planet)
            assert self.defender_planet.user_id == self.attacker.id

            # Verify colony initialization
            assert self.defender_planet.metal == 1000  # Starting resources
            assert self.defender_planet.crystal == 500
            assert self.defender_planet.deuterium == 0

            # Verify attacker now owns both planets
            attacker_planets = Planet.query.filter_by(user_id=self.attacker.id).all()
            assert len(attacker_planets) == 2
            planet_names = [p.name for p in attacker_planets]
            assert 'Attacker Home' in planet_names
            assert 'Defender Colony' in planet_names

    @patch('backend.services.tick.run_tick')
    def test_failed_attack_no_colonization(self, mock_tick, client, db_session):
        """Test that defender victory prevents colonization"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)
        self._setup_combat_fleets(db_session)

        # Mock defender victory
        def mock_defender_victory(attacker_fleet, defender_fleet, defender_planet=None):
            return {
                'winner': 'defender',
                'rounds': [{'attacker_fire': 1000, 'defender_fire': 1500}],
                'attacker_losses': {'light_fighter': 50, 'cruiser': 20},  # Heavy losses
                'defender_losses': {'light_fighter': 5},  # Minor losses
                'debris': {'metal': 1200, 'crystal': 800}
            }

        with self._mock_instant_travel(), \
             patch.object(CombatEngine, 'calculate_battle', side_effect=mock_defender_victory), \
             self._mock_fleet_arrival_processing():

            # Login as attacker
            login_response = client.post('/api/auth/login', json={
                'username': 'attacker_player',
                'password': 'password'
            })
            attacker_token = login_response.get_json()['access_token']

            # Send attack fleet
            attack_response = client.post('/api/fleet/send', headers={
                'Authorization': f'Bearer {attacker_token}'
            }, json={
                'fleet_id': self.attacker_fleet.id,
                'mission': 'attack',
                'target_planet_id': self.defender_planet.id
            })
            assert attack_response.status_code == 200

            # Update fleet status
            self.attacker_fleet.status = 'traveling'
            db_session.commit()

            # Process combat
            mock_tick()

            # Verify defender victory
            battle_reports = CombatReport.query.filter_by(attacker_id=self.attacker.id).all()
            assert len(battle_reports) == 1
            assert battle_reports[0].winner_id == self.defender.id

            # Verify planet is NOT available for colonization
            opportunities_response = client.get('/api/combat/colonization-opportunities', headers={
                'Authorization': f'Bearer {attacker_token}'
            })
            opportunities = opportunities_response.get_json().get('opportunities', [])
            planet_ids = [opp['planet']['id'] for opp in opportunities]
            assert self.defender_planet.id not in planet_ids

            # Verify ownership unchanged
            db_session.refresh(self.defender_planet)
            assert self.defender_planet.user_id == self.defender.id

    def test_colonization_insufficient_colony_ships(self, client, db_session):
        """Test colonization fails without colony ships"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)

        # Create fleet without colony ships
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            self.attacker.id,
            self.attacker_planet.id,
            light_fighter=10,  # No colony ship
            mission='stationed',
            status='stationed'
        )

        # Login and attempt colonization
        login_response = client.post('/api/auth/login', json={
            'username': 'attacker_player',
            'password': 'password'
        })
        token = login_response.get_json()['access_token']

        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 100,
            'target_y': 200,
            'target_z': 300
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'colony ship' in data['error'].lower()

    def test_colonization_occupied_coordinates(self, client, db_session):
        """Test colonization fails on occupied coordinates"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)

        # Create fleet with colony ship
        from tests.conftest import create_test_fleet_with_constraints
        fleet = create_test_fleet_with_constraints(
            db_session,
            self.attacker.id,
            self.attacker_planet.id,
            colony_ship=1,
            mission='stationed',
            status='stationed'
        )

        # Login and attempt colonization on occupied coordinates
        login_response = client.post('/api/auth/login', json={
            'username': 'attacker_player',
            'password': 'password'
        })
        token = login_response.get_json()['access_token']

        response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': fleet.id,
            'mission': 'colonize',
            'target_x': 0,  # Attacker's home planet coordinates
            'target_y': 0,
            'target_z': 0
        })

        assert response.status_code == 409
        data = response.get_json()
        assert 'occupied' in data['error'].lower()

    @patch('backend.services.tick.run_tick')
    def test_multiple_attackers_race_condition(self, mock_tick, client, db_session):
        """Test colonization race condition with multiple attackers"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)
        self._setup_combat_fleets(db_session)

        # Create second attacker with proper bcrypt hashing
        import bcrypt
        attacker2_password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        attacker2 = User(
            username='attacker2_player',
            email='attacker2@test.com',
            password_hash=attacker2_password_hash
        )
        db_session.add(attacker2)

        from tests.conftest import create_test_fleet_with_constraints
        attacker2_fleet = create_test_fleet_with_constraints(
            db_session,
            attacker2.id,
            self.attacker_planet.id,  # Same start planet for simplicity
            colony_ship=1,
            light_fighter=20,
            mission='stationed',
            status='stationed'
        )

        with self._mock_instant_travel(), \
             self._mock_attacker_victory_combat(), \
             self._mock_fleet_arrival_processing():

            # First attacker sends colonization fleet
            login1_response = client.post('/api/auth/login', json={
                'username': 'attacker_player',
                'password': 'password'
            })
            token1 = login1_response.get_json()['access_token']

            colonize1_response = client.post('/api/fleet/send', headers={
                'Authorization': f'Bearer {token1}'
            }, json={
                'fleet_id': self.attacker_fleet.id,
                'mission': 'colonize',
                'target_planet_id': self.defender_planet.id
            })
            assert colonize1_response.status_code == 200

            # Second attacker tries to colonize same planet
            login2_response = client.post('/api/auth/login', json={
                'username': 'attacker2_player',
                'password': 'password'
            })
            token2 = login2_response.get_json()['access_token']

            colonize2_response = client.post('/api/fleet/send', headers={
                'Authorization': f'Bearer {token2}'
            }, json={
                'fleet_id': attacker2_fleet.id,
                'mission': 'colonize',
                'target_planet_id': self.defender_planet.id
            })

            # Should fail because planet is already being colonized
            assert colonize2_response.status_code == 409
            data = colonize2_response.get_json()
            assert 'already colonized' in data['error'].lower()

    def test_combat_report_detailed_structure(self, client, db_session):
        """Test that battle reports contain all required detailed information"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)
        self._setup_combat_fleets(db_session)

        # Create a battle report manually for testing
        battle_report = CombatReport(
            attacker_id=self.attacker.id,
            defender_id=self.defender.id,
            planet_id=self.defender_planet.id,
            winner_id=self.attacker.id,
            rounds='[{"attacker_fire": 2500, "defender_fire": 1200, "attacker_damage": 800, "defender_damage": 400}]',
            attacker_losses='{"light_fighter": 5, "cruiser": 1}',
            defender_losses='{"light_fighter": 30, "heavy_fighter": 15, "cruiser": 10}',
            debris_metal=2400,
            debris_crystal=1800,
            timestamp=datetime.utcnow()
        )
        db_session.add(battle_report)
        db_session.commit()

        # Login and get battle reports
        login_response = client.post('/api/auth/login', json={
            'username': 'attacker_player',
            'password': 'password'
        })
        token = login_response.get_json()['access_token']

        response = client.get('/api/combat/reports', headers={
            'Authorization': f'Bearer {token}'
        })

        assert response.status_code == 200
        data = response.get_json()

        # Verify response structure
        assert 'reports' in data
        assert len(data['reports']) == 1

        report = data['reports'][0]
        assert 'id' in report
        assert 'timestamp' in report
        assert 'attacker' in report
        assert 'defender' in report
        assert 'planet' in report
        assert 'winner' in report
        assert 'rounds' in report
        assert 'attacker_losses' in report
        assert 'defender_losses' in report
        assert 'debris_metal' in report
        assert 'debris_crystal' in report

        # Verify attacker/defender/winner have correct structure
        assert 'id' in report['attacker']
        assert 'username' in report['attacker']
        assert 'id' in report['defender']
        assert 'username' in report['defender']
        assert 'id' in report['winner']
        assert 'username' in report['winner']

        # Verify planet information
        assert 'id' in report['planet']
        assert 'name' in report['planet']
        assert 'coordinates' in report['planet']

    def test_fleet_status_updates_during_workflow(self, client, db_session):
        """Test that fleet status updates correctly throughout the workflow"""
        # Setup test data
        self._setup_test_users_and_planets(db_session)
        self._setup_combat_fleets(db_session)

        # Login
        login_response = client.post('/api/auth/login', json={
            'username': 'attacker_player',
            'password': 'password'
        })
        token = login_response.get_json()['token']

        # Initial status check
        fleet_response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })
        initial_fleets = fleet_response.get_json()
        attacker_fleet_data = next(f for f in initial_fleets if f['id'] == self.attacker_fleet.id)
        assert attacker_fleet_data['status'] == 'stationed'
        assert attacker_fleet_data['mission'] == 'stationed'

        # Send attack fleet
        attack_response = client.post('/api/fleet/send', headers={
            'Authorization': f'Bearer {token}'
        }, json={
            'fleet_id': self.attacker_fleet.id,
            'mission': 'attack',
            'target_planet_id': self.defender_planet.id
        })
        assert attack_response.status_code == 200

        # Status should be traveling
        fleet_response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })
        updated_fleets = fleet_response.get_json()
        attacker_fleet_data = next(f for f in updated_fleets if f['id'] == self.attacker_fleet.id)
        assert attacker_fleet_data['status'] == 'traveling'
        assert attacker_fleet_data['mission'] == 'attack'

        # After combat (simulated)
        self.attacker_fleet.status = 'stationed'
        self.attacker_fleet.mission = 'stationed'
        db_session.commit()

        # Status should be back to stationed
        fleet_response = client.get('/api/fleet', headers={
            'Authorization': f'Bearer {token}'
        })
        final_fleets = fleet_response.get_json()
        attacker_fleet_data = next(f for f in final_fleets if f['id'] == self.attacker_fleet.id)
        assert attacker_fleet_data['status'] == 'stationed'
        assert attacker_fleet_data['mission'] == 'stationed'
