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
from backend.models import User, Planet, Fleet, Research, TickLog
from backend.config import get_forced_travel_time_seconds, get_min_travel_time_seconds
from backend.services.fleet_arrival import FleetArrivalService, COLONIZATION_ERRORS
from backend.services.fleet_state_machine import FleetStateMachine, FleetStateError
from datetime import datetime, timedelta, timezone
import math

fleet_mgmt_bp = Blueprint('fleet_mgmt', __name__, url_prefix='/api/fleet')

INVENTORY_FLEET_MISSION = 'inventory'
FLEET_SHIP_KEYS = (
    'small_cargo',
    'large_cargo',
    'light_fighter',
    'heavy_fighter',
    'cruiser',
    'battleship',
    'colony_ship',
    'recycler',
    'espionage_probe',
    'bomber',
    'destroyer',
    'deathstar',
    'battlecruiser',
)

def _iso_utc(dt: datetime | None) -> str | None:
    """Return ISO-8601 UTC timestamp with 'Z' suffix.

    Our DB stores naive datetimes; treat naive values as UTC to avoid client timezone misparsing.
    """
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

def serialize_fleet_ships(fleet):
    return {
        'small_cargo': fleet.small_cargo,
        'large_cargo': fleet.large_cargo,
        'light_fighter': fleet.light_fighter,
        'heavy_fighter': fleet.heavy_fighter,
        'cruiser': fleet.cruiser,
        'battleship': fleet.battleship,
        'colony_ship': fleet.colony_ship,
        'recycler': fleet.recycler,
        'espionage_probe': fleet.espionage_probe,
        'bomber': fleet.bomber,
        'destroyer': fleet.destroyer,
        'deathstar': fleet.deathstar,
        'battlecruiser': fleet.battlecruiser
    }


def _parse_ship_transfer_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError('Invalid ships payload')

    parsed = {}
    for ship_type, raw_count in payload.items():
        if ship_type not in FLEET_SHIP_KEYS:
            raise ValueError(f'Invalid ship type: {ship_type}')

        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            raise ValueError(f'Invalid count for {ship_type}')

        if count < 0:
            raise ValueError(f'Invalid count for {ship_type}')
        if count == 0:
            continue
        parsed[ship_type] = count

    if not parsed:
        raise ValueError('At least one ship must be specified')

    return parsed


def serialize_fleet(fleet, planet_dict=None):
    # Import here to avoid circular imports
    from backend.services.fleet_travel import FleetTravelService

    planet_dict = planet_dict or {}
    return {
        'id': fleet.id,
        'mission': fleet.mission,
        'start_planet_id': fleet.start_planet_id,
        'target_planet_id': fleet.target_planet_id,
        'status': fleet.status,
        'ships': serialize_fleet_ships(fleet),
        'departure_time': _iso_utc(fleet.departure_time),
        'arrival_time': _iso_utc(fleet.arrival_time),
        'eta': fleet.eta,
        'travel_info': FleetTravelService.calculate_travel_info(fleet),
        'start_planet': get_planet_info(fleet.start_planet_id, planet_dict),
        'target_planet': get_planet_info(fleet.target_planet_id, planet_dict) if fleet.target_planet_id and fleet.target_planet_id > 0 else None
    }

@fleet_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def get_user_fleets():
    print("DEBUG: Fleet GET endpoint called")
    user_id = int(get_jwt_identity())
    print(f"DEBUG: User ID from JWT: {user_id}")

    include_inventory = request.args.get('include_inventory', '0').lower() in ('1', 'true', 'yes')

    print("DEBUG: Querying fleets for user...")
    query = Fleet.query.filter_by(user_id=user_id)
    if not include_inventory:
        query = query.filter(Fleet.mission != INVENTORY_FLEET_MISSION)
    fleets = query.all()
    print(f"DEBUG: Found {len(fleets)} fleets for user")

    # Get planet information for display
    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

    print("DEBUG: Fleet GET endpoint successful")
    return jsonify([serialize_fleet(fleet, planet_dict) for fleet in fleets])

