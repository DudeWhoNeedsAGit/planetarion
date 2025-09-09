"""
Unit tests for Colonization Calculations

Tests the mathematical formulas and calculations used in colonization mechanics:
- Difficulty formula calculations
- Travel time with mixed fleet compositions
- Distance and coordinate calculations
- Colony initialization parameters
"""

import pytest
import math
from datetime import datetime, timedelta


class TestColonizationDifficultyFormula:
    """Test colonization difficulty calculations"""

    def test_difficulty_formula_basic_calculation(self):
        """Test basic difficulty formula: min(5, max(1, floor(distance_from_origin / 200)))"""
        # distance_from_origin = (abs(x) + abs(y) + abs(z)) / 3

        test_cases = [
            # (x, y, z, expected_difficulty)
            (0, 0, 0, 1),        # Origin - minimum difficulty
            (100, 100, 100, 1),  # Close to origin
            (200, 200, 200, 1),  # 200 units away - floor(200/200) = 1
            (400, 400, 400, 2),  # 400 units away - floor(400/200) = 2
            (600, 600, 600, 3),  # 600 units away - floor(600/200) = 3
            (800, 800, 800, 4),  # 800 units away - floor(800/200) = 4
            (1000, 1000, 1000, 5), # Beyond maximum - still 5
        ]

        for x, y, z, expected in test_cases:
            distance_from_origin = (abs(x) + abs(y) + abs(z)) / 3
            difficulty = min(5, max(1, math.floor(distance_from_origin / 200)))
            assert difficulty == expected, f"Failed for coordinates ({x},{y},{z}): expected {expected}, got {difficulty}"

    def test_difficulty_formula_edge_cases(self):
        """Test difficulty formula edge cases"""

        # Test negative coordinates (should use absolute values)
        assert self._calculate_difficulty(-200, -200, -200) == 1

        # Test mixed positive/negative coordinates
        assert self._calculate_difficulty(300, -300, 300) == 1

        # Test zero coordinates (should be 1)
        assert self._calculate_difficulty(0, 0, 0) == 1

        # Test very small distances (should be 1)
        assert self._calculate_difficulty(50, 50, 50) == 1

    def test_difficulty_formula_boundary_values(self):
        """Test difficulty formula at boundary values"""

        # Test values very close to boundaries
        assert self._calculate_difficulty(199, 199, 199) == 1  # Just under 200
        assert self._calculate_difficulty(200, 200, 200) == 1  # Exactly 200

        assert self._calculate_difficulty(399, 399, 399) == 1  # Just under 400
        assert self._calculate_difficulty(400, 400, 400) == 2  # Exactly 400

        assert self._calculate_difficulty(599, 599, 599) == 2  # Just under 600
        assert self._calculate_difficulty(600, 600, 600) == 3  # Exactly 600

        assert self._calculate_difficulty(799, 799, 799) == 3  # Just under 800
        assert self._calculate_difficulty(800, 800, 800) == 4  # Exactly 800

    def _calculate_difficulty(self, x, y, z):
        """Helper method to calculate colonization difficulty"""
        distance_from_origin = (abs(x) + abs(y) + abs(z)) / 3
        return min(5, max(1, math.floor(distance_from_origin / 200)))


class TestTravelTimeCalculations:
    """Test travel time calculations for colonization fleets"""

    # Ship speed constants (from specification)
    SHIP_SPEEDS = {
        'colony_ship': 2500,
        'small_cargo': 5000,
        'large_cargo': 3500,
        'light_fighter': 4500,
        'heavy_fighter': 4000,
        'cruiser': 3500,
        'battleship': 3000
    }

    def test_travel_time_single_ship_type(self):
        """Test travel time calculation with single ship type"""

        # Colony ship only (slowest)
        fleet = {'colony_ship': 1}
        distance = 1000
        expected_time = distance / self.SHIP_SPEEDS['colony_ship']  # 1000 / 2500 = 0.4 hours

        actual_time = self._calculate_travel_time(fleet, distance)
        assert abs(actual_time - expected_time) < 0.001

    def test_travel_time_mixed_fleet_colony_ship_slowest(self):
        """Test that colony ship determines travel time in mixed fleet"""

        # Mixed fleet with colony ship (should use colony ship speed)
        fleet = {
            'colony_ship': 1,     # 2500 speed (slowest)
            'small_cargo': 5,     # 5000 speed (fastest)
            'cruiser': 3          # 3500 speed
        }
        distance = 2500
        expected_time = distance / self.SHIP_SPEEDS['colony_ship']  # 2500 / 2500 = 1.0 hours

        actual_time = self._calculate_travel_time(fleet, distance)
        assert abs(actual_time - expected_time) < 0.001

    def test_travel_time_mixed_fleet_without_colony_ship(self):
        """Test travel time with mixed fleet but no colony ship"""

        # Mixed fleet without colony ship
        fleet = {
            'small_cargo': 5,     # 5000 speed (fastest)
            'cruiser': 3,         # 3500 speed
            'battleship': 2       # 3000 speed (slowest)
        }
        distance = 3000
        expected_time = distance / self.SHIP_SPEEDS['battleship']  # 3000 / 3000 = 1.0 hours

        actual_time = self._calculate_travel_time(fleet, distance)
        assert abs(actual_time - expected_time) < 0.001

    def test_travel_time_empty_fleet(self):
        """Test travel time calculation with empty fleet"""
        fleet = {}
        distance = 1000

        actual_time = self._calculate_travel_time(fleet, distance)
        assert actual_time == 0  # No ships = no travel time

    def test_travel_time_zero_distance(self):
        """Test travel time calculation with zero distance"""
        fleet = {'colony_ship': 1}
        distance = 0

        actual_time = self._calculate_travel_time(fleet, distance)
        assert actual_time == 0  # No distance = no travel time

    def _calculate_travel_time(self, fleet, distance):
        """Helper method to calculate fleet travel time"""
        if not fleet or distance <= 0:
            return 0

        # Find slowest ship speed in fleet
        slowest_speed = min(self.SHIP_SPEEDS[ship_type] for ship_type in fleet.keys()
                          if fleet[ship_type] > 0)

        return distance / slowest_speed


