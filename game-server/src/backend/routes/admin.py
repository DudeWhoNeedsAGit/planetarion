"""
Admin Routes

Administrative endpoints for system monitoring and maintenance.
Requires authentication and admin privileges.

Endpoints:
- GET /api/admin/fleet-health - Get fleet system health report
- POST /api/admin/fleet/cleanup - Force cleanup stuck fleets
- GET /api/admin/system-status - Get overall system status
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import User
from backend.services.fleet_travel_guard import FleetTravelGuard

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def is_admin(user_id):
    """Check if user has admin privileges"""
    # For now, check if user is e2etestuser (can be expanded later)
    user = User.query.get(user_id)
    return user and user.username == 'e2etestuser'

@admin_bp.route('/fleet-health', methods=['GET'])
@jwt_required()
def get_fleet_health():
    """Get comprehensive fleet health report"""
    user_id = get_jwt_identity()

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        health_report = FleetTravelGuard.get_fleet_health_report()
        return jsonify(health_report), 200
    except Exception as e:
        return jsonify({'error': f'Failed to generate health report: {str(e)}'}), 500

@admin_bp.route('/fleet/cleanup', methods=['POST'])
@jwt_required()
def cleanup_stuck_fleets():
    """Administrative endpoint to force cleanup stuck fleets"""
    user_id = get_jwt_identity()

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        # Get parameters
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)  # Default 24 hours
        target_user_id = data.get('user_id')  # Optional: cleanup specific user

        # Run cleanup
        cleaned_count = FleetTravelGuard.force_cleanup_stuck_fleets(
            user_id=target_user_id,
            max_age_hours=max_age_hours
        )

        return jsonify({
            'message': f'Successfully cleaned up {cleaned_count} stuck fleets',
            'cleaned_count': cleaned_count,
            'max_age_hours': max_age_hours,
            'target_user_id': target_user_id
        }), 200

    except Exception as e:
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@admin_bp.route('/fleet/validate-coordinates', methods=['POST'])
@jwt_required()
def validate_fleet_coordinates():
    """Validate and fix fleet coordinate issues"""
    user_id = get_jwt_identity()

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        issues_found = FleetTravelGuard.validate_fleet_coordinates()

        return jsonify({
            'message': f'Validated fleet coordinates, fixed {issues_found} issues',
            'issues_fixed': issues_found
        }), 200

    except Exception as e:
        return jsonify({'error': f'Coordinate validation failed: {str(e)}'}), 500

@admin_bp.route('/system-status', methods=['GET'])
@jwt_required()
def get_system_status():
    """Get overall system status and statistics"""
    user_id = get_jwt_identity()

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        from backend.services.tick import get_tick_statistics
        from backend.models import Planet, Fleet, User, Alliance

        # Get basic counts
        system_stats = {
            'users': User.query.count(),
            'planets': Planet.query.count(),
            'fleets': Fleet.query.count(),
            'alliances': Alliance.query.count(),
            'timestamp': db.func.now()
        }

        # Get fleet health
        fleet_health = FleetTravelGuard.get_fleet_health_report()

        # Get tick statistics
        tick_stats = get_tick_statistics()

        return jsonify({
            'system_stats': system_stats,
            'fleet_health': fleet_health,
            'tick_stats': tick_stats
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get system status: {str(e)}'}), 500

@admin_bp.route('/fleet/<int:fleet_id>/fix', methods=['POST'])
@jwt_required()
def fix_specific_fleet(fleet_id):
    """Fix a specific stuck fleet"""
    user_id = get_jwt_identity()

    if not is_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    try:
        from backend.models import Fleet

        fleet = Fleet.query.get(fleet_id)
        if not fleet:
            return jsonify({'error': 'Fleet not found'}), 404

        # Try to fix the fleet
        from backend.services.fleet_travel_guard import FleetTravelGuard
        current_time = db.func.now()

        if FleetTravelGuard._correct_fleet_state(fleet, current_time):
            db.session.commit()
            return jsonify({
                'message': f'Fleet {fleet_id} fixed successfully',
                'fleet_id': fleet_id,
                'new_status': fleet.status,
                'new_eta': fleet.eta
            }), 200
        else:
            return jsonify({
                'message': f'Fleet {fleet_id} was already in correct state',
                'fleet_id': fleet_id,
                'status': fleet.status,
                'eta': fleet.eta
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to fix fleet: {str(e)}'}), 500
