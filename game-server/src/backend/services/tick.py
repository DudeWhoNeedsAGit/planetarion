from datetime import datetime
from backend.database import db
from backend.models import Planet, Fleet, TickLog
from flask import current_app
import math

def run_tick():
    """Main tick function that runs every 5 seconds"""
    tick_number = get_next_tick_number()
    tick_start_time = datetime.utcnow()

    # Execute tick operations
    resource_changes = process_resource_generation()
    fleet_updates = process_fleet_movements(tick_start_time)

    # Process arrived fleets using the new FleetArrivalService
    from .fleet_arrival import FleetArrivalService
    FleetArrivalService.process_arrived_fleets()

    # Log tick completion
    tick_end_time = datetime.utcnow()
    log_tick(tick_number, tick_start_time, resource_changes, fleet_updates)

    print(f"Tick {tick_number} completed at {tick_end_time}")

    return resource_changes  # Return changes for manual tick endpoint

def get_next_tick_number():
    """Get the next tick number"""
    last_tick = TickLog.query.order_by(TickLog.tick_number.desc()).first()
    return (last_tick.tick_number + 1) if last_tick else 1

def process_resource_generation():
    """Process resource generation for all planets"""
    planets = Planet.query.all()
    changes = []

    for planet in planets:
        # Calculate production rates with planet trait bonuses
        metal_rate = calculate_production_rate(planet.metal_mine, 'metal', planet)
        crystal_rate = calculate_production_rate(planet.crystal_mine, 'crystal', planet)
        deuterium_rate = calculate_production_rate(planet.deuterium_synthesizer, 'deuterium', planet)

        # Calculate energy production and consumption
        energy_production = planet.solar_plant * 20 + planet.fusion_reactor * 50
        energy_consumption = (planet.metal_mine * 10 +
                            planet.crystal_mine * 10 +
                            planet.deuterium_synthesizer * 20)

        # Apply energy efficiency
        energy_ratio = min(1.0, energy_production / energy_consumption) if energy_consumption > 0 else 1.0

        # Calculate actual production for this tick (5 seconds = 1/72 hour for fast testing)
        # Use max(1, ...) to ensure at least 1 resource per tick for active mines
        tick_metal = max(1, int(metal_rate * energy_ratio / 72)) if planet.metal_mine > 0 else 0
        tick_crystal = max(1, int(crystal_rate * energy_ratio / 72)) if planet.crystal_mine > 0 else 0
        tick_deuterium = max(1, int(deuterium_rate * energy_ratio / 72)) if planet.deuterium_synthesizer > 0 else 0

        # Update planet resources
        planet.metal += tick_metal
        planet.crystal += tick_crystal
        planet.deuterium += tick_deuterium

        changes.append({
            'planet_id': planet.id,
            'metal_change': tick_metal,
            'crystal_change': tick_crystal,
            'deuterium_change': tick_deuterium
        })

    db.session.commit()
    return changes

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
        Fleet.status.in_(['traveling', 'returning']) |
        Fleet.status.like('colonizing:%') |
        Fleet.status.like('exploring:%')
    ).all()

    for fleet in arrived_fleets:
        if fleet.status.startswith('colonizing:'):
            # Handle enhanced colonization with trait bonuses
            coords = fleet.status.split(':')[1:]  # Extract coordinates
            x, y, z = map(int, coords)

            # Double-check coordinates are still empty
            existing_planet = Planet.query.filter_by(x=x, y=y, z=z).first()
            if existing_planet:
                # Coordinates occupied, fleet returns
                fleet.status = 'returning'
                fleet.mission = 'return'
                fleet.arrival_time = current_time + (fleet.arrival_time - fleet.departure_time)  # Same travel time back
                updates.append({
                    'fleet_id': fleet.id,
                    'event_type': 'colonization_failed',
                    'description': f'Colonization failed - coordinates {x}:{y}:{z} already occupied'
                })
            else:
                # Check colonization difficulty and user research level
                from backend.services.planet_traits import PlanetTraitService
                colonization_difficulty = PlanetTraitService.calculate_colonization_difficulty(x, y, z)

                # Get user's research level
                user_research_level = get_user_research_level(fleet.user_id)

                if colonization_difficulty > user_research_level:
                    # Insufficient technology, fleet returns
                    fleet.status = 'returning'
                    fleet.mission = 'return'
                    fleet.arrival_time = current_time + (fleet.arrival_time - fleet.departure_time)
                    updates.append({
                        'fleet_id': fleet.id,
                        'event_type': 'colonization_failed',
                        'description': f'Colonization failed - difficulty {colonization_difficulty} requires research level {colonization_difficulty}'
                    })
                else:
                    # Create new colony with enhanced starting resources based on traits
                    colony_name = generate_colony_name(fleet.user_id, x, y, z)

                    # Calculate starting resources based on planet traits
                    starting_resources = calculate_starting_resources(x, y, z)

                    colony = Planet(
                        name=colony_name,
                        x=x,
                        y=y,
                        z=z,
                        user_id=fleet.user_id,
                        metal=starting_resources['metal'],
                        crystal=starting_resources['crystal'],
                        deuterium=starting_resources['deuterium'],
                        metal_mine=1,   # Basic structures
                        crystal_mine=1,
                        deuterium_synthesizer=0,
                        solar_plant=1,
                        fusion_reactor=0
                    )
                    db.session.add(colony)
                    db.session.flush()  # Get the colony ID

                    # Generate planet traits for the colony
                    traits = PlanetTraitService.generate_planet_traits(colony)
                    db.session.add_all(traits)

                    # Update fleet
                    fleet.status = 'stationed'
                    fleet.target_planet_id = colony.id
                    fleet.start_planet_id = colony.id

                    trait_names = [t.trait_name for t in traits]
                    updates.append({
                        'fleet_id': fleet.id,
                        'event_type': 'colonization_success',
                        'description': f'New colony "{colony_name}" established at {x}:{y}:{z} with traits: {", ".join(trait_names)}'
                    })

        elif fleet.status == 'traveling':
            # Fleet has arrived at destination
            fleet.status = 'stationed'
            fleet.start_planet_id = fleet.target_planet_id  # Update start planet
            updates.append({
                'fleet_id': fleet.id,
                'event_type': 'arrival',
                'description': f'Fleet arrived at planet {fleet.target_planet_id}'
            })
        elif fleet.status.startswith('exploring:'):
            # Handle exploration
            coords = fleet.status.split(':')[1:]  # Extract coordinates
            x, y, z = map(int, coords)

            # Generate planets in the explored system
            discovered_planets = generate_exploration_planets(x, y, z, fleet.user_id)

            # Update user's explored systems
            from backend.models import User
            user = User.query.get(fleet.user_id)
            if user:
                import json
                explored_systems = []
                if user.explored_systems:
                    try:
                        explored_systems = json.loads(user.explored_systems)
                    except:
                        explored_systems = []

                # Add new system if not already explored
                system_key = f"{x}:{y}:{z}"
                if not any(s.get('coordinates') == system_key for s in explored_systems):
                    explored_systems.append({
                        'coordinates': system_key,
                        'x': x, 'y': y, 'z': z,
                        'planets': len(discovered_planets),
                        'explored_at': current_time.isoformat()
                    })

                user.explored_systems = json.dumps(explored_systems)

            # Store discovery information in fleet
            fleet.explored_coordinates = json.dumps([{
                'x': x, 'y': y, 'z': z,
                'planets': len(discovered_planets)
            }])

            # Fleet returns to origin
            fleet.status = 'returning'
            fleet.mission = 'return'
            fleet.arrival_time = current_time + (fleet.arrival_time - fleet.departure_time)  # Same travel time back

            updates.append({
                'fleet_id': fleet.id,
                'event_type': 'exploration_complete',
                'description': f'Exploration completed at {x}:{y}:{z}, discovered {len(discovered_planets)} planets'
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

def log_tick(tick_number, timestamp, resource_changes, fleet_updates):
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
        # Offset coordinates slightly for multiple planets in same system
        planet_x = x + random.randint(-5, 5)
        planet_y = y + random.randint(-5, 5)
        planet_z = z + random.randint(-5, 5)

        # Ensure coordinates are unique
        while Planet.query.filter_by(x=planet_x, y=planet_y, z=planet_z).first():
            planet_x = x + random.randint(-5, 5)
            planet_y = y + random.randint(-5, 5)
            planet_z = z + random.randint(-5, 5)

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
