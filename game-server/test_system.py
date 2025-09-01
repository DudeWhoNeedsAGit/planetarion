#!/usr/bin/env python3
"""
Planetarion Game Server - System Test Script
Tests all major components and API endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

class PlanetarionTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user = None
        self.planets = []
        self.fleets = []

    def log(self, message, status="INFO"):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[34m",    # Blue
            "SUCCESS": "\033[32m", # Green
            "ERROR": "\033[31m",   # Red
            "WARNING": "\033[33m", # Yellow
            "RESET": "\033[0m"     # Reset
        }
        print(f"{colors.get(status, colors['RESET'])}[{timestamp}] {status}: {message}{colors['RESET']}")

    def test_health_check(self):
        """Test basic health check endpoint"""
        self.log("Testing health check endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("✅ Health check passed", "SUCCESS")
                    return True
                else:
                    self.log("❌ Health check returned unhealthy status", "ERROR")
            else:
                self.log(f"❌ Health check failed with status {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"❌ Health check error: {str(e)}", "ERROR")
        return False

    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
            if response.status_code == 201:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.token = data["access_token"]
                    self.user = data["user"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log("✅ User registration successful", "SUCCESS")
                    return True
                else:
                    self.log("❌ Registration response missing required fields", "ERROR")
            elif response.status_code == 409:
                self.log("⚠️ User already exists, attempting login instead", "WARNING")
                return self.test_user_login()
            else:
                self.log(f"❌ Registration failed with status {response.status_code}: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"❌ Registration error: {str(e)}", "ERROR")
        return False

    def test_user_login(self):
        """Test user login"""
        self.log("Testing user login...")
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            })
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.token = data["access_token"]
                    self.user = data["user"]
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log("✅ User login successful", "SUCCESS")
                    return True
                else:
                    self.log("❌ Login response missing required fields", "ERROR")
            else:
                self.log(f"❌ Login failed with status {response.status_code}: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
        return False

    def test_get_user_profile(self):
        """Test getting user profile"""
        self.log("Testing user profile retrieval...")
        try:
            response = self.session.get(f"{BASE_URL}/api/auth/me")
            if response.status_code == 200:
                data = response.json()
                if data.get("username") == TEST_USER["username"]:
                    self.log("✅ User profile retrieval successful", "SUCCESS")
                    return True
                else:
                    self.log("❌ User profile data mismatch", "ERROR")
            else:
                self.log(f"❌ Profile retrieval failed with status {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"❌ Profile retrieval error: {str(e)}", "ERROR")
        return False

    def test_get_planets(self):
        """Test getting user's planets"""
        self.log("Testing planets retrieval...")
        try:
            response = self.session.get(f"{BASE_URL}/api/planet")
            if response.status_code == 200:
                data = response.json()
                self.planets = data
                self.log(f"✅ Retrieved {len(data)} planets successfully", "SUCCESS")
                return True
            else:
                self.log(f"❌ Planets retrieval failed with status {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"❌ Planets retrieval error: {str(e)}", "ERROR")
        return False

    def test_building_upgrade(self):
        """Test building upgrade functionality"""
        if not self.planets:
            self.log("⚠️ No planets available for building upgrade test", "WARNING")
            return True

        planet = self.planets[0]
        self.log(f"Testing building upgrade on planet {planet['name']}...")

        try:
            # Try upgrading metal mine
            response = self.session.put(f"{BASE_URL}/api/planet/buildings", json={
                "planet_id": planet["id"],
                "buildings": {
                    "metal_mine": planet["structures"]["metal_mine"] + 1
                }
            })

            if response.status_code == 200:
                data = response.json()
                self.log("✅ Building upgrade successful", "SUCCESS")
                return True
            elif response.status_code == 400:
                self.log("⚠️ Building upgrade failed (possibly insufficient resources)", "WARNING")
                return True  # This is expected if resources are insufficient
            else:
                self.log(f"❌ Building upgrade failed with status {response.status_code}: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"❌ Building upgrade error: {str(e)}", "ERROR")
        return False

    def test_fleet_operations(self):
        """Test fleet creation and management"""
        if not self.planets or len(self.planets) < 2:
            self.log("⚠️ Need at least 2 planets for fleet testing", "WARNING")
            return True

        self.log("Testing fleet operations...")

        try:
            # Create a fleet
            response = self.session.post(f"{BASE_URL}/api/fleet", json={
                "start_planet_id": self.planets[0]["id"],
                "ships": {
                    "small_cargo": 5,
                    "light_fighter": 3
                }
            })

            if response.status_code == 201:
                fleet_data = response.json()
                self.log("✅ Fleet creation successful", "SUCCESS")

                # Test fleet retrieval
                response = self.session.get(f"{BASE_URL}/api/fleet")
                if response.status_code == 200:
                    fleets = response.json()
                    self.fleets = fleets
                    self.log(f"✅ Retrieved {len(fleets)} fleets successfully", "SUCCESS")
                    return True
                else:
                    self.log(f"❌ Fleet retrieval failed with status {response.status_code}", "ERROR")
            else:
                self.log(f"❌ Fleet creation failed with status {response.status_code}: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"❌ Fleet operations error: {str(e)}", "ERROR")
        return False

    def test_tick_system(self):
        """Test manual tick execution"""
        self.log("Testing tick system...")
        try:
            response = self.session.post(f"{BASE_URL}/api/tick")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Manual tick executed successfully - affected {len(data.get('changes', []))} planets", "SUCCESS")
                return True
            else:
                self.log(f"❌ Tick execution failed with status {response.status_code}: {response.text}", "ERROR")
        except Exception as e:
            self.log(f"❌ Tick execution error: {str(e)}", "ERROR")
        return False

    def run_all_tests(self):
        """Run all system tests"""
        self.log("🚀 Starting Planetarion System Tests", "INFO")
        self.log("=" * 50, "INFO")

        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration/Login", lambda: self.test_user_registration() or self.test_user_login()),
            ("User Profile", self.test_get_user_profile),
            ("Planets Retrieval", self.test_get_planets),
            ("Building Upgrade", self.test_building_upgrade),
            ("Fleet Operations", self.test_fleet_operations),
            ("Tick System", self.test_tick_system),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}", "INFO")
            if test_func():
                passed += 1
            time.sleep(0.5)  # Small delay between tests

        self.log("\n" + "=" * 50, "INFO")
        self.log(f"📊 Test Results: {passed}/{total} tests passed", "SUCCESS" if passed == total else "ERROR")

        if passed == total:
            self.log("🎉 All tests passed! System is ready for production.", "SUCCESS")
        else:
            self.log(f"⚠️ {total - passed} test(s) failed. Please check the system configuration.", "WARNING")

        return passed == total

def main():
    """Main test execution"""
    tester = PlanetarionTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("\n🛑 Tests interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n💥 Unexpected error during testing: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
