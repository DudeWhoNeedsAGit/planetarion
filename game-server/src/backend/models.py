from datetime import datetime
from .database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    alliance_id = db.Column(db.Integer, db.ForeignKey('alliances.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Exploration data
    explored_systems = db.Column(db.Text)  # JSON string of explored coordinates

    # Relationships
    planets = db.relationship('Planet', backref='owner', lazy=True)
    fleets = db.relationship('Fleet', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Planet(db.Model):
    __tablename__ = 'planets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    z = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Resources
    metal = db.Column(db.BigInteger, default=1000)
    crystal = db.Column(db.BigInteger, default=500)
    deuterium = db.Column(db.BigInteger, default=0)

    # Structures
    metal_mine = db.Column(db.Integer, default=1)
    crystal_mine = db.Column(db.Integer, default=1)
    deuterium_synthesizer = db.Column(db.Integer, default=0)
    solar_plant = db.Column(db.Integer, default=1)
    fusion_reactor = db.Column(db.Integer, default=0)

    # Ships (for testing - in real game, ships would be tracked separately)
    small_cargo = db.Column(db.Integer, default=0)
    large_cargo = db.Column(db.Integer, default=0)
    light_fighter = db.Column(db.Integer, default=0)
    heavy_fighter = db.Column(db.Integer, default=0)
    cruiser = db.Column(db.Integer, default=0)
    battleship = db.Column(db.Integer, default=0)
    colony_ship = db.Column(db.Integer, default=0)

    # Planet traits and bonuses
    base_metal_bonus = db.Column(db.Float, default=0.0)
    base_crystal_bonus = db.Column(db.Float, default=0.0)
    base_deuterium_bonus = db.Column(db.Float, default=0.0)
    base_energy_bonus = db.Column(db.Float, default=0.0)
    base_defense_bonus = db.Column(db.Float, default=0.0)
    base_attack_bonus = db.Column(db.Float, default=0.0)
    colonization_difficulty = db.Column(db.Integer, default=1)  # 1-5 scale

    # Research lab for research point generation
    research_lab = db.Column(db.Integer, default=0)

    # Colony tracking
    is_home_planet = db.Column(db.Boolean, default=False)
    colonized_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Planet {self.name} ({self.x}:{self.y}:{self.z})>'


class Fleet(db.Model):
    __tablename__ = 'fleets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mission = db.Column(db.String(50), nullable=False)
    start_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)
    target_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)

    # Ships
    small_cargo = db.Column(db.Integer, default=0)
    large_cargo = db.Column(db.Integer, default=0)
    light_fighter = db.Column(db.Integer, default=0)
    heavy_fighter = db.Column(db.Integer, default=0)
    cruiser = db.Column(db.Integer, default=0)
    battleship = db.Column(db.Integer, default=0)
    colony_ship = db.Column(db.Integer, default=0)

    # Fleet status
    status = db.Column(db.String(20), default='stationed')
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    eta = db.Column(db.Integer, default=0)

    # Exploration data
    explored_coordinates = db.Column(db.Text)  # JSON string of explored coords

    # Coordinate-based targeting for colonization
    target_coordinates = db.Column(db.String(50))  # Format: "x:y:z"

    def __repr__(self):
        return f'<Fleet {self.mission} from {self.start_planet_id} to {self.target_planet_id}>'


class Alliance(db.Model):
    __tablename__ = 'alliances'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Members relationship
    members = db.relationship(
        'User',
        backref='alliance',
        lazy=True,
        primaryjoin='foreign(User.alliance_id) == Alliance.id',
        foreign_keys='[User.alliance_id]',
        viewonly=True
    )

    # Leader relationship
    leader = db.relationship(
        'User',
        foreign_keys='[Alliance.leader_id]',
        uselist=False,
        backref='led_alliance'
    )

    def __repr__(self):
        return f'<Alliance {self.name}>'


class TickLog(db.Model):
    __tablename__ = 'tick_logs'

    id = db.Column(db.Integer, primary_key=True)
    tick_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Resource changes
    planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'))
    metal_change = db.Column(db.BigInteger, default=0)
    crystal_change = db.Column(db.BigInteger, default=0)
    deuterium_change = db.Column(db.BigInteger, default=0)

    # Fleet events
    fleet_id = db.Column(db.Integer, db.ForeignKey('fleets.id'))
    event_type = db.Column(db.String(50))
    event_description = db.Column(db.Text)

    def __repr__(self):
        return f'<TickLog tick:{self.tick_number} event:{self.event_type}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)  # Cached for performance
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_system = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref='chat_messages')

    def __repr__(self):
        return f'<ChatMessage user:{self.username} system:{self.is_system}>'


class PlanetTrait(db.Model):
    __tablename__ = 'planet_traits'

    id = db.Column(db.Integer, primary_key=True)
    planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)
    trait_type = db.Column(db.String(50), nullable=False)  # 'resource_bonus', 'defense_bonus', etc.
    trait_name = db.Column(db.String(100), nullable=False)
    bonus_value = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)

    # Relationships
    planet = db.relationship('Planet', backref='traits')

    def __repr__(self):
        return f'<PlanetTrait {self.trait_name} (+{self.bonus_value})>'


class Research(db.Model):
    __tablename__ = 'research'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Research levels
    colonization_tech = db.Column(db.Integer, default=0)
    astrophysics = db.Column(db.Integer, default=0)
    interstellar_communication = db.Column(db.Integer, default=0)

    # Research points
    research_points = db.Column(db.BigInteger, default=0)

    # Relationships
    user = db.relationship('User', backref='research_data')

    def __repr__(self):
        return f'<Research user:{self.user_id} points:{self.research_points}>'
