import pytest
import json
from datetime import datetime
from backend.models import ChatMessage, User, db


class TestChatAPI:
    """Integration tests for chat API endpoints"""

    def test_get_messages_empty(self, client, auth_headers):
        """Test getting messages when none exist"""
        # Act
        response = client.get('/api/chat/messages', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0
        assert data['messages'] == []

    def test_send_message_success(self, client, auth_headers, test_user):
        """Test sending a message successfully"""
        # Arrange
        message_data = {'message': 'Hello world'}

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'id' in data
        assert 'timestamp' in data
        assert data['message'] == 'Message sent successfully'

        # Verify message was saved to database
        saved_message = ChatMessage.query.filter_by(id=data['id']).first()
        assert saved_message is not None
        assert saved_message.message == 'Hello world'
        assert saved_message.username == test_user.username
        assert saved_message.is_system == False

    def test_send_message_missing_field(self, client, auth_headers):
        """Test sending message without required field"""
        # Arrange
        message_data = {}  # Missing 'message' field

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error']

    def test_send_message_empty_after_sanitization(self, client, auth_headers):
        """Test sending message that becomes empty after sanitization"""
        # Arrange
        message_data = {'message': '   '}  # Only whitespace

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'empty' in data['error']

    def test_send_message_too_long(self, client, auth_headers):
        """Test sending message that exceeds length limit"""
        # Arrange
        long_message = 'a' * 600  # Exceeds 500 char limit
        message_data = {'message': long_message}

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 201  # Should succeed but be truncated
        data = json.loads(response.data)

        # Verify message was truncated
        saved_message = ChatMessage.query.filter_by(id=data['id']).first()
        assert len(saved_message.message) <= 503  # 500 + "..."
        assert saved_message.message.endswith('...')

    def test_get_messages_with_data(self, client, auth_headers, test_user):
        """Test getting messages when data exists"""
        # Arrange - Create some test messages
        msg1 = ChatMessage(user_id=test_user.id, username=test_user.username,
                          message="First message", is_system=False)
        msg2 = ChatMessage(user_id=test_user.id, username=test_user.username,
                          message="Second message", is_system=False)
        db.session.add_all([msg1, msg2])
        db.session.commit()

        # Act
        response = client.get('/api/chat/messages', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 2
        assert len(data['messages']) == 2

        # Check message order (should be chronological)
        messages = data['messages']
        assert messages[0]['message'] == "First message"
        assert messages[1]['message'] == "Second message"

        # Check message structure
        for msg in messages:
            assert 'id' in msg
            assert 'user_id' in msg
            assert 'username' in msg
            assert 'message' in msg
            assert 'timestamp' in msg
            assert 'is_system' in msg

    def test_get_messages_limit(self, client, auth_headers, test_user):
        """Test message limit parameter"""
        # Arrange - Create more messages than limit
        messages = []
        for i in range(10):
            msg = ChatMessage(user_id=test_user.id, username=test_user.username,
                             message=f"Message {i}", is_system=False)
            messages.append(msg)
        db.session.add_all(messages)
        db.session.commit()

        # Act - Request only 5 messages
        response = client.get('/api/chat/messages?limit=5', headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 5
        assert len(data['messages']) == 5

    def test_get_messages_max_limit(self, client, auth_headers, test_user):
        """Test that limit cannot exceed maximum"""
        # Arrange - Create many messages
        messages = []
        for i in range(150):
            msg = ChatMessage(user_id=test_user.id, username=test_user.username,
                             message=f"Message {i}", is_system=False)
            messages.append(msg)
        db.session.add_all(messages)
        db.session.commit()

        # Act - Try to request more than max limit (100)
        response = client.get('/api/chat/messages?limit=150', headers=auth_headers)

        # Assert - Should be limited to 100
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] <= 100

    def test_send_system_message(self, client, auth_headers, test_user):
        """Test sending system message"""
        # Arrange
        system_data = {'message': 'Server maintenance'}

        # Act
        response = client.post('/api/chat/messages/system',
                              json=system_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'id' in data

        # Verify system message was saved
        saved_message = ChatMessage.query.filter_by(id=data['id']).first()
        assert saved_message is not None
        assert saved_message.message == 'Server maintenance'
        assert saved_message.username == 'SYSTEM'
        assert saved_message.is_system == True

    def test_unauthorized_access(self, client):
        """Test accessing chat endpoints without authentication"""
        # Act
        response = client.get('/api/chat/messages')

        # Assert
        assert response.status_code == 401

    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting functionality"""
        # Clear any existing rate limiting data for this user
        from backend.routes.chat import user_message_counts
        test_user_id = '1'  # This is the user ID from our test setup
        if test_user_id in user_message_counts:
            user_message_counts[test_user_id] = []

        # Send messages up to the rate limit (5 messages per 10 seconds)
        for i in range(5):  # Should all succeed
            message_data = {'message': f'Test message {i}'}
            response = client.post('/api/chat/messages',
                                  json=message_data,
                                  headers=auth_headers)
            assert response.status_code == 201

        # The 6th message should be rate limited
        message_data = {'message': 'Test message 6'}
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)
        assert response.status_code == 429  # Too Many Requests

    def test_send_message_with_emojis(self, client, auth_headers, test_user):
        """Test sending message with emoji replacements"""
        # Clear any existing rate limiting data for this user
        from backend.routes.chat import user_message_counts
        test_user_id = '1'  # This is the user ID from our test setup
        if test_user_id in user_message_counts:
            user_message_counts[test_user_id] = []

        # Arrange
        message_data = {'message': 'I love this game <3 :)'}

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)

        # Verify emojis were replaced in the saved message
        saved_message = ChatMessage.query.filter_by(id=data['id']).first()
        assert saved_message is not None
        assert saved_message.message == 'I love this game ❤️ 😊'
        assert '<3' not in saved_message.message
        assert ':)' not in saved_message.message
        assert '❤️' in saved_message.message
        assert '😊' in saved_message.message

    def test_send_message_with_game_emojis(self, client, auth_headers, test_user):
        """Test sending message with game-specific emoji replacements"""
        # Clear any existing rate limiting data for this user
        from backend.routes.chat import user_message_counts
        test_user_id = '1'  # This is the user ID from our test setup
        if test_user_id in user_message_counts:
            user_message_counts[test_user_id] = []

        # Arrange
        message_data = {'message': 'I need more (metal) and (crystal) (y)'}

        # Act
        response = client.post('/api/chat/messages',
                              json=message_data,
                              headers=auth_headers)

        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)

        # Verify game emojis were replaced
        saved_message = ChatMessage.query.filter_by(id=data['id']).first()
        assert saved_message is not None
        assert saved_message.message == 'I need more ⛏️ and 💎 👍'
        assert '(metal)' not in saved_message.message
        assert '(crystal)' not in saved_message.message
        assert '(y)' not in saved_message.message
        assert '⛏️' in saved_message.message
        assert '💎' in saved_message.message
        assert '👍' in saved_message.message