@fleet_mgmt_bp.route('', methods=['POST'])
@jwt_required()
def create_fleet():
    print("DEBUG: Fleet POST endpoint called")
    user_id = int(get_jwt_identity())
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

    # Check if ships are available (inventory is a stationed fleet at this planet).
    ships = data.get('ships', {})
    total_ships = sum(ships.values())

    if total_ships == 0:
        return jsonify({'error': 'Fleet must contain at least one ship'}), 400

    inventory_fleet = (
        Fleet.query.filter_by(
            user_id=user_id,
            start_planet_id=data['start_planet_id'],
            status='stationed',
            mission=INVENTORY_FLEET_MISSION,
        )
        .order_by(Fleet.id.asc())
        .first()
    )
    if not inventory_fleet:
        # Backwards-compat: fall back to old inventory convention.
        inventory_fleet = (
            Fleet.query.filter_by(user_id=user_id, start_planet_id=data['start_planet_id'], status='stationed', mission='stationed')
            .order_by(Fleet.id.asc())
            .first()
        )

    if not inventory_fleet:
        # Backwards-compat: fall back to any stationed fleet.
        inventory_fleet = (
            Fleet.query.filter_by(user_id=user_id, start_planet_id=data['start_planet_id'], status='stationed')
            .order_by(Fleet.id.asc())
            .first()
        )

    if not inventory_fleet:
        # Legacy fallback: this codebase historically tracked ship inventory on the Planet model.
        # Create an inventory fleet from the planet's ship counts so older flows/tests keep working.
        inventory_fleet = Fleet(
            user_id=user_id,
            mission=INVENTORY_FLEET_MISSION,
            status='stationed',
            start_planet_id=data['start_planet_id'],
            target_planet_id=data['start_planet_id'],
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
            small_cargo=getattr(start_planet, 'small_cargo', 0) or 0,
            large_cargo=getattr(start_planet, 'large_cargo', 0) or 0,
            light_fighter=getattr(start_planet, 'light_fighter', 0) or 0,
            heavy_fighter=getattr(start_planet, 'heavy_fighter', 0) or 0,
            cruiser=getattr(start_planet, 'cruiser', 0) or 0,
            battleship=getattr(start_planet, 'battleship', 0) or 0,
            colony_ship=getattr(start_planet, 'colony_ship', 0) or 0,
        )
        db.session.add(inventory_fleet)
        db.session.flush()

    # If the planet still has legacy ship columns, migrate them into the inventory fleet once.
    # This keeps shipyard-created inventory fleets compatible with old populate datasets.
    for ship_col in (
        'small_cargo',
        'large_cargo',
        'light_fighter',
        'heavy_fighter',
        'cruiser',
        'battleship',
        'colony_ship',
    ):
        amount = getattr(start_planet, ship_col, 0) or 0
        if amount <= 0:
            continue
        current = getattr(inventory_fleet, ship_col, 0) or 0
        setattr(inventory_fleet, ship_col, current + amount)
        setattr(start_planet, ship_col, 0)

    # Validate ship availability on the inventory fleet.
    for ship_type, count in ships.items():
        if not count or count <= 0:
            continue
        if not hasattr(inventory_fleet, ship_type):
            return jsonify({'error': f'Invalid ship type: {ship_type}'}), 400
        available_ships = getattr(inventory_fleet, ship_type, 0) or 0
        if available_ships < count:
            return jsonify({
                'error': f'Not enough {ship_type} ships available. Requested: {count}, Available: {available_ships}'
            }), 400

    # Create fleet
    fleet = Fleet(
        user_id=user_id,
        mission='stationed',  # Default mission
        status='stationed',
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
        espionage_probe=ships.get('espionage_probe', 0),
        bomber=ships.get('bomber', 0),
        destroyer=ships.get('destroyer', 0),
        deathstar=ships.get('deathstar', 0),
        battlecruiser=ships.get('battlecruiser', 0),
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow()  # Will be updated when sent
    )

    # Deduct ships from inventory fleet.
    for ship_type, count in ships.items():
        if not count or count <= 0:
            continue
        current = getattr(inventory_fleet, ship_type, 0) or 0
        setattr(inventory_fleet, ship_type, max(0, current - count))

    db.session.add(fleet)
    db.session.commit()

    return jsonify({
        'message': 'Fleet created successfully',
        'fleet': serialize_fleet(fleet, {start_planet.id: start_planet})
    }), 201

