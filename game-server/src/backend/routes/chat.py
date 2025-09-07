from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import db
from ..models import ChatMessage, User
import re
from datetime import datetime, timedelta

chat_bp = Blueprint('chat', __name__)

# Rate limiting storage (in production, use Redis)
user_message_counts = {}

# Emoji mapping for text-to-emoji replacement
EMOJI_MAP = {
    '<3': '❤️',
    '<33': '💕',
    ':)': '😊',
    ':-)': '😊',
    ':(': '😢',
    ':-(': '😢',
    ':D': '😃',
    ':-D': '😃',
    ';)': '😉',
    ';-)': '😉',
    ':P': '😛',
    ':-P': '😛',
    ':p': '😛',
    ':-p': '😛',
    'o/': '👋',
    '\\o/': '🙌',
    ':*': '😘',
    ':-*': '😘',
    'B)': '😎',
    'B-)': '😎',
    '8)': '😎',
    '8-)': '😎',
    ':/': '😕',
    ':-/': '😕',
    ':\\': '😕',
    ':-\\': '😕',
    ':o': '😮',
    ':-o': '😮',
    ':O': '😮',
    ':-O': '😮',
    '>:(': '😠',
    '>:-(': '😠',
    'T_T': '😢',
    'T.T': '😢',
    '^_^': '😊',
    'u.u': '😢',
    'n.n': '😢',
    # Game-specific emojis
    '(y)': '👍',
    '(n)': '👎',
    '(metal)': '⛏️',
    '(crystal)': '💎',
    '(deuterium)': '⚡',
}

def check_rate_limit(user_id):
    """Check if user has exceeded rate limit (5 messages per 10 seconds)"""
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=10)

    if user_id not in user_message_counts:
        user_message_counts[user_id] = []

    # Remove old messages outside the window
    user_message_counts[user_id] = [
        timestamp for timestamp in user_message_counts[user_id]
        if timestamp > window_start
    ]

    # Check if under limit
    if len(user_message_counts[user_id]) >= 5:
        return False

    # Add current message timestamp
    user_message_counts[user_id].append(now)
    return True

def sanitize_message(message):
    """Sanitize message content"""
    if not message:
        return ""

    # Replace text emojis with Unicode emojis FIRST (before HTML removal)
    # Sort by length (longest first) to avoid partial replacements
    for text_emoji in sorted(EMOJI_MAP.keys(), key=len, reverse=True):
        message = message.replace(text_emoji, EMOJI_MAP[text_emoji])

    # Remove HTML tags (but be careful not to remove emoji Unicode)
    message = re.sub(r'<[^>]+>', '', message)

    # Basic profanity filter (expand as needed)
    profanity_words = ['badword1', 'badword2']  # Add actual words as needed
    for word in profanity_words:
        message = re.sub(r'\b' + re.escape(word) + r'\b', '***', message, flags=re.IGNORECASE)

    # Trim whitespace
    message = message.strip()

    # Limit length (after emoji replacement to account for emoji characters)
    if len(message) > 500:
        message = message[:500] + "..."

    return message

@chat_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """Get recent chat messages"""
    print("DEBUG: Chat get_messages endpoint called")

    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        if limit > 100:  # Max limit
            limit = 100

        print(f"DEBUG: Fetching {limit} messages")

        # Fetch messages ordered by timestamp (newest first)
        messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(limit).all()

        # Reverse to get chronological order (oldest first)
        messages.reverse()

        # Format response
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'user_id': msg.user_id,
                'username': msg.username,
                'message': msg.message,
                'timestamp': msg.timestamp.isoformat(),
                'is_system': msg.is_system
            })

        print(f"DEBUG: Returning {len(message_list)} messages")
        return jsonify({
            'messages': message_list,
            'count': len(message_list)
        }), 200

    except Exception as e:
        print(f"DEBUG: Error fetching messages: {e}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

@chat_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    """Send a new chat message"""
    print("DEBUG: Chat send_message endpoint called")

    try:
        # Get current user
        current_user_id = get_jwt_identity()
        print(f"DEBUG: User ID: {current_user_id}")

        # Get request data
        data = request.get_json()
        print(f"DEBUG: Request data: {data}")

        if not data or 'message' not in data:
            print("DEBUG: Missing message field")
            return jsonify({'error': 'Message is required'}), 400

        raw_message = data['message']
        print(f"DEBUG: Raw message: {raw_message}")

        # Validate user exists
        user = User.query.get(current_user_id)
        if not user:
            print("DEBUG: User not found")
            return jsonify({'error': 'User not found'}), 404

        # Check rate limit
        if not check_rate_limit(current_user_id):
            print("DEBUG: Rate limit exceeded")
            return jsonify({'error': 'Rate limit exceeded. Please wait before sending another message.'}), 429

        # Sanitize message
        sanitized_message = sanitize_message(raw_message)
        if not sanitized_message:
            print("DEBUG: Message empty after sanitization")
            return jsonify({'error': 'Message cannot be empty'}), 400

        print(f"DEBUG: Sanitized message: {sanitized_message}")

        # Create message
        chat_message = ChatMessage(
            user_id=current_user_id,
            username=user.username,
            message=sanitized_message,
            is_system=False
        )

        # Save to database
        db.session.add(chat_message)
        db.session.commit()

        print("DEBUG: Message saved successfully")
        print(f"DEBUG: Message ID: {chat_message.id}")

        # Return success response
        return jsonify({
            'message': 'Message sent successfully',
            'id': chat_message.id,
            'timestamp': chat_message.timestamp.isoformat()
        }), 201

    except Exception as e:
        print(f"DEBUG: Error sending message: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500

@chat_bp.route('/messages/system', methods=['POST'])
@jwt_required()
def send_system_message():
    """Send a system message (admin/debug only)"""
    print("DEBUG: Chat send_system_message endpoint called")

    try:
        # Get current user (for logging)
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get request data
        data = request.get_json()
        print(f"DEBUG: System message request: {data}")

        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400

        # Create system message
        system_message = ChatMessage(
            user_id=current_user_id,  # System messages still need a user_id for FK
            username='SYSTEM',
            message=data['message'],
            is_system=True
        )

        # Save to database
        db.session.add(system_message)
        db.session.commit()

        print("DEBUG: System message sent successfully")

        return jsonify({
            'message': 'System message sent successfully',
            'id': system_message.id
        }), 201

    except Exception as e:
        print(f"DEBUG: Error sending system message: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to send system message'}), 500
