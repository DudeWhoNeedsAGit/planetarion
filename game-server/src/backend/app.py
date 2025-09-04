from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import get_config
from .database import db, migrate
from .services.scheduler import GameScheduler

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt = JWTManager(app)

    # Initialize scheduler
    scheduler = GameScheduler()
    scheduler.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.planets import planets_bp
    from .routes.fleet import fleet_mgmt_bp
    from .routes.shipyard import shipyard_bp
    from .routes.static import static_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(planets_bp)
    app.register_blueprint(fleet_mgmt_bp)
    app.register_blueprint(shipyard_bp)
    app.register_blueprint(static_bp)

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})

    # Manual tick endpoint (for testing)
    @app.route('/api/tick', methods=['POST'])
    def manual_tick():
        from .services.tick import run_tick
        with app.app_context():
            run_tick()
        return jsonify({'message': 'Manual tick executed successfully'})

    # Start scheduler when app starts (only in development/testing)
    if app.config['FLASK_ENV'] in ['development', 'testing']:
        with app.app_context():
            db.create_all()
            scheduler.start()
            app.logger.info("Application started successfully")

    return app
