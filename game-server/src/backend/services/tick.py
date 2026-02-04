from datetime import datetime, timedelta, timezone
import inspect
from backend.database import db
from backend.models import Planet, Fleet, TickLog, User, Research
from flask import current_app
import math
from backend.config import get_planet_storage_caps
import json

RESPAWN_PROTECTION_MINUTES_DEFAULT = 10

def run_tick():
    """Main tick function that runs every 5 seconds"""
    tick_number = get_next_tick_number()
    tick_start_time = datetime.utcnow()

    # RUN FLEET TRAVEL GUARD FIRST - Validate and correct fleet states
    from .fleet_travel_guard import FleetTravelGuard
    guard_corrections = FleetTravelGuard.validate_and_correct_fleet_states()

    # Execute normal tick operations
    resource_changes = process_resource_generation()
    research_changes = process_research_points()
    # Fleet arrivals/missions are processed by FleetArrivalService. We intentionally
    # avoid mutating fleet statuses here to prevent prematurely "stationing" fleets
    # before mission handlers run.
    fleet_updates = []

    # Process arrived fleets using the FleetArrivalService
    from .fleet_arrival import FleetArrivalService
    FleetArrivalService.process_arrived_fleets()

    # Process research completion (tick-driven).
    process_research_queue(tick_start_time)

    # Process player elimination/respawn lifecycle (Phase 7).
    # We intentionally separate "mark eliminated" from "respawn" so the respawn happens
    # on the next tick (within 1 tick), matching the spec and keeping capture assertions stable.
    process_player_elimination_and_respawn(tick_start_time)

    # Log tick completion with guard statistics
    tick_end_time = datetime.utcnow()
    log_tick(tick_number, tick_start_time, resource_changes, fleet_updates, guard_corrections)

    print(f"Tick {tick_number} completed at {tick_end_time} (Guard: {guard_corrections} corrections)")

    return resource_changes  # Return changes for manual tick endpoint


def process_player_elimination_and_respawn(tick_start_time: datetime) -> None:
    """Mark players eliminated (0 planets) and respawn them on the next tick.

    Rules (MVP):
    - A player is eliminated when they have 0 planets.
    - On the *next* tick after elimination, they receive:
      - a new home planet (is_home_planet=True)
      - starter resources
      - a stationed starter fleet
      - a protection window (attack blocked; UI TBD)
    """

    now = datetime.utcnow()

    # Mark newly eliminated users.
    # Exclude pirates NPC user.
    users = User.query.all()
    for user in users:
        if user.username == "pirates":
            continue
        planet_count = Planet.query.filter_by(user_id=user.id).count()
        if planet_count == 0 and user.eliminated_at is None:
            user.eliminated_at = now

    db.session.commit()

    raw_protection = current_app.config.get("RESPAWN_PROTECTION_MINUTES", RESPAWN_PROTECTION_MINUTES_DEFAULT)
    # Some unit tests patch current_app with a MagicMock; guard against non-ints/awaitables.
    if inspect.isawaitable(raw_protection):
        raw_protection = None
    try:
        protection_minutes = int(raw_protection) if raw_protection is not None else RESPAWN_PROTECTION_MINUTES_DEFAULT
    except (TypeError, ValueError):
        protection_minutes = RESPAWN_PROTECTION_MINUTES_DEFAULT
    protection_until = now + timedelta(minutes=max(0, protection_minutes))

    # Respawn users that have been eliminated on a *previous* tick.
    for user in users:
        if user.username == "pirates":
            continue
        planet_count = Planet.query.filter_by(user_id=user.id).count()
        if planet_count != 0:
            continue
        if user.eliminated_at is None:
            continue
        if user.respawned_at is not None and (user.eliminated_at <= user.respawned_at):
            continue
        # Ensure respawn happens on the tick *after* elimination.
        if not (user.eliminated_at < tick_start_time):
            continue

        user.respawn_count = int(user.respawn_count or 0) + 1
        user.respawned_at = now
        user.protection_until = protection_until

        home_planet = _create_respawn_home_planet(user, now)
        _create_respawn_starter_fleet(user, home_planet, now)

    db.session.commit()


