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
from sqlalchemy import func, distinct
import os
import json
from backend.database import db
from backend.models import Planet, User, DebrisField
from backend.services.pirate_factions import is_pirate_username

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

@planets_bp.route('/galaxy/system/<x>/<y>/<z>', methods=['GET'])
@jwt_required()
def get_system_planets(x, y, z):
    """Get all planets in a specific system."""
    try:
        try:
            x = int(x)
            y = int(y)
            z = int(z)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid coordinates'}), 400

        user_id = int(get_jwt_identity())
        planets = Planet.query.filter_by(x=x, y=y, z=z).all()

        # Fog-of-war: only reveal planets if the system is explored, or if the user owns a planet here.
        # In FLASK_ENV=testing, disable fog to keep E2E flows deterministic and fast.
        if os.getenv('FLASK_ENV') != 'testing':
            system_key = f"{x}:{y}:{z}"
            user_owns_planet_in_system = any(p.user_id == user_id for p in planets)
            if not user_owns_planet_in_system:
                explored_systems = set()
                user = User.query.get(user_id)
                if user and user.explored_systems:
                    try:
                        explored_data = json.loads(user.explored_systems)
                        explored_systems = {
                            s.get('coordinates')
                            for s in explored_data
                            if isinstance(s, dict) and s.get('coordinates')
                        }
                    except Exception:
                        explored_systems = set()
                if system_key not in explored_systems:
                    return jsonify([])

        planet_ids = [p.id for p in planets]

        debris_by_planet_id = {}
        if planet_ids:
            debris_rows = (
                db.session.query(
                    DebrisField.planet_id,
                    func.sum(DebrisField.metal).label('metal'),
                    func.sum(DebrisField.crystal).label('crystal'),
                    func.sum(DebrisField.deuterium).label('deuterium'),
                )
                .filter(DebrisField.planet_id.in_(planet_ids))
                .group_by(DebrisField.planet_id)
                .all()
            )
            debris_by_planet_id = {
                int(pid): {
                    'metal': int(metal or 0),
                    'crystal': int(crystal or 0),
                    'deuterium': int(deuterium or 0),
                }
                for (pid, metal, crystal, deuterium) in debris_rows
            }

        result = [{
            'id': planet.id,
            'name': planet.name,
            'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
            'x': planet.x,
            'y': planet.y,
            'z': planet.z,
            'user_id': planet.user_id,
            'owner_name': planet.owner.username if planet.owner else None,
            'debris': debris_by_planet_id.get(planet.id, {'metal': 0, 'crystal': 0, 'deuterium': 0}),
        } for planet in planets]

        return jsonify(result)

    except Exception as e:
        print(f"ERROR: Galaxy system endpoint failed: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@planets_bp.route('/galaxy/nearby/<center_x>/<center_y>/<center_z>', methods=['GET'])
@jwt_required()
def get_nearby_systems(center_x, center_y, center_z):
    """Return system summaries within a range around the given center coordinates.

    Response:
      { systems: [...], meta: {...} }
    """
    try:
        user_id = int(get_jwt_identity())
        try:
            center_x = int(center_x)
            center_y = int(center_y)
            center_z = int(center_z)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid center coordinates'}), 400

        # Default exploration/intel range scales with interstellar communication.
        from backend.models import Research
        research = Research.query.filter_by(user_id=user_id).first()
        comm_level = research.interstellar_communication if research else 0
        default_range = 2000 + int(comm_level or 0) * 500
        range_limit = request.args.get('range', default_range, type=int)
        limit = request.args.get('limit', 500, type=int)
        offset = request.args.get('offset', 0, type=int)

        min_x, max_x = center_x - range_limit, center_x + range_limit
        min_y, max_y = center_y - range_limit, center_y + range_limit

        # GalaxyMap is currently 2D (X/Y) and locked to the player's Z slice for performance and clarity.
        # Default: only populate the current Z plane (z_band=0).
        # Future: allow a small Z band if/when the UI supports depth navigation.
        z_band = request.args.get('z_band', 0, type=int)
        z_band = int(z_band or 0)
        if z_band <= 0:
            min_z, max_z = center_z, center_z
        else:
            min_z, max_z = center_z - z_band, center_z + z_band

        explored_systems = set()
        user = User.query.get(user_id)
        if user and user.explored_systems:
            try:
                explored_data = json.loads(user.explored_systems)
                explored_systems = {
                    s.get('coordinates')
                    for s in explored_data
                    if isinstance(s, dict) and s.get('coordinates')
                }
            except Exception:
                explored_systems = set()

        rows = (
            db.session.query(
                Planet.x.label('x'),
                Planet.y.label('y'),
                Planet.z.label('z'),
                func.count(Planet.id).label('planet_count'),
                func.count(distinct(Planet.user_id)).label('owner_count'),
                func.min(Planet.user_id).label('min_owner'),
                func.max(Planet.user_id).label('max_owner'),
            )
            .filter(
                Planet.x.between(min_x, max_x),
                Planet.y.between(min_y, max_y),
                Planet.z.between(min_z, max_z),
            )
            .group_by(Planet.x, Planet.y, Planet.z)
            .order_by(Planet.x.asc(), Planet.y.asc(), Planet.z.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        debris_rows = (
            db.session.query(Planet.x, Planet.y, Planet.z)
            .join(DebrisField, DebrisField.planet_id == Planet.id)
            .filter(
                Planet.x.between(min_x, max_x),
                Planet.y.between(min_y, max_y),
                Planet.z.between(min_z, max_z),
                (DebrisField.metal + DebrisField.crystal + DebrisField.deuterium) > 0,
            )
            .group_by(Planet.x, Planet.y, Planet.z)
            .all()
        )
        debris_keys = {f"{x}:{y}:{z}" for (x, y, z) in debris_rows}

        owner_ids = {
            int(r.max_owner)
            for r in rows
            if r.owner_count == 1 and r.max_owner is not None
        }
        owners = {}
        if owner_ids:
            owners = {
                u.id: {"username": u.username, "alliance_id": u.alliance_id}
                for u in User.query.filter(User.id.in_(owner_ids)).all()
            }

        systems = []
        for r in rows:
            key = f"{r.x}:{r.y}:{r.z}"

            owner_id = int(r.max_owner) if r.owner_count == 1 and r.max_owner is not None else None
            owner_name = owners.get(owner_id, {}).get("username") if owner_id is not None else None

            if r.owner_count == 0:
                relation = 'unowned'
            elif r.owner_count > 1:
                relation = 'contested'
            elif owner_id == user_id:
                relation = 'self'
            elif is_pirate_username(owner_name):
                relation = 'pirates'
            elif user and user.alliance_id and owners.get(owner_id, {}).get("alliance_id") == user.alliance_id:
                relation = 'ally'
            else:
                relation = 'enemy'

            explored = (key in explored_systems) or (relation == 'self')

            systems.append({
                'key': key,
                'x': r.x,
                'y': r.y,
                'z': r.z,
                'planet_count': int(r.planet_count),
                # Backward-compatible alias for older UI code.
                'planets': int(r.planet_count),
                'owner_id': owner_id,
                'owner_name': owner_name,
                'relation': relation,
                'explored': explored,
                'flags': {
                    'has_debris': key in debris_keys,
                    'has_pirates': relation == 'pirates',
                }
            })

        return jsonify({
            'systems': systems,
            'meta': {
                'center': {'x': center_x, 'y': center_y, 'z': center_z},
                'range': range_limit,
                'z_band': z_band,
                'limit': limit,
                'offset': offset,
            }
        })

    except Exception as e:
        print(f"ERROR: Galaxy nearby endpoint failed: {str(e)}")
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
