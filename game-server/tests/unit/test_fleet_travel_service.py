"""
Unit tests for FleetTravelService

Tests the fleet travel calculation service including:
- Distance calculations between planets
- Fleet speed calculations based on ship composition
- Travel time estimation
- Progress tracking and position interpolation
- Coordinate-based mission handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from backend.services.fleet_travel import FleetTravelService
from backend.models import Planet, Fleet


class TestFleetTravelService:
    """Test suite for FleetTravelService"""

    def test_calculate_distance_basic(self):
        """Test basic distance calculation between two planets"""
        planet1 = Mock()
        planet1.x, planet1.y, planet1.z = 0, 0, 0

        planet2 = Mock()
        planet2.x, planet2.y, planet2.z = 3, 4, 5

        distance = FleetTravelService.calculate_distance(planet1, planet2)
        expected_distance = (3**2 + 4**2 + 5**2) ** 0.5  # 7.071

        assert abs(distance - expected_distance) < 0.001

    def test_calculate_distance_same_location(self):
        """Test distance calculation when planets are at same location"""
        planet1 = Mock()
        planet1.x, planet1.y, planet1.z = 10, 20, 30

        planet2 = Mock()
        planet2.x, planet2.y, planet2.z = 10, 20, 30

        distance = FleetTravelService.calculate_distance(planet1, planet2)
        assert distance == 1  # Minimum distance

    def test_calculate_distance_none_planets(self):
        """Test distance calculation with None planets"""
        distance = FleetTravelService.calculate_distance(None, None)
        assert distance == 0

    def test_calculate_fleet_speed_colony_ship_slowest(self):
        """Test fleet speed calculation with colony ship (slowest)"""
        fleet = Mock()
        fleet.colony_ship = 1
        fleet.small_cargo = 0
        fleet.large_cargo = 0
        fleet.light_fighter = 0
        fleet.heavy_fighter = 0
        fleet.cruiser = 0
        fleet.battleship = 0

        speed = FleetTravelService.calculate_fleet_speed(fleet)
        assert speed == 2500  # Colony ship speed

    def test_calculate_fleet_speed_small_cargo_fastest(self):
        """Test fleet speed calculation with small cargo (fastest)"""
        fleet = Mock()
        fleet.colony_ship = 0
        fleet.small_cargo = 1
        fleet.large_cargo = 0
        fleet.light_fighter = 0
        fleet.heavy_fighter = 0
        fleet.cruiser = 0
        fleet.battleship = 0

        speed = FleetTravelService.calculate_fleet_speed(fleet)
        assert speed == 5000  # Small cargo speed

    def test_calculate_fleet_speed_mixed_fleet(self):
        """Test fleet speed calculation with mixed ship types"""
        fleet = Mock()
        fleet.colony_ship = 1  # 2500 (slowest)
        fleet.small_cargo = 5  # 5000 (fastest)
        fleet.large_cargo = 2  # 3500
        fleet.light_fighter = 3  # 4500
        fleet.heavy_fighter = 1  # 4000
        fleet.cruiser = 2  # 3500
        fleet.battleship = 1  # 3000

        speed = FleetTravelService.calculate_fleet_speed(fleet)
        assert speed == 2500  # Should be colony ship speed (slowest)

    def test_calculate_fleet_speed_empty_fleet(self):
        """Test fleet speed calculation with no ships"""
        fleet = Mock()
        fleet.colony_ship = 0
        fleet.small_cargo = 0
        fleet.large_cargo = 0
        fleet.light_fighter = 0
        fleet.heavy_fighter = 0
        fleet.cruiser = 0
        fleet.battleship = 0

        speed = FleetTravelService.calculate_fleet_speed(fleet)
        assert speed == 5000  # Default speed

    def test_calculate_fleet_speed_none_fleet(self):
        """Test fleet speed calculation with None fleet"""
        speed = FleetTravelService.calculate_fleet_speed(None)
        assert speed == 0

    def test_format_time_remaining_seconds(self):
        """Test time formatting for seconds"""
        formatted = FleetTravelService.format_time_remaining(65)
        assert formatted == "01:05"

    def test_format_time_remaining_minutes(self):
        """Test time formatting for minutes and seconds"""
        formatted = FleetTravelService.format_time_remaining(3665)  # 1h 1m 5s
        assert formatted == "01:01:05"

    def test_format_time_remaining_zero(self):
        """Test time formatting for zero/negative time"""
        formatted = FleetTravelService.format_time_remaining(0)
        assert formatted == "Arrived"

        formatted = FleetTravelService.format_time_remaining(-100)
        assert formatted == "Arrived"

    def test_calculate_travel_info_stationed_fleet(self):
        """Test travel info calculation for stationed fleet"""
        fleet = Mock()
        fleet.status = 'stationed'

        info = FleetTravelService.calculate_travel_info(fleet)
        assert info is None

    def test_calculate_travel_info_traveling_fleet(self, app):
        """Test travel info calculation for traveling fleet"""
        with app.app_context():
            # Create mock planets
            start_planet = Planet(name='Start', x=0, y=0, z=0)
            target_planet = Planet(name='Target', x=10, y=0, z=0)

            # Create mock fleet with proper ship attributes
            fleet = Mock()
            fleet.status = 'traveling'
            fleet.start_planet_id = 1
            fleet.target_planet_id = 2
            fleet.departure_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
            fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)    # 1 hour from now
            # Add ship attributes to avoid Mock comparison issues
            fleet.small_cargo = 5
            fleet.large_cargo = 0
            fleet.light_fighter = 0
            fleet.heavy_fighter = 0
            fleet.cruiser = 0
            fleet.battleship = 0
            fleet.colony_ship = 0

            # Mock database queries
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.side_effect = [start_planet, target_planet]
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)

                assert info is not None
                assert 'distance' in info
                assert 'total_duration_hours' in info
                assert 'progress_percentage' in info
                assert 'current_position' in info
                assert 'fleet_speed' in info
                assert info['fleet_speed'] == 5000  # Small cargo speed
                assert abs(info['progress_percentage'] - 50.0) < 1.0  # Approximately halfway through

    def test_calculate_travel_info_coordinate_based_mission(self, app):
        """Test travel info calculation for coordinate-based missions"""
        with app.app_context():
            # Create mock start planet
            start_planet = Planet(name='Start', x=0, y=0, z=0)

            # Create mock fleet with coordinate-based status and ship attributes
            fleet = Mock()
            fleet.status = 'colonizing:100:200:300'
            fleet.start_planet_id = 1
            fleet.departure_time = datetime.utcnow() - timedelta(hours=1)
            fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)
            fleet.small_cargo = 5
            fleet.large_cargo = 0
            fleet.light_fighter = 0
            fleet.heavy_fighter = 0
            fleet.cruiser = 0
            fleet.battleship = 0
            fleet.colony_ship = 1

            # Mock database queries
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = start_planet
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)

                assert info is not None
                assert info['target_coordinates'] == '100:200:300'
                assert info['is_coordinate_based'] == True
                assert info['fleet_speed'] == 2500  # Colony ship speed

    def test_calculate_travel_info_invalid_coordinates(self, app):
        """Test travel info calculation with invalid coordinates in status"""
        with app.app_context():
            # Create mock start planet
            start_planet = Planet(name='Start', x=0, y=0, z=0)

            # Create mock fleet with invalid coordinate status
            fleet = Mock()
            fleet.status = 'colonizing:invalid:coords'
            fleet.start_planet_id = 1

            # Mock database queries
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = start_planet
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)
                assert info is None  # Should return None for invalid coordinates

    def test_calculate_travel_info_missing_start_planet(self, app):
        """Test travel info calculation when start planet doesn't exist"""
        with app.app_context():
            fleet = Mock()
            fleet.status = 'traveling'
            fleet.start_planet_id = 999
            fleet.small_cargo = 5
            fleet.large_cargo = 0
            fleet.light_fighter = 0
            fleet.heavy_fighter = 0
            fleet.cruiser = 0
            fleet.battleship = 0
            fleet.colony_ship = 0

            # Mock database queries to return None
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = None
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)
                assert info is None

    def test_get_fleet_status_info_complete_fleet(self, app):
        """Test complete fleet status info retrieval"""
        with app.app_context():
            # Create mock planets
            start_planet = Planet(name='Start', x=0, y=0, z=0)
            target_planet = Planet(name='Target', x=10, y=0, z=0)

            # Create mock fleet
            fleet = Mock()
            fleet.id = 123
            fleet.mission = 'colonize'
            fleet.status = 'traveling'
            fleet.departure_time = datetime.utcnow() - timedelta(hours=1)
            fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)
            fleet.eta = 3600
            fleet.start_planet_id = 1
            fleet.target_planet_id = 2
            fleet.small_cargo = 5
            fleet.large_cargo = 2
            fleet.colony_ship = 1

            # Mock database queries
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.side_effect = [start_planet, target_planet]
                mock_query.filter_by.return_value = mock_filter_by

                # Mock travel info
                with patch.object(FleetTravelService, 'calculate_travel_info', return_value={'test': 'data'}):
                    info = FleetTravelService.get_fleet_status_info(fleet)

                    assert info is not None
                    assert info['id'] == 123
                    assert info['mission'] == 'colonize'
                    assert info['status'] == 'traveling'
                    assert info['eta'] == 3600
                    assert 'travel_info' in info
                    assert 'ships' in info
                    assert info['ships']['colony_ship'] == 1

    def test_get_fleet_status_info_none_fleet(self):
        """Test fleet status info with None fleet"""
        info = FleetTravelService.get_fleet_status_info(None)
        assert info is None

    def test_progress_calculation_edge_cases(self, app):
        """Test progress calculation edge cases"""
        with app.app_context():
            # Create mock planets
            start_planet = Planet(name='Start', x=0, y=0, z=0)
            target_planet = Planet(name='Target', x=10, y=0, z=0)

            # Test completed journey (progress = 100%)
            fleet = Mock()
            fleet.status = 'traveling'
            fleet.start_planet_id = 1
            fleet.target_planet_id = 2
            fleet.departure_time = datetime.utcnow() - timedelta(hours=2)  # 2 hours ago
            fleet.arrival_time = datetime.utcnow() - timedelta(hours=1)    # 1 hour ago (completed)
            fleet.small_cargo = 5
            fleet.large_cargo = 0
            fleet.light_fighter = 0
            fleet.heavy_fighter = 0
            fleet.cruiser = 0
            fleet.battleship = 0
            fleet.colony_ship = 0

            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.side_effect = [start_planet, target_planet]
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)

                assert info is not None
                assert info['progress_percentage'] >= 100.0
                assert info['current_position'] == '10.0:0.0:0.0'  # Should be at target

    def test_current_position_interpolation(self, app):
        """Test current position interpolation during travel"""
        with app.app_context():
            # Create mock planets
            start_planet = Planet(name='Start', x=0, y=0, z=0)
            target_planet = Planet(name='Target', x=100, y=200, z=300)

            # Fleet halfway through journey
            fleet = Mock()
            fleet.status = 'traveling'
            fleet.start_planet_id = 1
            fleet.target_planet_id = 2
            fleet.departure_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour ago
            fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)    # 1 hour from now
            fleet.small_cargo = 5
            fleet.large_cargo = 0
            fleet.light_fighter = 0
            fleet.heavy_fighter = 0
            fleet.cruiser = 0
            fleet.battleship = 0
            fleet.colony_ship = 0

            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.side_effect = [start_planet, target_planet]
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)

                assert info is not None
                # Should be approximately halfway between start and target
                expected_x = 50   # (0 + 100) / 2
                expected_y = 100  # (0 + 200) / 2
                expected_z = 150  # (0 + 300) / 2

                current_pos = info['current_position']
                assert f"{expected_x}:" in current_pos or abs(float(current_pos.split(':')[0]) - expected_x) < 1


