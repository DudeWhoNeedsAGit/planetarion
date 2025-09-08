"""
Unit tests for Combat Engine

Tests the core combat calculation logic including:
- Fleet vs Fleet battles
- Ship combat statistics
- Rapid fire mechanics
- Shield absorption
- Hull damage calculation
- Debris field generation
"""

import pytest
from unittest.mock import Mock, patch
from backend.services.combat_engine import CombatEngine
from backend.models import Fleet, Planet, User


class TestCombatEngine:
    """Test suite for CombatEngine class"""

    def test_ship_stats_structure(self):
        """Test that ship stats are properly defined"""
        assert 'small_cargo' in CombatEngine.SHIP_STATS
        assert 'light_fighter' in CombatEngine.SHIP_STATS
        assert 'battleship' in CombatEngine.SHIP_STATS

        # Check required fields
        small_cargo = CombatEngine.SHIP_STATS['small_cargo']
        assert 'hull' in small_cargo
        assert 'shield' in small_cargo
        assert 'weapon' in small_cargo
        assert 'speed' in small_cargo
        assert 'cargo' in small_cargo
        assert 'fuel' in small_cargo

    def test_rapid_fire_structure(self):
        """Test that rapid fire bonuses are properly defined"""
        assert 'light_fighter' in CombatEngine.RAPID_FIRE
        assert 'cruiser' in CombatEngine.RAPID_FIRE

        # Check rapid fire values
        lf_rapid_fire = CombatEngine.RAPID_FIRE['light_fighter']
        assert 'heavy_fighter' in lf_rapid_fire
        assert lf_rapid_fire['heavy_fighter'] == 2

    @patch('backend.services.combat_engine.CombatEngine._fleet_to_combat_ships')
    @patch('backend.services.combat_engine.CombatEngine._calculate_round')
    @patch('backend.services.combat_engine.CombatEngine._calculate_losses')
    def test_calculate_battle_basic_flow(self, mock_calculate_losses, mock_calculate_round, mock_fleet_to_ships):
        """Test basic battle calculation flow"""
        # Setup mocks
        mock_fleet_to_ships.return_value = {
            'light_fighter': {'count': 10, 'hull': 4000, 'shield': 10, 'weapon': 50}
        }
        mock_calculate_round.return_value = {
            'attacker_fire': 500,
            'defender_fire': 300,
            'attacker_damage': 400,
            'defender_damage': 200
        }
        mock_calculate_losses.return_value = {'light_fighter': 2}

        # Create mock fleets without spec to avoid Flask context issues
        attacker_fleet = Mock()
        defender_fleet = Mock()

        # Configure ship attributes to return integers
        attacker_fleet.small_cargo = 5
        attacker_fleet.light_fighter = 10
        attacker_fleet.cruiser = 0
        attacker_fleet.battleship = 0
        attacker_fleet.colony_ship = 0
        attacker_fleet.heavy_fighter = 0
        attacker_fleet.recycler = 0

        defender_fleet.small_cargo = 0
        defender_fleet.light_fighter = 8
        defender_fleet.cruiser = 0
        defender_fleet.battleship = 0
        defender_fleet.colony_ship = 0
        defender_fleet.heavy_fighter = 0
        defender_fleet.recycler = 0

        # Execute battle
        result = CombatEngine.calculate_battle(attacker_fleet, defender_fleet)

        # Verify result structure
        assert 'winner' in result
        assert 'rounds' in result
        assert 'attacker_losses' in result
        assert 'defender_losses' in result
        assert 'debris' in result

        # Verify mocks were called (called multiple times due to internal logic)
        assert mock_fleet_to_ships.call_count >= 2
        assert mock_calculate_round.call_count >= 1  # Battle runs rounds until completion
        assert mock_calculate_losses.call_count >= 2

    def test_fleet_to_combat_ships_conversion(self):
        """Test conversion of fleet to combat-ready ship dictionary"""
        # Create a simple class to avoid Mock arithmetic issues
        class MockFleet:
            def __init__(self):
                self.small_cargo = 5
                self.light_fighter = 10
                self.cruiser = 0  # Zero ships should be excluded
                self.battleship = 3
                self.colony_ship = 0
                self.heavy_fighter = 0
                self.recycler = 0

        fleet = MockFleet()

        result = CombatEngine._fleet_to_combat_ships(fleet)

        # Check that ships with count > 0 are included
        assert 'small_cargo' in result
        assert 'light_fighter' in result
        assert 'battleship' in result
        assert 'cruiser' not in result  # Zero count excluded

        # Check ship data structure
        assert result['small_cargo']['count'] == 5
        assert 'hull' in result['small_cargo']
        assert 'shield' in result['small_cargo']
        assert 'weapon' in result['small_cargo']

    def test_calculate_firepower_basic(self):
        """Test basic firepower calculation"""
        attacker_ships = {
            'light_fighter': {'count': 10, 'weapon': 50}
        }
        defender_ships = {
            'light_fighter': {'count': 5, 'weapon': 50}
        }

        firepower = CombatEngine._calculate_firepower(attacker_ships, defender_ships, 'attacker')

        # 10 ships * 50 weapon = 500 firepower
        assert firepower == 500

    def test_calculate_firepower_with_rapid_fire(self):
        """Test firepower calculation with rapid fire bonuses"""
        attacker_ships = {
            'cruiser': {'count': 5, 'weapon': 400}
        }
        defender_ships = {
            'light_fighter': {'count': 20, 'weapon': 50}
        }

        firepower = CombatEngine._calculate_firepower(attacker_ships, defender_ships, 'attacker')

        # Cruiser has rapid fire 6 vs light fighters
        # Base fire: 5 * 400 = 2000
        # Rapid fire bonus: 20/6 ≈ 3.33 extra shots per cruiser
        # Total: 2000 * (1 + 3.33) ≈ 8666
        assert firepower > 2000  # Should be increased by rapid fire

    def test_shield_absorption(self):
        """Test shield absorption of damage"""
        damage = 1000
        target_ships = {
            'light_fighter': {'count': 10, 'shield': 10}  # 10 ships * 10 shield = 100 total shield
        }

        absorbed_damage = CombatEngine._apply_shields(damage, target_ships)

        # Should absorb 100 damage, leaving 900
        assert absorbed_damage == 900

    def test_hull_damage_application(self):
        """Test hull damage application to ships"""
        damage = 5000  # Enough to destroy some ships
        target_ships = {
            'light_fighter': {'count': 10, 'hull': 4000}  # Each ship has 4000 hull
        }

        CombatEngine._apply_hull_damage(damage, target_ships)

        # Should destroy 1 ship (4000 hull) and leave 1 ship with 1000 hull remaining
        # But since we don't track partial hull in this simplified system, it should destroy 1 full ship
        assert target_ships['light_fighter']['count'] == 9  # 10 - 1 destroyed

    def test_has_ships_check(self):
        """Test ship presence checking"""
        # Ships with count > 0
        ships_with_fleet = {
            'light_fighter': {'count': 5},
            'cruiser': {'count': 0}
        }
        assert CombatEngine._has_ships(ships_with_fleet) == True

        # All ships destroyed
        ships_empty = {
            'light_fighter': {'count': 0},
            'cruiser': {'count': 0}
        }
        assert CombatEngine._has_ships(ships_empty) == False

    def test_calculate_losses(self):
        """Test ship loss calculation"""
        # Create a simple class to avoid Mock arithmetic issues
        class MockFleet:
            def __init__(self):
                self.small_cargo = 10
                self.light_fighter = 20
                self.cruiser = 5
                self.battleship = 0
                self.colony_ship = 0
                self.heavy_fighter = 0
                self.recycler = 0

        original_fleet = MockFleet()

        # Remaining ships after battle
        remaining_ships = {
            'small_cargo': {'count': 8},
            'light_fighter': {'count': 15},
            'cruiser': {'count': 5}  # No losses
        }

        losses = CombatEngine._calculate_losses(original_fleet, remaining_ships)

        assert losses['small_cargo'] == 2  # 10 - 8
        assert losses['light_fighter'] == 5  # 20 - 15
        assert losses['cruiser'] == 0  # 5 - 5

    def test_calculate_debris(self):
        """Test debris field calculation"""
        # Create simple classes to avoid Mock issues
        class MockFleet:
            def __init__(self):
                self.small_cargo = 10
                self.light_fighter = 5
                self.cruiser = 0
                self.battleship = 0
                self.colony_ship = 0
                self.heavy_fighter = 0
                self.recycler = 0

        attacker_fleet = MockFleet()
        defender_fleet = MockFleet()
        defender_fleet.small_cargo = 0
        defender_fleet.light_fighter = 0
        defender_fleet.cruiser = 5
        defender_fleet.battleship = 3

        # Mock the _calculate_losses method to return known values
        with patch.object(CombatEngine, '_calculate_losses') as mock_losses:
            mock_losses.side_effect = [
                {'small_cargo': 2, 'light_fighter': 0},  # Attacker losses
                {'cruiser': 1, 'battleship': 0}  # Defender losses
            ]

            debris = CombatEngine._calculate_debris(attacker_fleet, defender_fleet)

            assert 'metal' in debris
            assert 'crystal' in debris
            assert debris['metal'] > 0
            assert debris['crystal'] > 0

    def test_process_combat_result_updates_fleet_stats(self):
        """Test that combat results update fleet statistics"""
        # Create simple classes to avoid Mock issues
        class MockUser:
            def __init__(self, username):
                self.username = username

        class MockFleet:
            def __init__(self, user):
                self.user = user
                self.user_id = 1 if user.username == 'attacker' else 2  # Add user_id
                self.combat_victories = 0
                self.combat_defeats = 0
                self.small_cargo = 10
                self.light_fighter = 10
                self.cruiser = 5  # Set initial cruiser count to 5
                self.battleship = 0
                self.colony_ship = 0
                self.heavy_fighter = 0
                self.recycler = 0

        attacker_user = MockUser('attacker')
        defender_user = MockUser('defender')
        attacker_fleet = MockFleet(attacker_user)
        defender_fleet = MockFleet(defender_user)
        planet = Mock()

        # Mock combat result with rounds
        combat_result = {
            'winner': 'attacker',
            'rounds': [{'attacker_fire': 500, 'defender_fire': 300}],
            'attacker_losses': {'light_fighter': 5},
            'defender_losses': {'cruiser': 2},
            'debris': {'metal': 1000, 'crystal': 500}
        }

        # Mock the database and related objects
        with patch('backend.services.combat_engine.db') as mock_db:
            with patch('backend.services.combat_engine.CombatReport') as mock_combat_report:
                # Create a mock battle report instance
                mock_report_instance = Mock()
                mock_report_instance.winner = Mock()
                mock_report_instance.winner.username = 'attacker'
                mock_combat_report.return_value = mock_report_instance

                CombatEngine.process_combat_result(combat_result, attacker_fleet, defender_fleet, planet)

                # Verify fleet stats were updated
                assert attacker_fleet.combat_victories == 1
                assert defender_fleet.combat_defeats == 1

                # Verify ship losses were applied
                assert attacker_fleet.light_fighter == 5  # 10 - 5
                assert defender_fleet.cruiser == 3  # 5 - 2

    def test_calculate_planet_attack_undefended(self):
        """Test attack calculation for undefended planet"""
        fleet = Mock()
        planet = Mock()
        planet.user_id = None  # Unowned planet

        result = CombatEngine.calculate_planet_attack(fleet, planet)

        assert result['winner'] == 'attacker'
        assert result['planet_captured'] == True
        assert result['attacker_losses']['small_cargo'] == 0  # No losses for undefended planet

    def test_battle_ends_after_max_rounds(self):
        """Test that battle ends after maximum rounds even if both sides have ships"""
        # Create simple classes to avoid Mock arithmetic issues
        class MockFleet:
            def __init__(self):
                self.id = 1  # Add id attribute for debug logging
                self.small_cargo = 0
                self.light_fighter = 10
                self.cruiser = 0
                self.battleship = 0
                self.colony_ship = 0
                self.heavy_fighter = 0
                self.recycler = 0

        attacker_fleet = MockFleet()
        defender_fleet = MockFleet()

        with patch('backend.services.combat_engine.CombatEngine._fleet_to_combat_ships') as mock_convert:
            with patch('backend.services.combat_engine.CombatEngine._calculate_round') as mock_round:
                with patch('backend.services.combat_engine.CombatEngine._calculate_losses') as mock_losses:
                    # Always return ships for both sides
                    mock_convert.return_value = {'light_fighter': {'count': 1}}
                    mock_round.return_value = {
                        'attacker_fire': 50,
                        'defender_fire': 50,
                        'attacker_damage': 50,
                        'defender_damage': 50
                    }
                    mock_losses.return_value = {'light_fighter': 0}

                    result = CombatEngine.calculate_battle(attacker_fleet, defender_fleet)

                    # Should have exactly 6 rounds (maximum)
                    assert len(result['rounds']) == 6
                    assert mock_round.call_count == 6
