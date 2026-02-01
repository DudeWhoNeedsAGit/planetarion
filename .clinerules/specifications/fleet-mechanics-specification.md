# Fleet Mechanics Specification & Test Plan

## Overview

This document provides a comprehensive specification for the fleet mechanics system, including ship types, fleet operations, travel mechanics, and combat integration. The fleet system is a core gameplay mechanic that enables player expansion, resource transportation, and military operations.

## Table of Contents

1. [Fleet System Architecture](#fleet-system-architecture)
2. [Ship Types & Statistics](#ship-types--statistics)
3. [Fleet Operations](#fleet-operations)
4. [Travel Mechanics](#travel-mechanics)
5. [Combat Integration](#combat-integration)
6. [Test Infrastructure Setup](#test-infrastructure-setup)
7. [Detailed Test Plan](#detailed-test-plan)

---

## Fleet System Architecture

### Core Components

#### 1. Fleet Model
```python
class Fleet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mission = db.Column(db.String(50), default='stationed')
    status = db.Column(db.String(100), default='stationed')

    # Planet references
    start_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)
    target_planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'), nullable=False)

    # Timing
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)

    # Ship composition
    small_cargo = db.Column(db.Integer, default=0)
    large_cargo = db.Column(db.Integer, default=0)
    light_fighter = db.Column(db.Integer, default=0)
    heavy_fighter = db.Column(db.Integer, default=0)
    cruiser = db.Column(db.Integer, default=0)
    battleship = db.Column(db.Integer, default=0)
    colony_ship = db.Column(db.Integer, default=0)
    recycler = db.Column(db.Integer, default=0)

    # Relationships
    user = db.relationship('User', backref='fleets')
    start_planet = db.relationship('Planet', foreign_keys=[start_planet_id])
    target_planet = db.relationship('Planet', foreign_keys=[target_planet_id])
```

#### 2. Fleet Service Layer
```python
class FleetService:
    @staticmethod
    def create_fleet(user_id, start_planet_id, ships):
        """Create a new fleet with ship composition"""

    @staticmethod
    def send_fleet(fleet_id, target_planet_id, mission):
        """Send fleet on mission with travel calculations"""

    @staticmethod
    def calculate_fleet_speed(fleet):
        """Calculate fleet speed (slowest ship rule)"""

    @staticmethod
    def calculate_travel_time(fleet, distance):
        """Calculate travel time based on speed and distance"""
```

#### 3. Fleet Travel Service
```python
class FleetTravelService:
    @staticmethod
    def calculate_distance(start_planet, target_planet):
        """Calculate 3D distance between planets"""

    @staticmethod
    def calculate_position_at_time(fleet, current_time):
        """Calculate fleet position during travel"""

    @staticmethod
    def format_coordinates(x, y, z):
        """Format coordinates as string"""
```

---

## Ship Types & Statistics

### Ship Classifications

#### 1. Cargo Ships
- **Small Cargo**: Fast, low capacity transport
- **Large Cargo**: Slow, high capacity transport

#### 2. Fighter Ships
- **Light Fighter**: Fast, low damage combat unit
- **Heavy Fighter**: Balanced speed/damage combat unit

#### 3. Capital Ships
- **Cruiser**: Heavy combat vessel
- **Battleship**: Ultimate combat vessel

#### 4. Special Ships
- **Colony Ship**: Enables planet colonization
- **Recycler**: Collects debris from battles

### Ship Statistics Configuration

```python
# backend/config.py
SHIP_SPEEDS = {
    'small_cargo': 5000,      # Fastest ship
    'large_cargo': 7500,
    'light_fighter': 12500,
    'heavy_fighter': 10000,
    'cruiser': 15000,
    'battleship': 10000,
    'colony_ship': 2500,      # Slowest ship
    'recycler': 2000
}

FUEL_RATES = {
    'small_cargo': 1.0,
    'large_cargo': 2.5,
    'light_fighter': 1.0,
    'heavy_fighter': 2.0,
    'cruiser': 3.0,
    'battleship': 5.0,
    'colony_ship': 10.0,
    'recycler': 8.0
}

SHIP_CAPACITIES = {
    'small_cargo': 5000,
    'large_cargo': 25000,
    'colony_ship': 7500,
    # Other ships have minimal cargo capacity
}
```

### Speed Calculation System

#### Global Speed Multiplier
```python
SPEED_MULTIPLIER = 30.0  # Configurable game speed

def get_ship_speed(ship_type):
    """Get speed with global multiplier applied"""
    base_speed = SHIP_SPEEDS.get(ship_type, 5000)
    return base_speed * SPEED_MULTIPLIER
```

#### Fleet Speed (Slowest Ship Rule)
```python
def calculate_fleet_speed(fleet):
    """Fleet speed determined by slowest ship type"""
    slowest_speed = float('inf')

    for ship_type in SHIP_TYPES:
        ship_count = getattr(fleet, ship_type, 0)
        if ship_count > 0:
            ship_speed = get_ship_speed(ship_type)
            slowest_speed = min(slowest_speed, ship_speed)

    return slowest_speed if slowest_speed != float('inf') else 0
```

---

## Fleet Operations

### Mission Types

#### 1. Transport Mission
- **Purpose**: Move resources between planets
- **Requirements**: Cargo ships with available capacity
- **Validation**: Check cargo capacity vs. loaded resources

#### 2. Attack Mission
- **Purpose**: Combat operations against enemy planets
- **Requirements**: Combat ships (fighters, cruisers, battleships)
- **Validation**: Target planet ownership check

#### 3. Colonize Mission
- **Purpose**: Establish new colonies
- **Requirements**: Colony ship, unowned target planet
- **Validation**: Planet ownership and colonization requirements

#### 4. Deploy Mission
- **Purpose**: Move ships between owned planets
- **Requirements**: Any ships, owned target planet
- **Validation**: Planet ownership check

#### 5. Espionage Mission
- **Purpose**: Gather intelligence on enemy planets
- **Requirements**: Espionage probe (future implementation)
- **Validation**: Target planet visibility

#### 6. Recycle Mission
- **Purpose**: Collect debris from battlefields
- **Requirements**: Recycler ships, debris field present
- **Validation**: Debris field existence and capacity

### Fleet Status States

#### Stationed
- Fleet is docked at planet
- Available for new missions
- Ships can be added/removed

#### Traveling
- Fleet is in transit between planets
- Position updates based on travel time
- Cannot be modified during travel

#### Returning
- Fleet is returning to origin planet
- Triggered by recall or mission completion
- Position updates until arrival

#### Colonizing
- Special status for colonization missions
- Fleet remains at target until colonization completes
- Status format: `colonizing:X:Y:Z`

---

## Travel Mechanics

### Distance Calculation

#### 3D Euclidean Distance
```python
def calculate_distance(start_planet, target_planet):
    """Calculate 3D distance between planets"""
    dx = target_planet.x - start_planet.x
    dy = target_planet.y - start_planet.y
    dz = target_planet.z - start_planet.z

    return math.sqrt(dx**2 + dy**2 + dz**2)
```

### Travel Time Calculation

#### Speed-Based Travel Time
```python
def calculate_travel_time(distance, fleet_speed):
    """Calculate travel time in seconds"""
    if fleet_speed <= 0:
        return float('inf')  # Cannot travel

    # Convert to hours (game time)
    travel_hours = distance / fleet_speed

    # Apply speed multiplier and convert to real seconds
    real_seconds = (travel_hours / SPEED_MULTIPLIER) * 3600

    return int(real_seconds)
```

### Position Interpolation

#### Real-time Position Updates
```python
def calculate_position_at_time(fleet, current_time):
    """Calculate fleet position during travel"""
    if fleet.status not in ['traveling', 'returning']:
        return fleet.start_planet

    departure = fleet.departure_time
    arrival = fleet.arrival_time
    total_time = (arrival - departure).total_seconds()
    elapsed_time = (current_time - departure).total_seconds()

    if elapsed_time >= total_time:
        return fleet.target_planet  # Arrived

    progress = elapsed_time / total_time

    # Linear interpolation in 3D space
    current_x = fleet.start_planet.x + (fleet.target_planet.x - fleet.start_planet.x) * progress
    current_y = fleet.start_planet.y + (fleet.target_planet.y - fleet.start_planet.y) * progress
    current_z = fleet.start_planet.z + (fleet.target_planet.z - fleet.start_planet.z) * progress

    return {
        'x': current_x,
        'y': current_y,
        'z': current_z,
        'coordinates': f"{int(current_x)}:{int(current_y)}:{int(current_z)}"
    }
```

### Fuel Consumption

#### Distance-Based Fuel Calculation
```python
def calculate_fuel_consumption(fleet, distance):
    """Calculate fuel consumption for fleet travel"""
    total_fuel = 0

    for ship_type in SHIP_TYPES:
        ship_count = getattr(fleet, ship_type, 0)
        if ship_count > 0:
            fuel_rate = FUEL_RATES.get(ship_type, 1.0)
            total_fuel += ship_count * fuel_rate * distance

    return int(total_fuel)
```

---

## Combat Integration

### Fleet Combat Statistics

#### Ship Combat Values
```python
SHIP_COMBAT_STATS = {
    'light_fighter': {
        'hull': 4000,
        'shield': 10,
        'weapon': 50,
        'cargo': 50
    },
    'heavy_fighter': {
        'hull': 10000,
        'shield': 25,
        'weapon': 150,
        'cargo': 100
    },
    'cruiser': {
        'hull': 27000,
        'shield': 50,
        'weapon': 400,
        'cargo': 800
    },
    'battleship': {
        'hull': 60000,
        'shield': 200,
        'weapon': 1000,
        'cargo': 1500
    }
}
```

### Rapid Fire System

#### Ship-Specific Rapid Fire
```python
RAPID_FIRE = {
    'light_fighter': {'heavy_fighter': 2, 'cruiser': 6, 'battleship': 3},
    'heavy_fighter': {'small_cargo': 3, 'large_cargo': 4, 'cruiser': 4, 'battleship': 7},
    'cruiser': {'light_fighter': 6, 'heavy_fighter': 4, 'battleship': 7},
    'battleship': {'small_cargo': 3, 'large_cargo': 4}
}
```

### Combat Resolution

#### Battle Calculation Flow
1. **Shield Absorption**: Damage applied to shields first
2. **Hull Damage**: Remaining damage applied to hull
3. **Rapid Fire**: Chance for multiple shots per round
4. **Round Resolution**: Both sides fire simultaneously
5. **Victory Conditions**: Side with remaining ships wins

---

## Test Infrastructure Setup

### SQLAlchemy Mocking Patterns (Following systemPatterns.md)

#### 1. Model Specification Mocking
```python
from unittest.mock import Mock
from backend.models import Fleet, Planet, User

# ✅ CORRECT: Use spec for attribute validation
def create_mock_fleet():
    fleet = Mock(spec=Fleet)
    fleet.id = 1
    fleet.user_id = 1
    fleet.mission = 'stationed'
    fleet.status = 'stationed'
    fleet.start_planet_id = 1
    fleet.target_planet_id = 1
    fleet.small_cargo = 10
    fleet.light_fighter = 5
    return fleet

# ❌ AVOID: Loose mocking leads to typos
def create_bad_mock_fleet():
    fleet = Mock()  # No spec - allows typos
    fleet.small_cargp = 10  # Typo not caught
    return fleet
```

#### 2. Database Query Mocking
```python
from unittest.mock import patch

# ✅ CORRECT: Mock at query level with real objects
@patch.object(Planet, 'query')
def test_fleet_travel(mock_query):
    # Create real Planet objects for arithmetic
    start_planet = Planet(name='Start', x=0, y=0, z=0)
    target_planet = Planet(name='Target', x=100, y=0, z=0)

    # Mock query.get to return real objects
    mock_get = Mock()
    mock_get.side_effect = lambda planet_id: (
        start_planet if planet_id == 1 else target_planet
    )
    mock_query.get = mock_get

    # Test distance calculation
    distance = FleetTravelService.calculate_distance(start_planet, target_planet)
    assert distance == 100.0  # Real arithmetic works
```

#### 3. Service Layer Mocking
```python
@patch('backend.services.fleet_travel.FleetTravelService.calculate_distance')
@patch('backend.services.fleet_travel.FleetTravelService.calculate_travel_time')
def test_send_fleet(mock_travel_time, mock_distance):
    # Mock service methods
    mock_distance.return_value = 100.0
    mock_travel_time.return_value = 3600  # 1 hour

    # Test fleet sending logic
    result = FleetService.send_fleet(1, 2, 'transport')

    mock_distance.assert_called_once()
    mock_travel_time.assert_called_once()
    assert result['status'] == 'traveling'
```

### Test Data Creation Patterns

#### 1. Fleet Creation with Constraints
```python
def create_test_fleet_with_constraints(db_session, user_id, planet_id, **kwargs):
    """Create fleet with all required database constraints satisfied"""
    from datetime import datetime

    fleet = Fleet(
        user_id=user_id,
        start_planet_id=planet_id,
        target_planet_id=kwargs.get('target_planet_id', planet_id),
        mission=kwargs.get('mission', 'stationed'),
        status=kwargs.get('status', 'stationed'),
        departure_time=kwargs.get('departure_time', datetime.utcnow()),
        arrival_time=kwargs.get('arrival_time', datetime.utcnow()),
        # Ship counts
        small_cargo=kwargs.get('small_cargo', 0),
        large_cargo=kwargs.get('large_cargo', 0),
        light_fighter=kwargs.get('light_fighter', 0),
        heavy_fighter=kwargs.get('heavy_fighter', 0),
        cruiser=kwargs.get('cruiser', 0),
        battleship=kwargs.get('battleship', 0),
        colony_ship=kwargs.get('colony_ship', 0),
        recycler=kwargs.get('recycler', 0)
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet
```

#### 2. Planet Creation for Testing
```python
def create_test_planet(db_session, user_id=None, **kwargs):
    """Create planet with proper defaults"""
    planet = Planet(
        name=kwargs.get('name', 'Test Planet'),
        x=kwargs.get('x', 0),
        y=kwargs.get('y', 0),
        z=kwargs.get('z', 0),
        user_id=user_id,
        metal=kwargs.get('metal', 1000),
        crystal=kwargs.get('crystal', 500),
        deuterium=kwargs.get('deuterium', 0)
    )
    db_session.add(planet)
    db_session.commit()
    return planet
```

### Authentication Setup for Integration Tests

#### 1. Proper Password Hashing
```python
import bcrypt

def create_test_user_with_hashed_password(db_session, username, email, plain_password='password'):
    """Create test user with properly hashed password for integration tests"""
    password_hash = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=username, email=email, password_hash=password_hash)
    db_session.add(user)
    db_session.commit()
    return user, plain_password  # Return both user and plain password for login testing
```

#### 2. Authentication Headers
```python
def make_auth_headers(user_id):
    """Create authentication headers for integration tests"""
    from tests.conftest import create_test_user_with_hashed_password

    user, password = create_test_user_with_hashed_password(db_session, f'testuser_{user_id}', f'test{user_id}@example.com')

    # Login to get JWT token
    login_response = client.post('/api/auth/login', json={
        'username': user.username,
        'password': password
    })

    token = login_response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}
```

---

## Detailed Test Plan

### Unit Test Coverage

#### 1. Fleet Service Tests
```python
class TestFleetService:
    def test_create_fleet_success(self):
        """Test successful fleet creation"""

    def test_create_fleet_empty_ships(self):
        """Test fleet creation with no ships fails"""

    def test_send_fleet_invalid_mission(self):
        """Test sending fleet with invalid mission type"""

    def test_calculate_fleet_speed_single_ship_type(self):
        """Test speed calculation for single ship type"""

    def test_calculate_fleet_speed_mixed_fleet(self):
        """Test speed calculation for mixed fleet (slowest ship rule)"""

    def test_calculate_fleet_speed_empty_fleet(self):
        """Test speed calculation for empty fleet"""
```

#### 2. Fleet Travel Service Tests
```python
class TestFleetTravelService:
    def test_calculate_distance_same_position(self):
        """Test distance calculation for same position"""

    def test_calculate_distance_different_positions(self):
        """Test distance calculation for different positions"""

    def test_calculate_travel_time_zero_speed(self):
        """Test travel time with zero speed"""

    def test_calculate_travel_time_normal_speed(self):
        """Test travel time with normal speed"""

    def test_calculate_position_at_departure(self):
        """Test position calculation at departure time"""

    def test_calculate_position_at_arrival(self):
        """Test position calculation at arrival time"""

    def test_calculate_position_mid_travel(self):
        """Test position calculation during travel"""

    def test_format_coordinates_integers(self):
        """Test coordinate formatting returns integers"""
```

#### 3. Ship Statistics Tests
```python
class TestShipStatistics:
    def test_get_ship_speed_with_multiplier(self):
        """Test ship speed includes global multiplier"""

    def test_get_ship_speed_unknown_ship(self):
        """Test unknown ship type returns default speed"""

    def test_calculate_fuel_consumption_single_ship(self):
        """Test fuel consumption for single ship"""

    def test_calculate_fuel_consumption_mixed_fleet(self):
        """Test fuel consumption for mixed fleet"""
```

### Integration Test Coverage

#### 1. Fleet CRUD Operations
```python
class TestFleetCRUD:
    def test_get_user_fleets_empty(self, client, sample_user):
        """Test getting fleets when user has none"""

    def test_get_user_fleets_with_data(self, client, sample_fleet):
        """Test getting fleets when user has data"""

    def test_create_fleet_success(self, client, sample_user, sample_planet):
        """Test successful fleet creation via API"""

    def test_create_fleet_missing_fields(self, client, sample_user):
        """Test fleet creation with missing required fields"""

    def test_create_fleet_invalid_planet(self, client, sample_user):
        """Test fleet creation on non-owned planet"""

    def test_create_fleet_empty_ships(self, client, sample_user, sample_planet):
        """Test fleet creation with no ships"""
```

#### 2. Fleet Mission Tests
```python
class TestFleetMissions:
    def test_send_fleet_transport_success(self, client, sample_fleet):
        """Test successful transport mission"""

    def test_send_fleet_attack_success(self, client, sample_fleet):
        """Test successful attack mission"""

    def test_send_fleet_colonize_success(self, client, sample_fleet):
        """Test successful colonization mission"""

    def test_send_fleet_invalid_fleet(self, client, sample_user):
        """Test sending non-existent fleet"""

    def test_send_fleet_already_moving(self, client, sample_fleet):
        """Test sending already moving fleet"""

    def test_recall_fleet_success(self, client, sample_fleet):
        """Test successful fleet recall"""

    def test_recall_fleet_stationed(self, client, sample_fleet):
        """Test recalling stationed fleet"""
```

#### 3. Fleet Travel Tests
```python
class TestFleetTravel:
    def test_fleet_travel_time_calculation(self, client, sample_fleet):
        """Test travel time calculation in API"""

    def test_fleet_position_updates(self, client, sample_fleet):
        """Test fleet position updates during travel"""

    def test_fleet_arrival_processing(self, client, sample_fleet):
        """Test fleet arrival processing"""

    def test_fleet_return_journey(self, client, sample_fleet):
        """Test fleet return journey after mission"""
```

### End-to-End Test Coverage

#### 1. Complete Fleet Workflow
```javascript
test('should complete full fleet lifecycle', async ({ page }) => {
  // Login
  // Create fleet
  // Send on mission
  // Monitor travel
  // Verify arrival
  // Check mission completion
});
```

#### 2. Multi-Fleet Operations
```javascript
test('should handle multiple simultaneous fleets', async ({ page }) => {
  // Create multiple fleets
  // Send on different missions
  // Monitor all fleets
  // Verify independent operation
});
```

#### 3. Fleet Combat Integration
```javascript
test('should handle fleet combat scenarios', async ({ page }) => {
  // Send attack fleet
  // Trigger combat
  // Verify battle report
  // Check debris collection
});
```

### Performance Test Coverage

#### 1. Large Fleet Operations
```python
def test_large_fleet_creation():
    """Test creating fleet with maximum ship counts"""

def test_multiple_fleet_operations():
    """Test operations with many simultaneous fleets"""
```

#### 2. Travel Calculation Performance
```python
def test_distance_calculation_performance():
    """Test distance calculation with many planets"""

def test_fleet_speed_calculation_performance():
    """Test speed calculation for complex fleets"""
```

### Edge Case Test Coverage

#### 1. Boundary Conditions
```python
def test_fleet_with_max_ships():
    """Test fleet with maximum allowed ships"""

def test_fleet_with_zero_ships():
    """Test fleet with no ships"""

def test_travel_to_same_planet():
    """Test travel to same planet (should still work)"""
```

#### 2. Error Conditions
```python
def test_send_fleet_to_invalid_planet():
    """Test sending fleet to non-existent planet"""

def test_recall_nonexistent_fleet():
    """Test recalling non-existent fleet"""

def test_create_fleet_insufficient_resources():
    """Test fleet creation without sufficient resources"""
```

### Test Execution Strategy

#### 1. Unit Tests
```bash
# Run all fleet unit tests
pytest tests/unit/ -k "fleet" -v

# Run specific test class
pytest tests/unit/test_fleet_travel_service.py::TestFleetTravelService -v
```

#### 2. Integration Tests
```bash
# Run all fleet integration tests
pytest tests/integration/ -k "fleet" -v

# Run with coverage
pytest tests/integration/test_fleet.py --cov=backend.services.fleet_service --cov-report=html
```

#### 3. E2E Tests
```bash
# Run fleet E2E tests
npx playwright test tests/e2e/fleet.spec.js

# Run with headed browser for debugging
npx playwright test tests/e2e/fleet.spec.js --headed
```

### Test Data Management

#### 1. Test Database Setup
```python
@pytest.fixture
def sample_fleet(db_session, sample_user, sample_planet):
    """Create sample fleet for testing"""
    return create_test_fleet_with_constraints(
        db_session, sample_user.id, sample_planet.id,
        small_cargo=10, light_fighter=5
    )

@pytest.fixture
def sample_planet(db_session, sample_user):
    """Create sample planet for testing"""
    return create_test_planet(db_session, sample_user.id, x=0, y=0, z=0)
```

#### 2. Test Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_fleets(db_session):
    """Clean up fleets after each test"""
    yield
    db_session.query(Fleet).delete()
    db_session.commit()
```

### Continuous Integration

#### 1. Test Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Fleet Unit Tests
  run: pytest tests/unit/ -k "fleet" --cov=backend.services.fleet_service --cov-fail-under=90

- name: Run Fleet Integration Tests
  run: pytest tests/integration/ -k "fleet"

- name: Run Fleet E2E Tests
  run: npx playwright test tests/e2e/fleet.spec.js
```

#### 2. Test Reporting
```python
# Generate coverage reports
pytest tests/ -k "fleet" --cov=backend --cov-report=html --cov-report=xml

# Generate test reports
pytest tests/ -k "fleet" --junitxml=test-results.xml
```

This comprehensive test plan ensures complete coverage of fleet mechanics from unit operations through full user workflows, with proper SQLAlchemy mocking patterns and robust error handling.