def _create_respawn_home_planet(user: User, now: datetime) -> Planet:
    """Create a deterministic respawn home planet for a user (SQLite-friendly, test-stable)."""
    base_x = 2000 + (user.id * 17) + (int(user.respawn_count or 1) * 3)
    base_y = 2000 + (user.id * 11) + (int(user.respawn_count or 1) * 7)
    base_z = 1000

    x, y, z = base_x, base_y, base_z
    # Ensure uniqueness (simple deterministic probing).
    for i in range(50):
        if Planet.query.filter_by(x=x, y=y, z=z).first() is None:
            break
        x += 1
        y += 1
        z += 0

    planet = Planet(
        name=f"{user.username.title()} Respawn {user.respawn_count}",
        x=x,
        y=y,
        z=z,
        user_id=user.id,
        is_home_planet=True,
        colonized_at=now,
        metal=150_000,
        crystal=100_000,
        deuterium=50_000,
        metal_mine=8,
        crystal_mine=6,
        deuterium_synthesizer=4,
        solar_plant=12,
    )
    db.session.add(planet)
    db.session.flush()
    return planet


def _create_respawn_starter_fleet(user: User, home_planet: Planet, now: datetime) -> Fleet:
    fleet = Fleet(
        user_id=user.id,
        mission="stationed",
        status="stationed",
        start_planet_id=home_planet.id,
        target_planet_id=home_planet.id,
        departure_time=now,
        arrival_time=now,
        eta=0,
        small_cargo=5,
        large_cargo=2,
        light_fighter=20,
        heavy_fighter=10,
        recycler=2,
        espionage_probe=2,
        colony_ship=1,
    )
    db.session.add(fleet)
    db.session.flush()
    return fleet

def get_next_tick_number():
    """Get the next tick number"""
    last_tick = TickLog.query.order_by(TickLog.tick_number.desc()).first()
    return (last_tick.tick_number + 1) if last_tick else 1

def process_resource_generation():
    """Process resource generation for all planets"""
    planets = Planet.query.all()
    changes = []

    for planet in planets:
        before_metal = planet.metal
        before_crystal = planet.crystal
        before_deuterium = planet.deuterium

        # Calculate production rates with planet trait bonuses
        metal_rate = calculate_production_rate(planet.metal_mine, 'metal', planet)
        crystal_rate = calculate_production_rate(planet.crystal_mine, 'crystal', planet)
        deuterium_rate = calculate_production_rate(planet.deuterium_synthesizer, 'deuterium', planet)

        # Calculate energy production and consumption
        energy_production = planet.solar_plant * 20 + planet.fusion_reactor * 50
        energy_consumption = (planet.metal_mine * 10 +
                            planet.crystal_mine * 10 +
                            planet.deuterium_synthesizer * 20 +
                            (planet.research_lab or 0) * 15)

        # Apply energy efficiency
        energy_ratio = min(1.0, energy_production / energy_consumption) if energy_consumption > 0 else 1.0

        # Calculate actual production for this tick (5 seconds = 1/72 hour for fast testing)
        # Use max(1, ...) to ensure at least 1 resource per tick for active mines
        tick_metal = max(1, int(metal_rate * energy_ratio / 72)) if planet.metal_mine > 0 else 0
        tick_crystal = max(1, int(crystal_rate * energy_ratio / 72)) if planet.crystal_mine > 0 else 0
        tick_deuterium = max(1, int(deuterium_rate * energy_ratio / 72)) if planet.deuterium_synthesizer > 0 else 0

        # Update planet resources with storage caps (do not reduce existing resources above cap).
        caps = get_planet_storage_caps(planet)
        if planet.metal < caps["metal"]:
            planet.metal = min(planet.metal + tick_metal, caps["metal"])
        if planet.crystal < caps["crystal"]:
            planet.crystal = min(planet.crystal + tick_crystal, caps["crystal"])
        if planet.deuterium < caps["deuterium"]:
            planet.deuterium = min(planet.deuterium + tick_deuterium, caps["deuterium"])

        changes.append({
            'planet_id': planet.id,
            'metal_change': planet.metal - before_metal,
            'crystal_change': planet.crystal - before_crystal,
            'deuterium_change': planet.deuterium - before_deuterium
        })

    db.session.commit()
    return changes


