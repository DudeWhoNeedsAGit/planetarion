"""
Sector Service - Business Logic for Sector-Based Fog of War

Following Service Layer Pattern from systemPatterns.md
Handles sector exploration, calculation, and management.
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from ..database import db
from ..models import User

# Configuration constants
SECTOR_SIZE = 50  # Units per sector (following existing patterns)


class SectorService:
    """Service layer for sector-based exploration management"""

    @staticmethod
    def system_to_sector(system_x: int, system_y: int) -> Dict[str, int]:
        """
        Convert system coordinates to sector coordinates

        Following established coordinate calculation patterns
        """
        return {
            'sector_x': system_x // SECTOR_SIZE,
            'sector_y': system_y // SECTOR_SIZE
        }

    @staticmethod
    def get_sector_bounds(sector_x: int, sector_y: int) -> Dict[str, int]:
        """
        Get the coordinate bounds for a sector

        Returns min/max coordinates for the sector
        """
        return {
            'min_x': sector_x * SECTOR_SIZE,
            'max_x': (sector_x + 1) * SECTOR_SIZE - 1,
            'min_y': sector_y * SECTOR_SIZE,
            'max_y': (sector_y + 1) * SECTOR_SIZE - 1
        }

    @staticmethod
    def mark_sector_explored(user_id: int, sector_x: int, sector_y: int) -> bool:
        """
        Mark a sector as explored for a user

        Following Repository Pattern for data access
        Returns True if sector was newly explored, False if already explored
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False

            # Parse existing explored sectors
            explored_sectors = []
            if user.explored_sectors:
                try:
                    explored_sectors = json.loads(user.explored_sectors)
                except json.JSONDecodeError:
                    explored_sectors = []

            # Check if sector is already explored
            sector_key = f"{sector_x}:{sector_y}"
            for sector in explored_sectors:
                if sector.get('x') == sector_x and sector.get('y') == sector_y:
                    return False  # Already explored

            # Add new explored sector
            explored_sectors.append({
                'x': sector_x,
                'y': sector_y,
                'explored_at': datetime.utcnow().isoformat()
            })

            # Update user record
            user.explored_sectors = json.dumps(explored_sectors)
            db.session.commit()

            return True  # Newly explored

        except Exception as e:
            db.session.rollback()
            print(f"Error marking sector explored: {e}")
            return False

    @staticmethod
    def get_explored_sectors(user_id: int) -> List[Dict]:
        """
        Get all explored sectors for a user

        Following Repository Pattern for data access
        Returns list of sector dictionaries with coordinates and timestamps
        """
        try:
            user = User.query.get(user_id)
            if not user or not user.explored_sectors:
                return []

            try:
                explored_sectors = json.loads(user.explored_sectors)
                return explored_sectors
            except json.JSONDecodeError:
                return []

        except Exception as e:
            print(f"Error getting explored sectors: {e}")
            return []

    @staticmethod
    def is_sector_explored(user_id: int, sector_x: int, sector_y: int) -> bool:
        """
        Check if a specific sector is explored by a user

        Following established query patterns
        """
        explored_sectors = SectorService.get_explored_sectors(user_id)

        for sector in explored_sectors:
            if sector.get('x') == sector_x and sector.get('y') == sector_y:
                return True

        return False

    @staticmethod
    def explore_system(user_id: int, system_x: int, system_y: int) -> Dict[str, any]:
        """
        Explore a system and mark its containing sector as explored

        Main business logic method following Service Layer Pattern
        Returns exploration result with sector information
        """
        sector_coords = SectorService.system_to_sector(system_x, system_y)

        # Mark sector as explored
        newly_explored = SectorService.mark_sector_explored(
            user_id,
            sector_coords['sector_x'],
            sector_coords['sector_y']
        )

        return {
            'system_x': system_x,
            'system_y': system_y,
            'sector_x': sector_coords['sector_x'],
            'sector_y': sector_coords['sector_y'],
            'newly_explored': newly_explored,
            'sector_bounds': SectorService.get_sector_bounds(
                sector_coords['sector_x'],
                sector_coords['sector_y']
            )
        }

    @staticmethod
    def get_sector_statistics(user_id: int) -> Dict[str, int]:
        """
        Get exploration statistics for a user

        Following established reporting patterns
        """
        explored_sectors = SectorService.get_explored_sectors(user_id)

        return {
            'total_explored_sectors': len(explored_sectors),
            'sectors_this_session': 0,  # Could be enhanced to track session stats
            'exploration_percentage': 0  # Could calculate based on total map size
        }

    @staticmethod
    def reset_exploration(user_id: int) -> bool:
        """
        Reset all exploration data for a user (admin/debug function)

        Following established admin patterns
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False

            user.explored_sectors = json.dumps([])
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error resetting exploration: {e}")
            return False
