from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import os
try:
    from flasgger import Swagger
except Exception:  # pragma: no cover
    Swagger = None
import json
from .config import get_config
from .database import db, migrate
from .services.scheduler import GameScheduler
from .services.event_bus import EventMessage, event_bus

def create_app(config_name=None):
    """Application factory pattern"""
    print("🚀 STARTING BACKEND APPLICATION...")
    print(f"📋 Config name: {config_name}")

    try:
        print("🏗️ Creating Flask app...")
        app = Flask(__name__)
        print("✅ Flask app created")

        def _display_db_uri(uri: str | None) -> str:
            if not uri:
                return "Not set"
            # Avoid leaking local absolute paths in logs (public repo friendliness).
            # Keep enough info to understand which DB file is in use.
            if uri.startswith("sqlite:////"):
                raw = uri[len("sqlite:////"):]
                marker = "/instance/"
                idx = raw.rfind(marker)
                if idx != -1:
                    suffix = raw[idx + 1 :]  # instance/...
                    return f"sqlite:///./{suffix}"
                return f"sqlite:///…/{os.path.basename(raw)}"
            return uri

        # Load configuration
        print("⚙️ Loading configuration...")
        config_class = get_config(config_name)
        app.config.from_object(config_class)
        print(f"✅ Configuration loaded: {config_class.__name__}")
        print(f"📊 FLASK_ENV: {app.config.get('FLASK_ENV')}")
        print(f"🗄️ DATABASE_URL: {_display_db_uri(app.config.get('SQLALCHEMY_DATABASE_URI'))}")

        # SQLite tuning: reduce "database is locked" errors under concurrent requests (Playwright, dev UI).
        # - WAL allows concurrent readers + a single writer.
        # - busy_timeout makes writes wait rather than immediately failing.
        # - check_same_thread=False lets us share connections across threads (Werkzeug dev server).
        uri = str(app.config.get("SQLALCHEMY_DATABASE_URI") or "")
        if uri.startswith("sqlite:"):
            app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {})
            engine_opts = app.config["SQLALCHEMY_ENGINE_OPTIONS"] or {}
            engine_opts.setdefault("connect_args", {})
            engine_opts["connect_args"].setdefault("timeout", 30)
            engine_opts["connect_args"].setdefault("check_same_thread", False)
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

            @event.listens_for(Engine, "connect")
            def _sqlite_pragmas(dbapi_connection, _connection_record):  # pragma: no cover
                try:
                    import sqlite3

                    if not isinstance(dbapi_connection, sqlite3.Connection):
                        return
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.execute("PRAGMA temp_store=MEMORY;")
                    cursor.execute("PRAGMA busy_timeout=30000;")
                    cursor.close()
                except Exception:
                    return

        # Initialize extensions
        print("🔧 Initializing database...")
        db.init_app(app)
        print("✅ Database initialized")

        # Import models BEFORE creating tables (critical for SQLAlchemy)
        print("📋 Importing models for table creation...")
        from .models import User, Planet, Fleet, Alliance, TickLog, EspionageReport
        print("✅ Models imported successfully")

        # Event-driven UI: broadcast significant TickLog rows to connected SSE clients.
        # Use low-level SQL via the connection to avoid ORM/session recursion in flush hooks.
        def _broadcast_ticklog(_mapper, connection, target):  # pragma: no cover
            try:
                event_type = (getattr(target, "event_type", None) or "").strip()
                event_desc = (getattr(target, "event_description", None) or "").strip()
                if not event_type and not event_desc:
                    return

                planet_id = getattr(target, "planet_id", None)
                fleet_id = getattr(target, "fleet_id", None)

                user_ids = set()
                if planet_id:
                    res = connection.execute(text("SELECT user_id FROM planets WHERE id = :id"), {"id": int(planet_id)}).fetchone()
                    if res and res[0] is not None:
                        user_ids.add(int(res[0]))
                if fleet_id:
                    res = connection.execute(text("SELECT user_id FROM fleets WHERE id = :id"), {"id": int(fleet_id)}).fetchone()
                    if res and res[0] is not None:
                        user_ids.add(int(res[0]))

                if not user_ids:
                    return

                ts = getattr(target, "timestamp", None)
                ts_iso = ts.isoformat() + "Z" if ts else None

                payload = {
                    "id": int(getattr(target, "id", 0) or 0),
                    "tick_number": int(getattr(target, "tick_number", 0) or 0),
                    "timestamp": ts_iso,
                    "planet_id": int(planet_id) if planet_id else None,
                    "fleet_id": int(fleet_id) if fleet_id else None,
                    "event_type": event_type or None,
                    "event_description": event_desc or None,
                }
                msg = EventMessage(event="activity", data=payload, id=payload["id"] or None)
                for uid in user_ids:
                    event_bus.publish(uid, msg)
            except Exception:
                # Never break the main transaction path.
                return

        try:
            # Avoid duplicate listeners when create_app() is called multiple times (tests, dev reloader).
            if not event.contains(TickLog, "after_insert", _broadcast_ticklog):
                event.listen(TickLog, "after_insert", _broadcast_ticklog)
        except Exception:
            pass

        print("🔄 Initializing migrate...")
        migrate.init_app(app, db)
        print("✅ Migrate initialized")

        print("🌐 Initializing CORS...")
        cors_origins = app.config.get('CORS_ORIGINS')
        # In testing, allow all origins so the React dev server (localhost:3000) can call the backend
        # without depending on environment-specific origin lists.
        if app.config.get('TESTING') or app.config.get('FLASK_ENV') == 'testing':
            cors_origins = '*'
        CORS(app, origins=cors_origins)
        print(f"✅ CORS initialized (origins={cors_origins})")

        print("🔐 Initializing JWT...")
        jwt = JWTManager(app)
        print("✅ JWT initialized")

        # Initialize Swagger documentation (optional in minimal test environments)
        if Swagger is not None:
            print("📚 Initializing Swagger...")
            swagger_config = {
                "headers": [],
                "specs": [
                    {
                        "endpoint": 'apispec',
                        "route": '/apispec.json',
                        "rule_filter": lambda rule: True,
                        "model_filter": lambda _tag: True,
                    }
                ],
                "static_url_path": "/flasgger_static",
                "swagger_ui": True,
                "specs_route": "/apidocs/"
            }
            swagger = Swagger(app, config=swagger_config)
            print("✅ Swagger initialized")
        else:
            swagger = None
            print("⚠️ Swagger not available (flasgger not installed)")

        # OpenAPI export endpoint
        @app.route("/export_openapi")
        def export_openapi():
            if swagger is None:
                return jsonify({"error": "Swagger not available"}), 501
            return json.dumps(swagger.get_apispecs())

        # Initialize scheduler
        print("⏰ Initializing scheduler...")
        scheduler = GameScheduler()
        scheduler.init_app(app)
        app.extensions['game_scheduler'] = scheduler
        print("✅ Scheduler initialized")
        try:
            print(f"⏲️  TICK_SCHEDULER_ENABLED: {bool(app.config.get('TICK_SCHEDULER_ENABLED'))}")
            print(f"⏲️  TICK_SCHEDULER_INTERVAL_SECONDS: {app.config.get('TICK_SCHEDULER_INTERVAL_SECONDS')}")
        except Exception:
            pass

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
        from .routes.chat import chat_bp
        from .routes import chat as chat_routes
        from .routes.research import research_bp
        from .routes.combat import combat_bp
        from .routes.admin import admin_bp
        from .routes.espionage import espionage_bp
        from .routes.events import events_bp

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

        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        print("✅ Chat blueprint registered")
        chat_routes.user_message_counts.clear()

        app.register_blueprint(research_bp)
        print("✅ Research blueprint registered")

        app.register_blueprint(combat_bp)
        print("✅ Combat blueprint registered")

        app.register_blueprint(espionage_bp)
        print("✅ Espionage blueprint registered")

        app.register_blueprint(admin_bp)
        print("✅ Admin blueprint registered")

        app.register_blueprint(events_bp)
        print("✅ Events blueprint registered")

        # Health check endpoint
        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy'})

        # Manual tick endpoint (for testing)
        @app.route('/api/tick', methods=['POST'])
        def manual_tick():
            from .services.tick import run_tick
            # Already running inside a request/app context; avoid creating a nested
            # app context which would create a separate scoped DB session and can
            # lead to stale reads during tests.
            changes = run_tick()
            return jsonify({
                'message': 'Manual tick executed successfully',
                'changes': changes
            })

        @app.route('/api/tick/logs', methods=['GET'])
        @jwt_required()
        def get_tick_logs():
            """Return recent TickLog entries relevant to the authenticated user."""
            from sqlalchemy import or_, and_
            from .models import Planet, Fleet, TickLog

            user_id = int(get_jwt_identity())
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            include_resource = request.args.get('include_resource', '0').lower() in ('1', 'true', 'yes')

            planet_ids = [pid for (pid,) in Planet.query.filter_by(user_id=user_id).with_entities(Planet.id).all()]
            fleet_ids = [fid for (fid,) in Fleet.query.filter_by(user_id=user_id).with_entities(Fleet.id).all()]

            conditions = []
            if planet_ids:
                conditions.append(TickLog.planet_id.in_(planet_ids))
            if fleet_ids:
                conditions.append(TickLog.fleet_id.in_(fleet_ids))

            if not conditions:
                return jsonify({'logs': [], 'total': 0, 'limit': limit, 'offset': offset})

            query = TickLog.query.filter(or_(*conditions))
            if not include_resource:
                # Default: hide per-tick resource production rows (which have no event_type/description and pollute the UI).
                # UI can explicitly request them with `include_resource=1`.
                query = query.filter(
                    or_(
                        and_(TickLog.event_type.isnot(None), TickLog.event_type != ''),
                        and_(TickLog.event_description.isnot(None), TickLog.event_description != ''),
                    )
                )

            logs = (
                query
                .order_by(TickLog.timestamp.desc(), TickLog.id.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            def serialize_log(log):
                planet = Planet.query.get(log.planet_id) if log.planet_id else None
                fleet = Fleet.query.get(log.fleet_id) if log.fleet_id else None
                return {
                    'id': log.id,
                    'tick_number': log.tick_number,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'planet': {
                        'id': planet.id,
                        'name': planet.name,
                        'coordinates': f"{planet.x}:{planet.y}:{planet.z}",
                    } if planet else None,
                    'fleet': {
                        'id': fleet.id,
                        'mission': fleet.mission,
                        'status': fleet.status,
                    } if fleet else None,
                    'event_type': log.event_type,
                    'event_description': log.event_description,
                    'resource_changes': {
                        'metal': int(log.metal_change or 0),
                        'crystal': int(log.crystal_change or 0),
                        'deuterium': int(log.deuterium_change or 0),
                    } if (log.metal_change or log.crystal_change or log.deuterium_change) else None,
                }

            return jsonify({
                'logs': [serialize_log(log) for log in logs],
                'total': len(logs),
                'limit': limit,
                'offset': offset,
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
                try:
                    from .services.sqlite_schema import (
                        ensure_planet_storage_columns,
                        ensure_planet_trait_columns,
                        ensure_fleet_cargo_columns,
                        ensure_user_lifecycle_columns,
                        ensure_user_profile_columns,
                        ensure_user_research_queue_columns,
                        ensure_research_fraction_columns,
                        ensure_research_tech_columns,
                        ensure_commander_xp_event_table,
                        ensure_pirate_ai_state_table,
                    )
                    ensure_planet_storage_columns(db.engine)
                    ensure_planet_trait_columns(db.engine)
                    ensure_fleet_cargo_columns(db.engine)
                    ensure_user_lifecycle_columns(db.engine)
                    ensure_user_profile_columns(db.engine)
                    ensure_user_research_queue_columns(db.engine)
                    ensure_research_fraction_columns(db.engine)
                    ensure_research_tech_columns(db.engine)
                    ensure_commander_xp_event_table(db.engine)
                    ensure_pirate_ai_state_table(db.engine)
                    print("✅ SQLite schema ensured (planet storage columns)")
                except Exception as e:
                    print(f"⚠️ SQLite schema ensure failed: {e}")

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
                try:
                    from .services.sqlite_schema import (
                        ensure_planet_storage_columns,
                        ensure_planet_trait_columns,
                        ensure_fleet_cargo_columns,
                        ensure_user_lifecycle_columns,
                        ensure_user_profile_columns,
                        ensure_user_research_queue_columns,
                        ensure_research_fraction_columns,
                        ensure_research_tech_columns,
                        ensure_commander_xp_event_table,
                        ensure_pirate_ai_state_table,
                    )
                    ensure_planet_storage_columns(db.engine)
                    ensure_planet_trait_columns(db.engine)
                    ensure_fleet_cargo_columns(db.engine)
                    ensure_user_lifecycle_columns(db.engine)
                    ensure_user_profile_columns(db.engine)
                    ensure_user_research_queue_columns(db.engine)
                    ensure_research_fraction_columns(db.engine)
                    ensure_research_tech_columns(db.engine)
                    ensure_commander_xp_event_table(db.engine)
                    ensure_pirate_ai_state_table(db.engine)
                except Exception:
                    # Tests recreate DB frequently; missing migration isn't fatal here.
                    pass

                app.logger.info("Test application started successfully")
                print("🧪 TEST APPLICATION STARTED SUCCESSFULLY!")

                # Optional: enable automatic ticks for manual play in test-env.
                if app.config.get("TICK_SCHEDULER_ENABLED"):
                    print("⏰ Starting scheduler (testing env; enabled by PLANETARION_TICK_SCHEDULER_ENABLED)...")
                    scheduler.start()
                    print("✅ Scheduler started")
                else:
                    print("⏸️  Scheduler not started in testing (set PLANETARION_TICK_SCHEDULER_ENABLED=true to enable auto ticks).")

        return app

    except Exception as e:
        print(f"❌ CRITICAL ERROR during app creation: {e}")
        print("🔍 Full traceback:")
        import traceback
        traceback.print_exc()
        raise
