import os
import pytest
from pathlib import Path

from src.backend.app import create_app
from src.config import PATHS, ensure_path_exists

class TestStaticFileServing:
    """Test cases for static file serving functionality"""

    @classmethod
    def setup_class(cls):
        """Set up test Flask app using our new app factory"""
        cls.app = create_app('testing')

        # Ensure static files exist for testing - use centralized config
        static_dir = PATHS['frontend_static']
        if not static_dir.exists():
            # Create mock static files for testing
            ensure_path_exists(static_dir)
            css_dir = PATHS['frontend_css']
            js_dir = PATHS['frontend_js']
            ensure_path_exists(css_dir)
            ensure_path_exists(js_dir)

            # Create mock files
            (css_dir / 'main.1c4a9c11.css').write_text('/* Mock CSS */')
            (js_dir / 'main.84284f6f.js').write_text('// Mock JS')

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
        static_dir = PATHS['frontend_static']

        css_file = PATHS['frontend_css'] / 'main.1c4a9c11.css'
        js_file = PATHS['frontend_js'] / 'main.84284f6f.js'

        assert css_file.exists(), f"CSS file does not exist: {css_file}"
        assert css_file.stat().st_size > 0, f"CSS file is empty: {css_file}"

        assert js_file.exists(), f"JS file does not exist: {js_file}"
        assert js_file.stat().st_size > 0, f"JS file is empty: {js_file}"

    def test_static_directory_structure(self):
        """Test that the static directory structure is correct"""
        static_dir = PATHS['frontend_static']

        assert static_dir.exists(), "Static directory does not exist"
        assert PATHS['frontend_css'].exists(), "CSS directory does not exist"
        assert PATHS['frontend_js'].exists(), "JS directory does not exist"

        # Check that we have the expected files
        css_files = list(PATHS['frontend_css'].glob('*.css'))
        js_files = list(PATHS['frontend_js'].glob('*.js'))

        assert len(css_files) > 0, "No CSS files found"
        assert len(js_files) > 0, "No JS files found"
