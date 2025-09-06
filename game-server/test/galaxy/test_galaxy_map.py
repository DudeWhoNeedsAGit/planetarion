#!/usr/bin/env python3
"""
Simple test script for Galaxy Map functionality
Tests the basic galaxy map API endpoints to ensure colonization is possible
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_planets_endpoint():
    """Test the basic planets endpoint"""
    print("🧪 Testing /api/planets endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/api/planets")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            planets = response.json()
            print(f"   ✅ Found {len(planets)} planets in database")
            if planets:
                print(f"   📍 Sample planet: {planets[0].get('name', 'Unknown')} at {planets[0].get('coordinates', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_galaxy_system_endpoint():
    """Test galaxy system endpoint"""
    print("\n🧪 Testing /api/galaxy/system/100/200/300 endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/api/galaxy/system/100/200/300")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            system_planets = response.json()
            print(f"   ✅ Found {len(system_planets)} planets in system 100:200:300")
            return True
        else:
            print(f"   ❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_nearby_systems_endpoint():
    """Test nearby systems endpoint"""
    print("\n🧪 Testing /api/galaxy/nearby/100/200/300 endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/api/galaxy/nearby/100/200/300")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            nearby_systems = response.json()
            print(f"   ✅ Found {len(nearby_systems)} nearby systems")
            if nearby_systems:
                sample = nearby_systems[0]
                print(f"   🌌 Sample system: {sample.get('x', '?')}:{sample.get('y', '?')}:{sample.get('z', '?')} (explored: {sample.get('explored', 'Unknown')})")
            return True
        else:
            print(f"   ❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Galaxy Map Functionality Test")
    print("=" * 40)

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/planets", timeout=5)
    except requests.exceptions.RequestException:
        print("❌ Backend is not running or not accessible")
        print("   Make sure to run: cd game-server && docker compose up -d")
        sys.exit(1)

    # Run tests
    tests = [
        test_planets_endpoint,
        test_galaxy_system_endpoint,
        test_nearby_systems_endpoint
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Galaxy Map is working! You can now colonize planets.")
        print("\n💡 Next steps:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Navigate to the Galaxy Map")
        print("   3. Look for unexplored systems to colonize")
        return 0
    else:
        print("⚠️  Some tests failed. Check the galaxy map functionality.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
