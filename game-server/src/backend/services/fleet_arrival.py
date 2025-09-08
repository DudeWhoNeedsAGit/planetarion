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
            elif fleet.mission == 'attack':
                FleetArrivalService._process_attack(fleet)
            elif fleet.mission == 'return':
                FleetArrivalService._process_return(fleet)
            elif fleet.mission == 'explore':
                FleetArrivalService._process_exploration(fleet)
            elif fleet.mission == 'recycle':
                FleetArrivalService._process_recycle(fleet)
            # Add other mission types as needed

    @staticmethod
    def _process_colonization(fleet):
        """Handle colonization fleet arrival"""
        print(f"DEBUG: Processing colonization for fleet {fleet.id}")

        try:
            # Parse target coordinates from fleet status or target_coordinates
            if ':' in fleet.status and fleet.status.startswith(('colonizing:', 'exploring:')):
                # Extract coordinates from status (format: colonizing:x:y:z or exploring:x:y:z)
                coords_part = fleet.status.split(':')[1:]
                try:
                    target_x, target_y, target_z = map(int, coords_part)
                except ValueError:
                    print(f"ERROR: Invalid coordinates in status for fleet {fleet.id}: {fleet.status}")
                    FleetArrivalService._return_fleet_to_stationed(fleet)
                    return
            elif hasattr(fleet, 'target_coordinates') and fleet.target_coordinates:
                # Extract coordinates from target_coordinates field
                try:
                    target_x, target_y, target_z = map(int, fleet.target_coordinates.split(':'))
                except ValueError:
                    print(f"ERROR: Invalid target_coordinates for fleet {fleet.id}: {fleet.target_coordinates}")
                    FleetArrivalService._return_fleet_to_stationed(fleet)
                    return
            else:
                print(f"ERROR: No coordinates found for fleet {fleet.id}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            print(f"DEBUG: Colonization target coordinates: {target_x}:{target_y}:{target_z}")

            # Find the target planet
            target_planet = Planet.query.filter_by(
                x=target_x, y=target_y, z=target_z
            ).first()

            if not target_planet:
                print(f"ERROR: Target planet not found at coordinates {target_x}:{target_y}:{target_z}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
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
            if ':' in fleet.status and fleet.status.startswith('exploring:'):
                # Extract coordinates from status (format: exploring:x:y:z)
                coords_part = fleet.status.split(':')[1:]
                try:
                    target_x, target_y, target_z = map(int, coords_part)
                except ValueError:
                    print(f"ERROR: Invalid coordinates in status for exploration fleet {fleet.id}: {fleet.status}")
                    FleetArrivalService._return_fleet_to_stationed(fleet)
                    return
            elif hasattr(fleet, 'target_coordinates') and fleet.target_coordinates:
                # Extract coordinates from target_coordinates field
                try:
                    target_x, target_y, target_z = map(int, fleet.target_coordinates.split(':'))
                except ValueError:
                    print(f"ERROR: Invalid target_coordinates for exploration fleet {fleet.id}: {fleet.target_coordinates}")
                    FleetArrivalService._return_fleet_to_stationed(fleet)
                    return
            else:
                print(f"ERROR: No coordinates found for exploration fleet {fleet.id}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Mark system as explored for the user
            user = fleet.user
            username = getattr(user, 'username', f'user_{fleet.user_id}')

            # Only update explored systems if user has the attribute (not a mock)
            if hasattr(user, 'explored_systems'):
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
                event_description=f'System {target_x}:{target_y}:{target_z} explored by {username}'
            )
            db.session.add(tick_log)

            # Return fleet to stationed status
            FleetArrivalService._return_fleet_to_stationed(fleet)

            db.session.commit()
            print(f"SUCCESS: System {target_x}:{target_y}:{target_z} explored")

        except Exception as e:
            print(f"ERROR: Failed to process exploration for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            # Ensure fleet is returned to stationed even on error
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_attack(fleet):
        """Handle attack fleet arrival"""
        print(f"DEBUG: Processing attack for fleet {fleet.id}")

        try:
            # Get target planet
            target_planet = Planet.query.get(fleet.target_planet_id)
            if not target_planet:
                print(f"ERROR: Target planet {fleet.target_planet_id} not found")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Check if planet is still owned by enemy (might have been captured)
            if target_planet.user_id == fleet.user_id:
                print(f"WARNING: Target planet {target_planet.id} now owned by attacker")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Find defending fleet
            defending_fleet = Fleet.query.filter_by(
                user_id=target_planet.user_id,
                start_planet_id=fleet.target_planet_id,
                status__in=['stationed', 'defending']
            ).first()

            if defending_fleet:
                # Fleet vs Fleet combat
                print(f"DEBUG: Fleet vs Fleet combat: {fleet.id} vs {defending_fleet.id}")
                from backend.services.combat_engine import CombatEngine
                combat_result = CombatEngine.calculate_battle(fleet, defending_fleet, target_planet)
                CombatEngine.process_combat_result(combat_result, fleet, defending_fleet, target_planet)
            else:
                # Attack on undefended planet
                print(f"DEBUG: Attacking undefended planet {target_planet.id}")
                from backend.services.combat_engine import CombatEngine
                combat_result = CombatEngine.calculate_planet_attack(fleet, target_planet)
                CombatEngine.process_planet_attack_result(combat_result, fleet, target_planet)

            print(f"SUCCESS: Attack mission completed for fleet {fleet.id}")

        except Exception as e:
            print(f"ERROR: Failed to process attack for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_recycle(fleet):
        """Handle recycle fleet arrival"""
        print(f"DEBUG: Processing recycle for fleet {fleet.id}")

        try:
            # Get target planet
            target_planet = Planet.query.get(fleet.target_planet_id)
            if not target_planet:
                print(f"ERROR: Target planet {fleet.target_planet_id} not found")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Find debris field at planet
            debris_field = target_planet.debris_fields.first()
            if not debris_field:
                print(f"WARNING: No debris field found at planet {target_planet.id}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Calculate recycler capacity
            recycler_capacity = fleet.recycler * 1000  # Assume 1000 cargo capacity per recycler

            # Collect resources
            collected_metal = min(debris_field.metal, recycler_capacity // 2)
            collected_crystal = min(debris_field.crystal, recycler_capacity // 2)
            collected_deuterium = min(debris_field.deuterium, recycler_capacity // 2)

            # Update debris field
            debris_field.metal -= collected_metal
            debris_field.crystal -= collected_crystal
            debris_field.deuterium -= collected_deuterium

            # Add resources to fleet (simplified - would need cargo tracking)
            # For now, just log the collection
            print(f"SUCCESS: Collected {collected_metal} metal, {collected_crystal} crystal, {collected_deuterium} deuterium")

            # Create tick log entry
            tick_log = TickLog(
                planet_id=target_planet.id,
                fleet_id=fleet.id,
                event_type='recycle',
                event_description=f'Fleet {fleet.id} collected {collected_metal}M {collected_crystal}C {collected_deuterium}D from debris field'
            )
            db.session.add(tick_log)

            # Clean up empty debris field
            if debris_field.metal <= 0 and debris_field.crystal <= 0 and debris_field.deuterium <= 0:
                db.session.delete(debris_field)

            FleetArrivalService._return_fleet_to_stationed(fleet)
            db.session.commit()

            print(f"SUCCESS: Recycle mission completed for fleet {fleet.id}")

        except Exception as e:
            print(f"ERROR: Failed to process recycle for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _return_fleet_to_stationed(fleet):
        """Return a fleet to stationed status"""
        print(f"DEBUG: Returning fleet {fleet.id} to stationed status")
        fleet.status = 'stationed'
        fleet.mission = 'stationed'
        fleet.arrival_time = None
        fleet.eta = 0
