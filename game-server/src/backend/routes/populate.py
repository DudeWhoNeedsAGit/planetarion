from flask import Blueprint, jsonify
from backend.database import db
from backend.models import User, Planet, Fleet, Alliance, TickLog
from faker import Faker
import random
from datetime import datetime, timedelta
import bcrypt
import math

populate_bp = Blueprint('populate', __name__)

# Initialize Faker
fake = Faker()

# Universe Configuration
UNIVERSE_CONFIG = {
    'min_coord': -10000,
    'max_coord': 10000,
    'min_distance': 25,  # Minimum distance between planets
    'num_clusters': 8,   # Number of galaxy clusters
    'cluster_radius': 800,  # Radius of each cluster
    'cluster_spacing': 3000,  # Minimum distance between clusters
}

def calculate_distance(x1, y1, z1, x2, y2, z2):
    """Calculate 3D distance between two points"""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

def is_valid_position(x, y, z, existing_planets, min_distance=25):
    """Check if a position is valid (not too close to existing planets)"""
    for planet in existing_planets:
        distance = calculate_distance(x, y, z, planet.x, planet.y, planet.z)
        if distance < min_distance:
            return False
    return True

def generate_cluster_centers(num_clusters, min_distance, fixed_z=None):
    """Generate centers for galaxy clusters"""
    centers = []
    max_attempts = 1000

    for _ in range(num_clusters):
        for attempt in range(max_attempts):
            x = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            y = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            z = int(fixed_z) if fixed_z is not None else random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])

            # Check distance from other cluster centers
            valid = True
            for cx, cy, cz in centers:
                if calculate_distance(x, y, z, cx, cy, cz) < min_distance:
                    valid = False
                    break

            if valid:
                centers.append((x, y, z))
                break
        else:
            # If we can't find a valid position, place it randomly
            x = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            y = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            z = int(fixed_z) if fixed_z is not None else random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            centers.append((x, y, z))

    return centers

def generate_planet_position(existing_planets, cluster_center=None, is_core_planet=False, fixed_z=None):
    """Generate a valid planet position"""
    max_attempts = 100

    for attempt in range(max_attempts):
        if cluster_center and not is_core_planet:
            # Generate position within cluster
            cx, cy, cz = cluster_center
            radius = UNIVERSE_CONFIG['cluster_radius']
            x = cx + random.randint(-radius, radius)
            y = cy + random.randint(-radius, radius)
            if fixed_z is not None:
                z = int(fixed_z)
            else:
                z = cz + random.randint(-radius, radius)
        else:
            # Generate random position across universe
            x = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            y = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
            z = int(fixed_z) if fixed_z is not None else random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])

        # Ensure coordinates are within bounds
        x = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], x))
        y = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], y))
        z = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], z))

        if is_valid_position(x, y, z, existing_planets, UNIVERSE_CONFIG['min_distance']):
            return x, y, z

    # If we can't find a valid position, place it with minimal distance check
    x = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
    y = random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
    z = int(fixed_z) if fixed_z is not None else random.randint(UNIVERSE_CONFIG['min_coord'], UNIVERSE_CONFIG['max_coord'])
    return x, y, z

