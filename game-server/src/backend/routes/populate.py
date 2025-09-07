from flask import Blueprint, jsonify
from backend.database import db
from backend.models import User, Planet, Fleet, Alliance, TickLog
from faker import Faker
import random
from datetime import datetime, timedelta
import bcrypt

populate_bp = Blueprint('populate', __name__)

# Initialize Faker
fake = Faker()

@populate_bp.route('/populate', methods=['POST'])
def populate_database():
    """Populate the database with realistic test data"""

    from flask import request

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
        import os
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

        # Generate planets
        planets = []
        planet_names = [
            "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
            "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
            "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
        ]

        for user in users:
            num_planets = 1 if minimal else random.randint(1, 5)
            for i in range(num_planets):
                x = random.randint(1, 1000)
                y = random.randint(1, 1000)
                z = random.randint(1, 1000)

                name = f"{planet_names[i % len(planet_names)]} {user.username}"

                # Add ships to test user's planets for E2E testing
                if user.username == 'e2etestuser':
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
                else:
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

        db.session.commit()

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
