import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from flask import Flask
from database import db
from models import User, Planet, Fleet, Alliance, TickLog
from flask_jwt_extended import JWTManager

class TestStaticFileServing:
    """Test cases for static file serving functionality"""

    @classmethod
    def setup_class(cls):
        """Set up test Flask app"""
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        cls.app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'

        db.init_app(cls.app)
        jwt = JWTManager(cls.app)

        # Import and register routes
        from routes.auth import auth_bp
        from routes.planet_user import planet_mgmt_bp
        from routes.fleet import fleet_mgmt_bp
        from routes.shipyard import shipyard_bp
        cls.app.register_blueprint(auth_bp)
        cls.app.register_blueprint(planet_mgmt_bp)
        cls.app.register_blueprint(fleet_mgmt_bp)
        cls.app.register_blueprint(shipyard_bp)

        # Add static file routes
        @cls.app.route('/static/<path:path>')
        def serve_static(path):
            """Serve React static files"""
            import os
            # Use absolute path to avoid relative path issues
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/build/static'))
            try:
                from flask import send_from_directory
                return send_from_directory(static_dir, path)
            except FileNotFoundError:
                from flask import jsonify
                return jsonify({'error': 'Static file not found'}), 404

        @cls.app.route('/dashboard')
        def serve_dashboard():
            """Serve the React dashboard"""
            from flask import send_from_directory
            return send_from_directory('../../frontend/build', 'index.html')

        @cls.app.route('/health')
        def health():
            return {'status': 'healthy'}

        with cls.app.app_context():
            db.create_all()

    def test_css_file_served(self):
        """Test that CSS files are served correctly"""
        with self.app.test_client() as client:
            response = client.get('/static/css/main.1c4a9c11.css')

            assert response.status_code == 200
            assert 'text/css' in response.content_type
            assert len(response.get_data()) > 0

    def test_js_file_served(self):
        """Test that JavaScript files are served correctly"""
        with self.app.test_client() as client:
            response = client.get('/static/js/main.84284f6f.js')

            assert response.status_code == 200
            assert 'application/javascript' in response.content_type
            assert len(response.get_data()) > 0

    def test_static_file_not_found(self):
        """Test that non-existent static files return 404"""
        with self.app.test_client() as client:
            response = client.get('/static/css/nonexistent.css')

            assert response.status_code == 404
            assert b'Static file not found' in response.get_data()

    def test_dashboard_route_serves_index(self):
        """Test that /dashboard serves the React index.html"""
        with self.app.test_client() as client:
            response = client.get('/dashboard')

            assert response.status_code == 200
            assert b'Planetarion' in response.get_data()

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        with self.app.test_client() as client:
            response = client.get('/health')

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'

    def test_static_files_exist(self):
        """Test that static files actually exist on disk"""
        static_dir = Path(__file__).parent.parent.parent / 'frontend' / 'build' / 'static'

        css_file = static_dir / 'css' / 'main.1c4a9c11.css'
        js_file = static_dir / 'js' / 'main.84284f6f.js'

        assert css_file.exists(), f"CSS file does not exist: {css_file}"
        assert css_file.stat().st_size > 0, f"CSS file is empty: {css_file}"

        assert js_file.exists(), f"JS file does not exist: {js_file}"
        assert js_file.stat().st_size > 0, f"JS file is empty: {js_file}"

    def test_static_directory_structure(self):
        """Test that the static directory structure is correct"""
        static_dir = Path(__file__).parent.parent.parent / 'frontend' / 'build' / 'static'

        assert static_dir.exists(), "Static directory does not exist"
        assert (static_dir / 'css').exists(), "CSS directory does not exist"
        assert (static_dir / 'js').exists(), "JS directory does not exist"

        # Check that we have the expected files
        css_files = list((static_dir / 'css').glob('*.css'))
        js_files = list((static_dir / 'js').glob('*.js'))

        assert len(css_files) > 0, "No CSS files found"
        assert len(js_files) > 0, "No JS files found"
