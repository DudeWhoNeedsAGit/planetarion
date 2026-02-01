"""
Colonization Service

This module centralizes colonization-related helpers so route handlers and
arrival processing can share consistent behavior.
"""

from backend.database import db
from backend.models import Planet, Research
from backend.services.planet_traits import PlanetTraitService


class ColonizationService:
    @staticmethod
    def get_or_create_target_planet(target_x, target_y, target_z):
        """Return a Planet row for the target coordinates, creating an unowned placeholder if needed."""
        target_planet = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).first()
        if target_planet:
            return target_planet, False

        target_planet = Planet(
            name='Uncharted Planet',
            x=target_x,
            y=target_y,
            z=target_z,
            user_id=None,
        )
        db.session.add(target_planet)
        db.session.flush()
        return target_planet, True

    @staticmethod
    def is_occupied(target_x, target_y, target_z):
        """Return True if a planet exists at coordinates and is owned by any user."""
        target_planet = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).first()
        return bool(target_planet and target_planet.user_id)

    @staticmethod
    def get_required_research_level(target_x, target_y, target_z):
        """Return colonization difficulty for coordinates."""
        return PlanetTraitService.calculate_colonization_difficulty(target_x, target_y, target_z)

    @staticmethod
    def get_user_colonization_tech(user_id):
        """Return user's colonization tech level."""
        research = Research.query.filter_by(user_id=user_id).first()
        return research.colonization_tech if research else 0

