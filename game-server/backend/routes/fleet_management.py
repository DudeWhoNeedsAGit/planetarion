from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, Planet, Fleet
from datetime import datetime, timedelta
import math

fleet_mgmt_bp = Blueprint('fleet_mgmt', __name__, url_prefix='/api/fleet')

@fleet_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def get_user_fleets():
    user_id = get_jwt_identity()
    fleets = Fleet.query.filter_by(user_id=user_id).all()

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
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'start_planet_id' not in data or 'ships' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Verify planet ownership
    start_planet = Planet.query.filter_by(id=data['start_planet_id'], user_id=user_id).first()
    if not start_planet:
        return jsonify({'error': 'Planet not found or not owned by user'}), 404

    # Check if ships are available on the planet (simplified - in real game would track ship counts)
    ships = data.get('ships', {})
    total_ships = sum(ships.values())

    if total_ships == 0:
        return jsonify({'error': 'Fleet must contain at least one ship'}), 400

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
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'fleet_id' not in data or 'target_planet_id' not in data or 'mission' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get fleet
    fleet = Fleet.query.filter_by(id=data['fleet_id'], user_id=user_id).first()
    if not fleet:
        return jsonify({'error': 'Fleet not found'}), 404

    if fleet.status != 'stationed':
        return jsonify({'error': 'Fleet is not available for sending'}), 400

    # Handle different mission types
    if data['mission'] == 'colonize':
        # Check if coordinates are already occupied
        target_planet = Planet.query.filter_by(
            x=data.get('target_x'),
            y=data.get('target_y'),
            z=data.get('target_z')
        ).first()
        if target_planet:
            return jsonify({'error': 'Coordinates already occupied'}), 409

        # For colonization, create a temporary planet entry for distance calculation
        target_planet = Planet(
            name='Empty Space',
            x=data['target_x'],
            y=data['target_y'],
            z=data['target_z'],
            user_id=None  # Unowned
        )
        # Don't commit this temporary planet to DB yet
    else:
        # For other missions, target planet must exist
        target_planet = Planet.query.get(data['target_planet_id'])
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

    # Calculate distance and travel time
    start_planet = Planet.query.get(fleet.start_planet_id)
    distance = calculate_distance(start_planet, target_planet)

    # Simplified speed calculation (small cargo ship speed = 5000)
    fleet_speed = 5000  # Would be calculated based on slowest ship in fleet
    travel_time_hours = distance / fleet_speed

    # Update fleet
    fleet.mission = data['mission']
    if data['mission'] == 'colonize':
        # Store coordinates in target_planet_id field temporarily (hack for demo)
        fleet.target_planet_id = 0  # Will be updated when colony is created
        # Store coordinates in a way we can retrieve them
        fleet.status = f'colonizing:{data["target_x"]}:{data["target_y"]}:{data["target_z"]}'
    else:
        fleet.target_planet_id = data['target_planet_id']
        fleet.status = 'traveling'

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
    user_id = get_jwt_identity()

    fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not fleet:
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

def calculate_distance(planet1, planet2):
    """Calculate distance between two planets using 3D coordinates"""
    dx = planet1.x - planet2.x
    dy = planet1.y - planet2.y
    dz = planet1.z - planet2.z

    # Euclidean distance in 3D space
    distance = math.sqrt(dx**2 + dy**2 + dz**2)

    # Minimum distance of 1 to avoid division by zero
    return max(distance, 1)
