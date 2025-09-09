"""
Fleet Travel Guard Service

This service provides comprehensive validation and correction of fleet travel states.
It runs every tick to ensure fleets don't get stuck in invalid states and automatically
corrects common issues like status/ETA mismatches.

Key Features:
- Automatic detection of stuck fleets
- State validation and correction
- Comprehensive logging for debugging
- Integration with tick system
- Administrative cleanup tools
"""

from datetime import datetime, timedelta
from backend.database import db
from backend.models import Fleet, Planet, User, TickLog
import logging

# Set up logger
logger = logging.getLogger(__name__)

class FleetTravelGuard:
    """Comprehensive fleet travel state validation and correction system"""

    @staticmethod
    def validate_and_correct_fleet_states():
        """Main validation function called every tick"""
        logger.info("Running fleet travel guard validation")

        corrections_made = 0
        current_time = datetime.utcnow()

        # Get all fleets that might need correction
        problematic_fleets = Fleet.query.filter(
            # Fleets that have arrived but wrong status
            ((Fleet.arrival_time <= current_time) &
             (Fleet.status.in_(['traveling', 'returning']) |
              Fleet.status.like('exploring:%') |
              Fleet.status.like('colonizing:%'))) |
            # Fleets with invalid status combinations
            ((Fleet.status == 'stationed') & (Fleet.arrival_time.isnot(None))) |
            # Fleets with negative ETA
            (Fleet.eta < 0)
        ).all()

        logger.info(f"Found {len(problematic_fleets)} fleets requiring validation")

        for fleet in problematic_fleets:
            if FleetTravelGuard._correct_fleet_state(fleet, current_time):
                corrections_made += 1

        if corrections_made > 0:
            db.session.commit()
            logger.info(f"Fleet travel guard corrected {corrections_made} fleets")

        return corrections_made

    @staticmethod
    def _correct_fleet_state(fleet, current_time):
        """Correct a single fleet's state based on current conditions"""
        corrected = False

        # Case 1: Fleet has arrived but still shows traveling
        if (fleet.arrival_time and fleet.arrival_time <= current_time and
            fleet.status in ['traveling', 'returning']):

            if fleet.status == 'returning':
                # Returning fleet has arrived home
                fleet.status = 'stationed'
                fleet.mission = 'stationed'
                fleet.target_planet_id = fleet.start_planet_id
                fleet.arrival_time = None
                fleet.eta = 0
                logger.info(f"Corrected returning fleet {fleet.id} to stationed at planet {fleet.start_planet_id}")

            elif fleet.status == 'traveling':
                # Traveling fleet has arrived at destination
                fleet.status = 'stationed'
                fleet.start_planet_id = fleet.target_planet_id  # Update home base
                fleet.arrival_time = None
                fleet.eta = 0
                logger.info(f"Corrected traveling fleet {fleet.id} to stationed at planet {fleet.target_planet_id}")

            corrected = True

        # Case 2: Exploration fleet has arrived at target
        elif (fleet.arrival_time and fleet.arrival_time <= current_time and
              fleet.status.startswith('exploring:')):

            # Set fleet to return to origin
            fleet.status = 'returning'
            fleet.mission = 'return'

            # Calculate return journey time (same as outbound)
            if fleet.departure_time and fleet.arrival_time:
                travel_time = fleet.arrival_time - fleet.departure_time
                fleet.arrival_time = current_time + travel_time
                fleet.eta = int(travel_time.total_seconds())
                logger.info(f"Exploration fleet {fleet.id} returning home, ETA: {fleet.eta} seconds")
            else:
                # Fallback: 1 hour return
                fleet.arrival_time = current_time + timedelta(hours=1)
                fleet.eta = 3600
                logger.warning(f"Exploration fleet {fleet.id} using fallback return time (1 hour)")

            corrected = True

        # Case 3: Colonization fleet has arrived
        elif (fleet.arrival_time and fleet.arrival_time <= current_time and
              fleet.status.startswith('colonizing:')):

            # Check if target coordinates are still available
            coords = fleet.status.split(':')[1:]
            if len(coords) >= 3:
                try:
                    target_x, target_y, target_z = map(int, coords)
                    existing_planet = Planet.query.filter_by(
                        x=target_x, y=target_y, z=target_z
                    ).first()

                    if existing_planet and existing_planet.user_id:
                        # Coordinates occupied, return fleet
                        fleet.status = 'returning'
                        fleet.mission = 'return'
                        if fleet.departure_time and fleet.arrival_time:
                            travel_time = fleet.arrival_time - fleet.departure_time
                            fleet.arrival_time = current_time + travel_time
                            fleet.eta = int(travel_time.total_seconds())
                        logger.warning(f"Colonization failed for fleet {fleet.id}, coordinates {target_x}:{target_y}:{target_z} occupied")
                    else:
                        # Coordinates available, set to stationed for processing
                        fleet.status = 'stationed'
                        fleet.mission = 'stationed'
                        fleet.arrival_time = None
                        fleet.eta = 0
                        logger.info(f"Colonization fleet {fleet.id} ready for processing at {target_x}:{target_y}:{target_z}")

                    corrected = True

                except ValueError as e:
                    logger.error(f"Invalid coordinates in fleet {fleet.id} status: {fleet.status} - {e}")
                    # Return fleet to stationed to prevent infinite loops
                    FleetTravelGuard._return_fleet_to_stationed(fleet)
                    corrected = True

        # Case 4: Stationed fleet with arrival time (shouldn't happen)
        elif fleet.status == 'stationed' and fleet.arrival_time:
            fleet.arrival_time = None
            fleet.eta = 0
            logger.warning(f"Cleared arrival time for stationed fleet {fleet.id}")
            corrected = True

        # Case 5: Negative ETA (shouldn't happen)
        elif fleet.eta < 0:
            fleet.eta = 0
            logger.warning(f"Corrected negative ETA for fleet {fleet.id}")
            corrected = True

        # Case 6: Fleet with invalid status format
        elif ':' in fleet.status and not (
            fleet.status.startswith(('exploring:', 'colonizing:')) or
            fleet.status in ['stationed', 'traveling', 'returning']
        ):
            logger.error(f"Fleet {fleet.id} has invalid status: {fleet.status}")
            FleetTravelGuard._return_fleet_to_stationed(fleet)
            corrected = True

        return corrected

    @staticmethod
    def _return_fleet_to_stationed(fleet):
        """Safely return a fleet to stationed status"""
        logger.info(f"Returning fleet {fleet.id} to stationed status")
        fleet.status = 'stationed'
        fleet.mission = 'stationed'
        fleet.arrival_time = None
        fleet.eta = 0

    @staticmethod
    def force_cleanup_stuck_fleets(user_id=None, max_age_hours=24):
        """Administrative function to force cleanup stuck fleets"""
        logger.info("Running forced cleanup of stuck fleets")

        query = Fleet.query

        # Filter by user if specified
        if user_id:
            query = query.filter_by(user_id=user_id)

        # Only clean fleets that have been stuck for more than max_age_hours
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stuck_fleets = query.filter(
            Fleet.arrival_time <= cutoff_time,
            Fleet.status.notin_(['stationed'])
        ).all()

        cleaned_count = 0
        for fleet in stuck_fleets:
            logger.warning(f"Force cleaning stuck fleet {fleet.id} (status: {fleet.status}, ETA: {fleet.eta})")
            FleetTravelGuard._return_fleet_to_stationed(fleet)
            cleaned_count += 1

        if cleaned_count > 0:
            db.session.commit()
            logger.info(f"Force cleaned {cleaned_count} stuck fleets")

        return cleaned_count

    @staticmethod
    def get_fleet_health_report():
        """Generate comprehensive fleet health report"""
        total_fleets = Fleet.query.count()

        # Count various problematic states
        stuck_fleets = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.notin_(['stationed'])
        ).count()

        invalid_states = Fleet.query.filter(
            (Fleet.status == 'stationed') & (Fleet.arrival_time.isnot(None)) |
            (Fleet.eta < 0)
        ).count()

        traveling_fleets = Fleet.query.filter(
            Fleet.status.in_(['traveling', 'returning'])
        ).count()

        exploration_fleets = Fleet.query.filter(
            Fleet.status.like('exploring:%') |
            Fleet.status.like('colonizing:%')
        ).count()

        # Calculate health percentage
        healthy_fleets = total_fleets - stuck_fleets - invalid_states
        health_percentage = (healthy_fleets / total_fleets * 100) if total_fleets > 0 else 100

        return {
            'total_fleets': total_fleets,
            'healthy_fleets': healthy_fleets,
            'stuck_fleets': stuck_fleets,
            'invalid_states': invalid_states,
            'traveling_fleets': traveling_fleets,
            'exploration_fleets': exploration_fleets,
            'health_percentage': round(health_percentage, 2),
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def validate_fleet_coordinates():
        """Validate that fleet coordinates are consistent with their status"""
        logger.info("Validating fleet coordinates")

        issues_found = 0

        # Check exploration fleets have valid coordinates
        exploration_fleets = Fleet.query.filter(
            Fleet.status.like('exploring:%') |
            Fleet.status.like('colonizing:%')
        ).all()

        for fleet in exploration_fleets:
            coords = fleet.status.split(':')[1:]
            if len(coords) < 3:
                logger.error(f"Fleet {fleet.id} has malformed coordinates in status: {fleet.status}")
                FleetTravelGuard._return_fleet_to_stationed(fleet)
                issues_found += 1
                continue

            try:
                x, y, z = map(int, coords)
                # Additional validation could be added here
            except ValueError:
                logger.error(f"Fleet {fleet.id} has invalid coordinates: {coords}")
                FleetTravelGuard._return_fleet_to_stationed(fleet)
                issues_found += 1

        if issues_found > 0:
            db.session.commit()
            logger.info(f"Fixed {issues_found} fleets with coordinate issues")

        return issues_found
