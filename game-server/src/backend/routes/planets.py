"""
Basic Planet Operations Routes

This module provides basic CRUD operations for planets:
- Public/admin access to planet information
- Planet creation (typically for admin or initial setup)
- General planet queries without authentication requirements

Note: For user-specific planet operations, see planet_user.py
This module is primarily for administrative or public planet data access.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Planet, User
from backend.services.sector import SectorService

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

@planets_bp.route('/galaxy/system/<int:x>/<int:y>/<int:z>', methods=['GET'])
def get_system_planets(x, y, z):
    """Get all planets in a specific system"""
    print("DEBUG: Galaxy system endpoint called")
    print(f"DEBUG: System coordinates: {x}:{y}:{z}")

    try:
        print("DEBUG: Querying database for planets in system...")
        planets = Planet.query.filter_by(x=x, y=y, z=z).all()
        print(f"DEBUG: Found {len(planets)} planets in system")

        result = [{
            'id': planet.id,
            'name': planet.name,
            'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
            'user_id': planet.user_id,
            'owner_name': planet.owner.username if planet.owner else None
        } for planet in planets]

        print(f"DEBUG: Returning {len(result)} planets data")
        print("DEBUG: Galaxy system endpoint successful")
        return jsonify(result)

    except Exception as e:
        print(f"ERROR: Galaxy system endpoint failed: {str(e)}")
        print("DEBUG: Galaxy system endpoint failed")
        return jsonify({'error': 'Internal server error'}), 500

@planets_bp.route('/galaxy/nearby/<int:center_x>/<int:center_y>/<int:center_z>', methods=['GET'])
def get_nearby_systems(center_x, center_y, center_z):
    """Get nearby systems that can be explored"""
    print("DEBUG: Galaxy nearby endpoint called")
    print(f"DEBUG: Center coordinates: {center_x}:{center_y}:{center_z}")

    try:
        # For now, return systems without auth for testing
        # TODO: Add JWT auth back when frontend is ready
        from backend.models import User
        import json

        # For testing, use a dummy user or skip user-specific logic
        user = None  # TODO: Add proper user handling
        print("DEBUG: User handling - using dummy user for now")

        # Get systems within exploration range (simplified to 50 units)
        range_limit = 50
        print(f"DEBUG: Exploration range: {range_limit} units")

        print("DEBUG: Querying database for planets within range...")
        # Find all planets within range
        planets = Planet.query.filter(
            Planet.x.between(center_x - range_limit, center_x + range_limit),
            Planet.y.between(center_y - range_limit, center_y + range_limit),
            Planet.z.between(center_z - range_limit, center_z + range_limit)
        ).all()
        print(f"DEBUG: Found {len(planets)} planets within range")

        # Group by system coordinates
        print("DEBUG: Grouping planets by system coordinates...")
        systems = {}
        for planet in planets:
            key = f"{planet.x}:{planet.y}:{planet.z}"
            if key not in systems:
                systems[key] = {
                    'x': planet.x,
                    'y': planet.y,
                    'z': planet.z,
                    'planets': 0,
                    'explored': True
                }
            systems[key]['planets'] += 1
        print(f"DEBUG: Grouped into {len(systems)} systems")

        # Load user's explored systems
        explored_systems = set()
        if user and user.explored_systems:
            try:
                explored_data = json.loads(user.explored_systems)
                explored_systems = {s['coordinates'] for s in explored_data}
                print(f"DEBUG: Loaded {len(explored_systems)} explored systems from user data")
            except:
                print("DEBUG: Failed to parse user explored systems data")
        else:
            print("DEBUG: No user data for explored systems")

        # Mark systems as explored based on user's history
        print("DEBUG: Marking systems as explored based on user history...")
        for key, system in systems.items():
            system['explored'] = key in explored_systems

        # Add some unexplored systems (placeholder for now)
        # In a real implementation, this would be based on exploration history
        unexplored_count = 5
        print(f"DEBUG: Adding {unexplored_count} placeholder unexplored systems...")
        for i in range(unexplored_count):
            x = center_x + (i - 2) * 20
            y = center_y + (i - 2) * 15
            z = center_z + (i - 2) * 10
            key = f"{x}:{y}:{z}"
            if key not in systems:
                systems[key] = {
                    'x': x,
                    'y': y,
                    'z': z,
                    'planets': 0,
                    'explored': key in explored_systems
                }

        result = list(systems.values())
        print(f"DEBUG: Returning {len(result)} systems data")
        print("DEBUG: Galaxy nearby endpoint successful")
        return jsonify(result)

    except Exception as e:
        print(f"ERROR: Galaxy nearby endpoint failed: {str(e)}")
        print("DEBUG: Galaxy nearby endpoint failed")
        return jsonify({'error': 'Internal server error'}), 500

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

# Sector-based Fog of War Endpoints
# Following RESTful API Design and Blueprint Pattern from systemPatterns.md

@planets_bp.route('/sectors/explored', methods=['GET'])
@jwt_required()
def get_explored_sectors():
    """
    Get all explored sectors for the authenticated user

    Following RESTful API Design patterns:
    - GET method for data retrieval
    - JWT authentication for user-specific data
    - Consistent JSON response format
    """
    try:
        user_id = get_jwt_identity()
        print(f"DEBUG: Getting explored sectors for user {user_id}")

        explored_sectors = SectorService.get_explored_sectors(user_id)
        print(f"DEBUG: Found {len(explored_sectors)} explored sectors")

        return jsonify({
            'explored_sectors': explored_sectors,
            'total_count': len(explored_sectors)
        })

    except Exception as e:
        print(f"ERROR: Failed to get explored sectors: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@planets_bp.route('/sectors/explore', methods=['POST'])
@jwt_required()
def explore_sector():
    """
    Mark a sector as explored (typically called when exploring a system)

    Following RESTful API Design patterns:
    - POST method for state changes
    - JWT authentication required
    - Proper error handling and status codes
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'system_x' not in data or 'system_y' not in data:
            return jsonify({'error': 'Missing required fields: system_x, system_y'}), 400

        system_x = data['system_x']
        system_y = data['system_y']

        print(f"DEBUG: Exploring system {system_x}:{system_y} for user {user_id}")

        # Use SectorService to handle exploration logic
        result = SectorService.explore_system(user_id, system_x, system_y)

        print(f"DEBUG: Exploration result: {result}")

        return jsonify({
            'success': True,
            'newly_explored': result['newly_explored'],
            'sector': {
                'x': result['sector_x'],
                'y': result['sector_y'],
                'bounds': result['sector_bounds']
            },
            'system': {
                'x': result['system_x'],
                'y': result['system_y']
            }
        })

    except Exception as e:
        print(f"ERROR: Failed to explore sector: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@planets_bp.route('/sectors/statistics', methods=['GET'])
@jwt_required()
def get_sector_statistics():
    """
    Get exploration statistics for the authenticated user

    Following established reporting patterns from systemPatterns.md
    """
    try:
        user_id = get_jwt_identity()
        print(f"DEBUG: Getting sector statistics for user {user_id}")

        stats = SectorService.get_sector_statistics(user_id)

        return jsonify({
            'statistics': stats,
            'user_id': user_id
        })

    except Exception as e:
        print(f"ERROR: Failed to get sector statistics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@planets_bp.route('/sectors/reset', methods=['POST'])
@jwt_required()
def reset_exploration():
    """
    Reset all exploration data for the authenticated user (admin/debug function)

    Following established admin patterns from systemPatterns.md
    """
    try:
        user_id = get_jwt_identity()
        print(f"DEBUG: Resetting exploration data for user {user_id}")

        success = SectorService.reset_exploration(user_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Exploration data reset successfully'
            })
        else:
            return jsonify({'error': 'Failed to reset exploration data'}), 500

    except Exception as e:
        print(f"ERROR: Failed to reset exploration: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
