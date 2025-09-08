#!/usr/bin/env python3
"""
Database Schema Update Script

This script updates the database schema to add new fields for colonization support.
"""

from src.backend.models import db
from flask import Flask

def update_schema():
    """Update database schema with new fields"""
    app = Flask(__name__)

    # Use the same database configuration as the main app
    import os
    from dotenv import load_dotenv
    load_dotenv()

    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/dev.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        # Create all tables (this will add new columns if they don't exist)
        db.create_all()
        print("✅ Database schema updated successfully!")

        # Verify the new columns exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)

        # Check Planet table
        planet_columns = [col['name'] for col in inspector.get_columns('planets')]
        required_planet_cols = ['is_home_planet', 'colonized_at']
        missing_planet_cols = [col for col in required_planet_cols if col not in planet_columns]

        # Check Fleet table
        fleet_columns = [col['name'] for col in inspector.get_columns('fleets')]
        required_fleet_cols = ['target_coordinates', 'combat_experience', 'last_combat_time', 'combat_victories', 'combat_defeats']
        missing_fleet_cols = [col for col in required_fleet_cols if col not in fleet_columns]

        # Check for new tables
        existing_tables = inspector.get_table_names()
        required_tables = ['combat_reports', 'debris_fields']
        missing_tables = [table for table in required_tables if table not in existing_tables]

        if missing_planet_cols or missing_fleet_cols or missing_tables:
            print("⚠️  Some columns/tables may be missing. You might need to recreate the database.")
            if missing_planet_cols:
                print(f"   Missing Planet columns: {missing_planet_cols}")
            if missing_fleet_cols:
                print(f"   Missing Fleet columns: {missing_fleet_cols}")
            if missing_tables:
                print(f"   Missing tables: {missing_tables}")
        else:
            print("✅ All required columns and tables are present!")

if __name__ == '__main__':
    update_schema()
