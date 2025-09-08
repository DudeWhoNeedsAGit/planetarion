"""
Unit tests for FleetArrivalService

Tests the fleet arrival processing logic including colonization, exploration, and return missions.

NOTE: This service is heavily database-dependent, so these are integration-style unit tests
that focus on business logic while mocking external dependencies where possible.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from backend.services.fleet_arrival import FleetArrivalService
from backend.models import Fleet, Planet, User


class TestFleetArrivalService:
    """Test suite for FleetArrivalService"""

    def test_return_fleet_to_stationed(self):
        """Test the _return_fleet_to_stationed helper method"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.status = 'traveling'
        mock_fleet.mission = 'attack'
        mock_fleet.arrival_time = datetime.utcnow()
        mock_fleet.eta = 3600

        # Call the helper method
        FleetArrivalService._return_fleet_to_stationed(mock_fleet)

        # Verify fleet state
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'
        assert mock_fleet.arrival_time == None
        assert mock_fleet.eta == 0

    def test_process_arrived_fleets_no_fleets(self, app):
        """Test processing when no fleets have arrived"""
        with app.app_context():
            # Call the service
            FleetArrivalService.process_arrived_fleets()
            # Should not raise any errors

    def test_process_arrived_fleets_empty_list(self, app):
        """Test processing with empty fleet list"""
        with app.app_context():
            # This should not raise any errors
            FleetArrivalService.process_arrived_fleets()

    def test_coordinate_parsing_from_status(self, app):
        """Test coordinate parsing from fleet status"""
        with app.app_context():
            # Test valid coordinate parsing
            mock_fleet = Mock()
            mock_fleet.status = 'colonizing:100:200:300'
            mock_fleet.colony_ship = 1
            mock_fleet.user_id = 1
            mock_fleet.user = Mock()
            mock_fleet.user.username = 'TestUser'

            # Mock planet query using proper SQLAlchemy mocking
            with patch.object(Planet, 'query') as mock_query:
                mock_planet = Mock()
                mock_planet.user_id = None
                mock_planet.name = 'Test Planet'

                # Set up the query chain
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = mock_planet
                mock_query.filter_by.return_value = mock_filter_by

                # Mock database operations
                with patch('backend.services.fleet_arrival.db') as mock_db:
                    with patch('backend.services.fleet_arrival.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)

                        FleetArrivalService._process_colonization(mock_fleet)

                        # Verify coordinates were parsed correctly
                        mock_query.filter_by.assert_called_with(x=100, y=200, z=300)

    def test_coordinate_parsing_from_target_coordinates(self, app):
        """Test coordinate parsing from target_coordinates field"""
        with app.app_context():
            # Test coordinate parsing from target_coordinates (when status doesn't have coordinates)
            mock_fleet = Mock()
            mock_fleet.status = 'traveling'  # Status without coordinates
            mock_fleet.target_coordinates = '400:500:600'  # Different coordinates
            mock_fleet.colony_ship = 1
            mock_fleet.user_id = 1
            mock_fleet.user = Mock()
            mock_fleet.user.username = 'TestUser'

            # Mock planet query using proper SQLAlchemy mocking
            with patch.object(Planet, 'query') as mock_query:
                mock_planet = Mock()
                mock_planet.user_id = None
                mock_planet.name = 'Test Planet'

                # Set up the query chain
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = mock_planet
                mock_query.filter_by.return_value = mock_filter_by

                # Mock database operations
                with patch('backend.services.fleet_arrival.db') as mock_db:
                    with patch('backend.services.fleet_arrival.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)

                        FleetArrivalService._process_colonization(mock_fleet)

                        # Verify target_coordinates were used
                        mock_query.filter_by.assert_called_with(x=400, y=500, z=600)

    def test_colonization_validation_no_colony_ship(self, app):
        """Test colonization validation without colony ships"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.colony_ship = 0
            mock_fleet.status = 'colonizing:100:200:300'

            with patch.object(Planet, 'query') as mock_query:
                mock_query.filter_by.return_value.first.return_value = Mock()

                with patch('backend.services.fleet_arrival.db'):
                    FleetArrivalService._process_colonization(mock_fleet)

                    # Verify fleet was returned to stationed
                    assert mock_fleet.status == 'stationed'
                    assert mock_fleet.mission == 'stationed'

    def test_colonization_validation_planet_already_owned(self, app):
        """Test colonization when planet is already owned"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.colony_ship = 1
            mock_fleet.status = 'colonizing:100:200:300'
            mock_fleet.user_id = 1

            # Mock owned planet
            with patch.object(Planet, 'query') as mock_query:
                mock_planet = Mock()
                mock_planet.user_id = 2  # Owned by different user

                mock_filter_by = Mock()
                mock_filter_by.first.return_value = mock_planet
                mock_query.filter_by.return_value = mock_filter_by

                with patch('backend.services.fleet_arrival.db'):
                    FleetArrivalService._process_colonization(mock_fleet)

                    # Verify fleet was returned to stationed
                    assert mock_fleet.status == 'stationed'
                    assert mock_fleet.mission == 'stationed'

    def test_colonization_successful(self, app):
        """Test successful colonization"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.colony_ship = 1
            mock_fleet.status = 'colonizing:100:200:300'
            mock_fleet.user_id = 1
            mock_fleet.user = Mock()
            mock_fleet.user.username = 'TestUser'

            # Mock unowned planet
            with patch.object(Planet, 'query') as mock_query:
                mock_planet = Mock()
                mock_planet.user_id = None
                mock_planet.name = 'Test Planet'

                mock_filter_by = Mock()
                mock_filter_by.first.return_value = mock_planet
                mock_query.filter_by.return_value = mock_filter_by

                with patch('backend.services.fleet_arrival.db') as mock_db:
                    with patch('backend.services.fleet_arrival.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)

                        FleetArrivalService._process_colonization(mock_fleet)

                        # Verify planet was colonized
                        assert mock_planet.user_id == 1
                        assert mock_planet.is_home_planet == False
                        assert mock_planet.colonized_at is not None
                        assert mock_planet.metal == 1000
                        assert mock_planet.crystal == 500
                        assert mock_planet.deuterium == 0

                        # Verify fleet was returned to stationed
                        assert mock_fleet.status == 'stationed'
                        assert mock_fleet.mission == 'stationed'

                        # Verify database commit
                        mock_db.session.commit.assert_called()

    def test_exploration_successful(self, app):
        """Test successful exploration"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.status = 'exploring:100:200:300'
            mock_fleet.user_id = 1
            mock_fleet.user = Mock()
            mock_fleet.user.username = 'TestUser'

            # Mock no existing planet
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = None
                mock_query.filter_by.return_value = mock_filter_by

                with patch('backend.services.fleet_arrival.db') as mock_db:
                    with patch('backend.services.fleet_arrival.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)

                        # Mock hasattr to return False for explored_systems to avoid JSON issues
                        with patch('backend.services.fleet_arrival.hasattr', side_effect=lambda obj, attr: False if attr == 'explored_systems' else hasattr.__wrapped__(obj, attr)):
                            FleetArrivalService._process_exploration(mock_fleet)

                            # Verify fleet was returned to stationed
                            assert mock_fleet.status == 'stationed'
                            assert mock_fleet.mission == 'stationed'

                            # Verify database commit
                            mock_db.session.commit.assert_called()

    def test_return_mission_processing(self):
        """Test return mission processing"""
        mock_fleet = Mock()
        mock_fleet.mission = 'return'
        mock_fleet.status = 'returning'
        mock_fleet.arrival_time = datetime.utcnow()
        mock_fleet.eta = 3600

        FleetArrivalService._process_return(mock_fleet)

        # Verify fleet was returned to stationed
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'
        assert mock_fleet.arrival_time == None
        assert mock_fleet.eta == 0

    def test_invalid_coordinate_parsing(self, app):
        """Test handling of invalid coordinate strings"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.status = 'colonizing:invalid:coordinates'
            mock_fleet.colony_ship = 1

            # Should handle error gracefully
            with patch.object(Planet, 'query') as mock_query:
                mock_query.filter_by.return_value.first.return_value = Mock()

                with patch('backend.services.fleet_arrival.db'):
                    FleetArrivalService._process_colonization(mock_fleet)

                    # Verify fleet was returned to stationed
                    assert mock_fleet.status == 'stationed'
                    assert mock_fleet.mission == 'stationed'

    def test_planet_not_found(self, app):
        """Test colonization when target planet doesn't exist"""
        with app.app_context():
            mock_fleet = Mock()
            mock_fleet.status = 'colonizing:999:999:999'
            mock_fleet.colony_ship = 1

            # Mock planet not found
            with patch.object(Planet, 'query') as mock_query:
                mock_filter_by = Mock()
                mock_filter_by.first.return_value = None
                mock_query.filter_by.return_value = mock_filter_by

                with patch('backend.services.fleet_arrival.db'):
                    FleetArrivalService._process_colonization(mock_fleet)

                    # Verify fleet was returned to stationed
                    assert mock_fleet.status == 'stationed'
                    assert mock_fleet.mission == 'stationed'


class TestFleetArrivalServiceIntegration:
    """Integration-style tests that verify service behavior"""

    def test_service_initialization(self):
        """Test that the service can be imported and initialized"""
        # This is more of a smoke test
        assert FleetArrivalService is not None
        assert hasattr(FleetArrivalService, 'process_arrived_fleets')
        assert hasattr(FleetArrivalService, '_process_colonization')
        assert hasattr(FleetArrivalService, '_process_exploration')
        assert hasattr(FleetArrivalService, '_process_return')
        assert hasattr(FleetArrivalService, '_return_fleet_to_stationed')

    def test_helper_method_isolation(self):
        """Test that helper methods work in isolation"""
        mock_fleet = Mock()
        mock_fleet.status = 'any_status'
        mock_fleet.mission = 'any_mission'
        mock_fleet.arrival_time = 'any_time'
        mock_fleet.eta = 1234

        # Call helper method
        FleetArrivalService._return_fleet_to_stationed(mock_fleet)

        # Verify only the expected changes
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'
        assert mock_fleet.arrival_time == None
        assert mock_fleet.eta == 0
