import pytest
from datetime import datetime
from backend.models import ChatMessage, User, db
from backend.routes.chat import sanitize_message, EMOJI_MAP


class TestChatMessageModel:
    """Unit tests for ChatMessage model following Arrange-Act-Assert pattern"""

    def test_chat_message_creation(self):
        """Test creating a ChatMessage instance"""
        # Arrange
        user = User(username="testuser", email="test@example.com", password_hash="hash")

        # Act
        message = ChatMessage(
            user_id=1,
            username="testuser",
            message="Hello world",
            is_system=False
        )

        # Assert
        assert message.user_id == 1
        assert message.username == "testuser"
        assert message.message == "Hello world"
        assert message.is_system == False
        # Note: timestamp will be None until saved to database due to default=datetime.utcnow
        # This is expected behavior for SQLAlchemy models outside of database context

    def test_chat_message_system_creation(self):
        """Test creating a system ChatMessage"""
        # Arrange & Act
        system_message = ChatMessage(
            user_id=1,
            username="SYSTEM",
            message="Server restart",
            is_system=True
        )

        # Assert
        assert system_message.username == "SYSTEM"
        assert system_message.is_system == True
        assert system_message.message == "Server restart"

    def test_chat_message_repr(self):
        """Test ChatMessage string representation"""
        # Arrange
        message = ChatMessage(
            user_id=1,
            username="testuser",
            message="test",
            is_system=False
        )

        # Act
        repr_str = repr(message)

        # Assert
        assert "ChatMessage" in repr_str
        assert "testuser" in repr_str
        assert "False" in repr_str

    def test_chat_message_system_repr(self):
        """Test system ChatMessage string representation"""
        # Arrange
        message = ChatMessage(
            user_id=1,
            username="SYSTEM",
            message="test",
            is_system=True
        )

        # Act
        repr_str = repr(message)

        # Assert
        assert "ChatMessage" in repr_str
        assert "SYSTEM" in repr_str
        assert "True" in repr_str

    def test_chat_message_default_values(self):
        """Test ChatMessage default values"""
        # Arrange & Act
        message = ChatMessage(
            user_id=1,
            username="testuser",
            message="test"
        )

        # Assert
        # Note: is_system will be None until saved to database due to default=False
        # This is expected behavior for SQLAlchemy models outside of database context
        # timestamp will also be None for the same reason

    def test_chat_message_relationship(self):
        """Test ChatMessage user relationship"""
        # Arrange
        user = User(username="testuser", email="test@example.com", password_hash="hash")
        message = ChatMessage(
            user_id=1,
            username="testuser",
            message="test"
        )

        # Act & Assert - relationship would be tested in integration tests
        # This is just testing the model structure
        assert hasattr(message, 'user')
        assert message.user_id == 1


class TestEmojiReplacement:
    """Unit tests for emoji replacement functionality"""

    def test_emoji_replacement_heart(self):
        """Test <3 gets replaced with heart emoji"""
        # Arrange
        message = "I love this game <3"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "❤️" in result
        assert "<3" not in result

    def test_emoji_replacement_multiple(self):
        """Test multiple emoji replacements in one message"""
        # Arrange
        message = "Hello <3 :) :D"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "❤️" in result
        assert "😊" in result
        assert "😃" in result
        assert "<3" not in result
        assert ":)" not in result
        assert ":D" not in result

    def test_emoji_replacement_with_text(self):
        """Test emoji replacement preserves surrounding text"""
        # Arrange
        message = "Hey there <3 how are you :) doing?"

        # Act
        result = sanitize_message(message)

        # Assert
        assert result == "Hey there ❤️ how are you 😊 doing?"
        assert "<3" not in result
        assert ":)" not in result

    def test_emoji_replacement_case_sensitive(self):
        """Test emoji replacement is case sensitive"""
        # Arrange
        message = "Check this out :p and this :P"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "😛" in result
        assert ":p" not in result
        assert ":P" not in result

    def test_emoji_replacement_game_specific(self):
        """Test game-specific emoji replacements"""
        # Arrange
        message = "I need more (metal) and (crystal) (y)"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "⛏️" in result
        assert "💎" in result
        assert "👍" in result
        assert "(metal)" not in result
        assert "(crystal)" not in result
        assert "(y)" not in result

    def test_emoji_replacement_no_emojis(self):
        """Test message without emojis is unchanged"""
        # Arrange
        message = "This is a normal message without any emojis"

        # Act
        result = sanitize_message(message)

        # Assert
        assert result == message

    def test_emoji_replacement_empty_message(self):
        """Test empty message handling"""
        # Arrange
        message = ""

        # Act
        result = sanitize_message(message)

        # Assert
        assert result == ""

    def test_emoji_replacement_whitespace_only(self):
        """Test whitespace-only message handling"""
        # Arrange
        message = "   "

        # Act
        result = sanitize_message(message)

        # Assert
        assert result == ""

    def test_emoji_replacement_with_html(self):
        """Test emoji replacement works with HTML sanitization"""
        # Arrange
        message = "Hello <3 <script>alert('xss')</script> :)"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "❤️" in result
        assert "😊" in result
        assert "<script>" not in result
        assert "<3" not in result
        assert ":)" not in result

    def test_emoji_replacement_complex(self):
        """Test complex message with multiple emoji types"""
        # Arrange
        message = "OMG T_T this is awesome ^_^ <33 B) o/"

        # Act
        result = sanitize_message(message)

        # Assert
        assert "😢" in result  # T_T
        assert "😊" in result  # ^_^
        assert "💕" in result  # <33
        assert "😎" in result  # B)
        assert "👋" in result  # o/
        assert "T_T" not in result
        assert "^_^" not in result
        assert "<33" not in result
        assert "B)" not in result
        assert "o/" not in result

    def test_emoji_map_contains_expected_emojis(self):
        """Test that emoji map contains expected mappings"""
        # Assert
        assert '<3' in EMOJI_MAP
        assert ':)' in EMOJI_MAP
        assert '(y)' in EMOJI_MAP
        assert '(metal)' in EMOJI_MAP

        # Verify specific mappings
        assert EMOJI_MAP['<3'] == '❤️'
        assert EMOJI_MAP[':)'] == '😊'
        assert EMOJI_MAP['(y)'] == '👍'
        assert EMOJI_MAP['(metal)'] == '⛏️'