def process_research_points():
    """Accrue research points for all users based on research labs (tick-based)."""
    users = User.query.all()
    raw_per_hour_per_level = current_app.config.get("RESEARCH_RP_PER_HOUR_PER_LAB_LEVEL", 10)
    if inspect.isawaitable(raw_per_hour_per_level):
        raw_per_hour_per_level = None
    try:
        per_hour_per_level = int(raw_per_hour_per_level) if raw_per_hour_per_level is not None else 10
    except (TypeError, ValueError):
        per_hour_per_level = 10
    changes = []

    for user in users:
        if user.username == "pirates":
            continue

        research = Research.query.filter_by(user_id=user.id).first()
        if not research:
            research = Research(user_id=user.id, research_points=0)
            db.session.add(research)
            db.session.flush()

        planets = Planet.query.filter_by(user_id=user.id).all()
        total_per_hour = 0.0
        for planet in planets:
            lvl = int(getattr(planet, "research_lab", 0) or 0)
            if lvl <= 0:
                continue

            energy_production = (planet.solar_plant or 0) * 20 + (planet.fusion_reactor or 0) * 50
            energy_consumption = (
                (planet.metal_mine or 0) * 10
                + (planet.crystal_mine or 0) * 10
                + (planet.deuterium_synthesizer or 0) * 20
                + (getattr(planet, "research_lab", 0) or 0) * 15
            )
            energy_ratio = min(1.0, energy_production / energy_consumption) if energy_consumption > 0 else 1.0
            total_per_hour += float(lvl * per_hour_per_level) * float(energy_ratio)

        # Accelerated tick scale (resources use divisor=72). Keep fractional remainder so low rates still accrue.
        tick_rp = float(total_per_hour / 72.0)
        if tick_rp <= 0:
            continue

        fraction = float(getattr(research, "research_points_fraction", 0.0) or 0.0) + tick_rp
        gain = int(fraction)
        fraction = fraction - gain
        research.research_points_fraction = fraction

        if gain <= 0:
            continue

        before = int(research.research_points or 0)
        research.research_points = before + gain
        changes.append({"user_id": user.id, "rp_change": gain})

    db.session.commit()
    return changes


def process_research_queue(tick_start_time: datetime) -> None:
    """Complete research projects whose completes_at has passed (one per user).

    We treat `tick_start_time` as the authoritative "now" for tick processing.
    This keeps completion deterministic in tests and matches the game's discrete
    tick semantics (events resolve on the next tick at/after their scheduled time).
    """
    tick_now = tick_start_time  # naive UTC (run_tick uses datetime.utcnow()).
    users = User.query.all()
    for user in users:
        raw = getattr(user, "research_queue", None)
        if not raw:
            continue
        try:
            queue = json.loads(raw)
        except Exception:
            user.research_queue = None
            continue
        if not isinstance(queue, dict):
            user.research_queue = None
            continue

        key = queue.get("key")
        target_level = int(queue.get("target_level") or 0)
        completes_at_raw = queue.get("completes_at")
        completes_at = None
        if isinstance(completes_at_raw, str):
            s = completes_at_raw.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                completes_at = datetime.fromisoformat(s)
            except Exception:
                completes_at = None

        # Normalize to naive UTC for comparison against `tick_now`.
        if completes_at and completes_at.tzinfo is not None:
            completes_at = completes_at.astimezone(timezone.utc).replace(tzinfo=None)

        if not key or key not in ("colonization_tech", "astrophysics", "interstellar_communication"):
            user.research_queue = None
            continue
        if not completes_at:
            continue
        # Ensure completion happens only after the scheduled time.
        if completes_at > tick_now:
            continue

        research = Research.query.filter_by(user_id=user.id).first()
        if not research:
            research = Research(user_id=user.id, research_points=0)
            db.session.add(research)
            db.session.flush()

        current_level = int(getattr(research, key) or 0)
        if target_level != current_level + 1:
            # Guard against corrupted queue or double-apply; normalize to next level.
            target_level = current_level + 1

        setattr(research, key, target_level)
        user.research_queue = None

        home = Planet.query.filter_by(user_id=user.id).order_by(Planet.is_home_planet.desc(), Planet.id.asc()).first()
        db.session.add(
            TickLog(
                tick_number=0,
                planet_id=home.id if home else None,
                event_type="research_complete",
                event_description=f"Research completed: {key} → Level {target_level}",
                timestamp=datetime.utcnow(),
            )
        )

    db.session.commit()