class TestFleetTravelServiceIntegration:
    """Integration tests for FleetTravelService"""

    def test_service_initialization(self):
        """Test that the service can be imported and initialized"""
        assert FleetTravelService is not None
        assert hasattr(FleetTravelService, 'calculate_travel_info')
        assert hasattr(FleetTravelService, 'calculate_distance')
        assert hasattr(FleetTravelService, 'calculate_fleet_speed')
        assert hasattr(FleetTravelService, 'format_time_remaining')
        assert hasattr(FleetTravelService, 'get_fleet_status_info')

    def test_realistic_fleet_scenario(self, app):
        """Test a realistic fleet travel scenario"""
        with app.app_context():
            # Create realistic planets
            earth = Planet(name='Earth', x=100, y=200, z=300)
            mars = Planet(name='Mars', x=150, y=250, z=350)

            # Create fleet with mixed ship composition
            fleet = Mock()
            fleet.status = 'traveling'
            fleet.start_planet_id = 1
            fleet.target_planet_id = 2
            fleet.departure_time = datetime.utcnow() - timedelta(minutes=30)  # 30 min ago
            fleet.arrival_time = datetime.utcnow() + timedelta(minutes=30)    # 30 min from now
            fleet.small_cargo = 10
            fleet.large_cargo = 5
            fleet.light_fighter = 20
            fleet.cruiser = 3

            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.side_effect = [earth, mars]
                mock_query.filter_by.return_value = mock_filter_by

                info = FleetTravelService.calculate_travel_info(fleet)

                assert info is not None
                assert info['distance'] > 0
                assert info['total_duration_hours'] > 0
                assert 0 <= info['progress_percentage'] <= 100
                assert ':' in info['current_position']
                assert info['fleet_speed'] == 5000  # Small cargo speed (fastest in fleet)
