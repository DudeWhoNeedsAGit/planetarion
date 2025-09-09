"""
Fleet Arrival Processing Service

This service handles the processing of fleets that have arrived at their destinations.
It manages colonization, resource collection, and other mission completion logic.
"""

from datetime import datetime, timedelta
from backend.database import db
from backend.models import Fleet, Planet, User, TickLog, Research
from backend.services.planet_traits import PlanetTraitService
from backend.config import calculate_fuel_consumption
import json

# Enhanced error handling constants
COLONIZATION_ERRORS = {
    'coordinates_occupied': 'Target coordinates are already occupied by another player',
    'insufficient_research': 'Research level too low for target colonization difficulty',
    'colony_limit_reached': 'Maximum colony limit reached for this account',
    'insufficient_fuel': 'Not enough fuel for colonization mission',
    'no_colony_ship': 'Fleet must contain at least one colony ship',
    'invalid_coordinates': 'Invalid coordinate format provided',
    'planet_not_found': 'Target planet not found at specified coordinates',
    'coordinates_claimed_during_travel': 'Coordinates were claimed by another player during travel',
    'system_error': 'System error occurred during colonization processing'
}

MISSION_ERRORS = {
    'invalid_target': 'Invalid mission target',
    'insufficient_resources': 'Insufficient resources for mission',
    'mission_not_supported': 'Mission type not supported',
    'fleet_not_found': 'Fleet not found',
    'planet_not_found': 'Target planet not found',
    'coordinates_invalid': 'Invalid coordinate format',
    'exploration_failed': 'Exploration mission failed',
    'combat_failed': 'Combat mission failed',
    'recycle_failed': 'Recycle mission failed'
}


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

        # Also check for coordinate-based missions that have arrived
        coordinate_based_fleets = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.like('exploring:%') |
            Fleet.status.like('colonizing:%')
        ).all()

        arrived_fleets.extend(coordinate_based_fleets)

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
        """Handle colonization fleet arrival with enhanced simultaneous colonization protection"""
        print(f"DEBUG: Processing colonization for fleet {fleet.id}")

        try:
            # Parse target coordinates from fleet status or target_coordinates
            coords_result = FleetArrivalService._parse_target_coordinates(fleet)
            if not coords_result['success']:
                print(f"ERROR: {coords_result['error']}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            target_x, target_y, target_z = coords_result['coordinates']
            print(f"DEBUG: Colonization target coordinates: {target_x}:{target_y}:{target_z}")

            # Enhanced simultaneous colonization protection
            colonization_result = FleetArrivalService._validate_colonization_target(fleet, target_x, target_y, target_z)
            if not colonization_result['success']:
                print(f"WARNING: {colonization_result['error']}")
                FleetArrivalService._return_fleet_to_stationed(fleet)

                # Create tick log for failed colonization
                tick_log = TickLog(
                    event_type='colonization_failed',
                    event_description=f'Colonization failed for fleet {fleet.id}: {colonization_result["error"]}'
                )
                db.session.add(tick_log)
                db.session.commit()
                return

            target_planet = colonization_result['planet']

            # Validate colony ship presence
            if not FleetArrivalService._validate_colony_ship(fleet):
                print(f"ERROR: Fleet {fleet.id} has no colony ships for colonization")
                FleetArrivalService._return_fleet_to_stationed(fleet)

                tick_log = TickLog(
                    event_type='colonization_failed',
                    event_description=f'Colonization failed for fleet {fleet.id}: No colony ships'
                )
                db.session.add(tick_log)
                db.session.commit()
                return

            # Successful colonization
            print(f"SUCCESS: Colonizing planet {target_planet.id} for user {fleet.user_id}")
            FleetArrivalService._complete_colonization(fleet, target_planet)

        except Exception as e:
            print(f"ERROR: Failed to process colonization for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _parse_target_coordinates(fleet):
        """Parse target coordinates from fleet status or target_coordinates field"""
        try:
            if ':' in fleet.status and fleet.status.startswith(('colonizing:', 'exploring:')):
                # Extract coordinates from status (format: colonizing:x:y:z or exploring:x:y:z)
                coords_part = fleet.status.split(':')[1:]
                target_x, target_y, target_z = map(int, coords_part)
            elif hasattr(fleet, 'target_coordinates') and fleet.target_coordinates:
                # Extract coordinates from target_coordinates field
                target_x, target_y, target_z = map(int, fleet.target_coordinates.split(':'))
            else:
                return {
                    'success': False,
                    'error': f'No coordinates found for fleet {fleet.id}'
                }

            return {
                'success': True,
                'coordinates': (target_x, target_y, target_z)
            }

        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid coordinates format for fleet {fleet.id}: {str(e)}'
            }

    @staticmethod
    def _validate_colonization_target(fleet, target_x, target_y, target_z):
        """Enhanced validation for colonization target with race condition protection"""
        # Find the target planet
        target_planet = Planet.query.filter_by(
            x=target_x, y=target_y, z=target_z
        ).first()

        if not target_planet:
            return {
                'success': False,
                'error': f'Target planet not found at coordinates {target_x}:{target_y}:{target_z}'
            }

        # Check if planet is already owned (race condition protection)
        if target_planet.user_id:
            owner_username = getattr(target_planet.user, 'username', f'user_{target_planet.user_id}')
            return {
                'success': False,
                'error': f'Planet already owned by {owner_username} (colonized during travel)'
            }

        # Additional validation could be added here:
        # - Check if planet is habitable
        # - Validate research requirements
        # - Check colony limits

        return {
            'success': True,
            'planet': target_planet
        }

    @staticmethod
    def _validate_colony_ship(fleet):
        """Validate that fleet has colony ships for colonization"""
        return fleet.colony_ship > 0

    @staticmethod
    def validate_colonization_fuel(fleet, distance):
        """Validate fuel requirements for colonization mission"""
        try:
            # Calculate fuel consumption based on fleet composition and distance
            fuel_required = FleetArrivalService._calculate_fuel_consumption(fleet, distance)

            # Get origin planet
            origin_planet = Planet.query.get(fleet.start_planet_id)
            if not origin_planet:
                return {
                    'success': False,
                    'error': 'Origin planet not found',
                    'fuel_required': fuel_required,
                    'fuel_available': 0
                }

            if origin_planet.deuterium < fuel_required:
                return {
                    'success': False,
                    'error': f'Insufficient fuel: {fuel_required} required, {origin_planet.deuterium} available',
                    'fuel_required': fuel_required,
                    'fuel_available': origin_planet.deuterium
                }

            return {
                'success': True,
                'fuel_required': fuel_required,
                'fuel_available': origin_planet.deuterium
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Fuel calculation error: {str(e)}',
                'fuel_required': 0,
                'fuel_available': 0
            }

    @staticmethod
    def _calculate_fuel_consumption(fleet, distance):
        """Calculate fuel consumption for a fleet traveling a given distance using centralized config"""
        return calculate_fuel_consumption(fleet, distance)

    @staticmethod
    def _complete_colonization(fleet, target_planet):
        """Complete the colonization process"""
        # Transfer ownership
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
        username = getattr(fleet.user, 'username', f'user_{fleet.user_id}')
        tick_log = TickLog(
            planet_id=target_planet.id,
            event_type='colonization',
            event_description=f'Planet {target_planet.name} colonized by {username}'
        )
        db.session.add(tick_log)

        # Return fleet to stationed status
        FleetArrivalService._return_fleet_to_stationed(fleet)

        db.session.commit()
        print(f"SUCCESS: Planet {target_planet.id} successfully colonized")

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

            # Generate planets in the explored system
            from backend.services.tick import generate_exploration_planets
            discovered_planets = generate_exploration_planets(target_x, target_y, target_z, fleet.user_id)

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
                        'fleet_id': fleet.id,
                        'planets_discovered': len(discovered_planets)
                    })
                    user.explored_systems = json.dumps(explored)

            # Create tick log entry
            tick_log = TickLog(
                event_type='exploration',
                event_description=f'System {target_x}:{target_y}:{target_z} explored by {username}, discovered {len(discovered_planets)} planets'
            )
            db.session.add(tick_log)

            # Commit all changes to database
            db.session.commit()

            # Set fleet to return to origin
            fleet.status = 'returning'
            fleet.mission = 'return'
            # Calculate return time (same as outbound journey)
            if fleet.departure_time and fleet.arrival_time:
                travel_time = fleet.arrival_time - fleet.departure_time
                fleet.arrival_time = datetime.utcnow() + travel_time
                fleet.eta = int(travel_time.total_seconds())
            else:
                # Fallback: assume 1 hour return time
                fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)
                fleet.eta = 3600

            db.session.commit()
            print(f"SUCCESS: System {target_x}:{target_y}:{target_z} explored, fleet returning")

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
