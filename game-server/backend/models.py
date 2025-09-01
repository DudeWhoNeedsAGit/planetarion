from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    planets = db.relationship('Planet', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Planet(db.Model):
    __tablename__ = 'planets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    z = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Planet {self.name} ({self.x}:{self.y}:{self.z})>'

class Fleet(db.Model):
    __tablename__ = 'fleets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mission = db.Column(db.String(50), nullable=False)  # attack, transport, etc.
    start_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)
    target_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)

    # Ships
    small_cargo = db.Column(db.Integer, default=0)
    large_cargo = db.Column(db.Integer, default=0)
    light_fighter = db.Column(db.Integer, default=0)
    heavy_fighter = db.Column(db.Integer, default=0)
    cruiser = db.Column(db.Integer, default=0)
    battleship = db.Column(db.Integer, default=0)

    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Fleet {self.mission} from {self.start_planet_id} to {self.target_planet_id}>'
