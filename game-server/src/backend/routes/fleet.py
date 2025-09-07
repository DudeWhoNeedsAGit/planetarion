"""
Fleet Management Routes

This module handles all fleet-related operations including:
- Creating new fleets with ship composition
- Sending fleets on missions (attack, transport, colonization)
- Recalling traveling fleets
- Retrieving fleet information for authenticated users

All endpoints require JWT authentication and operate on the user's own fleets.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import User, Planet, Fleet, Research
from datetime import datetime, timedelta
import math

fleet_mgmt_bp = Blueprint('fleet_mgmt', __name__, url_prefix='/api/fleet')

@fleet_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def get_user_fleets():
    print("DEBUG: Fleet GET endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    print("DEBUG: Querying fleets for user...")
    fleets = Fleet.query.filter_by(user_id=user_id).all()
    print(f"DEBUG: Found {len(fleets)} fleets for user")

    print("DEBUG: Fleet GET endpoint successful")
    return jsonify([{
        'id': fleet.id,
        'mission': fleet.mission,
        'start_planet_id': fleet.start_planet_id,
        'target_planet_id': fleet.target_planet_id,
        'status': fleet.status,
        'ships': {
            'small_cargo': fleet.small_cargo,
            'large_cargo': fleet.large_cargo,
            'light_fighter': fleet.light_fighter,
            'heavy_fighter': fleet.heavy_fighter,
            'cruiser': fleet.cruiser,
            'battleship': fleet.battleship,
            'colony_ship': fleet.colony_ship
        },
        'departure_time': fleet.departure_time.isoformat() if fleet.departure_time else None,
        'arrival_time': fleet.arrival_time.isoformat() if fleet.arrival_time else None,
        'eta': fleet.eta
    } for fleet in fleets])

@fleet_mgmt_bp.route('', methods=['POST'])
@jwt_required()
def create_fleet():
    print("DEBUG: Fleet POST endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")
    data = request.get_json()
    print(f"DEBUG: Request data: {data}")

    if not data or 'start_planet_id' not in data or 'ships' not in data:
        print("DEBUG: Missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400

    # Verify planet ownership
    start_planet = Planet.query.filter_by(id=data['start_planet_id'], user_id=user_id).first()
    if not start_planet:
        return jsonify({'error': 'Planet not found or not owned by user'}), 404

    # Check if ships are available on the planet
    ships = data.get('ships', {})
    total_ships = sum(ships.values())

    if total_ships == 0:
        return jsonify({'error': 'Fleet must contain at least one ship'}), 400

    # Validate ship availability on the planet
    for ship_type, count in ships.items():
        if count > 0:
            available_ships = getattr(start_planet, ship_type, 0)
            if available_ships < count:
                return jsonify({
                    'error': f'Not enough {ship_type} ships available. Requested: {count}, Available: {available_ships}'
                }), 400

    # Create fleet
    fleet = Fleet(
        user_id=user_id,
        mission='stationed',  # Default mission
        start_planet_id=data['start_planet_id'],
        target_planet_id=data['start_planet_id'],  # Same as start initially
        small_cargo=ships.get('small_cargo', 0),
        large_cargo=ships.get('large_cargo', 0),
        light_fighter=ships.get('light_fighter', 0),
        heavy_fighter=ships.get('heavy_fighter', 0),
        cruiser=ships.get('cruiser', 0),
        battleship=ships.get('battleship', 0),
        colony_ship=ships.get('colony_ship', 0),
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow()  # Will be updated when sent
    )

    db.session.add(fleet)
    db.session.commit()

    return jsonify({
        'message': 'Fleet created successfully',
        'fleet': {
            'id': fleet.id,
            'mission': fleet.mission,
            'start_planet_id': fleet.start_planet_id,
            'target_planet_id': fleet.target_planet_id,
            'status': fleet.status,
            'ships': {
                'small_cargo': fleet.small_cargo,
                'large_cargo': fleet.large_cargo,
                'light_fighter': fleet.light_fighter,
                'heavy_fighter': fleet.heavy_fighter,
                'cruiser': fleet.cruiser,
                'battleship': fleet.battleship,
                'colony_ship': fleet.colony_ship
            }
        }
    }), 201

@fleet_mgmt_bp.route('/send', methods=['POST'])
@jwt_required()
def send_fleet():
    print("DEBUG: Fleet send endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")
    data = request.get_json()
    print(f"DEBUG: Request data: {data}")

    if not data or 'fleet_id' not in data or 'mission' not in data:
        print("DEBUG: Missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400

    # Get fleet
    fleet = Fleet.query.filter_by(id=data['fleet_id'], user_id=user_id).first()
    if not fleet:
        return jsonify({'error': 'Fleet not found'}), 404

    if fleet.status != 'stationed':
        return jsonify({'error': 'Fleet is not available for sending'}), 400

    # Handle different mission types
    if data['mission'] == 'explore':
        # Exploration mission - target coordinates provided
        if 'target_x' not in data or 'target_y' not in data or 'target_z' not in data:
            return jsonify({'error': 'Target coordinates required for exploration'}), 400

        target_x, target_y, target_z = data['target_x'], data['target_y'], data['target_z']

        # Create temporary planet for distance calculation
        target_planet = Planet(
            name='Exploration Target',
            x=target_x,
            y=target_y,
            z=target_z,
            user_id=None
        )

        fleet.mission = 'explore'
        fleet.target_planet_id = 0  # Temporary
        fleet.status = f'exploring:{target_x}:{target_y}:{target_z}'

    elif data['mission'] == 'colonize':
        # Enhanced colonization validation
        target_x = data.get('target_x')
        target_y = data.get('target_y')
        target_z = data.get('target_z')

        if not all([target_x is not None, target_y is not None, target_z is not None]):
            return jsonify({'error': 'Target coordinates required for colonization'}), 400

        # Check if coordinates are already occupied
        existing_planet = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).first()
        if existing_planet:
            return jsonify({'error': 'Coordinates already occupied'}), 409

        # Check colonization limits
        from backend.services.planet_traits import PlanetTraitService
        colonization_difficulty = PlanetTraitService.calculate_colonization_difficulty(target_x, target_y, target_z)

        # Get user's research level
        user_research = Research.query.filter_by(user_id=user_id).first()
        user_research_level = user_research.colonization_tech if user_research else 0

        if colonization_difficulty > user_research_level:
            return jsonify({
                'error': f'Colonization difficulty {colonization_difficulty} requires research level {colonization_difficulty}',
                'required_level': colonization_difficulty,
                'current_level': user_research_level
            }), 400

        # Check colony limit
        user_planets = Planet.query.filter_by(user_id=user_id).all()
        current_colonies = len([p for p in user_planets if p.id != user_planets[0].id])  # Exclude home planet

        max_colonies = 5  # Base limit, will be enhanced with research later
        if user_research:
            # Add research bonuses to colony limit
            max_colonies += user_research.astrophysics * 2

        if current_colonies >= max_colonies:
            return jsonify({
                'error': f'Colony limit reached ({current_colonies}/{max_colonies})',
                'current_colonies': current_colonies,
                'max_colonies': max_colonies
            }), 400

        # Create temporary planet for distance calculation
        target_planet = Planet(
            name='Empty Space',
            x=target_x,
            y=target_y,
            z=target_z,
            user_id=None  # Unowned
        )

        fleet.mission = 'colonize'
        fleet.target_planet_id = 0  # Will be updated when colony is created
        fleet.status = f'colonizing:{target_x}:{target_y}:{target_z}'

    else:
        # For other missions, target planet must exist
        if 'target_planet_id' not in data:
            return jsonify({'error': 'Target planet required'}), 400

        target_planet = Planet.query.get(data['target_planet_id'])
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        fleet.mission = data['mission']
        fleet.target_planet_id = data['target_planet_id']
        fleet.status = 'traveling'

    # Calculate distance and travel time
    start_planet = Planet.query.get(fleet.start_planet_id)
    distance = calculate_distance(start_planet, target_planet)

    # Simplified speed calculation (small cargo ship speed = 5000)
    fleet_speed = 5000  # Would be calculated based on slowest ship in fleet
    travel_time_hours = distance / fleet_speed

    fleet.departure_time = datetime.utcnow()
    fleet.arrival_time = fleet.departure_time + timedelta(hours=travel_time_hours)
    fleet.eta = int(travel_time_hours * 3600)  # ETA in seconds

    db.session.commit()

    return jsonify({
        'message': 'Fleet sent successfully',
        'fleet': {
            'id': fleet.id,
            'mission': fleet.mission,
            'target_planet_id': fleet.target_planet_id,
            'status': fleet.status,
            'departure_time': fleet.departure_time.isoformat(),
            'arrival_time': fleet.arrival_time.isoformat(),
            'eta': fleet.eta
        }
    })

@fleet_mgmt_bp.route('/recall/<int:fleet_id>', methods=['POST'])
@jwt_required()
def recall_fleet(fleet_id):
    print("DEBUG: Fleet recall endpoint called")
    print(f"DEBUG: Fleet ID: {fleet_id}")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not fleet:
        print("DEBUG: Fleet not found")
        return jsonify({'error': 'Fleet not found'}), 404

    if fleet.status not in ['traveling', 'returning']:
        return jsonify({'error': 'Fleet cannot be recalled'}), 400

    # Calculate return time (simplified - same speed back)
    now = datetime.utcnow()
    if fleet.status == 'traveling':
        # Calculate remaining time to target and double it for return
        remaining_time = (fleet.arrival_time - now).total_seconds()
        return_time = remaining_time * 2
    else:
        # Already returning, just use current ETA
        return_time = fleet.eta

    fleet.status = 'returning'
    fleet.mission = 'return'
    fleet.arrival_time = now + timedelta(seconds=return_time)
    fleet.eta = int(return_time)

    db.session.commit()

    return jsonify({
        'message': 'Fleet recalled successfully',
        'fleet': {
            'id': fleet.id,
            'status': fleet.status,
            'mission': fleet.mission,
            'arrival_time': fleet.arrival_time.isoformat(),
            'eta': fleet.eta
        }
    })

@fleet_mgmt_bp.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all_fleets():
    """Clear all fleets for the current user (for testing purposes)"""
    print("DEBUG: Clear all fleets endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    # Delete all fleets for this user
    deleted_count = Fleet.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    print(f"DEBUG: Deleted {deleted_count} fleets for user {user_id}")
    return jsonify({
        'message': f'Cleared {deleted_count} fleets successfully',
        'deleted_count': deleted_count
    })

def calculate_distance(planet1, planet2):
    """Calculate distance between two planets using 3D coordinates"""
    dx = planet1.x - planet2.x
    dy = planet1.y - planet2.y
    dz = planet1.z - planet2.z

    # Euclidean distance in 3D space
    distance = math.sqrt(dx**2 + dy**2 + dz**2)

    # Minimum distance of 1 to avoid division by zero
    return max(distance, 1)
