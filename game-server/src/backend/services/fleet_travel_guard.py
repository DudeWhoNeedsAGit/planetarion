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
from backend.services.fleet_state_machine import FleetStateMachine
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

        # Only correct clearly invalid state combinations here.
        #
        # Mission completion (arrivals for traveling/returning/exploring/colonizing) is handled by
        # FleetArrivalService, and we must not "station" fleets early or clear arrival times, as that
        # prevents mission handlers from running and can violate DB constraints.
        # Note: Keep this query narrow (only clearly invalid states) to avoid churn that would
        # cause UI flicker or non-deterministic tests.
        problematic_fleets = Fleet.query.filter(
            (Fleet.eta < 0) |
            ((Fleet.status == 'stationed') & (
                (Fleet.eta != 0) |
                (Fleet.arrival_time > current_time) |
                (Fleet.departure_time.is_(None)) |
                (Fleet.arrival_time.is_(None))
            )) |
            # Some historical data can leave fleets "stationed" but with a non-stationary mission.
            ((Fleet.status == 'stationed') & (Fleet.mission.notin_(['stationed', 'inventory'])))
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

        # Case 1: Negative ETA (shouldn't happen)
        if fleet.eta < 0:
            fleet.eta = 0
            logger.warning(f"Corrected negative ETA for fleet {fleet.id}")
            corrected = True

        if fleet.status == 'stationed':
            # Inventory fleets are a special “dock” concept; keep their mission stable.
            if getattr(fleet, "mission", None) == "inventory":
                if fleet.eta != 0:
                    fleet.eta = 0
                    logger.warning(f"Cleared ETA for inventory fleet {fleet.id}")
                    corrected = True
                if fleet.arrival_time is None or fleet.arrival_time > current_time:
                    fleet.arrival_time = current_time
                    corrected = True
                if fleet.departure_time is None:
                    fleet.departure_time = current_time
                    corrected = True
                if getattr(fleet, "start_planet_id", None) and fleet.target_planet_id != fleet.start_planet_id:
                    fleet.target_planet_id = fleet.start_planet_id
                    corrected = True
                return corrected

            # Historical drift: some fleets are marked stationed but retain a travel mission.
            # Normalize them to a stationary representation so the UI doesn't show countdowns
            # or "Arrived (pending tick)" for stationary fleets.
            if fleet.mission == "defend":
                # Best-effort: treat a stationary defend fleet as "defending".
                fleet.status = "defending"
                fleet.eta = 0
                fleet.departure_time = current_time
                fleet.arrival_time = current_time
                if getattr(fleet, "start_planet_id", None):
                    fleet.target_planet_id = fleet.start_planet_id
                logger.warning(f"Normalized defend fleet {fleet.id} to defending status")
                return True

            if fleet.mission not in ("stationed", "inventory"):
                logger.warning(
                    f"Normalizing stationed fleet {fleet.id} with mission={fleet.mission} to mission=stationed"
                )
                FleetStateMachine.set_stationed(fleet, now=current_time)
                corrected = True
            else:
                # Stationed fleet with inconsistent timestamps/eta/target.
                if fleet.eta != 0:
                    fleet.eta = 0
                    corrected = True
                if fleet.arrival_time is None or fleet.arrival_time > current_time:
                    fleet.arrival_time = current_time
                    corrected = True
                if fleet.departure_time is None:
                    fleet.departure_time = current_time
                    corrected = True
                if getattr(fleet, "start_planet_id", None) and fleet.target_planet_id != fleet.start_planet_id:
                    fleet.target_planet_id = fleet.start_planet_id
                    corrected = True

        return corrected

    @staticmethod
    def _return_fleet_to_stationed(fleet):
        """Safely return a fleet to stationed status"""
        logger.info(f"Returning fleet {fleet.id} to stationed status")
        fleet.status = 'stationed'
        fleet.mission = 'stationed'
        fleet.arrival_time = datetime.utcnow()
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