def calculate_production_rate(level, resource_type, planet=None):
    """Calculate production rate for a building level with planet trait bonuses"""
    # Base production rates
    if resource_type == 'metal':
        base_rate = level * 30 * (1.1 ** level)
    elif resource_type == 'crystal':
        base_rate = level * 20 * (1.1 ** level)
    elif resource_type == 'deuterium':
        base_rate = level * 10 * (1.1 ** level)
    else:
        return 0

    # Apply planet trait bonuses if planet is provided
    if planet:
        bonus_multiplier = 1.0
        if resource_type == 'metal' and planet.base_metal_bonus:
            bonus_multiplier += planet.base_metal_bonus
        elif resource_type == 'crystal' and planet.base_crystal_bonus:
            bonus_multiplier += planet.base_crystal_bonus
        elif resource_type == 'deuterium' and planet.base_deuterium_bonus:
            bonus_multiplier += planet.base_deuterium_bonus

        base_rate *= bonus_multiplier

    return base_rate

def process_fleet_movements(current_time):
    """Process fleet movements and arrivals"""
    updates = []

    # Find fleets that have arrived
    arrived_fleets = Fleet.query.filter(
        Fleet.arrival_time <= current_time,
        Fleet.status.in_(['traveling', 'returning'])
    ).all()

    for fleet in arrived_fleets:
        if fleet.status == 'traveling':
            # Fleet has arrived at destination
            fleet.status = 'stationed'
            fleet.start_planet_id = fleet.target_planet_id  # Update start planet
            updates.append({
                'fleet_id': fleet.id,
                'event_type': 'arrival',
                'description': f'Fleet arrived at planet {fleet.target_planet_id}'
            })
        elif fleet.status == 'returning':
            # Fleet has returned to origin
            fleet.status = 'stationed'
            fleet.target_planet_id = fleet.start_planet_id
            updates.append({
                'fleet_id': fleet.id,
                'event_type': 'return',
                'description': f'Fleet returned to planet {fleet.start_planet_id}'
            })

    if arrived_fleets:
        db.session.commit()

    return updates

def log_tick(tick_number, timestamp, resource_changes, fleet_updates, guard_corrections=0):
    """Log tick events to database"""
    # Log resource changes
    for change in resource_changes:
        if change['metal_change'] > 0 or change['crystal_change'] > 0 or change['deuterium_change'] > 0:
            tick_log = TickLog(
                tick_number=tick_number,
                timestamp=timestamp,
                planet_id=change['planet_id'],
                metal_change=change['metal_change'],
                crystal_change=change['crystal_change'],
                deuterium_change=change['deuterium_change']
            )
            db.session.add(tick_log)

    # Log fleet events
    for update in fleet_updates:
        tick_log = TickLog(
            tick_number=tick_number,
            timestamp=timestamp,
            fleet_id=update['fleet_id'],
            event_type=update['event_type'],
            event_description=update['description']
        )
        db.session.add(tick_log)

    # Log guard corrections if any
    if guard_corrections > 0:
        tick_log = TickLog(
            tick_number=tick_number,
            timestamp=timestamp,
            event_type='guard_corrections',
            event_description=f'Fleet Travel Guard corrected {guard_corrections} fleet states'
        )
        db.session.add(tick_log)

    db.session.commit()

