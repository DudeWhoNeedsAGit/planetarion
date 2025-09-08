"""
Unit tests for FleetArrivalService

Tests the fleet arrival processing logic including colonization, exploration, and return missions.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from backend.services.fleet_arrival import FleetArrivalService
from backend.models import Fleet, Planet, User, Research, TickLog


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

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_no_fleets(self, mock_db, mock_fleet_query):
        """Test processing when no fleets have arrived"""
        # Mock empty query result
        mock_fleet_query.filter.return_value.all.return_value = []

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify no database operations were performed
        mock_db.session.commit.assert_not_called()

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    @patch('backend.services.fleet_arrival.PlanetTraitService')
    def test_process_arrived_fleets_colonization_success(self, mock_trait_service, mock_db, mock_planet_query, mock_fleet_query):
        """Test successful colonization fleet processing"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.user_id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:100:200:300'
        mock_fleet.colony_ship = 1

        # Create mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'TestUser'
        mock_fleet.user = mock_user

        # Create mock planet
        mock_planet = Mock()
        mock_planet.id = 1
        mock_planet.user_id = None  # Unowned planet
        mock_planet.name = 'Test Planet'

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_planet_query.filter_by.return_value.first.return_value = mock_planet

        # Mock trait service
        mock_trait_service.calculate_colonization_difficulty.return_value = 2
        mock_trait_service.generate_planet_traits.return_value = []

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify planet was colonized
        assert mock_planet.user_id == 1
        assert mock_planet.is_home_planet == False
        assert mock_planet.colonized_at is not None
        assert mock_planet.metal == 1000  # Starting resources
        assert mock_planet.crystal == 500
        assert mock_planet.deuterium == 0

        # Verify fleet was returned to stationed
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

        # Verify database commit was called
        mock_db.session.commit.assert_called()

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_colonization_already_owned(self, mock_db, mock_planet_query, mock_fleet_query):
        """Test colonization when planet is already owned"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.user_id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:100:200:300'
        mock_fleet.colony_ship = 1

        # Create mock planet that's already owned
        mock_planet = Mock()
        mock_planet.id = 1
        mock_planet.user_id = 2  # Owned by different user

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_planet_query.filter_by.return_value.first.return_value = mock_planet

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed (colonization failed)
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

        # Verify planet ownership didn't change
        assert mock_planet.user_id == 2

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_colonization_no_colony_ship(self, mock_db, mock_planet_query, mock_fleet_query):
        """Test colonization fleet without colony ships"""
        # Create mock fleet without colony ships
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.user_id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:100:200:300'
        mock_fleet.colony_ship = 0  # No colony ships

        # Create mock planet
        mock_planet = Mock()
        mock_planet.id = 1
        mock_planet.user_id = None

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_planet_query.filter_by.return_value.first.return_value = mock_planet

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed (colonization failed)
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

        # Verify planet was not colonized
        assert mock_planet.user_id == None

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_exploration_success(self, mock_db, mock_planet_query, mock_fleet_query):
        """Test successful exploration fleet processing"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.user_id = 1
        mock_fleet.mission = 'explore'
        mock_fleet.status = 'exploring:100:200:300'

        # Create mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'TestUser'
        mock_user.explored_systems = None
        mock_fleet.user = mock_user

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_planet_query.filter_by.return_value.first.return_value = None  # No existing planet

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

        # Verify database commit was called
        mock_db.session.commit.assert_called()

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_return_mission(self, mock_db, mock_fleet_query):
        """Test fleet return mission processing"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.mission = 'return'
        mock_fleet.status = 'returning'

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'
        assert mock_fleet.arrival_time == None
        assert mock_fleet.eta == 0

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_invalid_coordinates(self, mock_db, mock_fleet_query):
        """Test fleet processing with invalid coordinates"""
        # Create mock fleet with invalid status
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'invalid_status'

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed (error handling)
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_planet_not_found(self, mock_db, mock_planet_query, mock_fleet_query):
        """Test colonization when target planet doesn't exist"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.user_id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:999:999:999'
        mock_fleet.colony_ship = 1

        # Mock database queries - planet not found
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_planet_query.filter_by.return_value.first.return_value = None

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed (planet not found)
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.Planet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_mixed_missions(self, mock_db, mock_planet_query, mock_fleet_query):
        """Test processing fleets with mixed mission types"""
        # Create multiple mock fleets
        fleet1 = Mock()
        fleet1.id = 1
        fleet1.mission = 'colonize'
        fleet1.status = 'colonizing:100:200:300'
        fleet1.colony_ship = 1
        fleet1.user = Mock()
        fleet1.user.id = 1
        fleet1.user.username = 'User1'

        fleet2 = Mock()
        fleet2.id = 2
        fleet2.mission = 'return'
        fleet2.status = 'returning'

        fleet3 = Mock()
        fleet3.id = 3
        fleet3.mission = 'explore'
        fleet3.status = 'exploring:400:500:600'
        fleet3.user = Mock()
        fleet3.user.id = 2
        fleet3.user.username = 'User2'
        fleet3.user.explored_systems = None

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [fleet1, fleet2, fleet3]
        mock_planet_query.filter_by.return_value.first.side_effect = [
            Mock(),  # Planet for colonization
            None,    # No planet for exploration
        ]

        # Call the service
        FleetArrivalService.process_arrived_fleets()

        # Verify all fleets were processed
        assert fleet1.status == 'stationed'
        assert fleet1.mission == 'stationed'
        assert fleet2.status == 'stationed'
        assert fleet2.mission == 'stationed'
        assert fleet3.status == 'stationed'
        assert fleet3.mission == 'stationed'

        # Verify database commit was called
        mock_db.session.commit.assert_called()


class TestFleetArrivalServiceEdgeCases:
    """Test edge cases and error conditions"""

    def test_process_arrived_fleets_empty_fleet_list(self):
        """Test processing with empty fleet list"""
        # This should not raise any errors
        FleetArrivalService.process_arrived_fleets()

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_database_error(self, mock_db, mock_fleet_query):
        """Test handling of database errors during processing"""
        # Create mock fleet
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:100:200:300'

        # Mock database to raise exception
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]
        mock_db.session.commit.side_effect = Exception("Database error")

        # Call the service - should handle the error gracefully
        FleetArrivalService.process_arrived_fleets()

        # Verify rollback was called
        mock_db.session.rollback.assert_called()

    @patch('backend.services.fleet_arrival.Fleet.query')
    @patch('backend.services.fleet_arrival.db')
    def test_process_arrived_fleets_coordinate_parsing_error(self, mock_db, mock_fleet_query):
        """Test handling of malformed coordinate strings"""
        # Create mock fleet with malformed coordinates
        mock_fleet = Mock()
        mock_fleet.id = 1
        mock_fleet.mission = 'colonize'
        mock_fleet.status = 'colonizing:invalid:coordinates'

        # Mock database queries
        mock_fleet_query.filter.return_value.all.return_value = [mock_fleet]

        # Call the service - should handle parsing error gracefully
        FleetArrivalService.process_arrived_fleets()

        # Verify fleet was returned to stationed
        assert mock_fleet.status == 'stationed'
        assert mock_fleet.mission == 'stationed'
