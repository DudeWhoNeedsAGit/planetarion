#!/usr/bin/env python3
"""
Script to populate the database with realistic test data for Planetarion game server.
Can work with either HTTP API or direct database population for testing.
"""

import requests
import sys
import os
import time

def populate_via_api():
    """Populate database via HTTP API call to running backend"""

    # Backend URL - adjust if needed
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    database_url = os.getenv('DATABASE_URL', 'sqlite:///:memory:')

    print("🌐 Connecting to running backend...")
    print(f"📍 Backend URL: {backend_url}")
    print(f"🗄️  Database URL: {database_url}")
    print(f"🔧 Environment DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')}")

    # Wait for backend to be ready
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready")
                break
        except requests.exceptions.RequestException:
            pass

        if attempt < max_attempts - 1:
            print(f"⏳ Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(2)
    else:
        print("❌ Backend not ready after maximum attempts")
        sys.exit(1)

    # Call populate endpoint
    print("📊 Calling populate endpoint...")
    try:
        response = requests.post(f"{backend_url}/populate", timeout=60)

        if response.status_code == 200:
            data = response.json()
            print("✅ Database populated successfully!")
            print(f"   👥 Users: {data.get('users', 'N/A')}")
            print(f"   🪐 Planets: {data.get('planets', 'N/A')}")
            print(f"   🚀 Fleets: {data.get('fleets', 'N/A')}")
            print(f"   🤝 Alliances: {data.get('alliances', 'N/A')}")
            print(f"   📈 Tick Logs: {data.get('tick_logs', 'N/A')}")

            # Verify e2etestuser was created with correct credentials
            print("\n Verifying e2etestuser creation...")
            try:
                users_response = requests.get(f"{backend_url}/users", timeout=5)
                if users_response.status_code == 200:
                    users = users_response.json()
                    for user in users:
                        if user.get('username') == 'e2etestuser':
                            print("   ✅ e2etestuser found!")
                            print(f"      ID: {user.get('id')}")
                            print(f"      Email: {user.get('email')}")
                            print("   🔑 Test credentials: e2etestuser / testpassword123")
                            break
                    else:
                        print("   ❌ e2etestuser not found after population!")
                else:
                    print(f"   ❌ Could not verify users: {users_response.status_code}")
            except Exception as e:
                print(f"   ❌ Error verifying user: {e}")

            return True
        else:
            print(f"❌ Populate request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        return False

def populate_direct():
    """Populate database directly using Flask app with testing configuration"""
    print("🧪 Using direct database population for testing...")

    # Add the src directory to Python path for imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    src_path = project_root / 'src'
    sys.path.insert(0, str(src_path))

    try:
        # Import Flask app and configuration
        from backend.app import create_app
        from backend.config import TestingConfig

        print("🏗️ Creating Flask app with testing configuration...")
        app = create_app(TestingConfig)

        with app.app_context():
            print("📊 Populating database directly...")

            # Import populate function
            from backend.routes.populate import populate_database

            # Create a mock request object for deterministic mode
            from unittest.mock import Mock
            mock_request = Mock()
            mock_request.args = {'deterministic': 'true'}

            # Monkey patch the request object
            import backend.routes.populate
            original_request = getattr(backend.routes.populate, 'request', None)
            backend.routes.populate.request = mock_request

            try:
                # Call the populate function directly
                result = populate_database()
                if result[1] == 200:
                    data = result[0].get_json()
                    print("✅ Database populated successfully!")
                    print(f"   👥 Users: {data.get('users', 'N/A')}")
                    print(f"   🪐 Planets: {data.get('planets', 'N/A')}")
                    print(f"   🚀 Fleets: {data.get('fleets', 'N/A')}")
                    print(f"   🤝 Alliances: {data.get('alliances', 'N/A')}")
                    print(f"   📈 Tick Logs: {data.get('tick_logs', 'N/A')}")
                    return True
                else:
                    print(f"❌ Populate failed: {result[0].get_json()}")
                    return False
            finally:
                # Restore original request object
                if original_request is not None:
                    backend.routes.populate.request = original_request

    except Exception as e:
        print(f"❌ Direct population failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Check if we should use direct population (for testing)
    use_direct = os.getenv('POPULATE_DIRECT', 'false').lower() == 'true'

    if use_direct:
        success = populate_direct()
    else:
        success = populate_via_api()

    if success:
        print("🎉 Test data population completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test data population failed!")
        sys.exit(1)
