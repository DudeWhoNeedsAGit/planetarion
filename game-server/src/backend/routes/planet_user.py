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
from backend.database import db
from backend.models import User, Planet
from backend.config import get_planet_storage_caps

planet_mgmt_bp = Blueprint('planet_mgmt', __name__, url_prefix='/api/planet')

ALLOWED_BUILDINGS = {
    'metal_mine',
    'crystal_mine',
    'deuterium_synthesizer',
    'solar_plant',
    'fusion_reactor',
    'metal_storage',
    'crystal_storage',
    'deuterium_tank',
    'research_lab',
}


def _planet_to_dict(planet):
    caps = get_planet_storage_caps(planet)
    return {
        'id': planet.id,
        'user_id': planet.user_id,
        'name': planet.name,
        'x': planet.x,
        'y': planet.y,
        'z': planet.z,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'resources': {
            'metal': planet.metal,
            'crystal': planet.crystal,
            'deuterium': planet.deuterium,
        },
        'storage': {
            'metal': caps['metal'],
            'crystal': caps['crystal'],
            'deuterium': caps['deuterium'],
        },
        'ships': {
            'small_cargo': getattr(planet, 'small_cargo', 0),
            'large_cargo': getattr(planet, 'large_cargo', 0),
            'light_fighter': getattr(planet, 'light_fighter', 0),
            'heavy_fighter': getattr(planet, 'heavy_fighter', 0),
            'cruiser': getattr(planet, 'cruiser', 0),
            'battleship': getattr(planet, 'battleship', 0),
            'colony_ship': getattr(planet, 'colony_ship', 0),
            'recycler': getattr(planet, 'recycler', 0),
            'espionage_probe': getattr(planet, 'espionage_probe', 0),
            'bomber': getattr(planet, 'bomber', 0),
            'destroyer': getattr(planet, 'destroyer', 0),
            'deathstar': getattr(planet, 'deathstar', 0),
            'battlecruiser': getattr(planet, 'battlecruiser', 0),
        },
        'structures': {
            'metal_mine': planet.metal_mine,
            'crystal_mine': planet.crystal_mine,
            'deuterium_synthesizer': planet.deuterium_synthesizer,
            'solar_plant': planet.solar_plant,
            'fusion_reactor': planet.fusion_reactor,
            'metal_storage': getattr(planet, 'metal_storage', 0),
            'crystal_storage': getattr(planet, 'crystal_storage', 0),
            'deuterium_tank': getattr(planet, 'deuterium_tank', 0),
            'research_lab': getattr(planet, 'research_lab', 0),
        },
        'production_rates': calculate_production_rates(planet),
    }


@planet_mgmt_bp.route('', methods=['GET'])
@jwt_required()
def get_user_planets():
    user_id = int(get_jwt_identity())
    User.query.get_or_404(user_id)

    planets = Planet.query.filter_by(user_id=user_id).all()
    return jsonify([_planet_to_dict(planet) for planet in planets])

@planet_mgmt_bp.route('/<int:planet_id>', methods=['GET'])
@jwt_required()
def get_planet(planet_id):
    user_id = int(get_jwt_identity())
    planet = Planet.query.filter_by(id=planet_id, user_id=user_id).first_or_404()

    return jsonify(_planet_to_dict(planet))


@planet_mgmt_bp.route('/buildings', methods=['PUT'])
@jwt_required()
def update_buildings():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    planet_id = data.get('planet_id')
    buildings = data.get('buildings')
    if not planet_id or not isinstance(buildings, dict):
        return jsonify({'error': 'Missing required data'}), 400

    planet = Planet.query.filter_by(id=planet_id, user_id=user_id).first_or_404()

    total_cost_metal = 0
    total_cost_crystal = 0
    total_cost_deuterium = 0

    upgrades = {}
    for building, new_level in buildings.items():
        if building not in ALLOWED_BUILDINGS:
            continue
        if not isinstance(new_level, int):
            continue

        current_level = getattr(planet, building)
        if new_level <= current_level:
            continue

        # Cost should be cumulative for each level upgraded (prevents skipping levels cheaply).
        for level in range(current_level + 1, new_level + 1):
            cost_multiplier = 1.5 ** (level - 1)
            if building in {'metal_mine', 'crystal_mine'}:
                total_cost_metal += int(60 * cost_multiplier)
                total_cost_crystal += int(15 * cost_multiplier)
            elif building == 'deuterium_synthesizer':
                total_cost_metal += int(225 * cost_multiplier)
                total_cost_crystal += int(75 * cost_multiplier)
            elif building == 'solar_plant':
                total_cost_metal += int(75 * cost_multiplier)
                total_cost_crystal += int(30 * cost_multiplier)
            elif building == 'fusion_reactor':
                total_cost_metal += int(900 * cost_multiplier)
                total_cost_crystal += int(360 * cost_multiplier)
                total_cost_deuterium += int(180 * cost_multiplier)
            elif building in {'metal_storage', 'crystal_storage', 'deuterium_tank'}:
                total_cost_metal += int(100 * cost_multiplier)
                total_cost_crystal += int(50 * cost_multiplier)
            elif building == 'research_lab':
                total_cost_metal += int(200 * cost_multiplier)
                total_cost_crystal += int(100 * cost_multiplier)
                total_cost_deuterium += int(50 * cost_multiplier)

        upgrades[building] = new_level

    if (
        planet.metal < total_cost_metal
        or planet.crystal < total_cost_crystal
        or planet.deuterium < total_cost_deuterium
    ):
        return jsonify({'error': 'Insufficient resources'}), 400

    planet.metal -= total_cost_metal
    planet.crystal -= total_cost_crystal
    planet.deuterium -= total_cost_deuterium

    for building, new_level in upgrades.items():
        setattr(planet, building, new_level)

    db.session.commit()

    return jsonify(
        {
            'message': 'Buildings updated successfully',
            'resources': {
                'metal': planet.metal,
                'crystal': planet.crystal,
                'deuterium': planet.deuterium,
            },
            'structures': {
                'metal_mine': planet.metal_mine,
                'crystal_mine': planet.crystal_mine,
                'deuterium_synthesizer': planet.deuterium_synthesizer,
                'solar_plant': planet.solar_plant,
                'fusion_reactor': planet.fusion_reactor,
                'metal_storage': getattr(planet, 'metal_storage', 0),
                'crystal_storage': getattr(planet, 'crystal_storage', 0),
                'deuterium_tank': getattr(planet, 'deuterium_tank', 0),
                'research_lab': getattr(planet, 'research_lab', 0),
            },
        }
    )

def calculate_production_rates(planet):
    """Calculate resource production rates based on buildings"""
    # Simplified production formulas
    metal_rate = planet.metal_mine * 30 * (1.1 ** planet.metal_mine)  # Base production with exponential growth
    crystal_rate = planet.crystal_mine * 20 * (1.1 ** planet.crystal_mine)
    deuterium_rate = planet.deuterium_synthesizer * 10 * (1.1 ** planet.deuterium_synthesizer)

    # Energy consumption affects production
    energy_production = planet.solar_plant * 20 + planet.fusion_reactor * 50
    energy_consumption = (
        planet.metal_mine * 10
        + planet.crystal_mine * 10
        + planet.deuterium_synthesizer * 20
        + (planet.research_lab or 0) * 15
    )

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
