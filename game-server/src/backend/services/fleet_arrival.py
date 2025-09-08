"""
Fleet Arrival Processing Service

This service handles the processing of fleets that have arrived at their destinations.
It manages colonization, resource collection, and other mission completion logic.
"""

from datetime import datetime
from backend.database import db
from backend.models import Fleet, Planet, User, TickLog, Research
from backend.services.planet_traits import PlanetTraitService
import json


class FleetArrivalService:
    """Service for processing arrived fleets and completing their missions"""

    @staticmethod
    def process_arrived_fleets():
        """Process all fleets that have arrived at their destinations"""
        print("DEBUG: Processing arrived fleets")
        arrived_fleets = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.in_(['traveling', 'returning'])
        ).all()

        print(f"DEBUG: Found {len(arrived_fleets)} arrived fleets")
        for fleet in arrived_fleets:
            print(f"DEBUG: Processing fleet {fleet.id} with mission {fleet.mission}")
            if fleet.mission == 'colonize':
                FleetArrivalService._process_colonization(fleet)
            elif fleet.mission == 'return':
                FleetArrivalService._process_return(fleet)
            elif fleet.mission == 'explore':
                FleetArrivalService._process_exploration(fleet)
            # Add other mission types as needed

    @staticmethod
    def _process_colonization(fleet):
        """Handle colonization fleet arrival"""
        print(f"DEBUG: Processing colonization for fleet {fleet.id}")

        try:
            # Parse target coordinates from fleet status or target_coordinates
            if ':' in fleet.status:
                # Extract coordinates from status (format: colonizing:x:y:z)
                coords_part = fleet.status.split(':')[1:]
                target_x, target_y, target_z = map(int, coords_part)
            elif fleet.target_coordinates:
                # Extract coordinates from target_coordinates field
                target_x, target_y, target_z = map(int, fleet.target_coordinates.split(':'))
            else:
                print(f"ERROR: No coordinates found for colonization fleet {fleet.id}")
                return

            print(f"DEBUG: Colonization target coordinates: {target_x}:{target_y}:{target_z}")

            # Find the target planet
            target_planet = Planet.query.filter_by(
                x=target_x, y=target_y, z=target_z
            ).first()

            if not target_planet:
                print(f"ERROR: Target planet not found at coordinates {target_x}:{target_y}:{target_z}")
                return

            if target_planet.user_id:
                print(f"WARNING: Planet {target_planet.id} already owned by user {target_planet.user_id}")
                # Planet was colonized by someone else during travel
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Check if fleet has colony ship
            if fleet.colony_ship <= 0:
                print(f"ERROR: Fleet {fleet.id} has no colony ships for colonization")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Successful colonization
            print(f"SUCCESS: Colonizing planet {target_planet.id} for user {fleet.user_id}")
            target_planet.user_id = fleet.user_id
            target_planet.is_home_planet = False  # Colonies are not home planets
            target_planet.colonized_at = datetime.utcnow()

            # Initialize colony with starting resources
            target_planet.metal = 1000
            target_planet.crystal = 500
            target_planet.deuterium = 0

            # Initialize basic buildings
            target_planet.metal_mine = 1
            target_planet.crystal_mine = 1
            target_planet.solar_plant = 1

            # Create tick log entry
            tick_log = TickLog(
                planet_id=target_planet.id,
                event_type='colonization',
                event_description=f'Planet {target_planet.name} colonized by {fleet.user.username}'
            )
            db.session.add(tick_log)

            # Return fleet to stationed status
            FleetArrivalService._return_fleet_to_stationed(fleet)

            db.session.commit()
            print(f"SUCCESS: Planet {target_planet.id} successfully colonized")

        except Exception as e:
            print(f"ERROR: Failed to process colonization for fleet {fleet.id}: {str(e)}")
            db.session.rollback()

    @staticmethod
    def _process_return(fleet):
        """Handle returning fleet arrival"""
        print(f"DEBUG: Processing return for fleet {fleet.id}")
        FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_exploration(fleet):
        """Handle exploration fleet arrival"""
        print(f"DEBUG: Processing exploration for fleet {fleet.id}")

        try:
            # Parse target coordinates
            if ':' in fleet.status:
                coords_part = fleet.status.split(':')[1:]
                target_x, target_y, target_z = map(int, coords_part)
            elif fleet.target_coordinates:
                target_x, target_y, target_z = map(int, fleet.target_coordinates.split(':'))
            else:
                print(f"ERROR: No coordinates found for exploration fleet {fleet.id}")
                return

            # Mark system as explored for the user
            user = fleet.user
            if user.explored_systems:
                try:
                    explored = json.loads(user.explored_systems)
                except:
                    explored = []
            else:
                explored = []

            system_key = f"{target_x}:{target_y}:{target_z}"
            if system_key not in explored:
                explored.append({
                    'coordinates': system_key,
                    'explored_at': datetime.utcnow().isoformat(),
                    'fleet_id': fleet.id
                })
                user.explored_systems = json.dumps(explored)

            # Create tick log entry
            tick_log = TickLog(
                event_type='exploration',
                event_description=f'System {system_key} explored by {user.username}'
            )
            db.session.add(tick_log)

            # Return fleet to stationed status
            FleetArrivalService._return_fleet_to_stationed(fleet)

            db.session.commit()
            print(f"SUCCESS: System {system_key} explored")

        except Exception as e:
            print(f"ERROR: Failed to process exploration for fleet {fleet.id}: {str(e)}")
            db.session.rollback()

    @staticmethod
    def _return_fleet_to_stationed(fleet):
        """Return a fleet to stationed status"""
        print(f"DEBUG: Returning fleet {fleet.id} to stationed status")
        fleet.status = 'stationed'
        fleet.mission = 'stationed'
        fleet.arrival_time = None
        fleet.eta = 0
