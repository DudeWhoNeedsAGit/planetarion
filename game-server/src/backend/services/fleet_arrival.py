"""
Fleet Arrival Processing Service

This service handles the processing of fleets that have arrived at their destinations.
It manages colonization, resource collection, and other mission completion logic.
"""

from datetime import datetime, timedelta
from backend.database import db
from backend.models import Fleet, Planet, User, TickLog, Research, DebrisField, EspionageReport
from backend.services.planet_traits import PlanetTraitService
from backend.config import calculate_fuel_consumption
from backend.services.fleet_state_machine import FleetStateMachine
from backend.services.commander_xp import CommanderXPService, xp_from_resources
from backend.services.pirate_factions import is_pirate_username, is_pirate_user
import json

# Enhanced error handling constants
COLONIZATION_ERRORS = {
    'coordinates_occupied': 'Target coordinates are already colonized (occupied by another player)',
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
    def _get_fleet_user(fleet):
        user = getattr(fleet, 'owner', None)
        if user is not None:
            return user
        return User.query.get(fleet.user_id)

    @staticmethod
    def process_arrived_fleets(user_id: int | None = None):
        """Process fleets that have arrived at their destinations.

        If `user_id` is provided, only process fleets owned by that user. This is
        important for request-scoped catch-up flows (e.g. /api/auth/me) where we
        must not mutate other players' fleets.
        """
        print("DEBUG: Processing arrived fleets")
        arrived_query = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.in_(['traveling', 'returning', 'defending'])
        )
        if user_id is not None:
            arrived_query = arrived_query.filter(Fleet.user_id == int(user_id))
        arrived_fleets = arrived_query.all()

        # Also check for coordinate-based missions that have arrived
        coord_query = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.like('exploring:%') |
            Fleet.status.like('colonizing:%')
        )
        if user_id is not None:
            coord_query = coord_query.filter(Fleet.user_id == int(user_id))
        coordinate_based_fleets = coord_query.all()

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
            elif fleet.mission == 'espionage':
                FleetArrivalService._process_espionage(fleet)
            elif fleet.mission == 'transport':
                FleetArrivalService._process_transport(fleet)
            elif fleet.mission == 'deploy':
                FleetArrivalService._process_deploy(fleet)
            elif fleet.mission == 'defend':
                FleetArrivalService._process_defend(fleet)
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
                    tick_number=0,
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
                    tick_number=0,
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
            owner_username = getattr(getattr(target_planet, 'owner', None), 'username', f'user_{target_planet.user_id}')
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
        user = FleetArrivalService._get_fleet_user(fleet)
        username = getattr(user, 'username', f'user_{fleet.user_id}')
        tick_log = TickLog(
            tick_number=0,
            planet_id=target_planet.id,
            fleet_id=fleet.id,
            event_type='colonization',
            event_description=f'Planet {target_planet.name} colonized by {username}'
        )
        db.session.add(tick_log)
        if is_pirate_username(username):
            db.session.add(
                TickLog(
                    tick_number=0,
                    planet_id=target_planet.id,
                    fleet_id=fleet.id,
                    event_type="pirate_colonization_completed",
                    event_description=f"Pirate faction {username} established colony at {target_planet.x}:{target_planet.y}:{target_planet.z}",
                )
            )

        # Commander XP (idempotent per TickLog row if possible).
        try:
            db.session.flush()
            difficulty = int(getattr(target_planet, "colonization_difficulty", 1) or 1)
            CommanderXPService.award_xp(
                user_id=int(fleet.user_id),
                xp=200 + max(0, difficulty - 1) * 50,
                source_type="colonization",
                source_id=str(getattr(tick_log, "id", None) or f"planet:{target_planet.id}:fleet:{fleet.id}"),
            )
        except Exception:
            pass

        # Return fleet to stationed status
        FleetArrivalService._return_fleet_to_stationed(fleet)

        db.session.commit()
        print(f"SUCCESS: Planet {target_planet.id} successfully colonized")

    @staticmethod
    def _process_return(fleet):
        """Handle returning fleet arrival"""
        print(f"DEBUG: Processing return for fleet {fleet.id}")
        # Deliver any cargo carried back to the origin planet.
        try:
            cargo_metal = int(getattr(fleet, "cargo_metal", 0) or 0)
            cargo_crystal = int(getattr(fleet, "cargo_crystal", 0) or 0)
            cargo_deuterium = int(getattr(fleet, "cargo_deuterium", 0) or 0)
        except (TypeError, ValueError):
            cargo_metal = cargo_crystal = cargo_deuterium = 0

        if cargo_metal or cargo_crystal or cargo_deuterium:
            origin_planet = Planet.query.get(getattr(fleet, "start_planet_id", None))
            if origin_planet:
                origin_planet.metal += cargo_metal
                origin_planet.crystal += cargo_crystal
                origin_planet.deuterium += cargo_deuterium

            fleet.cargo_metal = 0
            fleet.cargo_crystal = 0
            fleet.cargo_deuterium = 0

            try:
                db.session.add(TickLog(
                    tick_number=0,
                    planet_id=getattr(fleet, "start_planet_id", None),
                    fleet_id=fleet.id,
                    event_type="cargo_delivered",
                    event_description=f"Fleet {fleet.id} delivered {cargo_metal}M {cargo_crystal}C {cargo_deuterium}D",
                ))
            except RuntimeError:
                pass

        try:
            db.session.add(TickLog(
                tick_number=0,
                planet_id=fleet.start_planet_id,
                fleet_id=fleet.id,
                event_type='fleet_returned',
                event_description=f'Fleet {fleet.id} returned and is now stationed'
            ))
        except RuntimeError:
            # Unit tests may call this without an application context.
            pass
        FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_transport(fleet):
        """Handle transport arrival: unload cargo to target (if owned), then return home."""
        print(f"DEBUG: Processing transport for fleet {fleet.id}")
        arrival_processed_at = datetime.utcnow()

        try:
            target_planet = Planet.query.get(getattr(fleet, "target_planet_id", None))
            if not target_planet:
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            # MVP: only allow transporting to your own planets.
            if target_planet.user_id != fleet.user_id:
                db.session.add(TickLog(
                    tick_number=0,
                    fleet_id=fleet.id,
                    planet_id=getattr(fleet, "start_planet_id", None),
                    event_type="transport_failed",
                    event_description=f"Fleet {fleet.id} transport failed: target not owned by sender",
                ))
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            cargo_metal = int(getattr(fleet, "cargo_metal", 0) or 0)
            cargo_crystal = int(getattr(fleet, "cargo_crystal", 0) or 0)
            cargo_deuterium = int(getattr(fleet, "cargo_deuterium", 0) or 0)

            if cargo_metal or cargo_crystal or cargo_deuterium:
                target_planet.metal += cargo_metal
                target_planet.crystal += cargo_crystal
                target_planet.deuterium += cargo_deuterium

                fleet.cargo_metal = 0
                fleet.cargo_crystal = 0
                fleet.cargo_deuterium = 0

                db.session.add(TickLog(
                    tick_number=0,
                    planet_id=target_planet.id,
                    fleet_id=fleet.id,
                    event_type="transport_unloaded",
                    event_description=f"Fleet {fleet.id} unloaded {cargo_metal}M {cargo_crystal}C {cargo_deuterium}D",
                ))

            # Return to origin after unloading.
            if fleet.departure_time and fleet.arrival_time:
                travel_time_seconds = max(0, (fleet.arrival_time - fleet.departure_time).total_seconds())
            else:
                travel_time_seconds = 3600

            FleetStateMachine.set_returning(
                fleet,
                now=arrival_processed_at,
                return_time_seconds=travel_time_seconds,
            )
            db.session.commit()
        except Exception as e:
            print(f"ERROR: Failed to process transport for fleet {fleet.id}: {e}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)
            db.session.commit()

    @staticmethod
    def _process_deploy(fleet):
        """Handle deploy arrival: move fleet to target and station there (no return), unload cargo if any."""
        print(f"DEBUG: Processing deploy for fleet {fleet.id}")
        arrival_processed_at = datetime.utcnow()

        try:
            target_planet = Planet.query.get(getattr(fleet, "target_planet_id", None))
            if not target_planet:
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            if target_planet.user_id != fleet.user_id:
                db.session.add(TickLog(
                    tick_number=0,
                    fleet_id=fleet.id,
                    planet_id=getattr(fleet, "start_planet_id", None),
                    event_type="deploy_failed",
                    event_description=f"Fleet {fleet.id} deploy failed: target not owned by sender",
                ))
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            cargo_metal = int(getattr(fleet, "cargo_metal", 0) or 0)
            cargo_crystal = int(getattr(fleet, "cargo_crystal", 0) or 0)
            cargo_deuterium = int(getattr(fleet, "cargo_deuterium", 0) or 0)

            if cargo_metal or cargo_crystal or cargo_deuterium:
                target_planet.metal += cargo_metal
                target_planet.crystal += cargo_crystal
                target_planet.deuterium += cargo_deuterium
                fleet.cargo_metal = 0
                fleet.cargo_crystal = 0
                fleet.cargo_deuterium = 0

                db.session.add(TickLog(
                    tick_number=0,
                    planet_id=target_planet.id,
                    fleet_id=fleet.id,
                    event_type="deploy_unloaded",
                    event_description=f"Fleet {fleet.id} deployed {cargo_metal}M {cargo_crystal}C {cargo_deuterium}D",
                ))

            # Fleet is now stationed at the target planet.
            fleet.start_planet_id = target_planet.id
            FleetStateMachine.set_stationed(fleet, now=arrival_processed_at)
            fleet.mission = "deploy"

            db.session.commit()
        except Exception as e:
            print(f"ERROR: Failed to process deploy for fleet {fleet.id}: {e}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)
            db.session.commit()

    @staticmethod
    def _process_defend(fleet):
        """Handle defend arrival: station fleet at target in defending status."""
        print(f"DEBUG: Processing defend for fleet {fleet.id}")
        arrival_processed_at = datetime.utcnow()

        try:
            target_planet = Planet.query.get(getattr(fleet, "target_planet_id", None))
            if not target_planet:
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            if target_planet.user_id != fleet.user_id:
                db.session.add(TickLog(
                    tick_number=0,
                    fleet_id=fleet.id,
                    planet_id=getattr(fleet, "start_planet_id", None),
                    event_type="defend_failed",
                    event_description=f"Fleet {fleet.id} defend failed: target not owned by sender",
                ))
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            fleet.start_planet_id = target_planet.id
            FleetStateMachine.set_sent_defending(fleet, target_planet_id=target_planet.id)
            fleet.departure_time = arrival_processed_at
            fleet.arrival_time = arrival_processed_at
            fleet.eta = 0
            db.session.add(TickLog(
                tick_number=0,
                planet_id=target_planet.id,
                fleet_id=fleet.id,
                event_type="defend_arrived",
                event_description=f"Fleet {fleet.id} is now defending {target_planet.name}",
            ))
            db.session.commit()
        except Exception as e:
            print(f"ERROR: Failed to process defend for fleet {fleet.id}: {e}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)
            db.session.commit()

    @staticmethod
    def _process_exploration(fleet):
        """Handle exploration fleet arrival with comprehensive debug logging"""
        print(f"DEBUG: Processing exploration for fleet {fleet.id}")
        print(f"DEBUG: Fleet status: {fleet.status}")
        print(f"DEBUG: Fleet mission: {fleet.mission}")
        print(f"DEBUG: Fleet target_coordinates: {getattr(fleet, 'target_coordinates', 'None')}")

        try:
            # Parse target coordinates with detailed logging
            coords_result = FleetArrivalService._parse_target_coordinates(fleet)
            print(f"DEBUG: Coordinate parsing result: {coords_result}")

            if not coords_result['success']:
                print(f"ERROR: {coords_result['error']}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            target_x, target_y, target_z = coords_result['coordinates']
            print(f"DEBUG: Successfully parsed coordinates: {target_x}:{target_y}:{target_z}")

            # Generate planets in the explored system
            print(f"DEBUG: Calling generate_exploration_planets for coordinates {target_x}:{target_y}:{target_z}")
            from backend.services.tick import generate_exploration_planets

            try:
                discovered_planets = generate_exploration_planets(target_x, target_y, target_z, fleet.user_id)
                print(f"DEBUG: generate_exploration_planets returned {len(discovered_planets)} planets")
            except Exception as gen_error:
                print(f"ERROR: generate_exploration_planets failed: {str(gen_error)}")
                print(f"DEBUG: Attempting fallback planet creation")
                # Fallback: create planets directly
                discovered_planets = FleetArrivalService._create_exploration_planets_fallback(target_x, target_y, target_z, fleet.user_id)
                print(f"DEBUG: Fallback created {len(discovered_planets)} planets")

            # Mark system as explored for the user
            user = FleetArrivalService._get_fleet_user(fleet)
            username = getattr(user, 'username', f'user_{fleet.user_id}')
            print(f"DEBUG: Processing exploration data for user {username}")

            # Only update explored systems if user has the attribute (not a mock)
            if hasattr(user, 'explored_systems'):
                print(f"DEBUG: User has explored_systems attribute")
                if user.explored_systems:
                    try:
                        explored = json.loads(user.explored_systems)
                        print(f"DEBUG: Loaded existing explored systems: {len(explored)} systems")
                    except:
                        explored = []
                        print(f"DEBUG: Failed to parse explored_systems, starting fresh")
                else:
                    explored = []
                    print(f"DEBUG: No existing explored systems")

                system_key = f"{target_x}:{target_y}:{target_z}"
                if system_key not in explored:
                    explored.append({
                        'coordinates': system_key,
                        'explored_at': datetime.utcnow().isoformat(),
                        'fleet_id': fleet.id,
                        'planets_discovered': len(discovered_planets)
                    })
                    user.explored_systems = json.dumps(explored)
                    print(f"DEBUG: Added system {system_key} to explored systems")
                else:
                    print(f"DEBUG: System {system_key} already explored")
            else:
                print(f"DEBUG: User does not have explored_systems attribute (likely test mock)")

            # Create tick log entry
            tick_log = TickLog(
                tick_number=0,
                event_type='exploration',
                event_description=f'System {target_x}:{target_y}:{target_z} explored by {username}, discovered {len(discovered_planets)} planets'
            )
            db.session.add(tick_log)
            print(f"DEBUG: Created tick log entry for exploration")

            # Commit all changes to database
            db.session.commit()
            print(f"DEBUG: Committed exploration changes to database")

            # Set fleet to return to origin
            fleet.status = 'returning'
            fleet.mission = 'return'
            # Calculate return time (same as outbound journey)
            if fleet.departure_time and fleet.arrival_time:
                travel_time = fleet.arrival_time - fleet.departure_time
                fleet.arrival_time = datetime.utcnow() + travel_time
                fleet.eta = int(travel_time.total_seconds())
                print(f"DEBUG: Set fleet return time: {travel_time} (ETA: {fleet.eta}s)")
            else:
                # Fallback: assume 1 hour return time
                fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)
                fleet.eta = 3600
                print(f"DEBUG: Used fallback return time: 1 hour")

            db.session.commit()
            print(f"SUCCESS: System {target_x}:{target_y}:{target_z} explored, fleet returning")

        except Exception as e:
            print(f"ERROR: Failed to process exploration for fleet {fleet.id}: {str(e)}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            db.session.rollback()
            # Ensure fleet is returned to stationed even on error
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_attack(fleet):
        """Handle attack fleet arrival"""
        print(f"DEBUG: Processing attack for fleet {fleet.id}")

        try:
            arrival_processed_at = datetime.utcnow()

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
            defending_fleet = (
                Fleet.query.filter(
                    Fleet.user_id == target_planet.user_id,
                    Fleet.start_planet_id == fleet.target_planet_id,
                    Fleet.status.in_(['stationed', 'defending']),
                )
                .order_by(Fleet.id.asc())
                .first()
            )

            if defending_fleet:
                # Fleet vs Fleet combat
                print(f"DEBUG: Fleet vs Fleet combat: {fleet.id} vs {defending_fleet.id}")
                from backend.services.combat_engine import CombatEngine
                combat_result = CombatEngine.calculate_battle(fleet, defending_fleet, target_planet)
                CombatEngine.process_combat_result(combat_result, fleet, defending_fleet, target_planet)
                attacker_user = FleetArrivalService._get_fleet_user(fleet)
                defender_user = FleetArrivalService._get_fleet_user(defending_fleet)
                if is_pirate_user(attacker_user) and is_pirate_user(defender_user):
                    db.session.add(
                        TickLog(
                            tick_number=0,
                            planet_id=int(target_planet.id),
                            fleet_id=int(fleet.id),
                            event_type="pirate_skirmish_resolved",
                            event_description=(
                                f"Pirate skirmish resolved at {target_planet.x}:{target_planet.y}:{target_planet.z} "
                                f"winner={combat_result.get('winner', 'unknown')}"
                            ),
                        )
                    )
            else:
                # Attack on undefended planet.
                #
                # For pirate raids (attacker == pirates NPC), we still want a CombatReport and
                # debris via ship losses (MVP spec). If the defender has no stationed fleet,
                # synthesize a minimal defending fleet from the planet's legacy ship columns.
                attacker_username = getattr(getattr(fleet, "owner", None), "username", None)
                is_pirate_attacker = is_pirate_username(attacker_username)

                if is_pirate_attacker:
                    print(f"DEBUG: Pirate raid against undefended planet {target_planet.id}; creating defender inventory fleet")
                    defending_fleet = (
                        Fleet.query.filter_by(
                            user_id=target_planet.user_id,
                            start_planet_id=target_planet.id,
                            status="stationed",
                            mission="inventory",
                        )
                        .order_by(Fleet.id.asc())
                        .first()
                    )
                    if not defending_fleet:
                        defending_fleet = Fleet(
                            user_id=target_planet.user_id,
                            mission="inventory",
                            status="stationed",
                            start_planet_id=target_planet.id,
                            target_planet_id=target_planet.id,
                            departure_time=arrival_processed_at,
                            arrival_time=arrival_processed_at,
                            eta=0,
                        )
                        for ship_col in (
                            "small_cargo",
                            "large_cargo",
                            "light_fighter",
                            "heavy_fighter",
                            "cruiser",
                            "battleship",
                            "colony_ship",
                        ):
                            amount = int(getattr(target_planet, ship_col, 0) or 0)
                            if amount > 0:
                                setattr(defending_fleet, ship_col, amount)
                                setattr(target_planet, ship_col, 0)
                        db.session.add(defending_fleet)
                        db.session.flush()

                    from backend.services.combat_engine import CombatEngine
                    combat_result = CombatEngine.calculate_battle(fleet, defending_fleet)
                    CombatEngine.process_combat_result(combat_result, fleet, defending_fleet, target_planet)
                else:
                    print(f"DEBUG: Attacking undefended planet {target_planet.id}")
                    from backend.services.combat_engine import CombatEngine
                    combat_result = CombatEngine.calculate_planet_attack(fleet, target_planet)
                    CombatEngine.process_planet_attack_result(combat_result, fleet, target_planet)

            # After combat, fleet returns home.
            if fleet.departure_time and fleet.arrival_time:
                travel_time_seconds = max(0, (fleet.arrival_time - fleet.departure_time).total_seconds())
            else:
                travel_time_seconds = 3600

            FleetStateMachine.set_returning(
                fleet,
                now=arrival_processed_at,
                return_time_seconds=travel_time_seconds,
            )

            db.session.commit()
            print(f"SUCCESS: Attack mission completed for fleet {fleet.id}")

        except Exception as e:
            print(f"ERROR: Failed to process attack for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_espionage(fleet):
        """Handle espionage fleet arrival: create a spy report, then return to origin."""
        print(f"DEBUG: Processing espionage for fleet {fleet.id}")
        arrival_processed_at = datetime.utcnow()

        try:
            target_planet = Planet.query.get(fleet.target_planet_id)
            if not target_planet:
                FleetArrivalService._return_fleet_to_stationed(fleet)
                db.session.commit()
                return

            intel = {
                "planet": {
                    "id": target_planet.id,
                    "name": target_planet.name,
                    "coordinates": f"{target_planet.x}:{target_planet.y}:{target_planet.z}",
                },
                "owner": {
                    "user_id": target_planet.user_id,
                    "username": target_planet.owner.username if target_planet.owner else None,
                },
                "resources": {
                    "metal": target_planet.metal,
                    "crystal": target_planet.crystal,
                    "deuterium": target_planet.deuterium,
                },
                "structures": {
                    "metal_mine": target_planet.metal_mine,
                    "crystal_mine": target_planet.crystal_mine,
                    "deuterium_synthesizer": target_planet.deuterium_synthesizer,
                    "solar_plant": target_planet.solar_plant,
                    "fusion_reactor": target_planet.fusion_reactor,
                    "research_lab": target_planet.research_lab,
                },
                "ships": {
                    "small_cargo": getattr(target_planet, "small_cargo", 0),
                    "large_cargo": getattr(target_planet, "large_cargo", 0),
                    "light_fighter": getattr(target_planet, "light_fighter", 0),
                    "heavy_fighter": getattr(target_planet, "heavy_fighter", 0),
                    "cruiser": getattr(target_planet, "cruiser", 0),
                    "battleship": getattr(target_planet, "battleship", 0),
                    "colony_ship": getattr(target_planet, "colony_ship", 0),
                    "recycler": getattr(target_planet, "recycler", 0),
                    "espionage_probe": getattr(target_planet, "espionage_probe", 0),
                    "bomber": getattr(target_planet, "bomber", 0),
                    "destroyer": getattr(target_planet, "destroyer", 0),
                    "deathstar": getattr(target_planet, "deathstar", 0),
                    "battlecruiser": getattr(target_planet, "battlecruiser", 0),
                },
            }

            db.session.add(EspionageReport(
                user_id=fleet.user_id,
                target_planet_id=target_planet.id,
                target_user_id=target_planet.user_id,
                fleet_id=fleet.id,
                timestamp=arrival_processed_at,
                success=True,
                intel=json.dumps(intel),
            ))

            db.session.add(TickLog(
                tick_number=0,
                planet_id=fleet.start_planet_id,
                fleet_id=fleet.id,
                event_type="espionage_report",
                event_description=f"Espionage report created for planet {target_planet.id}",
            ))

            if fleet.departure_time and fleet.arrival_time:
                return_time = max(0, (fleet.arrival_time - fleet.departure_time).total_seconds())
            else:
                return_time = 3600

            FleetStateMachine.set_returning(
                fleet,
                now=arrival_processed_at,
                return_time_seconds=return_time,
            )

            db.session.commit()
        except Exception as e:
            print(f"ERROR: Failed to process espionage for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _process_recycle(fleet):
        """Handle recycle fleet arrival"""
        print(f"DEBUG: Processing recycle for fleet {fleet.id}")

        try:
            arrival_processed_at = datetime.utcnow()

            # Get target planet
            target_planet = Planet.query.get(fleet.target_planet_id)
            if not target_planet:
                print(f"ERROR: Target planet {fleet.target_planet_id} not found")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Find debris field at planet
            debris_field = DebrisField.query.filter_by(planet_id=target_planet.id).first()
            if not debris_field:
                print(f"WARNING: No debris field found at planet {target_planet.id}")
                FleetArrivalService._return_fleet_to_stationed(fleet)
                return

            # Calculate recycler capacity
            recycler_capacity = int(getattr(fleet, "recycler", 0) or 0) * 1000  # Assume 1000 cargo capacity per recycler

            # Determine recycling focus (stored as target_coordinates = "recycle:<focus>")
            focus = None
            raw_focus = getattr(fleet, "target_coordinates", None)
            if isinstance(raw_focus, str) and raw_focus.startswith("recycle:"):
                focus = raw_focus.split(":", 1)[1].strip().lower() or None
            if focus not in (None, "proportional", "metal", "crystal", "deuterium"):
                focus = None

            available_metal = int(debris_field.metal or 0)
            available_crystal = int(debris_field.crystal or 0)
            available_deuterium = int(debris_field.deuterium or 0)

            collected_metal = 0
            collected_crystal = 0
            collected_deuterium = 0

            if recycler_capacity <= 0:
                raise RuntimeError("Fleet has no recycler capacity")

            if focus in ("metal", "crystal", "deuterium"):
                if focus == "metal":
                    collected_metal = min(available_metal, recycler_capacity)
                elif focus == "crystal":
                    collected_crystal = min(available_crystal, recycler_capacity)
                else:
                    collected_deuterium = min(available_deuterium, recycler_capacity)
            else:
                # Proportional split across resources present (capacity-constrained).
                total_available = available_metal + available_crystal + available_deuterium
                if total_available <= 0:
                    collected_metal = collected_crystal = collected_deuterium = 0
                else:
                    # First-pass proportional allocation with flooring.
                    def alloc(amount):
                        return int((recycler_capacity * amount) // total_available) if amount > 0 else 0

                    collected_metal = min(available_metal, alloc(available_metal))
                    collected_crystal = min(available_crystal, alloc(available_crystal))
                    collected_deuterium = min(available_deuterium, alloc(available_deuterium))

                    used = collected_metal + collected_crystal + collected_deuterium
                    remaining = max(0, recycler_capacity - used)

                    # Distribute remaining capacity to resources that still have debris left.
                    for key in ("metal", "crystal", "deuterium"):
                        if remaining <= 0:
                            break
                        if key == "metal":
                            room = max(0, available_metal - collected_metal)
                            add = min(room, remaining)
                            collected_metal += add
                            remaining -= add
                        elif key == "crystal":
                            room = max(0, available_crystal - collected_crystal)
                            add = min(room, remaining)
                            collected_crystal += add
                            remaining -= add
                        else:
                            room = max(0, available_deuterium - collected_deuterium)
                            add = min(room, remaining)
                            collected_deuterium += add
                            remaining -= add

            # Update debris field
            debris_field.metal -= collected_metal
            debris_field.crystal -= collected_crystal
            debris_field.deuterium -= collected_deuterium

            # Load collected resources into fleet cargo. Cargo is delivered when the fleet returns.
            fleet.cargo_metal = int(getattr(fleet, "cargo_metal", 0) or 0) + int(collected_metal or 0)
            fleet.cargo_crystal = int(getattr(fleet, "cargo_crystal", 0) or 0) + int(collected_crystal or 0)
            fleet.cargo_deuterium = int(getattr(fleet, "cargo_deuterium", 0) or 0) + int(collected_deuterium or 0)

            print(f"SUCCESS: Collected {collected_metal} metal, {collected_crystal} crystal, {collected_deuterium} deuterium")

            # Create tick log entry
            tick_log = TickLog(
                tick_number=0,
                planet_id=target_planet.id,
                fleet_id=fleet.id,
                event_type='recycle',
                event_description=f'Fleet {fleet.id} collected {collected_metal}M {collected_crystal}C {collected_deuterium}D from debris field'
            )
            db.session.add(tick_log)

            # Commander XP (idempotent per TickLog row if possible).
            try:
                db.session.flush()
                CommanderXPService.award_xp(
                    user_id=int(fleet.user_id),
                    xp=int(xp_from_resources(collected_metal, collected_crystal, collected_deuterium)),
                    source_type="recycle",
                    source_id=str(getattr(tick_log, "id", None) or f"fleet:{fleet.id}:planet:{target_planet.id}"),
                )
            except Exception:
                pass

            # Clean up empty debris field
            if debris_field.metal <= 0 and debris_field.crystal <= 0 and debris_field.deuterium <= 0:
                db.session.delete(debris_field)

            # Set fleet to return to origin, then deliver cargo on return arrival.
            if fleet.departure_time and fleet.arrival_time:
                return_time = max(0, (fleet.arrival_time - fleet.departure_time).total_seconds())
            else:
                return_time = 3600
            FleetStateMachine.set_returning(
                fleet,
                now=arrival_processed_at,
                return_time_seconds=return_time,
            )
            db.session.commit()

            print(f"SUCCESS: Recycle mission completed for fleet {fleet.id}")

        except Exception as e:
            print(f"ERROR: Failed to process recycle for fleet {fleet.id}: {str(e)}")
            db.session.rollback()
            FleetArrivalService._return_fleet_to_stationed(fleet)

    @staticmethod
    def _create_exploration_planets_fallback(target_x, target_y, target_z, user_id):
        """Fallback planet creation when generate_exploration_planets fails"""
        print(f"DEBUG: Using fallback planet creation for system {target_x}:{target_y}:{target_z}")

        import random

        discovered_planets = []

        # Check if system already has planets
        existing_planets = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).all()
        if existing_planets:
            print(f"DEBUG: System already has {len(existing_planets)} planets")
            return existing_planets

        # Generate 1-3 planets per system
        num_planets = random.randint(1, 3)
        print(f"DEBUG: Creating {num_planets} planets in system")

        for i in range(num_planets):
            # Offset coordinates slightly for multiple planets in same system
            planet_x = target_x + random.randint(-5, 5)
            planet_y = target_y + random.randint(-5, 5)
            # Keep exploration on the same Z slice to match the 2D GalaxyMap and reduce wasted depth.
            planet_z = target_z

            # Ensure coordinates are unique
            while Planet.query.filter_by(x=planet_x, y=planet_y, z=planet_z).first():
                planet_x = target_x + random.randint(-5, 5)
                planet_y = target_y + random.randint(-5, 5)
                planet_z = target_z

            # Generate planet properties
            planet_names = [
                "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
                "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
                "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
            ]

            planet_name = f"{random.choice(planet_names)} {target_x}:{target_y}:{target_z}"

            # Create planet with random starting resources
            planet = Planet(
                name=planet_name,
                x=planet_x,
                y=planet_y,
                z=planet_z,
                user_id=None,  # Unowned
                metal=random.randint(100, 1000),
                crystal=random.randint(50, 500),
                deuterium=random.randint(0, 200),
                metal_mine=0,      # No structures initially
                crystal_mine=0,
                deuterium_synthesizer=0,
                solar_plant=0,
                fusion_reactor=0
            )

            db.session.add(planet)
            db.session.flush()  # Get planet ID for trait generation

            # Generate planet traits
            try:
                from backend.services.planet_traits import PlanetTraitService
                traits = PlanetTraitService.generate_planet_traits(planet)
                db.session.add_all(traits)
                print(f"DEBUG: Generated {len(traits)} traits for planet {planet.id}")
            except Exception as trait_error:
                print(f"WARNING: Failed to generate traits for planet {planet.id}: {str(trait_error)}")

            discovered_planets.append(planet)
            print(f"DEBUG: Created planet {planet.id} at {planet_x}:{planet_y}:{planet_z}")

        db.session.commit()
        print(f"DEBUG: Committed {len(discovered_planets)} planets to database")
        return discovered_planets

    @staticmethod
    def _return_fleet_to_stationed(fleet):
        """Return a fleet to stationed status"""
        print(f"DEBUG: Returning fleet {fleet.id} to stationed status")
        FleetStateMachine.set_stationed(fleet)
