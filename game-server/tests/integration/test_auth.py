import pytest
import json
import os
import sys
from flask_jwt_extended import decode_token

from backend.models import User

class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_register_success(self, client, db_session):
        """Test successful user registration"""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }

        response = client.post('/api/auth/register',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'user' in data
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'newuser@example.com'

    def test_register_duplicate_username(self, client, db_session, sample_user):
        """Test registration with duplicate username"""
        user_data = {
            'username': 'testuser',  # Same as sample_user
            'email': 'different@example.com',
            'password': 'securepassword123'
        }

        response = client.post('/api/auth/register',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_register_duplicate_email(self, client, db_session, sample_user):
        """Test registration with duplicate email"""
        user_data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Same as sample_user
            'password': 'securepassword123'
        }

        response = client.post('/api/auth/register',
                             data=json.dumps(user_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        incomplete_data = {
            'username': 'testuser'
            # Missing email and password
        }

        response = client.post('/api/auth/register',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        invalid_data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'securepassword123'
        }

        response = client.post('/api/auth/register',
                             data=json.dumps(invalid_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_success(self, client, db_session, sample_user):
        """Test successful login"""
        # First register the user
        register_data = {
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'testpassword123'
        }

        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')

        # Now try to login
        login_data = {
            'username': 'loginuser',
            'password': 'testpassword123'
        }

        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['username'] == 'loginuser'

        # Verify token is valid
        token = data['access_token']
        decoded = decode_token(token)
        assert decoded['sub'] == 'loginuser'

    def test_login_wrong_password(self, client, db_session):
        """Test login with wrong password"""
        # First register the user
        register_data = {
            'username': 'wrongpassuser',
            'email': 'wrongpass@example.com',
            'password': 'correctpassword'
        }

        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')

        # Try to login with wrong password
        login_data = {
            'username': 'wrongpassuser',
            'password': 'wrongpassword'
        }

        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        login_data = {
            'username': 'nonexistent',
            'password': 'password123'
        }

        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')

        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data

    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        incomplete_data = {
            'username': 'testuser'
            # Missing password
        }

        response = client.post('/api/auth/login',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

class TestAuthIntegration:
    """Test authentication integration scenarios"""

    def test_register_then_login_workflow(self, client):
        """Test complete register -> login workflow"""
        # Register
        register_data = {
            'username': 'workflowuser',
            'email': 'workflow@example.com',
            'password': 'workflowpass123'
        }

        register_response = client.post('/api/auth/register',
                                      data=json.dumps(register_data),
                                      content_type='application/json')

        assert register_response.status_code == 201

        # Login
        login_data = {
            'username': 'workflowuser',
            'password': 'workflowpass123'
        }

        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')

        assert login_response.status_code == 200

        login_data = json.loads(login_response.data)
        assert 'access_token' in login_data

    def test_multiple_registrations_unique(self, client):
        """Test multiple registrations with unique data"""
        users = [
            {'username': 'user1', 'email': 'user1@example.com', 'password': 'pass1'},
            {'username': 'user2', 'email': 'user2@example.com', 'password': 'pass2'},
            {'username': 'user3', 'email': 'user3@example.com', 'password': 'pass3'}
        ]

        for user_data in users:
            response = client.post('/api/auth/register',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201

    def test_login_updates_last_login(self, client, db_session):
        """Test that login updates user's last_login timestamp"""
        from models import User
        from datetime import datetime

        # Register user
        register_data = {
            'username': 'lastloginuser',
            'email': 'lastlogin@example.com',
            'password': 'password123'
        }

        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')

        # Login
        login_data = {
            'username': 'lastloginuser',
            'password': 'password123'
        }

        before_login = datetime.utcnow()
        client.post('/api/auth/login',
                   data=json.dumps(login_data),
                   content_type='application/json')

        # Check last_login was updated
        user = db_session.query(User).filter_by(username='lastloginuser').first()
        assert user.last_login is not None
        assert user.last_login >= before_login
