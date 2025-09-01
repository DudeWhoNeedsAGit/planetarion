from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/planetarion')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from database import db, migrate
db.init_app(app)
migrate.init_app(app, db)
CORS(app)

# Import models
from models import User, Planet, Fleet

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
    app.register_blueprint(users_bp)
    app.register_blueprint(planets_bp)

register_blueprints()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
