import pytest
import json
from src.backend.models import User

class TestUsersEndpoints:
    """Test user management endpoints"""

    def test_get_users_list(self, client, db_session, sample_user):
        """Test getting list of all users"""
        response = client.get('/users')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the sample user

        # Check structure of returned user data
        user_data = data[0]
        assert 'id' in user_data
        assert 'username' in user_data
        assert 'email' in user_data
        assert 'created_at' in user_data

    def test_get_user_by_id_success(self, client, db_session, sample_user):
        """Test getting a specific user by ID"""
        response = client.get(f'/users/{sample_user.id}')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['id'] == sample_user.id
        assert data['username'] == sample_user.username
        assert data['email'] == sample_user.email
        assert 'created_at' in data

    def test_get_user_by_id_not_found(self, client):
        """Test getting a non-existent user returns 404"""
        response = client.get('/users/99999')

        assert response.status_code == 404

    def test_get_user_by_id_invalid_format(self, client):
        """Test getting user with invalid ID format"""
        response = client.get('/users/invalid')

        assert response.status_code == 404

    def test_create_user_success(self, client, db_session):
        """Test successful user creation"""
        user_data = {
            'username': 'newtestuser',
            'email': 'newtest@example.com',
            'password': 'securepass123'
        }

        response = client.post('/users',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data['id'] is not None
        assert data['username'] == 'newtestuser'
        assert data['email'] == 'newtest@example.com'

        # Verify user was actually created in database
        user = db_session.query(User).filter_by(username='newtestuser').first()
        assert user is not None
        assert user.email == 'newtest@example.com'

    def test_create_user_duplicate_username(self, client, db_session, sample_user):
        """Test creating user with duplicate username fails"""
        user_data = {
            'username': sample_user.username,  # Duplicate username
            'email': 'different@example.com',
            'password': 'securepass123'
        }

        response = client.post('/users',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_user_duplicate_email(self, client, db_session, sample_user):
        """Test creating user with duplicate email fails"""
        user_data = {
            'username': 'differentuser',
            'email': sample_user.email,  # Duplicate email
            'password': 'securepass123'
        }

        response = client.post('/users',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_user_missing_fields(self, client):
        """Test creating user with missing required fields"""
        incomplete_data = {
            'username': 'testuser'
            # Missing email and password
        }

        response = client.post('/users',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_user_empty_fields(self, client):
        """Test creating user with empty required fields"""
        empty_data = {
            'username': '',
            'email': '',
            'password': ''
        }

        response = client.post('/users',
                             data=json.dumps(empty_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_user_invalid_email(self, client):
        """Test creating user with invalid email format"""
        invalid_data = {
            'username': 'testuser',
            'email': 'invalid-email-format',
            'password': 'securepass123'
        }

        response = client.post('/users',
                             data=json.dumps(invalid_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestUsersIntegration:
    """Test user management integration scenarios"""

    def test_multiple_users_creation(self, client, db_session):
        """Test creating multiple users with unique data"""
        users_data = [
            {'username': 'multiuser1', 'email': 'multi1@example.com', 'password': 'pass1'},
            {'username': 'multiuser2', 'email': 'multi2@example.com', 'password': 'pass2'},
            {'username': 'multiuser3', 'email': 'multi3@example.com', 'password': 'pass3'}
        ]

        created_users = []
        for user_data in users_data:
            response = client.post('/users',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201
            created_users.append(json.loads(response.data))

        # Verify all users were created
        assert len(created_users) == 3
        for user in created_users:
            assert user['id'] is not None
            assert 'username' in user
            assert 'email' in user

    def test_get_users_after_creation(self, client, db_session):
        """Test that newly created users appear in the users list"""
        # Create a new user
        user_data = {
            'username': 'listtestuser',
            'email': 'listtest@example.com',
            'password': 'listpass123'
        }

        create_response = client.post('/users',
                                    data=json.dumps(user_data),
                                    content_type='application/json')
        assert create_response.status_code == 201

        # Get users list
        list_response = client.get('/users')
        assert list_response.status_code == 200

        users_list = json.loads(list_response.data)

        # Find our newly created user in the list
        created_user = None
        for user in users_list:
            if user['username'] == 'listtestuser':
                created_user = user
                break

        assert created_user is not None
        assert created_user['email'] == 'listtest@example.com'

    def test_user_data_consistency(self, client, db_session):
        """Test that user data is consistent between creation and retrieval"""
        # Create user
        original_data = {
            'username': 'consistencyuser',
            'email': 'consistency@example.com',
            'password': 'consistencypass123'
        }

        create_response = client.post('/users',
                                    data=json.dumps(original_data),
                                    content_type='application/json')
        assert create_response.status_code == 201

        created_data = json.loads(create_response.data)
        user_id = created_data['id']

        # Retrieve user by ID
        get_response = client.get(f'/users/{user_id}')
        assert get_response.status_code == 200

        retrieved_data = json.loads(get_response.data)

        # Verify data consistency
        assert retrieved_data['id'] == created_data['id']
        assert retrieved_data['username'] == created_data['username']
        assert retrieved_data['email'] == created_data['email']
        assert retrieved_data['username'] == original_data['username']
        assert retrieved_data['email'] == original_data['email']
