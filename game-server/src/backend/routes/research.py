"""
Research Management Routes

This module handles research progression and technology upgrades:
- Research point generation and spending
- Technology level progression
- Research requirements and prerequisites
- Research queue management

All endpoints require JWT authentication and operate on the user's research.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import User, Research, Planet
from datetime import datetime

research_bp = Blueprint('research', __name__, url_prefix='/api/research')

@research_bp.route('', methods=['GET'])
@jwt_required()
def get_research():
    """Get user's current research status"""
    print("DEBUG: Research GET endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    # Get or create research record
    research = Research.query.filter_by(user_id=user_id).first()
    if not research:
        research = Research(user_id=user_id)
        db.session.add(research)
        db.session.commit()

    # Calculate current research points
    research_points = calculate_research_points(user_id)
    research.research_points = research_points

    print("DEBUG: Research GET endpoint successful")
    return jsonify({
        'research_points': research.research_points,
        'levels': {
            'colonization_tech': research.colonization_tech,
            'astrophysics': research.astrophysics,
            'interstellar_communication': research.interstellar_communication
        },
        'next_level_costs': {
            'colonization_tech': calculate_research_cost('colonization_tech', research.colonization_tech + 1),
            'astrophysics': calculate_research_cost('astrophysics', research.astrophysics + 1),
            'interstellar_communication': calculate_research_cost('interstellar_communication', research.interstellar_communication + 1)
        }
    })

@research_bp.route('/upgrade/<research_type>', methods=['POST'])
@jwt_required()
def upgrade_research(research_type):
    """Upgrade a specific research technology"""
    print("DEBUG: Research upgrade endpoint called")
    print(f"DEBUG: Research type: {research_type}")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    # Validate research type
    valid_types = ['colonization_tech', 'astrophysics', 'interstellar_communication']
    if research_type not in valid_types:
        return jsonify({'error': 'Invalid research type'}), 400

    # Get or create research record
    research = Research.query.filter_by(user_id=user_id).first()
    if not research:
        research = Research(user_id=user_id)
        db.session.add(research)
        db.session.commit()

    # Get current level
    current_level = getattr(research, research_type)

    # Calculate upgrade cost
    upgrade_cost = calculate_research_cost(research_type, current_level + 1)

    # Check if user has enough research points
    if research.research_points < upgrade_cost:
        return jsonify({
            'error': 'Insufficient research points',
            'required': upgrade_cost,
            'available': research.research_points
        }), 400

    # Perform upgrade
    setattr(research, research_type, current_level + 1)
    research.research_points -= upgrade_cost

    db.session.commit()

    return jsonify({
        'message': f'{research_type} upgraded to level {current_level + 1}',
        'new_level': current_level + 1,
        'research_points_remaining': research.research_points,
        'next_upgrade_cost': calculate_research_cost(research_type, current_level + 2)
    })

@research_bp.route('/points', methods=['GET'])
@jwt_required()
def get_research_points():
    """Get current research points (real-time calculation)"""
    print("DEBUG: Research points endpoint called")
    user_id = get_jwt_identity()
    print(f"DEBUG: User ID from JWT: {user_id}")

    research_points = calculate_research_points(user_id)

    return jsonify({
        'research_points': research_points,
        'last_updated': datetime.utcnow().isoformat()
    })

def calculate_research_cost(research_type, target_level):
    """Calculate research cost for a specific technology and level"""
    if target_level <= 0:
        return 0

    # Base costs for each research type
    base_costs = {
        'colonization_tech': 100,
        'astrophysics': 150,
        'interstellar_communication': 200
    }

    base_cost = base_costs.get(research_type, 100)

    # Exponential cost increase: cost = base * (level ^ 1.5)
    cost = int(base_cost * (target_level ** 1.5))

    return cost

def calculate_research_points(user_id):
    """Calculate total research points from all user's planets"""
    user_planets = Planet.query.filter_by(user_id=user_id).all()

    total_points = 0
    for planet in user_planets:
        # Research points based on research lab level
        if planet.research_lab and planet.research_lab > 0:
            # Base points per lab level
            base_points = planet.research_lab * 10

            # Apply energy efficiency
            energy_production = planet.solar_plant * 20 + planet.fusion_reactor * 50
            energy_consumption = (planet.metal_mine * 10 +
                                planet.crystal_mine * 10 +
                                planet.deuterium_synthesizer * 20 +
                                planet.research_lab * 15)  # Research labs consume energy

            energy_ratio = min(1.0, energy_production / energy_consumption) if energy_consumption > 0 else 1.0

            # Calculate points for this tick (5 seconds = 1/72 hour)
            tick_points = max(1, int(base_points * energy_ratio / 72)) if planet.research_lab > 0 else 0

            total_points += tick_points

    return total_points

def get_research_info(research_type):
    """Get information about a research technology"""
    research_info = {
        'colonization_tech': {
            'name': 'Colonization Technology',
            'description': 'Allows colonization of planets with higher difficulty ratings',
            'benefits': [
                'Unlocks colonization of planets with difficulty up to your research level',
                'Reduces colonization failure chance',
                'Enables faster colony establishment'
            ],
            'max_level': 10
        },
        'astrophysics': {
            'name': 'Astrophysics',
            'description': 'Advances understanding of space travel and colonization',
            'benefits': [
                '+2 colony limit per level',
                'Reduces fleet travel time',
                'Improves exploration efficiency'
            ],
            'max_level': 15
        },
        'interstellar_communication': {
            'name': 'Interstellar Communication',
            'description': 'Enhances communication across vast distances',
            'benefits': [
                'Enables alliance communications',
                'Improves fleet coordination',
                'Reduces communication delays'
            ],
            'max_level': 12
        }
    }

    return research_info.get(research_type, {
        'name': 'Unknown Research',
        'description': 'Research information not available',
        'benefits': [],
        'max_level': 10
    })

@research_bp.route('/info/<research_type>', methods=['GET'])
@jwt_required()
def get_research_details(research_type):
    """Get detailed information about a research technology"""
    print("DEBUG: Research info endpoint called")
    print(f"DEBUG: Research type: {research_type}")

    info = get_research_info(research_type)

    return jsonify(info)
