"""
Unit tests for centralized speed configuration
"""

import pytest
import sys
import os

# Add the src directory to the path so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from backend.config import (
    SPEED_MULTIPLIER,
    get_ship_speed,
    get_ship_fuel_rate,
    get_all_ship_speeds,
    calculate_fleet_speed,
    calculate_fuel_consumption,
    validate_config
)


class TestSpeedConfig:
    """Test centralized speed configuration functionality"""

    def test_speed_multiplier_value(self):
        """Test that speed multiplier is set to expected value"""
        assert SPEED_MULTIPLIER == 30.0

    def test_get_ship_speed_with_multiplier(self):
        """Test that ship speeds are multiplied correctly"""
        # Colony ship: 2500 * 30 = 75000
        assert get_ship_speed('colony_ship') == 75000

        # Small cargo: 5000 * 30 = 150000
        assert get_ship_speed('small_cargo') == 150000

        # Light fighter: 12500 * 30 = 375000
        assert get_ship_speed('light_fighter') == 375000

    def test_get_ship_fuel_rate(self):
        """Test fuel rate retrieval"""
        assert get_ship_fuel_rate('colony_ship') == 3.0
        assert get_ship_fuel_rate('small_cargo') == 1.0
        assert get_ship_fuel_rate('light_fighter') == 1.0

    def test_get_all_ship_speeds(self):
        """Test getting all ship speeds with multiplier applied"""
        all_speeds = get_all_ship_speeds()

        # Verify structure
        assert isinstance(all_speeds, dict)
        assert 'colony_ship' in all_speeds
        assert 'small_cargo' in all_speeds

        # Verify multiplier is applied
        assert all_speeds['colony_ship'] == 2500 * SPEED_MULTIPLIER
        assert all_speeds['small_cargo'] == 5000 * SPEED_MULTIPLIER

    def test_calculate_fleet_speed_single_ship(self):
        """Test fleet speed calculation with single ship type"""
        # Mock fleet with only colony ships
        class MockFleet:
            def __init__(self):
                self.colony_ship = 5
                self.small_cargo = 0
                self.light_fighter = 0

        fleet = MockFleet()
        speed = calculate_fleet_speed(fleet)

        # Should be colony ship speed (slowest)
        expected_speed = 2500 * SPEED_MULTIPLIER
        assert speed == expected_speed

    def test_calculate_fleet_speed_mixed_fleet(self):
        """Test fleet speed calculation with mixed ship types"""
        # Mock fleet with different ship types
        class MockFleet:
            def __init__(self):
                self.colony_ship = 1  # Slowest
                self.small_cargo = 5  # Fast
                self.light_fighter = 3  # Medium

        fleet = MockFleet()
        speed = calculate_fleet_speed(fleet)

        # Should be slowest ship speed (colony ship)
        expected_speed = 2500 * SPEED_MULTIPLIER
        assert speed == expected_speed

    def test_calculate_fleet_speed_no_ships(self):
        """Test fleet speed calculation with no ships"""
        class MockFleet:
            def __init__(self):
                self.colony_ship = 0
                self.small_cargo = 0
                self.light_fighter = 0

        fleet = MockFleet()
        speed = calculate_fleet_speed(fleet)

        # Should return 0 for empty fleet
        assert speed == 0

    def test_calculate_fuel_consumption(self):
        """Test fuel consumption calculation"""
        # Mock fleet
        class MockFleet:
            def __init__(self):
                self.colony_ship = 2  # 3.0 fuel rate each
                self.small_cargo = 3  # 1.0 fuel rate each

        fleet = MockFleet()
        distance = 100

        fuel = calculate_fuel_consumption(fleet, distance)

        # Expected: (2 * 3.0 * 100) + (3 * 1.0 * 100) = 600 + 300 = 900
        assert fuel == 900

    def test_calculate_fuel_consumption_zero_distance(self):
        """Test fuel consumption with zero distance"""
        class MockFleet:
            def __init__(self):
                self.colony_ship = 1

        fleet = MockFleet()
        fuel = calculate_fuel_consumption(fleet, 0)

        assert fuel == 0

    def test_calculate_fuel_consumption_no_fleet(self):
        """Test fuel consumption with no fleet"""
        fuel = calculate_fuel_consumption(None, 100)

        assert fuel == 0

    def test_config_validation(self):
        """Test configuration validation"""
        # Should not raise exception
        validate_config()

    def test_unknown_ship_type_speed(self):
        """Test handling of unknown ship types"""
        # Should return default speed
        speed = get_ship_speed('unknown_ship')
        assert speed == 5000 * SPEED_MULTIPLIER  # Default speed * multiplier

    def test_unknown_ship_type_fuel(self):
        """Test handling of unknown ship types for fuel"""
        # Should return default fuel rate
        fuel_rate = get_ship_fuel_rate('unknown_ship')
        assert fuel_rate == 1.0  # Default fuel rate
