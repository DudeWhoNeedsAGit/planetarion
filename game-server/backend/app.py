from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv
import bcrypt

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

# Import models
from models import User, Planet, Fleet, Alliance, TickLog

@app.route('/')
def hello():
    return {'message': 'Planetarion Game Server API'}

@app.route('/health')
def health():
    return {'status': 'healthy'}

# Register blueprints after all models are defined
def register_blueprints():
    from routes.users import users_bp
    from routes.planets import planets_bp
    from routes.auth import auth_bp
    from routes.planet_management import planet_mgmt_bp
    app.register_blueprint(users_bp)
    app.register_blueprint(planets_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(planet_mgmt_bp)

register_blueprints()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