def create_enemy_planets_around_player(player_planets, num_enemies=5):
    """Create enemy planets with defensive fleets around player planets"""
    enemy_data = []
    used_emails = set()  # Track used emails to prevent duplicates

    for player_planet in player_planets:
        for i in range(num_enemies):
            # Create enemy user with unique identifiers
            enemy_username = f"enemy_player_{player_planet.id}_{i}"
            enemy_email = f"enemy_{player_planet.id}_{i}@example.com"

            # Ensure email uniqueness across all enemy users
            base_email = enemy_email
            counter = 0
            while enemy_email in used_emails:
                counter += 1
                enemy_email = f"enemy_{player_planet.id}_{i}_{counter}@example.com"

            used_emails.add(enemy_email)

            # Check if enemy user already exists
            existing_enemy = User.query.filter_by(username=enemy_username).first()
            if existing_enemy:
                enemy_user = existing_enemy
            else:
                # Create new enemy user with hashed password
                enemy_password_hash = bcrypt.hashpw('enemypassword123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                enemy_user = User(
                    username=enemy_username,
                    email=enemy_email,
                    password_hash=enemy_password_hash,
                    created_at=fake.date_time_this_year()
                )
                db.session.add(enemy_user)
                db.session.flush()  # Get user ID

            # Generate position around player planet
            distance = random.randint(500, 1000)  # 500-1000 units away
            angle = random.uniform(0, 2 * math.pi)
            # Keep enemies on the same Z slice as the player for a denser, more navigable 2D map.
            height_offset = 0

            enemy_x = int(player_planet.x + distance * math.cos(angle))
            enemy_y = int(player_planet.y + distance * math.sin(angle))
            enemy_z = int(player_planet.z + height_offset)

            # Ensure coordinates are within universe bounds
            enemy_x = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], enemy_x))
            enemy_y = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], enemy_y))
            enemy_z = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], enemy_z))

            # Create enemy planet
            enemy_planet_name = f"Enemy Base {i+1} near {player_planet.name}"
            enemy_planet = Planet(
                name=enemy_planet_name,
                x=enemy_x,
                y=enemy_y,
                z=enemy_z,
                user_id=enemy_user.id,
                metal=random.randint(50000, 200000),    # Moderate resources
                crystal=random.randint(30000, 150000),
                deuterium=random.randint(10000, 50000),
                metal_mine=random.randint(5, 15),        # Decent infrastructure
                crystal_mine=random.randint(3, 10),
                deuterium_synthesizer=random.randint(1, 5),
                solar_plant=random.randint(10, 20),
                fusion_reactor=random.randint(0, 3),
                created_at=fake.date_time_this_year()
            )

            # Create defensive fleet
            defensive_fleet = Fleet(
                user_id=enemy_user.id,
                mission='defend',
                start_planet_id=enemy_planet.id,  # Will be set after planet creation
                target_planet_id=enemy_planet.id, # Stationed at planet
                status='stationed',
                departure_time=datetime.utcnow(),
                arrival_time=datetime.utcnow(),
                eta=0,
                # Balanced defensive fleet composition
                small_cargo=random.randint(10, 50),
                large_cargo=random.randint(5, 25),
                light_fighter=random.randint(20, 100),
                heavy_fighter=random.randint(10, 50),
                cruiser=random.randint(5, 20),
                battleship=random.randint(1, 10),
                colony_ship=random.randint(0, 2),
                recycler=random.randint(0, 5)
            )

            enemy_data.append((enemy_planet, defensive_fleet))

    return enemy_data


def create_pirate_camps_around_player(player_planets, num_camps=2):
    """Create pirate camp planets owned by a dedicated 'pirates' NPC user."""
    import bcrypt
    import random
    import math

    # Get or create pirates user
    pirates = User.query.filter_by(username="pirates").first()
    if not pirates:
        pirates_pw = bcrypt.hashpw('pirates'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        pirates = User(username="pirates", email="pirates@example.com", password_hash=pirates_pw)
        db.session.add(pirates)
        db.session.commit()

    pirate_data = []
    for player_planet in player_planets[: max(1, len(player_planets))]:
        for i in range(num_camps):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.randint(300, 900)
            # Keep pirate camps on the same Z slice as the player for a denser, more navigable 2D map.
            height_offset = 0

            x = int(player_planet.x + distance * math.cos(angle))
            y = int(player_planet.y + distance * math.sin(angle))
            z = int(player_planet.z + height_offset)

            x = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], x))
            y = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], y))
            z = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], z))

            name = f"Pirate Camp {i+1} near {player_planet.name}"
            planet = Planet(name=name, x=x, y=y, z=z, user_id=pirates.id, metal=50000, crystal=25000, deuterium=10000)
            db.session.add(planet)
            db.session.flush()

            # Defensive fleet parked at the camp
            now = datetime.utcnow()
            fleet = Fleet(
                user_id=pirates.id,
                mission='defend',
                status='stationed',
                start_planet_id=planet.id,
                target_planet_id=planet.id,
                departure_time=now,
                arrival_time=now,
                eta=0,
                light_fighter=200 + i * 50,
                heavy_fighter=100 + i * 25,
                cruiser=25 + i * 5,
                battleship=10 + i * 2,
            )
            db.session.add(fleet)
            pirate_data.append((planet, fleet))

    db.session.commit()
    return pirate_data


