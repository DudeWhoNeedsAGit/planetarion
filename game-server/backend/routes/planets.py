from flask import Blueprint, request, jsonify
from ..database import db
from ..models import Planet, User

planets_bp = Blueprint('planets', __name__, url_prefix='/api')

@planets_bp.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([{
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'user_id': planet.user_id,
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
    } for planet in planets])

@planets_bp.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get_or_404(planet_id)
    return jsonify({
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'user_id': planet.user_id,
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

@planets_bp.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'x', 'y', 'z', 'user_id')):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user exists
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if coordinates are already occupied
    existing_planet = Planet.query.filter_by(x=data['x'], y=data['y'], z=data['z']).first()
    if existing_planet:
        return jsonify({'error': 'Coordinates already occupied'}), 409

    planet = Planet(
        name=data['name'],
        x=data['x'],
        y=data['y'],
        z=data['z'],
        user_id=data['user_id']
    )

    db.session.add(planet)
    db.session.commit()

    return jsonify({
        'id': planet.id,
        'name': planet.name,
        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
        'user_id': planet.user_id
    }), 201