@fleet_mgmt_bp.route('/<int:fleet_id>/dissolve', methods=['POST'])
@jwt_required()
def dissolve_fleet(fleet_id: int):
    """
    Dissolve a stationed fleet back into the planet's inventory fleet.

    Allowed only for stationed fleets that are not the inventory fleet.
    """
    user_id = int(get_jwt_identity())

    fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not fleet:
        return jsonify({'error': 'Fleet not found'}), 404

    if fleet.status != 'stationed':
        return jsonify({'error': 'Only stationed fleets can be dissolved'}), 400

    if fleet.mission == INVENTORY_FLEET_MISSION:
        return jsonify({'error': 'Inventory fleet cannot be dissolved'}), 400

    # Find (or create) inventory fleet for this planet.
    inventory_fleet = (
        Fleet.query.filter_by(
            user_id=user_id,
            start_planet_id=fleet.start_planet_id,
            status='stationed',
            mission=INVENTORY_FLEET_MISSION,
        )
        .order_by(Fleet.id.asc())
        .first()
    )
    if not inventory_fleet:
        # Backwards-compat: prefer old convention before falling back to creating from Planet.
        inventory_fleet = (
            Fleet.query.filter_by(
                user_id=user_id,
                start_planet_id=fleet.start_planet_id,
                status='stationed',
                mission='stationed',
            )
            .order_by(Fleet.id.asc())
            .first()
        )

    if not inventory_fleet:
        start_planet = Planet.query.filter_by(id=fleet.start_planet_id, user_id=user_id).first()
        if not start_planet:
            return jsonify({'error': 'Start planet not found'}), 404
        inventory_fleet = Fleet(
            user_id=user_id,
            mission=INVENTORY_FLEET_MISSION,
            status='stationed',
            start_planet_id=fleet.start_planet_id,
            target_planet_id=fleet.start_planet_id,
            departure_time=datetime.utcnow(),
            arrival_time=datetime.utcnow(),
        )
        db.session.add(inventory_fleet)
        db.session.flush()

    # Return ships from this fleet into inventory.
    for ship_type, count in serialize_fleet_ships(fleet).items():
        if not count:
            continue
        current = getattr(inventory_fleet, ship_type, 0) or 0
        setattr(inventory_fleet, ship_type, current + count)
        setattr(fleet, ship_type, 0)

    db.session.delete(fleet)
    db.session.commit()

    return jsonify({'message': 'Fleet dissolved successfully'}), 200

@fleet_mgmt_bp.route('/<int:fleet_id>/split', methods=['POST'])
@jwt_required()
def split_fleet(fleet_id: int):
    """
    Split ships from one stationed fleet into a new stationed fleet on the same planet.

    The new fleet is always created with mission='stationed' to avoid creating duplicate
    inventory fleets.
    """
    user_id = int(get_jwt_identity())
    payload = request.get_json() or {}
    ships_raw = payload.get('ships')

    source_fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not source_fleet:
        return jsonify({'error': 'Fleet not found'}), 404

    if source_fleet.status != 'stationed':
        return jsonify({'error': 'Only stationed fleets can be split'}), 400

    try:
        ships = _parse_ship_transfer_payload(ships_raw)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    for ship_type, count in ships.items():
        available = getattr(source_fleet, ship_type, 0) or 0
        if available < count:
            return jsonify({
                'error': f'Not enough {ship_type} ships available. Requested: {count}, Available: {available}'
            }), 400

    new_fleet = Fleet(
        user_id=user_id,
        mission='stationed',
        status='stationed',
        start_planet_id=source_fleet.start_planet_id,
        target_planet_id=source_fleet.start_planet_id,
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow(),
    )
    db.session.add(new_fleet)
    db.session.flush()

    for ship_type, count in ships.items():
        source_value = getattr(source_fleet, ship_type, 0) or 0
        target_value = getattr(new_fleet, ship_type, 0) or 0
        setattr(source_fleet, ship_type, source_value - count)
        setattr(new_fleet, ship_type, target_value + count)

    db.session.commit()

    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

    return jsonify({
        'message': 'Fleet split successfully',
        'source_fleet': serialize_fleet(source_fleet, planet_dict),
        'new_fleet': serialize_fleet(new_fleet, planet_dict),
    }), 200


