#!/usr/bin/env python3
"""
Simple test to verify 5-second tick system is working.
This test connects to the running server and checks if resources increase over time.
"""

import time
import requests
import json

def test_5second_ticks():
    """Test that resources increase with 5-second ticks"""

    # Server should be running on localhost:5001
    base_url = "http://localhost:5001"

    print("Testing 5-second tick system...")
    print("=" * 50)

    # First, create a test user and planet
    print("1. Creating test user...")
    register_data = {
        "username": "test_tick_user",
        "email": "test@example.com",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        if response.status_code != 200:
            print(f"Failed to register user: {response.text}")
            return False
        print("✓ User registered successfully")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        print("Make sure the server is running with: cd game-server/backend && python app.py")
        return False

    # Login to get token
    print("2. Logging in...")
    login_data = {
        "username": "test_tick_user",
        "password": "testpass123"
    }

    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Failed to login: {response.text}")
        return False

    token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    print("✓ Login successful")

    # Get initial planet data
    print("3. Getting initial planet data...")
    response = requests.get(f"{base_url}/api/planet", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get planets: {response.text}")
        return False

    planets = response.json()
    if not planets:
        print("No planets found")
        return False

    planet = planets[0]
    initial_metal = planet['resources']['metal']
    initial_crystal = planet['resources']['crystal']
    initial_deuterium = planet['resources']['deuterium']

    print(f"Initial resources - Metal: {initial_metal}, Crystal: {initial_crystal}, Deuterium: {initial_deuterium}")

    # Wait for 3 ticks (15 seconds)
    print("4. Waiting 15 seconds for 3 automatic ticks...")
    time.sleep(15)

    # Get updated planet data
    print("5. Checking resource increases...")
    response = requests.get(f"{base_url}/api/planet", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get updated planets: {response.text}")
        return False

    updated_planets = response.json()
    updated_planet = updated_planets[0]

    final_metal = updated_planet['resources']['metal']
    final_crystal = updated_planet['resources']['crystal']
    final_deuterium = updated_planet['resources']['deuterium']

    print(f"Final resources - Metal: {final_metal}, Crystal: {final_crystal}, Deuterium: {final_deuterium}")

    # Check if resources increased
    metal_increase = final_metal - initial_metal
    crystal_increase = final_crystal - initial_crystal
    deuterium_increase = final_deuterium - initial_deuterium

    print(f"Resource increases - Metal: {metal_increase}, Crystal: {crystal_increase}, Deuterium: {deuterium_increase}")

    # Verify increases
    success = True
    if metal_increase <= 0:
        print("❌ Metal did not increase")
        success = False
    else:
        print("✅ Metal increased correctly")

    if crystal_increase <= 0:
        print("❌ Crystal did not increase")
        success = False
    else:
        print("✅ Crystal increased correctly")

    if deuterium_increase <= 0:
        print("❌ Deuterium did not increase")
        success = False
    else:
        print("✅ Deuterium increased correctly")

    if success:
        print("\n🎉 SUCCESS: 5-second tick system is working!")
        print("Resources are being generated automatically every 5 seconds.")
        return True
    else:
        print("\n❌ FAILURE: Tick system is not working properly")
        return False

if __name__ == "__main__":
    test_5second_ticks()
