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
        # Calculate production rates
        metal_rate = calculate_production_rate(planet.metal_mine, 'metal')
        crystal_rate = calculate_production_rate(planet.crystal_mine, 'crystal')
        deuterium_rate = calculate_production_rate(planet.deuterium_synthesizer, 'deuterium')

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

def calculate_production_rate(level, resource_type):
    """Calculate production rate for a building level"""
    if resource_type == 'metal':
        return level * 30 * (1.1 ** level)
    elif resource_type == 'crystal':
        return level * 20 * (1.1 ** level)
    elif resource_type == 'deuterium':
        return level * 10 * (1.1 ** level)
    return 0

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
            # Handle colonization
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
                # Create new colony
                colony = Planet(
                    name=f"Colony {fleet.user_id}",
                    x=x,
                    y=y,
                    z=z,
                    user_id=fleet.user_id,
                    metal=500,      # Colony starting resources
                    crystal=250,
                    deuterium=0,
                    metal_mine=1,   # Basic structures
                    crystal_mine=1,
                    deuterium_synthesizer=0,
                    solar_plant=1,
                    fusion_reactor=0
                )
                db.session.add(colony)
                db.session.flush()  # Get the colony ID

                # Update fleet
                fleet.status = 'stationed'
                fleet.target_planet_id = colony.id
                fleet.start_planet_id = colony.id  # Fleet is now stationed at the colony

                updates.append({
                    'fleet_id': fleet.id,
                    'event_type': 'colonization_success',
                    'description': f'New colony established at {x}:{y}:{z}'
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
        discovered_planets.append(planet)

    db.session.commit()
    return discovered_planets

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
