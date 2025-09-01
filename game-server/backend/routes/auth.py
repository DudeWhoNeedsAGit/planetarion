from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db
from models import User, Planet
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
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate email format
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()

    # Create starting planet for new user
    x, y, z = generate_starting_planet_coordinates()
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

    # Create access token
    access_token = create_access_token(identity=str(user.id))

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
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'Missing username or password'}), 400

    # Find user by username
    user = User.query.filter_by(username=data['username']).first()

    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Update last login timestamp
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Create access token
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 200
