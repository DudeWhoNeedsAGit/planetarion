from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os
from dotenv import load_dotenv
import bcrypt
import atexit

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/planetarion')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = 60  # 1 hour

# Initialize extensions
from database import db, migrate
db.init_app(app)
migrate.init_app(app, db)
CORS(app)
jwt = JWTManager(app)

# Initialize scheduler
scheduler = BackgroundScheduler()

# Import models
from models import User, Planet, Fleet, Alliance, TickLog

@app.route('/')
def hello():
    return {'message': 'Planetarion Game Server API'}

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/api/tick', methods=['POST'])
def manual_tick():
    """Admin endpoint to manually trigger a tick (for testing/debugging)"""
    # In production, this should have admin authentication
    # For now, it's open for development purposes

    # Simple tick logic - increment resources for all planets
    planets = Planet.query.all()
    tick_changes = []

    for planet in planets:
        # Calculate production for this tick (simplified - 1 hour worth)
        metal_produced = planet.metal_mine * 30
        crystal_produced = planet.crystal_mine * 20
        deuterium_produced = planet.deuterium_synthesizer * 10

        # Update planet resources
        planet.metal += metal_produced
        planet.crystal += crystal_produced
        planet.deuterium += deuterium_produced

        tick_changes.append({
            'planet_id': planet.id,
            'metal_change': metal_produced,
            'crystal_change': crystal_produced,
            'deuterium_change': deuterium_produced
        })

    db.session.commit()

    return jsonify({
        'message': 'Manual tick executed successfully',
        'changes': tick_changes
    })

# Register blueprints after all models are defined
def register_blueprints():
    from routes.users import users_bp
    from routes.planets import planets_bp
    from routes.auth import auth_bp
    from routes.planet_management import planet_mgmt_bp
    from routes.fleet_management import fleet_mgmt_bp
    app.register_blueprint(users_bp)
    app.register_blueprint(planets_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(planet_mgmt_bp)
    app.register_blueprint(fleet_mgmt_bp)

register_blueprints()

def start_scheduler():
    """Start the tick scheduler"""
    from services.tick import run_tick

    # Add tick job to run every 5 minutes
    scheduler.add_job(
        func=run_tick,
        trigger=IntervalTrigger(minutes=5),
        id='game_tick',
        name='Game Tick',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()
    app.logger.info("Tick scheduler started - ticks will run every 5 minutes")

def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown()
        app.logger.info("Tick scheduler shut down")

# Start scheduler when app starts
with app.app_context():
    start_scheduler()

# Register shutdown handler
atexit.register(shutdown_scheduler)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
