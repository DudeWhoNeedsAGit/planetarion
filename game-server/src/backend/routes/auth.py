from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.database import db
from backend.models import User, Planet
from backend.services.commander_xp import xp_progress
import bcrypt
import re
import random

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email):
    """Simple email validation using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_starting_planet_coordinates():
    """Generate random unoccupied coordinates for a new user's starting planet"""
    max_attempts = 100
    for _ in range(max_attempts):
        x = random.randint(1, 100)
        y = random.randint(1, 100)
        z = random.randint(1, 100)

        # Check if coordinates are already occupied
        existing_planet = Planet.query.filter_by(x=x, y=y, z=z).first()
        if not existing_planet:
            return x, y, z

    # If we can't find empty coordinates after max attempts, use a larger range
    x = random.randint(1, 500)
    y = random.randint(1, 500)
    z = random.randint(1, 500)
    return x, y, z

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              description: Unique username for the user
              example: "johndoe"
            email:
              type: string
              format: email
              description: Valid email address
              example: "john@example.com"
            password:
              type: string
              minLength: 8
              description: Password for authentication
              example: "securepassword123"
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User registered successfully"
            access_token:
              type: string
              description: JWT access token for authentication
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: "johndoe"
                email:
                  type: string
                  example: "john@example.com"
      400:
        description: Missing required fields or invalid email format
      409:
        description: Username or email already exists
    """
    print("DEBUG: Register endpoint called")
    data = request.get_json()
    print(f"DEBUG: Registration data received: {data}")

    if not data or not all(k in data for k in ('username', 'email', 'password')):
        print("DEBUG: Missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate email format
    if not validate_email(data['email']):
        print("DEBUG: Invalid email format")
        return jsonify({'error': 'Invalid email format'}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        print(f"DEBUG: Username already exists: {data['username']}")
        return jsonify({'error': 'Username already exists'}), 409

    existing_email = User.query.filter_by(email=data['email']).first()
    if existing_email:
        print(f"DEBUG: Email already exists: {data['email']}")
        return jsonify({'error': 'Email already exists'}), 409

    print("DEBUG: Hashing password")
    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    print("DEBUG: Creating new user")
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()
    print(f"DEBUG: User created with ID: {user.id}")

    # Create starting planet for new user
    x, y, z = generate_starting_planet_coordinates()
    print(f"DEBUG: Creating starting planet at coordinates: {x}, {y}, {z}")
    starting_planet = Planet(
        name=f"{user.username}'s Homeworld",
        x=x,
        y=y,
        z=z,
        user_id=user.id,
        metal=1000,      # Starting resources
        crystal=500,
        deuterium=0,
        metal_mine=1,    # Basic structures
        crystal_mine=1,
        deuterium_synthesizer=0,
        solar_plant=1,
        fusion_reactor=0
    )

    db.session.add(starting_planet)
    db.session.commit()
    print(f"DEBUG: Starting planet created with ID: {starting_planet.id}")

    # Create access token
    access_token = create_access_token(identity=str(user.id))
    print("DEBUG: Access token created")

    print("DEBUG: Registration successful")
    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    ---
    tags:
      - Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: User's username
              example: "johndoe"
            password:
              type: string
              description: User's password
              example: "securepassword123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Login successful"
            token:
              type: string
              description: JWT token (backward compatibility)
            access_token:
              type: string
              description: JWT access token
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: "johndoe"
                email:
                  type: string
                  example: "john@example.com"
      400:
        description: Missing username or password
      401:
        description: Invalid username or password
    """
    print("DEBUG: Login endpoint called")
    data = request.get_json()
    print(f"DEBUG: Login data received: username={data.get('username', 'N/A')}")

    if not data or not all(k in data for k in ('username', 'password')):
        print("DEBUG: Missing username or password")
        return jsonify({'error': 'Missing username or password'}), 400

    # Find user by username
    print(f"DEBUG: Looking up user: {data['username']}")
    user = User.query.filter_by(username=data['username']).first()

    if not user:
        print(f"DEBUG: User not found: {data['username']}")
        return jsonify({'error': 'Invalid username or password'}), 401

    print(f"DEBUG: User found with ID: {user.id}")
    print(f"DEBUG: Checking password for user: {user.username}")

    try:
        password_valid = bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8'))
        print(f"DEBUG: Password validation result: {password_valid}")
    except Exception as e:
        print(f"DEBUG: Password validation error: {e}")
        return jsonify({'error': 'Invalid username or password'}), 401

    if not password_valid:
        print("DEBUG: Password validation failed")
        return jsonify({'error': 'Invalid username or password'}), 401

    print("DEBUG: Password validation successful")

    # Update last login timestamp
    from datetime import datetime
    user.last_login = datetime.utcnow()
    # Treat a successful login as "seen now" so idle catch-up is computed from the prior seen time.
    if getattr(user, "last_seen_at", None) is None:
        user.last_seen_at = user.last_login
    db.session.commit()
    print("DEBUG: Last login timestamp updated")

    # Create access token
    access_token = create_access_token(identity=str(user.id))
    print("DEBUG: Access token created")

    print("DEBUG: Login successful")
    return jsonify({
        'message': 'Login successful',
        'token': access_token,        # Backward compatibility for old tests
        'access_token': access_token, # New standard format
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    # Apply offline catch-up in a delta-based way (no tick replay).
    idle = None
    try:
        from backend.services.idle_catchup import apply_idle_catchup

        idle = apply_idle_catchup(user_id)
        # `apply_idle_catchup` commits and updates user.last_seen_at; keep the user object fresh.
        user = User.query.get_or_404(user_id)
    except Exception:
        # Non-fatal; do not block auth/me.
        idle = None

    commander_xp = int(getattr(user, "commander_xp", 0) or 0)
    xp_into_level, xp_to_next = xp_progress(commander_xp)

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if getattr(user, "last_login", None) else None,
        'last_seen_at': user.last_seen_at.isoformat() if getattr(user, "last_seen_at", None) else None,
        'commander_level': int(getattr(user, "commander_level", 1) or 1),
        'commander_xp': commander_xp,
        'commander_xp_progress': {'into_level': int(xp_into_level), 'to_next': int(xp_to_next)},
        'portrait_key': getattr(user, "portrait_key", None),
        'frame_key': getattr(user, "frame_key", None),
        'idle_gains': (
            {
                'since': idle.since.isoformat() if idle else None,
                'until': idle.until.isoformat() if idle else None,
                'duration_seconds': int(idle.duration_seconds),
                'resources': idle.resources,
                'research_points': int(idle.research_points),
                'events': idle.events,
            }
            if idle
            else None
        ),
    }), 200


@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_current_user_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    from flask import request

    payload = request.get_json(silent=True) or {}
    allowed_portrait_keys = {None, "", "male", "female"}
    allowed_frame_keys = {None, ""}  # MVP: frames are derived from level; keep reserved for later.

    if "portrait_key" in payload:
        raw = payload.get("portrait_key", None)
        key = None if raw is None else str(raw).strip().lower()
        if key not in allowed_portrait_keys:
            return jsonify({"error": "Invalid portrait_key"}), 400
        user.portrait_key = key or None

    if "frame_key" in payload:
        raw = payload.get("frame_key", None)
        key = None if raw is None else str(raw).strip().lower()
        if key not in allowed_frame_keys:
            return jsonify({"error": "Invalid frame_key"}), 400
        user.frame_key = key or None

    db.session.commit()
    return jsonify(
        {
            "id": user.id,
            "portrait_key": getattr(user, "portrait_key", None),
            "frame_key": getattr(user, "frame_key", None),
        }
    ), 200