@fleet_mgmt_bp.route('/<int:fleet_id>/transfer', methods=['POST'])
@jwt_required()
def transfer_fleet_ships(fleet_id: int):
    """Transfer ships between two stationed fleets on the same planet."""
    user_id = int(get_jwt_identity())
    payload = request.get_json() or {}
    ships_raw = payload.get('ships')
    target_fleet_id = payload.get('target_fleet_id')

    source_fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not source_fleet:
        return jsonify({'error': 'Fleet not found'}), 404
    if source_fleet.status != 'stationed':
        return jsonify({'error': 'Only stationed fleets can transfer ships'}), 400

    try:
        target_fleet_id = int(target_fleet_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid target_fleet_id'}), 400

    target_fleet = Fleet.query.filter_by(id=target_fleet_id, user_id=user_id).first()
    if not target_fleet:
        return jsonify({'error': 'Target fleet not found'}), 404
    if target_fleet.id == source_fleet.id:
        return jsonify({'error': 'Cannot transfer ships to the same fleet'}), 400
    if target_fleet.status != 'stationed':
        return jsonify({'error': 'Target fleet must be stationed'}), 400
    if target_fleet.start_planet_id != source_fleet.start_planet_id:
        return jsonify({'error': 'Fleets must be stationed on the same planet'}), 400

    try:
        ships = _parse_ship_transfer_payload(ships_raw)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    for ship_type, count in ships.items():
        available = getattr(source_fleet, ship_type, 0) or 0
        if available < count:
            return jsonify({
                'error': f'Not enough {ship_type} ships available. Requested: {count}, Available: {available}'
            }), 400

    for ship_type, count in ships.items():
        source_value = getattr(source_fleet, ship_type, 0) or 0
        target_value = getattr(target_fleet, ship_type, 0) or 0
        setattr(source_fleet, ship_type, source_value - count)
        setattr(target_fleet, ship_type, target_value + count)

    db.session.commit()

    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

    return jsonify({
        'message': 'Fleet transfer completed',
        'source_fleet': serialize_fleet(source_fleet, planet_dict),
        'target_fleet': serialize_fleet(target_fleet, planet_dict),
    }), 200

@fleet_mgmt_bp.route('/send', methods=['POST'])
@jwt_required()
def send_fleet():
    print("DEBUG: Fleet send endpoint called")
    user_id = int(get_jwt_identity())
    print(f"DEBUG: User ID from JWT: {user_id}")
    data = request.get_json()
    print(f"DEBUG: Request data: {data}")

    if not data or 'fleet_id' not in data or 'mission' not in data:
        print("DEBUG: Missing required fields")
        return jsonify({'error': 'Missing required fields'}), 400

    # Get fleet
    try:
        fleet_id = int(data['fleet_id'])
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid fleet_id'}), 400

    fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not fleet:
        return jsonify({'error': 'Fleet not found'}), 404

    try:
        FleetStateMachine.ensure_can_send(fleet, data.get('mission'))
    except FleetStateError as e:
        return jsonify({'error': str(e)}), 400

    raw_target_planet_id = data.get('target_planet_id')
    target_planet_id = None
    if raw_target_planet_id is not None and raw_target_planet_id != '':
        try:
            target_planet_id = int(raw_target_planet_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid target_planet_id'}), 400

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
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required for attack mission'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Cannot attack own planets
        if target_planet.user_id == user_id:
            return jsonify({'error': 'Cannot attack your own planet'}), 400

        # Check if target planet is owned (attacks on unowned planets would be colonization)
        if not target_planet.user_id:
            return jsonify({'error': 'Cannot attack unowned planet. Use colonization instead.'}), 400

        # PvP protection: block attacks against protected players, but never block attacks on pirates NPC.
        target_owner = User.query.get(target_planet.user_id) if target_planet.user_id else None
        target_owner_name = str(getattr(target_owner, 'username', '') or '').lower()
        target_protection_until = getattr(target_owner, 'protection_until', None)
        if (
            target_owner
            and target_owner_name != 'pirates'
            and target_protection_until is not None
            and target_protection_until > datetime.utcnow()
        ):
            return jsonify({'error': 'Target player is under protection'}), 400

        fleet.mission = 'attack'
        fleet.target_planet_id = target_planet_id
        fleet.status = 'traveling'

    elif data['mission'] == 'defend':
        # Defend mission - station fleet at planet for defense
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required for defend mission'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Must own the planet to defend it
        if target_planet.user_id != user_id:
            return jsonify({'error': 'Cannot defend planet you do not own'}), 400

        # Defend behaves like "deploy fleet to your planet and keep it there".
        # While traveling, keep status=traveling so arrival processing can finalize to defending.
        fleet.mission = 'defend'
        fleet.target_planet_id = target_planet_id
        fleet.status = 'traveling'

    elif data['mission'] == 'recycle':
        # Recycle mission - collect debris from planet
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required for recycle mission'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # Check if there are recyclers in the fleet
        if fleet.recycler <= 0:
            return jsonify({'error': 'Fleet must contain recycler ships for recycle mission'}), 400

        recycle_focus = (data.get('recycle_focus') or data.get('recycle_resource') or 'proportional')
        recycle_focus = str(recycle_focus).strip().lower()
        if recycle_focus not in ('proportional', 'metal', 'crystal', 'deuterium'):
            return jsonify({'error': 'Invalid recycle_focus'}), 400

        fleet.mission = 'recycle'
        fleet.target_planet_id = target_planet_id
        fleet.status = 'traveling'
        # Store recycler focus without altering schema. (This field is otherwise used for colonization/exploration coords.)
        fleet.target_coordinates = f"recycle:{recycle_focus}"

    elif data['mission'] in ('transport', 'deploy'):
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        # MVP: only allow transport/deploy to your own planets.
        if target_planet.user_id != user_id:
            return jsonify({'error': 'Target planet must be owned by you'}), 400

        # Parse optional cargo. (UI wiring can come later; tests use this now.)
        def parse_non_negative_int(value, field):
            if value is None or value == '':
                return 0
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid {field}")
            if parsed < 0:
                raise ValueError(f"Invalid {field}")
            return parsed

        try:
            cargo_metal = parse_non_negative_int(data.get('cargo_metal'), 'cargo_metal')
            cargo_crystal = parse_non_negative_int(data.get('cargo_crystal'), 'cargo_crystal')
            cargo_deuterium = parse_non_negative_int(data.get('cargo_deuterium'), 'cargo_deuterium')
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        start_planet = Planet.query.get(fleet.start_planet_id)
        if not start_planet:
            return jsonify({'error': 'Origin planet not found'}), 404

        if start_planet.metal < cargo_metal or start_planet.crystal < cargo_crystal or start_planet.deuterium < cargo_deuterium:
            return jsonify({'error': 'Insufficient resources to load cargo'}), 400

        start_planet.metal -= cargo_metal
        start_planet.crystal -= cargo_crystal
        start_planet.deuterium -= cargo_deuterium

        fleet.cargo_metal = cargo_metal
        fleet.cargo_crystal = cargo_crystal
        fleet.cargo_deuterium = cargo_deuterium

        fleet.mission = data['mission']
        fleet.target_planet_id = target_planet_id
        fleet.status = 'traveling'

    elif data['mission'] == 'espionage':
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required for espionage mission'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        if fleet.espionage_probe <= 0:
            return jsonify({'error': 'Fleet must contain espionage probes for espionage mission'}), 400

        fleet.mission = 'espionage'
        fleet.target_planet_id = target_planet_id
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
                if existing_planet.user_id:
                    return jsonify({'error': COLONIZATION_ERRORS['coordinates_occupied']}), 409
                fleet.target_planet_id = existing_planet.id
            else:
                # Create an unowned placeholder planet so arrival processing can claim it.
                placeholder = Planet(
                    name='Uncharted Planet',
                    x=target_x,
                    y=target_y,
                    z=target_z,
                    user_id=None,
                )
                db.session.add(placeholder)
                db.session.flush()
                fleet.target_planet_id = placeholder.id

        else:
            return jsonify({'error': COLONIZATION_ERRORS['invalid_coordinates']}), 400

        # Prevent multiple simultaneous colonization attempts to the same target.
        existing_colonizer = Fleet.query.filter(
            Fleet.id != fleet.id,
            Fleet.mission == 'colonize',
            Fleet.status == f'colonizing:{target_x}:{target_y}:{target_z}'
        ).first()
        if existing_colonizer:
            return jsonify({'error': COLONIZATION_ERRORS['coordinates_occupied']}), 409

        # Validate research requirements
        from backend.services.planet_traits import PlanetTraitService
        colonization_difficulty = PlanetTraitService.calculate_colonization_difficulty(target_x, target_y, target_z)

        user_research = Research.query.filter_by(user_id=user_id).first()
        user_research_level = user_research.colonization_tech if user_research else 0

        if colonization_difficulty > user_research_level:
            return jsonify({
                'error': f'{COLONIZATION_ERRORS["insufficient_research"]} (requires L{colonization_difficulty}, you have L{user_research_level})',
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
        if target_planet_id is None:
            return jsonify({'error': 'Target planet required'}), 400

        target_planet = Planet.query.get(target_planet_id)
        if not target_planet:
            return jsonify({'error': 'Target planet not found'}), 404

        fleet.mission = data['mission']
        fleet.target_planet_id = target_planet_id
        fleet.status = 'traveling'

    # Calculate distance and travel time
    start_planet = Planet.query.get(fleet.start_planet_id)
    distance = calculate_distance(start_planet, target_planet)

    # Use FleetTravelService for consistent speed calculation (now 30x faster)
    from backend.services.fleet_travel import FleetTravelService
    fleet_speed = FleetTravelService.calculate_fleet_speed(fleet)
    travel_time_hours = distance / fleet_speed if fleet_speed > 0 else 0

    # Research effect: Astrophysics reduces travel time.
    user_research = Research.query.filter_by(user_id=user_id).first()
    astro_level = user_research.astrophysics if user_research else 0
    travel_multiplier = 1.0 / (1.0 + (astro_level or 0) * 0.05)

    # Apply minimum travel time to prevent instant arrivals (configurable; 0 in testing),
    # with an optional forced override for fast E2E runs.
    MIN_TRAVEL_TIME_SECONDS = get_min_travel_time_seconds()
    travel_time_seconds = max(travel_time_hours * 3600 * travel_multiplier, MIN_TRAVEL_TIME_SECONDS)
    forced_travel = get_forced_travel_time_seconds()
    if forced_travel is not None:
        travel_time_seconds = forced_travel
    travel_time_hours = travel_time_seconds / 3600

    fleet.departure_time = datetime.utcnow()
    fleet.arrival_time = fleet.departure_time + timedelta(seconds=travel_time_seconds)
    fleet.eta = int(travel_time_seconds)

    start_name = getattr(start_planet, 'name', f'Planet {fleet.start_planet_id}')
    if data['mission'] == 'explore':
        to_label = f"{target_planet.x}:{target_planet.y}:{target_planet.z}"
    elif data['mission'] == 'colonize' and 'target_x' in locals() and target_x is not None:
        to_label = f"{target_x}:{target_y}:{target_z}"
    else:
        to_label = getattr(target_planet, 'name', f'Planet {fleet.target_planet_id}')

    db.session.add(TickLog(
        tick_number=0,
        planet_id=fleet.start_planet_id,
        fleet_id=fleet.id,
        event_type='fleet_sent',
        event_description=f'Fleet {fleet.id} sent ({fleet.mission}) from {start_name} to {to_label}'
    ))

    db.session.commit()

    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

    return jsonify({
        'message': 'Fleet sent successfully',
        'fleet': serialize_fleet(fleet, planet_dict)
    })

@fleet_mgmt_bp.route('/recall/<int:fleet_id>', methods=['POST'])
@jwt_required()
def recall_fleet(fleet_id):
    print("DEBUG: Fleet recall endpoint called")
    print(f"DEBUG: Fleet ID: {fleet_id}")
    user_id = int(get_jwt_identity())
    print(f"DEBUG: User ID from JWT: {user_id}")

    fleet = Fleet.query.filter_by(id=fleet_id, user_id=user_id).first()
    if not fleet:
        print("DEBUG: Fleet not found")
        return jsonify({'error': 'Fleet not found'}), 404

    try:
        FleetStateMachine.ensure_can_recall(fleet)
    except FleetStateError as e:
        return jsonify({'error': str(e)}), 400

    # Calculate return time (simplified - same speed back)
    now = datetime.utcnow()
    if fleet.status == 'traveling':
        # Calculate remaining time to target and double it for return
        remaining_time = (fleet.arrival_time - now).total_seconds()
        remaining_time = max(0, remaining_time)
        return_time = remaining_time * 2
    else:
        # Already returning, just use current ETA
        return_time = fleet.eta

    # Prevent instant / negative returns (keep consistent with outbound min travel time).
    MIN_TRAVEL_TIME_SECONDS = get_min_travel_time_seconds()
    return_time = max(MIN_TRAVEL_TIME_SECONDS, return_time)

    FleetStateMachine.set_returning(fleet, now=now, return_time_seconds=return_time)

    db.session.add(TickLog(
        tick_number=0,
        planet_id=fleet.start_planet_id,
        fleet_id=fleet.id,
        event_type='fleet_recalled',
        event_description=f'Fleet {fleet.id} recalled and is returning'
    ))

    db.session.commit()

    planets = Planet.query.filter_by(user_id=user_id).all()
    planet_dict = {p.id: p for p in planets}

    return jsonify({
        'message': 'Fleet recalled successfully',
        'fleet': serialize_fleet(fleet, planet_dict)
    })

@fleet_mgmt_bp.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all_fleets():
    """Clear all fleets for the current user (for testing purposes)"""
    print("DEBUG: Clear all fleets endpoint called")
    user_id = int(get_jwt_identity())
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
