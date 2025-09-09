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
from backend.services.fleet_arrival import FleetArrivalService, COLONIZATION_ERRORS, MISSION_ERRORS
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

    # Import here to avoid circular imports
    from backend.services.fleet_travel import FleetTravelService

    # Get planet information for display
    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

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
            'colony_ship': fleet.colony_ship,
            'recycler': fleet.recycler
        },
        'departure_time': fleet.departure_time.isoformat() if fleet.departure_time else None,
        'arrival_time': fleet.arrival_time.isoformat() if fleet.arrival_time else None,
        'eta': fleet.eta,
        # Enhanced travel information
        'travel_info': FleetTravelService.calculate_travel_info(fleet),
        'start_planet': get_planet_info(fleet.start_planet_id, planet_dict),
        'target_planet': get_planet_info(fleet.target_planet_id, planet_dict) if fleet.target_planet_id and fleet.target_planet_id > 0 else None
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
        recycler=ships.get('recycler', 0),
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
                'colony_ship': fleet.colony_ship,
                'recycler': fleet.recycler
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

    elif data['mission'] == 'attack':
        # Attack mission - target must be enemy planet
        if 'target_planet_id' not in data:
            return jsonify({'error': 'Target planet required for attack mission'}), 400

        target_planet = Planet.query.get(data['target_planet_id'])
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Cannot attack own planets
        if target_planet.user_id == user_id:
            return jsonify({'error': 'Cannot attack your own planet'}), 400

        # Check if target planet is owned (attacks on unowned planets would be colonization)
        if not target_planet.user_id:
            return jsonify({'error': 'Cannot attack unowned planet. Use colonization instead.'}), 400

        fleet.mission = 'attack'
        fleet.target_planet_id = data['target_planet_id']
        fleet.status = 'traveling'

    elif data['mission'] == 'defend':
        # Defend mission - station fleet at planet for defense
        if 'target_planet_id' not in data:
            return jsonify({'error': 'Target planet required for defend mission'}), 400

        target_planet = Planet.query.get(data['target_planet_id'])
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Must own the planet to defend it
        if target_planet.user_id != user_id:
            return jsonify({'error': 'Cannot defend planet you do not own'}), 400

        fleet.mission = 'defend'
        fleet.target_planet_id = data['target_planet_id']
        fleet.status = 'defending'

    elif data['mission'] == 'recycle':
        # Recycle mission - collect debris from planet
        if 'target_planet_id' not in data:
            return jsonify({'error': 'Target planet required for recycle mission'}), 400

        target_planet = Planet.query.get(data['target_planet_id'])
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Check if there are recyclers in the fleet
        if fleet.recycler <= 0:
            return jsonify({'error': 'Fleet must contain recycler ships for recycle mission'}), 400

        fleet.mission = 'recycle'
        fleet.target_planet_id = data['target_planet_id']
        fleet.status = 'traveling'

    elif data['mission'] == 'colonize':
        # Enhanced colonization validation with comprehensive error handling

        # Validate colony ship presence
        if fleet.colony_ship <= 0:
            return jsonify({'error': COLONIZATION_ERRORS['no_colony_ship']}), 400

        # Parse target coordinates
        target_x = data.get('target_x')
        target_y = data.get('target_y')
        target_z = data.get('target_z')
        target_planet_id = data.get('target_planet_id')

        # Handle planet selection
        if target_planet_id and str(target_planet_id).isdigit():
            target_planet = Planet.query.get(int(target_planet_id))
            if not target_planet:
                return jsonify({'error': COLONIZATION_ERRORS['planet_not_found']}), 404

            if target_planet.user_id:
                return jsonify({'error': COLONIZATION_ERRORS['coordinates_occupied']}), 409

            # Use planet's coordinates
            target_x, target_y, target_z = target_planet.x, target_planet.y, target_planet.z
            fleet.target_planet_id = target_planet.id

        # Handle direct coordinate entry
        elif target_x is not None and target_y is not None and target_z is not None:
            try:
                target_x, target_y, target_z = int(target_x), int(target_y), int(target_z)
            except ValueError:
                return jsonify({'error': COLONIZATION_ERRORS['invalid_coordinates']}), 400

            # Check if coordinates are already occupied
            existing_planet = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).first()
            if existing_planet:
                return jsonify({'error': COLONIZATION_ERRORS['coordinates_occupied']}), 409

            fleet.target_planet_id = 0  # Will be updated when colony is created

        else:
            return jsonify({'error': COLONIZATION_ERRORS['invalid_coordinates']}), 400

        # Validate research requirements
        from backend.services.planet_traits import PlanetTraitService
        colonization_difficulty = PlanetTraitService.calculate_colonization_difficulty(target_x, target_y, target_z)

        user_research = Research.query.filter_by(user_id=user_id).first()
        user_research_level = user_research.colonization_tech if user_research else 0

        if colonization_difficulty > user_research_level:
            return jsonify({
                'error': COLONIZATION_ERRORS['insufficient_research'],
                'required_level': colonization_difficulty,
                'current_level': user_research_level
            }), 400

        # Validate colony limits
        user_planets = Planet.query.filter_by(user_id=user_id).all()
        current_colonies = len([p for p in user_planets if not getattr(p, 'is_home_planet', False)])

        max_colonies = 5  # Base limit
        if user_research:
            max_colonies += user_research.astrophysics * 2

        if current_colonies >= max_colonies:
            return jsonify({
                'error': COLONIZATION_ERRORS['colony_limit_reached'],
                'current_colonies': current_colonies,
                'max_colonies': max_colonies
            }), 400

        # Validate fuel requirements
        start_planet = Planet.query.get(fleet.start_planet_id)
        distance = calculate_distance(start_planet, Planet(
            name='Target', x=target_x, y=target_y, z=target_z, user_id=None
        ))

        fuel_validation = FleetArrivalService.validate_colonization_fuel(fleet, distance)
        if not fuel_validation['success']:
            return jsonify({
                'error': fuel_validation['error'],
                'fuel_required': fuel_validation['fuel_required'],
                'fuel_available': fuel_validation['fuel_available']
            }), 400

        # Deduct fuel from origin planet
        start_planet.deuterium -= fuel_validation['fuel_required']

        # Create temporary planet for distance calculation
        target_planet = Planet(
            name='Empty Space',
            x=target_x,
            y=target_y,
            z=target_z,
            user_id=None  # Unowned
        )

        fleet.mission = 'colonize'
        fleet.target_coordinates = f"{target_x}:{target_y}:{target_z}"  # Store coordinates for arrival processing
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

    # Use FleetTravelService for consistent speed calculation (now 30x faster)
    from backend.services.fleet_travel import FleetTravelService
    fleet_speed = FleetTravelService.calculate_fleet_speed(fleet)
    travel_time_hours = distance / fleet_speed if fleet_speed > 0 else 0

    # Apply minimum travel time to prevent instant arrivals (30 seconds minimum)
    MIN_TRAVEL_TIME_SECONDS = 30
    travel_time_seconds = max(travel_time_hours * 3600, MIN_TRAVEL_TIME_SECONDS)
    travel_time_hours = travel_time_seconds / 3600

    fleet.departure_time = datetime.utcnow()
    fleet.arrival_time = fleet.departure_time + timedelta(seconds=travel_time_seconds)
    fleet.eta = int(travel_time_seconds)

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

    if fleet.status not in ['traveling', 'returning'] and not fleet.status.startswith('exploring:') and not fleet.status.startswith('colonizing:'):
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
            'eta': fleet.eta,
            'ships': {  # Include ships data to prevent frontend crashes
                'small_cargo': fleet.small_cargo,
                'large_cargo': fleet.large_cargo,
                'light_fighter': fleet.light_fighter,
                'heavy_fighter': fleet.heavy_fighter,
                'cruiser': fleet.cruiser,
                'battleship': fleet.battleship,
                'colony_ship': fleet.colony_ship,
                'recycler': fleet.recycler
            }
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

def get_planet_info(planet_id, planet_dict):
    """Get planet information for API response"""
    if not planet_id:
        return None

    # Try to get from cached dict first
    planet = planet_dict.get(planet_id)
    if not planet:
        # Fallback to database query
        planet = Planet.query.get(planet_id)

    if not planet:
        return {
            'id': planet_id,
            'name': 'Unknown',
            'coordinates': 'N/A'
        }

    return {
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}"
    }

def calculate_distance(planet1, planet2):
    """Calculate distance between two planets using 3D coordinates"""
    dx = planet1.x - planet2.x
    dy = planet1.y - planet2.y
    dz = planet1.z - planet2.z

    # Euclidean distance in 3D space
    distance = math.sqrt(dx**2 + dy**2 + dz**2)

    # Minimum distance of 1 to avoid division by zero
    return max(distance, 1)