def create_local_unowned_planets_on_same_z(existing_planets, center_planet, count=80, radius=1800):
    """Create extra unowned planets near a player's start location on the same Z slice.

    The current GalaxyMap UI is 2D (X/Y) and keeps Z fixed to the player's home Z.
    Without local density on that Z slice, the map can feel empty (only a handful of systems).
    """
    if not center_planet:
        return []

    created = []
    attempts = 0
    max_attempts = max(500, count * 20)

    # Use a slightly larger spacing locally so markers don't look like a blob.
    local_min_distance = max(UNIVERSE_CONFIG['min_distance'], 80)

    while len(created) < count and attempts < max_attempts:
        attempts += 1
        # Sample a point in a disk for better spread.
        angle = random.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(random.random())
        x = int(center_planet.x + r * math.cos(angle))
        y = int(center_planet.y + r * math.sin(angle))
        z = int(center_planet.z)

        # Keep within universe bounds.
        x = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], x))
        y = max(UNIVERSE_CONFIG['min_coord'], min(UNIVERSE_CONFIG['max_coord'], y))

        if not is_valid_position(x, y, z, existing_planets + created, local_min_distance):
            continue

        planet = Planet(
            name=f"Uncharted {random.choice(['Belt', 'Rock', 'World', 'Orbit'])} {random.randint(100, 999)}",
            x=x,
            y=y,
            z=z,
            user_id=None,
            metal=random.randint(500, 5000),
            crystal=random.randint(250, 2500),
            deuterium=random.randint(0, 1500),
            metal_mine=0,
            crystal_mine=0,
            deuterium_synthesizer=0,
            solar_plant=0,
            fusion_reactor=0,
            created_at=fake.date_time_this_year()
        )
        created.append(planet)

    return created

