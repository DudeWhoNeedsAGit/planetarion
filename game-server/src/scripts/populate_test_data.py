#!/usr/bin/env python3
"""
Script to populate the database with realistic test data for Planetarion game server.
Generates users, planets, fleets, alliances, and tick logs using Faker library.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path

# Import from centralized config using backend import (removing src. dependency)
from backend.config import PATHS

from flask import Flask
from backend.database import db
from backend.models import User, Planet, Fleet, Alliance, TickLog

# Initialize Faker
fake = Faker()

def create_app():
    """Create Flask app with test database configuration"""
    app = Flask(__name__)

    # Use SQLite for testing to avoid PostgreSQL dependency
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app

def generate_users(num_users=200):
    """Generate fake users"""
    users = []
    for _ in range(num_users):
        username = fake.user_name()
        email = fake.email()
        password_hash = fake.password()  # In real app, this would be hashed

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=fake.date_time_this_year(),
            last_login=fake.date_time_this_month() if random.choice([True, False]) else None
        )
        users.append(user)
    return users

def generate_planets(users, min_per_user=1, max_per_user=5):
    """Generate planets for users"""
    planets = []
    planet_names = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
        "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
        "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
    ]

    for user in users:
        num_planets = random.randint(min_per_user, max_per_user)
        for i in range(num_planets):
            x = random.randint(1, 1000)
            y = random.randint(1, 1000)
            z = random.randint(1, 1000)

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
    return planets

def generate_fleets(users, planets, num_fleets=500):
    """Generate fleets"""
    fleets = []
    missions = ['attack', 'transport', 'deploy', 'espionage', 'recycle']
    ship_types = ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter',
                  'cruiser', 'battleship']

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
        eta = random.randint(60, 3600)  # 1 min to 1 hour
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

        # Add random ships
        for ship_type in ship_types:
            setattr(fleet, ship_type, random.randint(0, 1000))

        fleets.append(fleet)
    return fleets

def generate_alliances(users, num_alliances=20):
    """Generate alliances"""
    alliances = []
    alliance_names = [fake.company() for _ in range(num_alliances)]

    for name in alliance_names:
        leader = random.choice(users)
        alliance = Alliance(
            name=name,
            description=fake.text(max_nb_chars=200),
            leader_id=leader.id,
            created_at=fake.date_time_this_year()
        )
        alliances.append(alliance)

        # Assign members to alliance
        num_members = random.randint(2, 10)
        potential_members = [u for u in users if u.id != leader.id]
        members = random.sample(potential_members, min(num_members, len(potential_members)))
        for member in members:
            member.alliance_id = alliance.id

    return alliances

def generate_tick_logs(planets, num_logs=1000):
    """Generate tick logs"""
    tick_logs = []
    for _ in range(num_logs):
        planet = random.choice(planets)
        tick_number = random.randint(1, 10000)
        timestamp = fake.date_time_this_year()

        # Random resource changes
        metal_change = random.randint(-1000, 5000)
        crystal_change = random.randint(-500, 2500)
        deuterium_change = random.randint(-200, 1000)

        tick_log = TickLog(
            tick_number=tick_number,
            timestamp=timestamp,
            planet_id=planet.id,
            metal_change=metal_change,
            crystal_change=crystal_change,
            deuterium_change=deuterium_change
        )
        tick_logs.append(tick_log)
    return tick_logs

def populate_database():
    """Main function to populate the database"""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()

        print("Generating test data...")

        # Generate users
        users = generate_users(200)
        db.session.add_all(users)
        db.session.commit()
        print(f"Created {len(users)} users")

        # Generate planets
        planets = generate_planets(users)
        db.session.add_all(planets)
        db.session.commit()
        print(f"Created {len(planets)} planets")

        # Generate alliances
        alliances = generate_alliances(users)
        db.session.add_all(alliances)
        db.session.commit()
        print(f"Created {len(alliances)} alliances")

        # Generate fleets
        fleets = generate_fleets(users, planets)
        db.session.add_all(fleets)
        db.session.commit()
        print(f"Created {len(fleets)} fleets")

        # Generate tick logs
        tick_logs = generate_tick_logs(planets)
        db.session.add_all(tick_logs)
        db.session.commit()
        print(f"Created {len(tick_logs)} tick logs")

        print("Test data population completed successfully!")
        print(f"Database file: {app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')}")

if __name__ == '__main__':
    populate_database()
