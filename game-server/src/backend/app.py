from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import get_config
from .database import db, migrate
from .services.scheduler import GameScheduler

def create_app(config_name=None):
    """Application factory pattern"""
    print("🚀 STARTING BACKEND APPLICATION...")
    print(f"📋 Config name: {config_name}")

    try:
        print("🏗️ Creating Flask app...")
        app = Flask(__name__)
        print("✅ Flask app created")

        # Load configuration
        print("⚙️ Loading configuration...")
        config_class = get_config(config_name)
        app.config.from_object(config_class)
        print(f"✅ Configuration loaded: {config_class.__name__}")
        print(f"📊 FLASK_ENV: {app.config.get('FLASK_ENV')}")
        print(f"🗄️ DATABASE_URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")

        # Initialize extensions
        print("🔧 Initializing database...")
        db.init_app(app)
        print("✅ Database initialized")

        print("🔄 Initializing migrate...")
        migrate.init_app(app, db)
        print("✅ Migrate initialized")

        print("🌐 Initializing CORS...")
        CORS(app, origins=app.config['CORS_ORIGINS'])
        print("✅ CORS initialized")

        print("🔐 Initializing JWT...")
        jwt = JWTManager(app)
        print("✅ JWT initialized")

        # Initialize scheduler
        print("⏰ Initializing scheduler...")
        scheduler = GameScheduler()
        scheduler.init_app(app)
        print("✅ Scheduler initialized")

        # Register blueprints
        print("📦 Registering blueprints...")
        from .routes.auth import auth_bp
        from .routes.planets import planets_bp
        from .routes.fleet import fleet_mgmt_bp
        from .routes.shipyard import shipyard_bp
        from .routes.planet_user import planet_mgmt_bp
        from .routes.users import users_bp
        from .routes.static import static_bp
        from .routes.populate import populate_bp

        app.register_blueprint(auth_bp)
        print("✅ Auth blueprint registered")

        app.register_blueprint(planets_bp)
        print("✅ Planets blueprint registered")

        app.register_blueprint(fleet_mgmt_bp)
        print("✅ Fleet blueprint registered")

        app.register_blueprint(shipyard_bp)
        print("✅ Shipyard blueprint registered")

        app.register_blueprint(planet_mgmt_bp)
        print("✅ Planet management blueprint registered")

        app.register_blueprint(users_bp)
        print("✅ Users blueprint registered")

        app.register_blueprint(static_bp)
        print("✅ Static blueprint registered")

        app.register_blueprint(populate_bp)
        print("✅ Populate blueprint registered")

        # Health check endpoint
        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy'})

        # Manual tick endpoint (for testing)
        @app.route('/api/tick', methods=['POST'])
        def manual_tick():
            from .services.tick import run_tick
            with app.app_context():
                changes = run_tick()
            return jsonify({
                'message': 'Manual tick executed successfully',
                'changes': changes
            })

        # Debug route to check URL matching
        @app.route('/debug/routes')
        def debug_routes():
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(str(rule))
            return jsonify({'routes': routes})

        # Debug route to check database connection
        @app.route('/api/debug/db')
        def debug_database():
            from backend.database import db
            return jsonify({
                'database_uri': str(db.engine.url),
                'database_type': str(db.engine.url).split(':')[0] if ':' in str(db.engine.url) else 'unknown'
            })

        # Catch-all debug route
        @app.before_request
        def debug_request():
            from flask import request
            if request.path.startswith('/static/'):
                print(f"DEBUG APP: Request path: {request.path}")
                print(f"DEBUG APP: Request method: {request.method}")
                print(f"DEBUG APP: Matched endpoint: {request.endpoint}")

        # Start scheduler when app starts (only in development)
        print(f"🎯 Environment: {app.config['FLASK_ENV']}")
        if app.config['FLASK_ENV'] == 'development':
            print("🗄️ Creating database tables...")
            with app.app_context():
                db.create_all()
                print("✅ Database tables created")

                print("⏰ Starting scheduler...")
                scheduler.start()
                print("✅ Scheduler started")

                app.logger.info("Application started successfully")
                print("🎉 APPLICATION STARTED SUCCESSFULLY!")

        elif app.config['FLASK_ENV'] == 'testing':
            print("🧪 Setting up test database...")
            with app.app_context():
                db.create_all()
                print("✅ Test database tables created")

                app.logger.info("Test application started successfully")
                print("🧪 TEST APPLICATION STARTED SUCCESSFULLY!")

        return app

    except Exception as e:
        print(f"❌ CRITICAL ERROR during app creation: {e}")
        print("🔍 Full traceback:")
        import traceback
        traceback.print_exc()
        raise
