"""
Integration Tests for Sector Exploration API

Following Testing Patterns from systemPatterns.md:
- Integration Testing: pytest with test client
- API endpoint testing with full request-response cycle
- Database interactions and service layer integration
- Authentication and authorization testing
"""

import pytest
import json
from datetime import datetime

from backend.models import User
from tests.conftest import make_auth_headers


class TestSectorExplorationAPI:
    """Integration tests for sector exploration API endpoints"""

    def test_get_explored_sectors_authenticated(self, client, db_session, sample_user):
        """Test getting explored sectors for authenticated user"""
        # Arrange - Add some explored sectors to the user
        explored_data = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'},
            {'x': 3, 'y': 4, 'explored_at': '2023-01-02T00:00:00'}
        ]
        sample_user.explored_sectors = json.dumps(explored_data)
        db_session.commit()

        # Act - Make authenticated request
        headers = make_auth_headers(sample_user.id)
        response = client.get('/api/sectors/explored', headers=headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'explored_sectors' in data
        assert 'total_count' in data
        assert data['total_count'] == 2
        assert len(data['explored_sectors']) == 2
        assert data['explored_sectors'][0]['x'] == 1
        assert data['explored_sectors'][0]['y'] == 2

    def test_get_explored_sectors_unauthenticated(self, client):
        """Test getting explored sectors without authentication"""
        # Act
        response = client.get('/api/sectors/explored')

        # Assert
        assert response.status_code == 401

    def test_get_explored_sectors_empty(self, client, db_session, sample_user):
        """Test getting explored sectors when user has none"""
        # Arrange - Ensure user has no explored sectors
        sample_user.explored_sectors = None
        db_session.commit()

        # Act
        headers = make_auth_headers(sample_user.id)
        response = client.get('/api/sectors/explored', headers=headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['explored_sectors'] == []
        assert data['total_count'] == 0

    def test_explore_sector_success(self, client, db_session, sample_user):
        """Test successfully exploring a sector"""
        # Arrange - Ensure user starts with no explored sectors
        sample_user.explored_sectors = None
        db_session.commit()

        # Act - Explore system at coordinates (125, 175) which should be in sector (2, 3)
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/sectors/explore',
            json={'system_x': 125, 'system_y': 175},
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['newly_explored'] is True
        assert data['sector']['x'] == 2  # 125 // 50 = 2
        assert data['sector']['y'] == 3  # 175 // 50 = 3
        assert data['system']['x'] == 125
        assert data['system']['y'] == 175

        # Verify data was saved to database
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors is not None
        explored_data = json.loads(sample_user.explored_sectors)
        assert len(explored_data) == 1
        assert explored_data[0]['x'] == 2
        assert explored_data[0]['y'] == 3

    def test_explore_sector_already_explored(self, client, db_session, sample_user):
        """Test exploring a sector that's already been explored"""
        # Arrange - Mark sector (2, 3) as already explored
        existing_data = [{'x': 2, 'y': 3, 'explored_at': '2023-01-01T00:00:00'}]
        sample_user.explored_sectors = json.dumps(existing_data)
        db_session.commit()

        # Act - Try to explore the same sector again
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/sectors/explore',
            json={'system_x': 125, 'system_y': 175},  # Same sector (2, 3)
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['newly_explored'] is False  # Should be False since already explored

        # Verify no additional data was added
        db_session.refresh(sample_user)
        explored_data = json.loads(sample_user.explored_sectors)
        assert len(explored_data) == 1  # Should still be 1

    def test_explore_sector_missing_data(self, client, sample_user):
        """Test exploring sector with missing required data"""
        # Act - Missing system_y
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/sectors/explore',
            json={'system_x': 125},
            headers=headers
        )

        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required fields' in data['error']

    def test_explore_sector_unauthenticated(self, client):
        """Test exploring sector without authentication"""
        # Act
        response = client.post('/api/sectors/explore',
            json={'system_x': 125, 'system_y': 175}
        )

        # Assert
        assert response.status_code == 401

    def test_get_sector_statistics(self, client, db_session, sample_user):
        """Test getting sector exploration statistics"""
        # Arrange - Add some explored sectors
        explored_data = [
            {'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'},
            {'x': 3, 'y': 4, 'explored_at': '2023-01-02T00:00:00'},
            {'x': 5, 'y': 6, 'explored_at': '2023-01-03T00:00:00'}
        ]
        sample_user.explored_sectors = json.dumps(explored_data)
        db_session.commit()

        # Act
        headers = make_auth_headers(sample_user.id)
        response = client.get('/api/sectors/statistics', headers=headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'statistics' in data
        assert 'user_id' in data
        assert data['statistics']['total_explored_sectors'] == 3

    def test_reset_exploration_success(self, client, db_session, sample_user):
        """Test successfully resetting exploration data"""
        # Arrange - Add some explored sectors
        explored_data = [{'x': 1, 'y': 2, 'explored_at': '2023-01-01T00:00:00'}]
        sample_user.explored_sectors = json.dumps(explored_data)
        db_session.commit()

        # Act
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/sectors/reset', headers=headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data

        # Verify data was reset in database
        db_session.refresh(sample_user)
        assert sample_user.explored_sectors == json.dumps([])

    def test_reset_exploration_unauthenticated(self, client):
        """Test resetting exploration without authentication"""
        # Act
        response = client.post('/api/sectors/reset')

        # Assert
        assert response.status_code == 401

    def test_sector_bounds_calculation(self, client, sample_user):
        """Test that sector bounds are correctly calculated in API response"""
        # Act - Explore a system and check bounds calculation
        headers = make_auth_headers(sample_user.id)
        response = client.post('/api/sectors/explore',
            json={'system_x': 125, 'system_y': 175},
            headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)

        # Sector (2, 3) should have bounds:
        # min_x = 2 * 50 = 100, max_x = (2 + 1) * 50 - 1 = 149
        # min_y = 3 * 50 = 150, max_y = (3 + 1) * 50 - 1 = 199
        assert data['sector']['bounds']['min_x'] == 100
        assert data['sector']['bounds']['max_x'] == 149
        assert data['sector']['bounds']['min_y'] == 150
        assert data['sector']['bounds']['max_y'] == 199

    def test_multiple_sector_exploration(self, client, db_session, sample_user):
        """Test exploring multiple different sectors"""
        # Arrange
        sample_user.explored_sectors = None
        db_session.commit()

        # Act - Explore systems in different sectors
        sectors_to_explore = [
            (25, 75),    # Sector (0, 1)
            (125, 175),  # Sector (2, 3)
            (225, 275),  # Sector (4, 5)
        ]

        explored_sectors = []
        for system_x, system_y in sectors_to_explore:
            headers = make_auth_headers(sample_user.id)
            response = client.post('/api/sectors/explore',
                json={'system_x': system_x, 'system_y': system_y},
                headers=headers
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            explored_sectors.append((data['sector']['x'], data['sector']['y']))

        # Assert - Should have explored 3 different sectors
        assert len(explored_sectors) == 3
        assert explored_sectors[0] == (0, 1)  # 25//50=0, 75//50=1
        assert explored_sectors[1] == (2, 3)  # 125//50=2, 175//50=3
        assert explored_sectors[2] == (4, 5)  # 225//50=4, 275//50=5

        # Verify all sectors are stored
        db_session.refresh(sample_user)
        stored_data = json.loads(sample_user.explored_sectors)
        assert len(stored_data) == 3
