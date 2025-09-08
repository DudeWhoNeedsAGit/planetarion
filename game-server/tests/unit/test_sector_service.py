"""
Unit Tests for Sector Service

Following Testing Patterns from systemPatterns.md:
- Unit Testing: pytest with fixtures
- Arrange-Act-Assert structure
- Real database operations within app context (following existing test patterns)
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock

# Import the service to test
from backend.services.sector import SectorService
from backend.models import User


class TestSectorService:
    """Test suite for SectorService following established testing patterns"""

    def test_system_to_sector_basic_conversion(self):
        """Test basic system to sector coordinate conversion"""
        # Arrange
        system_x, system_y = 125, 175

        # Act
        result = SectorService.system_to_sector(system_x, system_y)

        # Assert
        assert result['sector_x'] == 2  # 125 // 50 = 2
        assert result['sector_y'] == 3  # 175 // 50 = 3

    def test_system_to_sector_edge_cases(self):
        """Test system to sector conversion with edge cases"""
        # Test cases: (system_x, system_y, expected_sector_x, expected_sector_y)
        test_cases = [
            (0, 0, 0, 0),           # Origin
            (49, 49, 0, 0),         # Upper bounds of sector 0,0
            (50, 50, 1, 1),         # Lower bounds of sector 1,1
            (99, 99, 1, 1),         # Upper bounds of sector 1,1
            (-1, -1, -1, -1),       # Negative coordinates
            (1000, 2000, 20, 40),   # Large coordinates
        ]

        for system_x, system_y, expected_x, expected_y in test_cases:
            result = SectorService.system_to_sector(system_x, system_y)
            assert result['sector_x'] == expected_x
            assert result['sector_y'] == expected_y

    def test_get_sector_bounds(self):
        """Test sector bounds calculation"""
        # Arrange
        sector_x, sector_y = 2, 3

        # Act
        bounds = SectorService.get_sector_bounds(sector_x, sector_y)

        # Assert
        assert bounds['min_x'] == 100  # 2 * 50
        assert bounds['max_x'] == 149  # (2 + 1) * 50 - 1
        assert bounds['min_y'] == 150  # 3 * 50
        assert bounds['max_y'] == 199  # (3 + 1) * 50 - 1

    def test_mark_sector_explored_new_sector(self, db_session, sample_user):
        """Test marking a new sector as explored"""
        # Arrange - user starts with no explored sectors
        sample_user.explored_sectors = None

        # Act
        result = SectorService.mark_sector_explored(sample_user.id, 2, 3)

        # Assert
        assert result is True  # Should return True for newly explored

        # Verify data was saved to database
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors is not None

        # Verify data structure
        explored_data = json.loads(sample_user.explored_sectors)
        assert len(explored_data) == 1
        assert explored_data[0]['x'] == 2
        assert explored_data[0]['y'] == 3
        assert 'explored_at' in explored_data[0]

    def test_mark_sector_explored_already_explored(self, db_session, sample_user):
        """Test marking an already explored sector"""
        # Arrange - user already has sector 2,3 explored
        existing_data = json.dumps([{'x': 2, 'y': 3, 'explored_at': '2023-01-01T00:00:00'}])
        sample_user.explored_sectors = existing_data
        db_session.commit()

        # Act
        result = SectorService.mark_sector_explored(sample_user.id, 2, 3)

        # Assert
        assert result is False  # Should return False for already explored

        # Verify data was not modified
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors == existing_data

    def test_mark_sector_explored_invalid_user(self, db_session):
        """Test marking sector explored for non-existent user"""
        # Act
        result = SectorService.mark_sector_explored(99999, 2, 3)

        # Assert
        assert result is False

    def test_get_explored_sectors_with_data(self, db_session, sample_user):
        """Test getting explored sectors with existing data"""
        # Arrange
        test_data = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'},
            {'x': 3, 'y': 4, 'explored_at': '2023-01-02T00:00:00'}
        ]
        sample_user.explored_sectors = json.dumps(test_data)
        db_session.commit()

        # Act
        result = SectorService.get_explored_sectors(sample_user.id)

        # Assert
        assert len(result) == 2
        assert result[0]['x'] == 1
        assert result[0]['y'] == 2
        assert result[1]['x'] == 3
        assert result[1]['y'] == 4

    def test_get_explored_sectors_empty(self, db_session, sample_user):
        """Test getting explored sectors with no data"""
        # Arrange
        sample_user.explored_sectors = None
        db_session.commit()

        # Act
        result = SectorService.get_explored_sectors(sample_user.id)

        # Assert
        assert result == []

    def test_get_explored_sectors_invalid_json(self, db_session, sample_user):
        """Test getting explored sectors with invalid JSON data"""
        # Arrange
        sample_user.explored_sectors = "invalid json"
        db_session.commit()

        # Act
        result = SectorService.get_explored_sectors(sample_user.id)

        # Assert
        assert result == []

    def test_is_sector_explored_true(self):
        """Test checking if sector is explored - positive case"""
        # Arrange
        explored_sectors = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'},
            {'x': 3, 'y': 4, 'explored_at': '2023-01-02T00:00:00'}
        ]

        # Act & Assert - mock the get_explored_sectors method
        with patch.object(SectorService, 'get_explored_sectors', return_value=explored_sectors):
            assert SectorService.is_sector_explored(1, 1, 2) is True
            assert SectorService.is_sector_explored(1, 3, 4) is True

    def test_is_sector_explored_false(self):
        """Test checking if sector is explored - negative case"""
        # Arrange
        explored_sectors = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'}
        ]

        # Act & Assert
        with patch.object(SectorService, 'get_explored_sectors', return_value=explored_sectors):
            assert SectorService.is_sector_explored(1, 3, 4) is False
            assert SectorService.is_sector_explored(1, 5, 6) is False

    @patch('backend.services.sector.datetime')
    def test_explore_system_integration(self, mock_datetime):
        """Test the main explore_system method integration"""
        # Arrange
        mock_datetime.utcnow.return_value.isoformat.return_value = '2023-01-01T00:00:00'

        with patch.object(SectorService, 'mark_sector_explored', return_value=True) as mock_mark:
            # Act
            result = SectorService.explore_system(1, 125, 175)

            # Assert
            assert result['system_x'] == 125
            assert result['system_y'] == 175
            assert result['sector_x'] == 2  # 125 // 50
            assert result['sector_y'] == 3  # 175 // 50
            assert result['newly_explored'] is True
            assert 'sector_bounds' in result
            assert 'min_x' in result['sector_bounds']

            mock_mark.assert_called_once_with(1, 2, 3)

    def test_get_sector_statistics(self):
        """Test sector statistics generation"""
        # Arrange
        explored_sectors = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'},
            {'x': 3, 'y': 4, 'explored_at': '2023-01-02T00:00:00'}
        ]

        # Act
        with patch.object(SectorService, 'get_explored_sectors', return_value=explored_sectors):
            result = SectorService.get_sector_statistics(1)

        # Assert
        assert result['total_explored_sectors'] == 2
        assert result['sectors_this_session'] == 0  # Not implemented yet
        assert result['exploration_percentage'] == 0  # Not implemented yet

    def test_reset_exploration_success(self, db_session, sample_user):
        """Test successful exploration reset"""
        # Arrange
        sample_user.explored_sectors = json.dumps([{'x': 1, 'y': 2}])
        db_session.commit()

        # Act
        result = SectorService.reset_exploration(sample_user.id)

        # Assert
        assert result is True

        # Verify data was reset in database
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors == json.dumps([])

    def test_reset_exploration_failure(self, db_session):
        """Test exploration reset failure"""
        # Act
        result = SectorService.reset_exploration(99999)

        # Assert
        assert result is False

    def test_explore_system_real_database(self, db_session, sample_user):
        """Test the main explore_system method with real database"""
        # Arrange - user starts with no explored sectors
        sample_user.explored_sectors = None
        db_session.commit()

        # Act
        result = SectorService.explore_system(sample_user.id, 125, 175)

        # Assert
        assert result['system_x'] == 125
        assert result['system_y'] == 175
        assert result['sector_x'] == 2  # 125 // 50
        assert result['sector_y'] == 3  # 175 // 50
        assert result['newly_explored'] is True
        assert 'sector_bounds' in result
        assert 'min_x' in result['sector_bounds']

        # Verify sector was marked as explored in database
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors is not None
        explored_data = json.loads(sample_user.explored_sectors)
        assert len(explored_data) == 1
        assert explored_data[0]['x'] == 2
        assert explored_data[0]['y'] == 3


class TestSectorServiceConstants:
    """Test sector service constants and configuration"""

    def test_sector_size_constant(self):
        """Test that sector size is properly defined"""
        # This test ensures the SECTOR_SIZE constant exists and is reasonable
        from backend.services.sector import SECTOR_SIZE

        assert isinstance(SECTOR_SIZE, int)
        assert SECTOR_SIZE > 0
        assert SECTOR_SIZE == 50  # Based on our implementation