@populate_bp.route('/populate', methods=['POST'])
def populate_database():
    """Populate the database with realistic test data"""

    from flask import request
    import os
    from flask import current_app

    # Safety: this endpoint clears and recreates data, so only allow it in testing.
    if (current_app.config.get('FLASK_ENV') != 'testing') and (os.getenv('FLASK_ENV') != 'testing'):
        return jsonify({'error': 'Populate is only available when FLASK_ENV=testing'}), 403

    # Check if deterministic mode is requested
    deterministic = request.args.get('deterministic', 'false').lower() == 'true'
    minimal = request.args.get('minimal', 'false').lower() == 'true'

    try:
        # Clear existing data in reverse dependency order to avoid foreign key issues
        print("DEBUG: Clearing existing data...")
        db.session.query(TickLog).delete()
        db.session.query(Fleet).delete()
        db.session.query(Planet).delete()
        db.session.query(Alliance).delete()
        db.session.query(User).delete()
        db.session.commit()
        print("DEBUG: Data cleared successfully")

        # Make generation deterministic for testing
        if deterministic or os.getenv('FLASK_ENV') == 'testing':
            random.seed(42)  # Fixed seed for deterministic results
            fake.seed_instance(42)  # Fixed seed for Faker
            print("DEBUG: Using deterministic mode")

        # Generate users (including test user)
        users = []

        # Create the specific test user that E2E tests expect
        test_password_hash = bcrypt.hashpw('testpassword123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        test_user = User(
            username='e2etestuser',
            email='e2etestuser@example.com',
            password_hash=test_password_hash,
            created_at=fake.date_time_this_year(),
            last_login=fake.date_time_this_month()
        )
        users.append(test_user)
        db.session.add(test_user)

        # Generate remaining fake users
        if not minimal:
            usernames = set()
            emails = set()
            for _ in range(199):  # Total 200 users
                username = fake.user_name()
                while username in usernames:
                    username = fake.user_name()
                usernames.add(username)

                email = fake.email()
                while email in emails:
                    email = fake.email()
                emails.add(email)

                # Generate a proper bcrypt hash for the fake password
                fake_password = fake.password()
                hashed_password = bcrypt.hashpw(fake_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                user = User(
                    username=username,
                    email=email,
                    password_hash=hashed_password,
                    created_at=fake.date_time_this_year(),
                    last_login=fake.date_time_this_month() if random.choice([True, False]) else None
                )
                users.append(user)
                db.session.add(user)

        db.session.commit()

        # Generate planets with improved spacing and clustering
        planets = []
        planet_names = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
            "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
            "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
        ]

        print("DEBUG: Generating galaxy clusters...")
        # GalaxyMap is currently 2D (X/Y) and keeps Z fixed. In testing we keep the
        # entire populated universe on a single Z slice to improve density and
        # reduce wasted "depth" data the player can't reach/see.
        fixed_z = 0
        try:
            if users and any(u.username == 'e2etestuser' for u in users):
                fixed_z = None  # will be set after we pick the test user's cluster
        except Exception:
            fixed_z = 0

        cluster_centers = generate_cluster_centers(
            UNIVERSE_CONFIG['num_clusters'],
            UNIVERSE_CONFIG['cluster_spacing'],
            fixed_z=fixed_z,
        )
        print(f"DEBUG: Generated {len(cluster_centers)} galaxy clusters")

        # Assign users to clusters - ensure e2etestuser gets a dedicated cluster
        user_clusters = {}
        test_user_cluster = cluster_centers[0]  # Reserve first cluster for test user
        fixed_z = test_user_cluster[2]

        for i, user in enumerate(users):
            if user.username == 'e2etestuser':
                user_clusters[user.id] = test_user_cluster
                print(f"DEBUG: Assigned e2etestuser to cluster at {test_user_cluster}")
            else:
                # Start from cluster 1 for other users
                cluster_idx = (i % (len(cluster_centers) - 1)) + 1
                cx, cy, _cz = cluster_centers[cluster_idx]
                user_clusters[user.id] = (cx, cy, fixed_z)

        print("DEBUG: Generating planets with proper spacing...")

        for user in users:
            num_planets = 1 if minimal else random.randint(1, 5)
            cluster_center = user_clusters.get(user.id)

            # Special handling for e2etestuser to ensure proper spacing
            if user.username == 'e2etestuser':
                print(f"DEBUG: Generating {num_planets} planets for e2etestuser with spacing")
                # Generate positions for all e2etestuser planets first to ensure proper spacing
                test_user_positions = []
                for i in range(num_planets):
                    x, y, z = generate_planet_position(
                        planets + test_user_positions,  # Include already generated positions
                        cluster_center,
                        is_core_planet=(i == 0),  # First planet is core planet
                        fixed_z=fixed_z,
                    )
                    test_user_positions.append(type('MockPlanet', (), {'x': x, 'y': y, 'z': z})())

                # Now create the actual planets with the pre-calculated positions
                for i, mock_planet in enumerate(test_user_positions):
                    x, y, z = mock_planet.x, mock_planet.y, mock_planet.z
                    name = f"{planet_names[i % len(planet_names)]} {user.username}"

                    planet = Planet(
                        name=name,
                        x=x,
                        y=y,
                        z=z,
                        user_id=user.id,
                        metal=2000000,  # Fixed abundant resources for E2E testing
                        crystal=1500000,
                        deuterium=1000000,
                        metal_mine=random.randint(1, 20),
                        crystal_mine=random.randint(1, 15),
                        deuterium_synthesizer=random.randint(0, 10),
                        solar_plant=random.randint(1, 25),
                        fusion_reactor=random.randint(0, 5),
                        # Add ships for testing
                        small_cargo=50,
                        large_cargo=25,
                        light_fighter=30,
                        heavy_fighter=15,
                        cruiser=10,
                        battleship=5,
                        colony_ship=2,
                        created_at=fake.date_time_this_year()
                    )
                    planets.append(planet)
                    db.session.add(planet)
                    print(f"DEBUG: Created e2etestuser planet '{name}' at ({x}, {y}, {z})")
            else:
                # Standard planet generation for other users
                for i in range(num_planets):
                    # Use improved positioning with spacing
                    x, y, z = generate_planet_position(
                        planets,
                        cluster_center,
                        is_core_planet=(i == 0),  # First planet is core planet
                        fixed_z=fixed_z,
                    )

                    name = f"{planet_names[i % len(planet_names)]} {user.username}"

                    planet = Planet(
                        name=name,
                        x=x,
                        y=y,
                        z=z,
                        user_id=user.id,
                        metal=random.randint(1000, 1000000),
                        crystal=random.randint(500, 500000),
                        deuterium=random.randint(0, 200000),
                        metal_mine=random.randint(1, 20),
                        crystal_mine=random.randint(1, 15),
                        deuterium_synthesizer=random.randint(0, 10),
                        solar_plant=random.randint(1, 25),
                        fusion_reactor=random.randint(0, 5),
                        created_at=fake.date_time_this_year()
                    )
                    planets.append(planet)
                    db.session.add(planet)

        print(f"DEBUG: Generated {len(planets)} planets across {len(cluster_centers)} clusters")
        print(f"DEBUG: Universe bounds: {UNIVERSE_CONFIG['min_coord']} to {UNIVERSE_CONFIG['max_coord']}")
        print(f"DEBUG: Minimum planet spacing: {UNIVERSE_CONFIG['min_distance']} units")

        db.session.commit()

        # Add extra unowned planets on the same Z slice near the test user to make the
        # 2D GalaxyMap feel populated without requiring a 3D depth selector.
        try:
            test_user = User.query.filter_by(username='e2etestuser').first()
            if test_user:
                test_home = Planet.query.filter_by(user_id=test_user.id).order_by(Planet.id.asc()).first()
                # Minimal mode is used by fast tests that assert the smallest possible dataset.
                # Keep it truly minimal: only the single test-user planet should exist.
                if not minimal:
                    extra_count = 120
                    extra = create_local_unowned_planets_on_same_z(planets, test_home, count=extra_count, radius=2000)
                    if extra:
                        for p in extra:
                            planets.append(p)
                            db.session.add(p)
                        db.session.commit()
                        print(f"DEBUG: Added {len(extra)} extra unowned planets near e2etestuser on Z={test_home.z}")
        except Exception as e:
            print(f"WARNING: Failed to add local unowned planets: {e}")

        # Generate alliances
        alliances = []
        alliance_names = set()
        num_alliances = 1 if minimal else 20
        for _ in range(num_alliances):
            name = fake.company()
            while name in alliance_names:
                name = fake.company()
            alliance_names.add(name)

            leader = random.choice(users)
            alliance = Alliance(
                name=name,
                description=fake.text(max_nb_chars=200),
                leader_id=leader.id,
                created_at=fake.date_time_this_year()
            )
            alliances.append(alliance)
            db.session.add(alliance)

            # Assign members
            num_members = random.randint(2, 10)
            potential_members = [u for u in users if u.id != leader.id]
            members = random.sample(potential_members, min(num_members, len(potential_members)))
            for member in members:
                member.alliance_id = alliance.id

        db.session.commit()

        # Generate fleets
        missions = ['attack', 'transport', 'deploy', 'espionage', 'recycle']
        ship_types = ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter',
                      'cruiser', 'battleship']

        num_fleets = 1 if minimal else 500
        for _ in range(num_fleets):
            user = random.choice(users)
            user_planets = [p for p in planets if p.user_id == user.id]
            if not user_planets:
                continue

            start_planet = random.choice(user_planets)
            target_planet = random.choice(planets)

            mission = random.choice(missions)
            status = random.choice(['stationed', 'traveling', 'returning'])

            departure_time = fake.date_time_this_month()
            eta = random.randint(60, 3600)
            arrival_time = departure_time + timedelta(seconds=eta)

            fleet = Fleet(
                user_id=user.id,
                mission=mission,
                start_planet_id=start_planet.id,
                target_planet_id=target_planet.id,
                status=status,
                departure_time=departure_time,
                arrival_time=arrival_time,
                eta=eta
            )

            # Add ships
            for ship_type in ship_types:
                setattr(fleet, ship_type, random.randint(0, 1000))

            db.session.add(fleet)

        db.session.commit()

        # Generate tick logs
        num_tick_logs = 1 if minimal else 1000
        for _ in range(num_tick_logs):
            planet = random.choice(planets)
            tick_number = random.randint(1, 10000)
            timestamp = fake.date_time_this_year()

            tick_log = TickLog(
                tick_number=tick_number,
                timestamp=timestamp,
                planet_id=planet.id,
                metal_change=random.randint(-1000, 5000),
                crystal_change=random.randint(-500, 2500),
                deuterium_change=random.randint(-200, 1000)
            )
            db.session.add(tick_log)

        # Create enemy planets with defensive fleets around test user for combat testing
        if not minimal:
            test_user = User.query.filter_by(username='e2etestuser').first()
            if test_user:
                test_user_planets = [p for p in planets if p.user_id == test_user.id]
                enemy_data = create_enemy_planets_around_player(test_user_planets, num_enemies=3)

                for enemy_planet, enemy_fleet in enemy_data:
                    planets.append(enemy_planet)
                    db.session.add(enemy_planet)
                    db.session.flush()  # Get planet ID before creating fleet

                    # Update fleet with planet ID
                    enemy_fleet.start_planet_id = enemy_planet.id
                    enemy_fleet.target_planet_id = enemy_planet.id
                    db.session.add(enemy_fleet)

                    print(f"DEBUG: Created enemy planet with fleet at ({enemy_planet.x}, {enemy_planet.y}, {enemy_planet.z})")

                pirate_data = create_pirate_camps_around_player(test_user_planets, num_camps=1)
                for pirate_planet, pirate_fleet in pirate_data:
                    planets.append(pirate_planet)
                    db.session.add(pirate_planet)
                    db.session.flush()
                    pirate_fleet.start_planet_id = pirate_planet.id
                    pirate_fleet.target_planet_id = pirate_planet.id
                    db.session.add(pirate_fleet)
                    print(f"DEBUG: Created pirate camp at ({pirate_planet.x}, {pirate_planet.y}, {pirate_planet.z})")

        db.session.commit()

        return jsonify({
            'message': 'Database populated successfully',
            'users': len(users),
            'planets': len(planets),
            'fleets': num_fleets,
            'alliances': len(alliances),
            'tick_logs': num_tick_logs
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
