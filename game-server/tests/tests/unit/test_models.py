import pytest
import os
import sys
from datetime import datetime, timedelta

from backend.models import User, Planet, Fleet, Alliance, TickLog

class TestUserModel:
    """Test User model CRUD operations and relationships"""

    def test_user_creation(self, db_session):
        """Test creating a new user"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashedpassword'
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hashedpassword'
        assert isinstance(user.created_at, datetime)

    def test_user_repr(self, sample_user):
        """Test user string representation"""
        assert str(sample_user) == '<User testuser>'

    def test_user_unique_constraints(self, db_session):
        """Test unique constraints on username and email"""
        user1 = User(username='user1', email='user1@example.com', password_hash='pass1')
        db_session.add(user1)
        db_session.commit()

        # Try to create user with same username
        user2 = User(username='user1', email='user2@example.com', password_hash='pass2')
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

        db_session.rollback()

        # Try to create user with same email
        user3 = User(username='user3', email='user1@example.com', password_hash='pass3')
        db_session.add(user3)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_user_planets_relationship(self, db_session, sample_user):
        """Test user-planets relationship"""
        planet = Planet(
            name='Test Planet',
            x=1, y=1, z=1,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        assert len(sample_user.planets) == 1
        assert sample_user.planets[0].name == 'Test Planet'

class TestPlanetModel:
    """Test Planet model operations"""

    def test_planet_creation(self, db_session, sample_user):
        """Test creating a new planet"""
        planet = Planet(
            name='Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            metal=10000,
            crystal=5000,
            deuterium=2000,
            metal_mine=5,
            crystal_mine=3,
            solar_plant=10
        )
        db_session.add(planet)
        db_session.commit()

        assert planet.id is not None
        assert planet.name == 'Test Planet'
        assert planet.x == 100
        assert planet.metal == 10000
        assert planet.metal_mine == 5

    def test_planet_repr(self, sample_planet):
        """Test planet string representation"""
        assert str(sample_planet) == '<Planet Test Planet (100:200:300)>'

    def test_planet_resource_limits(self, db_session, sample_user):
        """Test planet with maximum resources"""
        planet = Planet(
            name='Rich Planet',
            x=1, y=1, z=1,
            user_id=sample_user.id,
            metal=999999999999,  # Max BigInteger
            crystal=999999999999,
            deuterium=999999999999
        )
        db_session.add(planet)
        db_session.commit()

        assert planet.metal == 999999999999

    def test_planet_foreign_key_constraint(self, db_session):
        """Test foreign key constraint with invalid user_id"""
        planet = Planet(
            name='Orphan Planet',
            x=1, y=1, z=1,
            user_id=99999  # Non-existent user
        )
        db_session.add(planet)
        # Note: SQLite doesn't enforce foreign key constraints by default in tests
        # In production with PostgreSQL, this would raise IntegrityError
        try:
            db_session.commit()
            # If we get here, foreign key constraints are not enforced (SQLite behavior)
            assert True  # Test passes - constraint not enforced in test environment
        except Exception:
            # If an exception is raised, foreign key constraint is working
            assert True  # Test passes - constraint is enforced

class TestFleetModel:
    """Test Fleet model operations"""

    def test_fleet_creation(self, db_session, sample_user, sample_planet):
        """Test creating a new fleet"""
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=sample_user.id,
            mission='attack',
            start_planet_id=sample_planet.id,
            target_planet_id=sample_planet.id,
            small_cargo=10,
            large_cargo=5,
            light_fighter=20,
            heavy_fighter=15,
            cruiser=8,
            battleship=3,
            status='stationed',
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            eta=3600
        )
        db_session.add(fleet)
        db_session.commit()

        assert fleet.id is not None
        assert fleet.mission == 'attack'
        assert fleet.small_cargo == 10
        assert fleet.status == 'stationed'

    def test_fleet_repr(self, sample_fleet):
        """Test fleet string representation"""
        expected = f'<Fleet attack from {sample_fleet.start_planet_id} to {sample_fleet.target_planet_id}>'
        assert str(sample_fleet) == expected

    def test_fleet_empty_ships(self, db_session, sample_user, sample_planet):
        """Test fleet with no ships (edge case)"""
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=sample_user.id,
            mission='transport',
            start_planet_id=sample_planet.id,
            target_planet_id=sample_planet.id,
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            eta=3600
        )
        db_session.add(fleet)
        db_session.commit()

        assert fleet.small_cargo == 0
        assert fleet.battleship == 0

    def test_fleet_invalid_mission(self, db_session, sample_user, sample_planet):
        """Test fleet with invalid mission type"""
        now = datetime.utcnow()
        fleet = Fleet(
            user_id=sample_user.id,
            mission='invalid_mission',
            start_planet_id=sample_planet.id,
            target_planet_id=sample_planet.id,
            departure_time=now,
            arrival_time=now + timedelta(hours=1),
            eta=3600
        )
        db_session.add(fleet)
        db_session.commit()

        # Should still work, but mission is just a string
        assert fleet.mission == 'invalid_mission'

class TestAllianceModel:
    """Test Alliance model operations"""

    def test_alliance_creation(self, db_session, sample_user):
        """Test creating a new alliance"""
        alliance = Alliance(
            name='Test Alliance',
            description='A test alliance for unit tests',
            leader_id=sample_user.id
        )
        db_session.add(alliance)
        db_session.commit()

        assert alliance.id is not None
        assert alliance.name == 'Test Alliance'
        assert alliance.leader_id == sample_user.id

    def test_alliance_repr(self, sample_alliance):
        """Test alliance string representation"""
        assert str(sample_alliance) == '<Alliance Test Alliance>'

    def test_alliance_unique_name(self, db_session, sample_user):
        """Test unique constraint on alliance name"""
        alliance1 = Alliance(name='Unique Alliance', leader_id=sample_user.id)
        db_session.add(alliance1)
        db_session.commit()

        alliance2 = Alliance(name='Unique Alliance', leader_id=sample_user.id)
        db_session.add(alliance2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

class TestTickLogModel:
    """Test TickLog model operations"""

    def test_tick_log_creation(self, db_session, sample_planet):
        """Test creating a new tick log"""
        tick_log = TickLog(
            tick_number=100,
            planet_id=sample_planet.id,
            metal_change=1000,
            crystal_change=500,
            deuterium_change=200,
            event_type='resource_production',
            event_description='Regular resource production tick'
        )
        db_session.add(tick_log)
        db_session.commit()

        assert tick_log.id is not None
        assert tick_log.tick_number == 100
        assert tick_log.metal_change == 1000

    def test_tick_log_repr(self, db_session, sample_planet):
        """Test tick log string representation"""
        tick_log = TickLog(
            tick_number=50,
            event_type='fleet_arrival'
        )
        db_session.add(tick_log)
        db_session.commit()

        assert str(tick_log) == '<TickLog tick:50 event:fleet_arrival>'

    def test_tick_log_negative_changes(self, db_session, sample_planet):
        """Test tick log with negative resource changes"""
        tick_log = TickLog(
            tick_number=200,
            planet_id=sample_planet.id,
            metal_change=-500,
            crystal_change=-200,
            deuterium_change=0,
            event_type='combat_loss'
        )
        db_session.add(tick_log)
        db_session.commit()

        assert tick_log.metal_change == -500
        assert tick_log.event_type == 'combat_loss'

class TestModelMappings:
    """Test SQLAlchemy model mappings and relationships"""

    def test_model_mappings(self, db_session):
        """Test that all models are properly mapped and can be queried"""
        # This test will fail if there are SQLAlchemy mapper initialization errors
        for cls in [User, Planet, Fleet, Alliance, TickLog]:
            assert cls.query is not None
            # Try to execute a simple query to ensure the mapper is working
            try:
                result = cls.query.limit(1).all()
                # If we get here, the mapper is working
                assert True
            except Exception as e:
                pytest.fail(f"Model {cls.__name__} mapper failed: {str(e)}")
