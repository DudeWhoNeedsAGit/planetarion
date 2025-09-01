"""
User Planet Management Routes

This module handles authenticated user operations on planets including:
- Retrieving user's planets with resource and production information
- Upgrading buildings (mines, power plants, research facilities)
- Managing planet-specific operations

All endpoints require JWT authentication and operate only on the user's owned planets.
Building upgrades include resource cost calculations and production rate updates.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import User, Planet

planet_mgmt_bp = Blueprint('planet_mgmt', __name__, url_prefix='/api/planet')

@planet_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def get_user_planets():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    planets = Planet.query.filter_by(user_id=user_id).all()

    return jsonify([{
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'resources': {
            'metal': planet.metal,
            'crystal': planet.crystal,
            'deuterium': planet.deuterium
        },
        'structures': {
            'metal_mine': planet.metal_mine,
            'crystal_mine': planet.crystal_mine,
            'deuterium_synthesizer': planet.deuterium_synthesizer,
            'solar_plant': planet.solar_plant,
            'fusion_reactor': planet.fusion_reactor
        },
        'production_rates': calculate_production_rates(planet)
    } for planet in planets])

@planet_mgmt_bp.route('/<int:planet_id>', methods=['GET'])
@jwt_required()
def get_planet(planet_id):
    user_id = get_jwt_identity()
    planet = Planet.query.filter_by(id=planet_id, user_id=user_id).first_or_404()

    return jsonify({
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'resources': {
            'metal': planet.metal,
            'crystal': planet.crystal,
            'deuterium': planet.deuterium
        },
        'structures': {
            'metal_mine': planet.metal_mine,
            'crystal_mine': planet.crystal_mine,
            'deuterium_synthesizer': planet.deuterium_synthesizer,
            'solar_plant': planet.solar_plant,
            'fusion_reactor': planet.fusion_reactor
        },
        'production_rates': calculate_production_rates(planet)
    })

@planet_mgmt_bp.route('/buildings', methods=['PUT'])
@jwt_required()
def update_buildings():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'planet_id' not in data or 'buildings' not in data:
        return jsonify({'error': 'Missing planet_id or buildings data'}), 400

    planet = Planet.query.filter_by(id=data['planet_id'], user_id=user_id).first_or_404()

    # Calculate costs and check resources
    total_cost_metal = 0
    total_cost_crystal = 0
    total_cost_deuterium = 0

    for building, new_level in data['buildings'].items():
        if building not in ['metal_mine', 'crystal_mine', 'deuterium_synthesizer', 'solar_plant', 'fusion_reactor']:
            continue

        current_level = getattr(planet, building)
        if new_level <= current_level:
            continue

        # Calculate upgrade cost (simplified formula)
        cost_multiplier = 1.5 ** (new_level - 1)
        if building in ['metal_mine', 'crystal_mine']:
            metal_cost = int(60 * cost_multiplier)
            crystal_cost = int(15 * cost_multiplier)
            total_cost_metal += metal_cost
            total_cost_crystal += crystal_cost
        elif building == 'deuterium_synthesizer':
            metal_cost = int(225 * cost_multiplier)
            crystal_cost = int(75 * cost_multiplier)
            total_cost_metal += metal_cost
            total_cost_crystal += crystal_cost
        elif building == 'solar_plant':
            metal_cost = int(75 * cost_multiplier)
            crystal_cost = int(30 * cost_multiplier)
            total_cost_metal += metal_cost
            total_cost_crystal += crystal_cost
        elif building == 'fusion_reactor':
            metal_cost = int(900 * cost_multiplier)
            crystal_cost = int(360 * cost_multiplier)
            deuterium_cost = int(180 * cost_multiplier)
            total_cost_metal += metal_cost
            total_cost_crystal += crystal_cost
            total_cost_deuterium += deuterium_cost

    # Check if user has enough resources
    if (planet.metal < total_cost_metal or
        planet.crystal < total_cost_crystal or
        planet.deuterium < total_cost_deuterium):
        return jsonify({'error': 'Insufficient resources'}), 400

    # Deduct resources and update buildings
    planet.metal -= total_cost_metal
    planet.crystal -= total_cost_crystal
    planet.deuterium -= total_cost_deuterium

    for building, new_level in data['buildings'].items():
        if hasattr(planet, building):
            setattr(planet, building, new_level)

    db.session.commit()

    return jsonify({
        'message': 'Buildings updated successfully',
        'resources': {
            'metal': planet.metal,
            'crystal': planet.crystal,
            'deuterium': planet.deuterium
        },
        'structures': {
            'metal_mine': planet.metal_mine,
            'crystal_mine': planet.crystal_mine,
            'deuterium_synthesizer': planet.deuterium_synthesizer,
            'solar_plant': planet.solar_plant,
            'fusion_reactor': planet.fusion_reactor
        }
    })

def calculate_production_rates(planet):
    """Calculate resource production rates based on buildings"""
    # Simplified production formulas
    metal_rate = planet.metal_mine * 30 * (1.1 ** planet.metal_mine)  # Base production with exponential growth
    crystal_rate = planet.crystal_mine * 20 * (1.1 ** planet.crystal_mine)
    deuterium_rate = planet.deuterium_synthesizer * 10 * (1.1 ** planet.deuterium_synthesizer)

    # Energy consumption affects production
    energy_production = planet.solar_plant * 20 + planet.fusion_reactor * 50
    energy_consumption = planet.metal_mine * 10 + planet.crystal_mine * 10 + planet.deuterium_synthesizer * 20

    if energy_consumption > energy_production:
        # Reduce production if not enough energy
        energy_ratio = energy_production / energy_consumption
        metal_rate *= energy_ratio
        crystal_rate *= energy_ratio
        deuterium_rate *= energy_ratio

    return {
        'metal_per_hour': int(metal_rate),
        'crystal_per_hour': int(crystal_rate),
        'deuterium_per_hour': int(deuterium_rate),
        'energy_production': energy_production,
        'energy_consumption': energy_consumption
    }
