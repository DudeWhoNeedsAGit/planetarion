"""
Combat Routes

This module handles combat-related API endpoints including:
- Battle reports retrieval
- Debris field information
- Combat statistics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import CombatReport, DebrisField, Planet, User
import json

combat_bp = Blueprint('combat', __name__, url_prefix='/api/combat')


def _get_explored_system_keys(user: User) -> set[str]:
    explored_systems = set()
    if not user or not getattr(user, "explored_systems", None):
        return explored_systems
    try:
        explored_data = json.loads(user.explored_systems) or []
        for entry in explored_data:
            if isinstance(entry, dict) and entry.get("coordinates"):
                explored_systems.add(str(entry["coordinates"]))
    except Exception:
        return set()
    return explored_systems


def _is_planet_visible_to_user(*, user_id: int, user: User | None, planet: Planet, fought_planet_ids: set[int]) -> bool:
    if planet.user_id == user_id:
        return True
    if planet.id in fought_planet_ids:
        return True
    if user is None:
        return False
    explored = _get_explored_system_keys(user)
    return f"{planet.x}:{planet.y}:{planet.z}" in explored


@combat_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_combat_reports():
    """Get combat reports for the authenticated user"""
    print("DEBUG: Combat reports endpoint called")
    user_id = int(get_jwt_identity())
    print(f"DEBUG: User ID from JWT: {user_id}")

    # Get query parameters
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    print(f"DEBUG: Fetching combat reports with limit={limit}, offset={offset}")

    # Get reports where user is attacker or defender
    reports = CombatReport.query.filter(
        db.or_(
            CombatReport.attacker_id == user_id,
            CombatReport.defender_id == user_id
        )
    ).order_by(CombatReport.timestamp.desc()).limit(limit).offset(offset).all()

    print(f"DEBUG: Found {len(reports)} combat reports")

    # Format reports for response
    formatted_reports = []
    for report in reports:
        formatted_reports.append({
            'id': report.id,
            'timestamp': report.timestamp.isoformat(),
            'attacker': {
                'id': report.attacker.id,
                'username': report.attacker.username
            },
            'defender': {
                'id': report.defender.id,
                'username': report.defender.username
            },
            'planet': {
                'id': report.planet.id,
                'name': report.planet.name,
                'coordinates': f"{report.planet.x}:{report.planet.y}:{report.planet.z}"
            },
            'winner': {
                'id': report.winner.id,
                'username': report.winner.username
            },
            'rounds': report.rounds,
            'attacker_losses': report.attacker_losses,
            'defender_losses': report.defender_losses,
            'debris_metal': report.debris_metal,
            'debris_crystal': report.debris_crystal,
            'debris_deuterium': report.debris_deuterium
        })

    return jsonify({
        'reports': formatted_reports,
        'total': len(formatted_reports),
        'limit': limit,
        'offset': offset
    })

@combat_bp.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_combat_report(report_id):
    """Get detailed combat report by ID"""
    print(f"DEBUG: Get combat report {report_id}")
    user_id = int(get_jwt_identity())

    report = CombatReport.query.filter_by(id=report_id).first()
    if not report:
        return jsonify({'error': 'Combat report not found'}), 404

    # Check if user has permission to view this report
    if report.attacker_id != user_id and report.defender_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'id': report.id,
        'timestamp': report.timestamp.isoformat(),
        'attacker': {
            'id': report.attacker.id,
            'username': report.attacker.username
        },
        'defender': {
            'id': report.defender.id,
            'username': report.defender.username
        },
        'planet': {
            'id': report.planet.id,
            'name': report.planet.name,
            'coordinates': f"{report.planet.x}:{report.planet.y}:{report.planet.z}"
        },
        'winner': {
            'id': report.winner.id,
            'username': report.winner.username
        },
        'rounds': report.rounds,
        'attacker_losses': report.attacker_losses,
        'defender_losses': report.defender_losses,
        'debris_metal': report.debris_metal,
        'debris_crystal': report.debris_crystal,
        'debris_deuterium': report.debris_deuterium
    })

@combat_bp.route('/debris', methods=['GET'])
@jwt_required()
def get_debris_fields():
    """Get debris fields visible to the user"""
    print("DEBUG: Debris fields endpoint called")
    user_id = int(get_jwt_identity())

    # Visible debris fields should be limited to:
    # - planets you own
    # - planets you've fought at (attacker or defender)
    # - planets in systems you've explored
    user = User.query.get(user_id)

    fought_planet_ids_rows = (
        db.session.query(CombatReport.planet_id)
        .filter(
            db.or_(
                CombatReport.attacker_id == user_id,
                CombatReport.defender_id == user_id,
            )
        )
        .distinct()
        .all()
    )
    fought_planet_ids = {int(r[0]) for r in fought_planet_ids_rows if r and r[0] is not None}

    debris_fields = (
        DebrisField.query.join(Planet, DebrisField.planet_id == Planet.id)
        .filter((DebrisField.metal + DebrisField.crystal + DebrisField.deuterium) > 0)
        .all()
    )

    formatted_debris = []
    for debris in debris_fields:
        planet = debris.planet
        if not planet:
            continue
        if not _is_planet_visible_to_user(user_id=user_id, user=user, planet=planet, fought_planet_ids=fought_planet_ids):
            continue
        formatted_debris.append({
            'id': debris.id,
            'planet': {
                'id': planet.id,
                'name': planet.name,
                'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
                'owner': planet.owner.username if getattr(planet, 'owner', None) else None
            },
            'resources': {
                'metal': debris.metal,
                'crystal': debris.crystal,
                'deuterium': debris.deuterium
            },
            'created_at': debris.created_at.isoformat(),
            'recycler_fleet_id': debris.recycler_fleet_id
        })

    return jsonify({
        'debris_fields': formatted_debris,
        'total': len(formatted_debris)
    })

@combat_bp.route('/debris/<int:planet_id>', methods=['GET'])
@jwt_required()
def get_planet_debris(planet_id):
    """Get debris field for a specific planet"""
    print(f"DEBUG: Get debris for planet {planet_id}")
    user_id = int(get_jwt_identity())

    debris = DebrisField.query.filter_by(planet_id=planet_id).first()
    if not debris:
        return jsonify({'error': 'No debris field found at this planet'}), 404

    user = User.query.get(user_id)
    fought_planet_ids_rows = (
        db.session.query(CombatReport.planet_id)
        .filter(
            db.or_(
                CombatReport.attacker_id == user_id,
                CombatReport.defender_id == user_id,
            )
        )
        .distinct()
        .all()
    )
    fought_planet_ids = {int(r[0]) for r in fought_planet_ids_rows if r and r[0] is not None}
    if debris.planet and not _is_planet_visible_to_user(user_id=user_id, user=user, planet=debris.planet, fought_planet_ids=fought_planet_ids):
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'id': debris.id,
        'planet': {
            'id': debris.planet.id,
            'name': debris.planet.name,
            'coordinates': f"{debris.planet.x}:{debris.planet.y}:{debris.planet.z}",
            'owner': debris.planet.owner.username if getattr(debris.planet, 'owner', None) else None
        },
        'resources': {
            'metal': debris.metal,
            'crystal': debris.crystal,
            'deuterium': debris.deuterium
        },
        'created_at': debris.created_at.isoformat(),
        'recycler_fleet_id': debris.recycler_fleet_id
    })

@combat_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_combat_statistics():
    """Get combat statistics for the authenticated user"""
    print("DEBUG: Combat statistics endpoint called")
    user_id = int(get_jwt_identity())

    # Get user's fleets for combat statistics
    from backend.models import Fleet
    user_fleets = Fleet.query.filter_by(user_id=user_id).all()

    total_victories = sum(fleet.combat_victories for fleet in user_fleets)
    total_defeats = sum(fleet.combat_defeats for fleet in user_fleets)
    total_experience = sum(fleet.combat_experience for fleet in user_fleets)

    # Get user's combat reports
    attacker_reports = CombatReport.query.filter_by(attacker_id=user_id).count()
    defender_reports = CombatReport.query.filter_by(defender_id=user_id).count()
    won_reports = CombatReport.query.filter_by(winner_id=user_id).count()

    return jsonify({
        'fleet_statistics': {
            'total_victories': total_victories,
            'total_defeats': total_defeats,
            'total_experience': total_experience,
            'win_rate': (total_victories / (total_victories + total_defeats)) * 100 if (total_victories + total_defeats) > 0 else 0
        },
        'battle_statistics': {
            'total_battles': attacker_reports + defender_reports,
            'battles_won': won_reports,
            'battles_lost': (attacker_reports + defender_reports) - won_reports,
            'win_rate': (won_reports / (attacker_reports + defender_reports)) * 100 if (attacker_reports + defender_reports) > 0 else 0
        }
    })
