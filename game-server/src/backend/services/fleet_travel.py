"""
Fleet Travel Service

This service provides comprehensive travel information for fleets including:
- Distance calculations
- Travel time estimates
- Current position tracking
- Progress calculations
- Fleet speed calculations

Used by both backend API responses and frontend displays.
"""

from datetime import datetime
import math
from backend.models import Planet, Fleet


class FleetTravelService:
    """Service for calculating fleet travel information"""

    @staticmethod
    def calculate_travel_info(fleet):
        """
        Calculate comprehensive travel information for a fleet

        Args:
            fleet: Fleet model instance

        Returns:
            dict: Travel information including distance, duration, progress, position
        """
        # Allow traveling, returning, and coordinate-based missions (colonizing, exploring)
        valid_statuses = ['traveling', 'returning']
        is_coordinate_based = fleet.status and (fleet.status.startswith('colonizing:') or fleet.status.startswith('exploring:'))

        if not fleet or (fleet.status not in valid_statuses and not is_coordinate_based):
            return None

        # Get start and target planets
        start_planet = Planet.query.get(fleet.start_planet_id)
        if not start_planet:
            return None

        # For coordinate-based missions (colonization, exploration), create target planet
        if fleet.status and (fleet.status.startswith('colonizing:') or fleet.status.startswith('exploring:')):
            # Extract coordinates from status
            coords_part = fleet.status.split(':')[1:]
            if len(coords_part) == 3:
                try:
                    target_x, target_y, target_z = map(int, coords_part)
                    target_planet = Planet(
                        name='Target Location',
                        x=target_x,
                        y=target_y,
                        z=target_z
                    )
                except ValueError:
                    return None
            else:
                return None
        else:
            # Use target planet from database
            target_planet = Planet.query.get(fleet.target_planet_id)
            if not target_planet:
                return None

        # Calculate distance
        distance = FleetTravelService.calculate_distance(start_planet, target_planet)

        # Calculate fleet speed (based on slowest ship)
        fleet_speed = FleetTravelService.calculate_fleet_speed(fleet)

        # Calculate total duration
        total_duration_hours = distance / fleet_speed if fleet_speed > 0 else 0

        # Calculate current progress
        if fleet.departure_time and fleet.arrival_time:
            total_duration = (fleet.arrival_time - fleet.departure_time).total_seconds() / 3600
            elapsed_time = (datetime.utcnow() - fleet.departure_time).total_seconds() / 3600
            progress_percentage = min(100, max(0, (elapsed_time / total_duration) * 100)) if total_duration > 0 else 0

            # Calculate current position (linear interpolation)
            if progress_percentage < 100:
                current_x = start_planet.x + (target_planet.x - start_planet.x) * (progress_percentage / 100)
                current_y = start_planet.y + (target_planet.y - start_planet.y) * (progress_percentage / 100)
                current_z = start_planet.z + (target_planet.z - start_planet.z) * (progress_percentage / 100)
            else:
                current_x, current_y, current_z = target_planet.x, target_planet.y, target_planet.z
        else:
            progress_percentage = 0
            current_x, current_y, current_z = start_planet.x, start_planet.y, start_planet.z

        # Ensure coordinates are numeric before formatting
        try:
            current_pos = f"{float(current_x):.1f}:{float(current_y):.1f}:{float(current_z):.1f}"
            start_coords = f"{float(start_planet.x)}:{float(start_planet.y)}:{float(start_planet.z)}"
            target_coords = f"{float(target_planet.x)}:{float(target_planet.y)}:{float(target_planet.z)}"
        except (TypeError, ValueError):
            # Fallback for cases where coordinates might not be numeric (e.g., test mocks)
            current_pos = f"{current_x}:{current_y}:{current_z}"
            start_coords = f"{start_planet.x}:{start_planet.y}:{start_planet.z}"
            target_coords = f"{target_planet.x}:{target_planet.y}:{target_planet.z}"

        return {
            'distance': round(distance, 2),
            'total_duration_hours': round(total_duration_hours, 2),
            'progress_percentage': round(progress_percentage, 1),
            'current_position': current_pos,
            'fleet_speed': round(fleet_speed, 1),
            'start_coordinates': start_coords,
            'target_coordinates': target_coords,
            'is_coordinate_based': ':' in str(fleet.status)
        }

    @staticmethod
    def calculate_distance(planet1, planet2):
        """
        Calculate distance between two planets using 3D coordinates

        Args:
            planet1, planet2: Planet model instances

        Returns:
            float: Distance in coordinate units
        """
        if not planet1 or not planet2:
            return 0

        dx = planet1.x - planet2.x
        dy = planet1.y - planet2.y
        dz = planet1.z - planet2.z

        # Euclidean distance in 3D space
        distance = math.sqrt(dx**2 + dy**2 + dz**2)

        # Minimum distance of 1 to avoid division by zero
        return max(distance, 1)

    @staticmethod
    def calculate_fleet_speed(fleet):
        """
        Calculate fleet speed based on ship composition
        Speed is determined by the slowest ship in the fleet

        Args:
            fleet: Fleet model instance

        Returns:
            float: Fleet speed in units per hour
        """
        if not fleet:
            return 0

        # Ship speed hierarchy (slowest to fastest)
        ship_speeds = {
            'colony_ship': 2500,      # Slowest - colony ships are heavy
            'battleship': 3000,       # Heavy combat ships
            'cruiser': 3500,          # Medium combat ships
            'heavy_fighter': 4000,    # Heavy fighters
            'light_fighter': 4500,    # Light fighters
            'large_cargo': 3500,      # Large cargo ships
            'small_cargo': 5000       # Fastest - small cargo ships
        }

        slowest_speed = float('inf')

        # Check each ship type in the fleet
        for ship_type, speed in ship_speeds.items():
            ship_count = getattr(fleet, ship_type, 0)
            if ship_count > 0 and speed < slowest_speed:
                slowest_speed = speed

        # If no ships found, use default speed
        if slowest_speed == float('inf'):
            slowest_speed = 5000  # Default small cargo speed

        return slowest_speed

    @staticmethod
    def format_time_remaining(seconds):
        """
        Format time remaining into human-readable string

        Args:
            seconds: Time in seconds

        Returns:
            str: Formatted time string
        """
        if seconds <= 0:
            return 'Arrived'

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def get_fleet_status_info(fleet):
        """
        Get comprehensive status information for a fleet

        Args:
            fleet: Fleet model instance

        Returns:
            dict: Status information
        """
        if not fleet:
            return None

        travel_info = FleetTravelService.calculate_travel_info(fleet)

        return {
            'id': fleet.id,
            'mission': fleet.mission,
            'status': fleet.status,
            'departure_time': fleet.departure_time.isoformat() if fleet.departure_time else None,
            'arrival_time': fleet.arrival_time.isoformat() if fleet.arrival_time else None,
            'eta': fleet.eta,
            'eta_formatted': FleetTravelService.format_time_remaining(fleet.eta) if fleet.eta else None,
            'travel_info': travel_info,
            'ships': {
                'small_cargo': fleet.small_cargo,
                'large_cargo': fleet.large_cargo,
                'light_fighter': fleet.light_fighter,
                'heavy_fighter': fleet.heavy_fighter,
                'cruiser': fleet.cruiser,
                'battleship': fleet.battleship,
                'colony_ship': fleet.colony_ship
            }
        }