def generate_exploration_planets(x, y, z, user_id):
    """Generate planets when exploring a new system"""
    import random

    discovered_planets = []

    # Check if system already has planets
    existing_planets = Planet.query.filter_by(x=x, y=y, z=z).all()
    if existing_planets:
        return existing_planets  # Return existing planets

    # Generate 1-3 planets per system
    num_planets = random.randint(1, 3)

    for i in range(num_planets):
        # Offset coordinates slightly for multiple planets in same system.
        # Ensure at least one axis differs from the system center (so we never place a planet exactly at x:y:z).
        # Keep exploration on the same Z slice to match the 2D GalaxyMap and reduce wasted depth.
        planet_z = z
        while True:
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            if dx != 0 or dy != 0:
                planet_x = x + dx
                planet_y = y + dy
                break

        # Ensure coordinates are unique
        while Planet.query.filter_by(x=planet_x, y=planet_y, z=planet_z).first():
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            if dx == 0 and dy == 0:
                continue
            planet_x = x + dx
            planet_y = y + dy
            planet_z = z

        # Generate planet properties
        planet_names = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
            "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
            "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
        ]

        planet_name = f"{random.choice(planet_names)} {x}:{y}:{z}"

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
        from backend.services.planet_traits import PlanetTraitService
        traits = PlanetTraitService.generate_planet_traits(planet)
        db.session.add_all(traits)

        discovered_planets.append(planet)

    db.session.commit()
    return discovered_planets

def get_user_research_level(user_id):
    """Get user's colonization research level"""
    from backend.models import Research
    research = Research.query.filter_by(user_id=user_id).first()
    if research:
        return research.colonization_tech
    return 0  # Default research level

def generate_colony_name(user_id, x, y, z):
    """Generate a unique colony name"""
    from backend.models import Planet, User

    # Get user's existing colonies
    user_planets = Planet.query.filter_by(user_id=user_id).all()
    colony_number = len([p for p in user_planets if p.id != user_planets[0].id]) + 1

    # Get user info for name generation
    user = User.query.get(user_id)
    if user:
        return f"{user.username}'s Colony {colony_number}"
    else:
        return f"Colony {colony_number}"

def calculate_starting_resources(x, y, z):
    """Calculate starting resources for a new colony based on location and traits"""
    import random

    # Base starting resources
    base_metal = 500
    base_crystal = 250
    base_deuterium = 0

    # Distance from origin affects starting resources (closer = more resources)
    distance_from_origin = math.sqrt(x*x + y*y + z*z)
    distance_multiplier = max(0.5, 2.0 - (distance_from_origin / 1000))  # Closer planets get more resources

    # Add some randomness
    metal = int(base_metal * distance_multiplier * random.uniform(0.8, 1.2))
    crystal = int(base_crystal * distance_multiplier * random.uniform(0.8, 1.2))
    deuterium = int(base_deuterium + random.randint(0, 50))  # Small random deuterium

    return {
        'metal': metal,
        'crystal': crystal,
        'deuterium': deuterium
    }

def get_tick_statistics():
    """Get statistics about recent ticks"""
    recent_ticks = TickLog.query.order_by(TickLog.timestamp.desc()).limit(10).all()

    stats = {
        'total_ticks': TickLog.query.count(),
        'last_tick': None,
        'recent_activity': []
    }

    if recent_ticks:
        stats['last_tick'] = recent_ticks[0].timestamp.isoformat()

        for tick in recent_ticks[:5]:  # Show last 5 ticks
            stats['recent_activity'].append({
                'tick_number': tick.tick_number,
                'timestamp': tick.timestamp.isoformat(),
                'event_type': tick.event_type,
                'description': tick.event_description
            })

    return stats

def process_tick():
    """Public wrapper for run_tick() - for test compatibility"""
    return run_tick()

# Export public functions
__all__ = ['run_tick', 'process_tick', 'get_next_tick_number', 'get_tick_statistics']
