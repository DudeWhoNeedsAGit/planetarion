"""
Shipyard Routes

This module handles ship construction and shipyard operations including:
- Building ships of various types (colony ships, cargo ships, fighters, etc.)
- Resource cost calculations for ship construction
- Fleet integration for newly built ships
- Ship cost information retrieval

All construction endpoints require JWT authentication and operate on user's planets.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..database import db
from ..models import User, Planet, Fleet

shipyard_bp = Blueprint('shipyard', __name__, url_prefix='/api/shipyard')

# Ship costs (simplified for demo)
SHIP_COSTS = {
    'colony_ship': {
        'metal': 10000,
        'crystal': 20000,
        'deuterium': 10000
    }
}

@shipyard_bp.route('/build', methods=['POST'])
@jwt_required()
def build_ship():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'planet_id' not in data or 'ship_type' not in data or 'quantity' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Verify planet ownership
    planet = Planet.query.filter_by(id=data['planet_id'], user_id=user_id).first()
    if not planet:
        return jsonify({'error': 'Planet not found or not owned by user'}), 404

    ship_type = data['ship_type']
    quantity = data['quantity']

    if ship_type not in SHIP_COSTS:
        return jsonify({'error': 'Invalid ship type'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400

    # Calculate total cost
    costs = SHIP_COSTS[ship_type]
    total_cost_metal = costs['metal'] * quantity
    total_cost_crystal = costs['crystal'] * quantity
    total_cost_deuterium = costs['deuterium'] * quantity

    # Check if planet has enough resources
    if (planet.metal < total_cost_metal or
        planet.crystal < total_cost_crystal or
        planet.deuterium < total_cost_deuterium):
        return jsonify({'error': 'Insufficient resources'}), 400

    # Deduct resources
    planet.metal -= total_cost_metal
    planet.crystal -= total_cost_crystal
    planet.deuterium -= total_cost_deuterium

    # Create or update fleet with the new ships
    # For demo simplicity, we'll add ships to an existing fleet or create a new one
    fleet = Fleet.query.filter_by(
        user_id=user_id,
        start_planet_id=data['planet_id'],
        status='stationed'
    ).first()

    if not fleet:
        # Create new fleet
        fleet = Fleet(
            user_id=user_id,
            mission='stationed',
            start_planet_id=data['planet_id'],
            target_planet_id=data['planet_id'],
            departure_time=db.func.now(),
            arrival_time=db.func.now()
        )
        db.session.add(fleet)
        db.session.flush()

    # Add ships to fleet
    if ship_type == 'colony_ship':
        fleet.colony_ship += quantity

    db.session.commit()

    return jsonify({
        'message': f'Successfully built {quantity} {ship_type}(s)',
        'planet_resources': {
            'metal': planet.metal,
            'crystal': planet.crystal,
            'deuterium': planet.deuterium
        },
        'fleet': {
            'id': fleet.id,
            'colony_ship': fleet.colony_ship
        }
    }), 200

@shipyard_bp.route('/costs', methods=['GET'])
def get_ship_costs():
    """Get costs for all ship types"""
    return jsonify(SHIP_COSTS), 200