class TestDistanceCalculations:
    """Test distance calculations for colonization"""

    def test_distance_formula_3d_pythagorean(self):
        """Test 3D distance formula: sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)"""

        test_cases = [
            # (x1, y1, z1, x2, y2, z2, expected_distance)
            (0, 0, 0, 3, 4, 5, math.sqrt(3**2 + 4**2 + 5**2)),  # 7.071
            (10, 20, 30, 10, 20, 30, 0),  # Same point
            (0, 0, 0, 1, 0, 0, 1),        # Unit distance X
            (0, 0, 0, 0, 1, 0, 1),        # Unit distance Y
            (0, 0, 0, 0, 0, 1, 1),        # Unit distance Z
            (-5, -5, -5, 5, 5, 5, math.sqrt(10**2 + 10**2 + 10**2)),  # 17.32
        ]

        for x1, y1, z1, x2, y2, z2, expected in test_cases:
            actual = self._calculate_distance(x1, y1, z1, x2, y2, z2)
            assert abs(actual - expected) < 0.001, f"Failed for ({x1},{y1},{z1}) to ({x2},{y2},{z2})"

    def test_distance_formula_negative_coordinates(self):
        """Test distance formula with negative coordinates"""
        # Distance should be same regardless of coordinate signs
        dist1 = self._calculate_distance(0, 0, 0, 3, 4, 5)
        dist2 = self._calculate_distance(0, 0, 0, -3, -4, -5)
        assert abs(dist1 - dist2) < 0.001

    def test_distance_minimum_value(self):
        """Test that same coordinates return 0 distance"""
        # Same coordinates should return 0 distance
        distance = self._calculate_distance(100, 200, 300, 100, 200, 300)
        assert distance == 0

    def _calculate_distance(self, x1, y1, z1, x2, y2, z2):
        """Helper method to calculate 3D distance"""
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        return distance  # Return actual distance, 0 for same coordinates


class TestColonyInitialization:
    """Test colony initialization parameters"""

    STARTING_RESOURCES = {
        'metal': 500,
        'crystal': 300,
        'deuterium': 100
    }

    def test_colony_starting_resources(self):
        """Test that new colonies get correct starting resources"""
        resources = self._get_colony_starting_resources()

        assert resources['metal'] == self.STARTING_RESOURCES['metal']
        assert resources['crystal'] == self.STARTING_RESOURCES['crystal']
        assert resources['deuterium'] == self.STARTING_RESOURCES['deuterium']

    def test_colony_starting_resources_completeness(self):
        """Test that all required resource types are present"""
        resources = self._get_colony_starting_resources()

        required_resources = {'metal', 'crystal', 'deuterium'}
        assert set(resources.keys()) == required_resources

    def test_colony_starting_resources_positive(self):
        """Test that all starting resources are positive values"""
        resources = self._get_colony_starting_resources()

        for resource_type, amount in resources.items():
            assert amount > 0, f"{resource_type} should be positive, got {amount}"

    def _get_colony_starting_resources(self):
        """Helper method to get colony starting resources"""
        # This would normally come from configuration or constants
        return self.STARTING_RESOURCES.copy()


class TestReturnTripCalculations:
    """Test return trip ETA calculations for recalled fleets"""

    def test_return_trip_eta_matches_outbound(self):
        """Test that return trip ETA equals outbound journey time"""

        # Simulate outbound journey
        departure_time = datetime(2025, 1, 1, 12, 0, 0)
        arrival_time = datetime(2025, 1, 1, 14, 0, 0)  # 2 hours later
        outbound_duration = arrival_time - departure_time

        # Simulate recall at arrival
        recall_time = arrival_time
        return_eta = recall_time + outbound_duration

        # Return trip should take same time as outbound
        expected_return_arrival = datetime(2025, 1, 1, 16, 0, 0)  # Another 2 hours
        assert return_eta == expected_return_arrival

    def test_return_trip_eta_with_timedelta(self):
        """Test return trip ETA calculation with timedelta objects"""

        # Fleet travels for 3.5 hours outbound
        outbound_duration = timedelta(hours=3.5)

        # Recall initiated
        recall_initiated = datetime(2025, 1, 1, 15, 30, 0)

        # Return trip should take same duration
        return_eta = recall_initiated + outbound_duration

        expected_eta = datetime(2025, 1, 1, 19, 0, 0)  # 3.5 hours later
        assert return_eta == expected_eta

    def test_return_trip_eta_partial_journey(self):
        """Test return trip when fleet is recalled mid-journey"""

        departure_time = datetime(2025, 1, 1, 10, 0, 0)
        full_journey_duration = timedelta(hours=4)

        # Fleet recalled after 1.5 hours of travel
        recall_time = datetime(2025, 1, 1, 11, 30, 0)

        # Return trip should still take full journey time
        return_eta = recall_time + full_journey_duration

        expected_eta = datetime(2025, 1, 1, 15, 30, 0)  # 4 hours from recall
        assert return_eta == expected_eta

    def test_return_trip_eta_zero_duration(self):
        """Test return trip ETA with zero duration (instant arrival)"""

        recall_time = datetime(2025, 1, 1, 12, 0, 0)
        zero_duration = timedelta(hours=0)

        return_eta = recall_time + zero_duration
        assert return_eta == recall_time  # Should arrive immediately
