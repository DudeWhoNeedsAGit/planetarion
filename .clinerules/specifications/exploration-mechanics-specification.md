# Exploration Mechanics Specification & Test Plan

## Overview

This document provides a comprehensive specification for the exploration mechanics system, including galaxy discovery, system scanning, planet detection, and exploration fleet operations. The exploration system enables players to discover new planets and expand their knowledge of the galaxy.

## Table of Contents

1. [Exploration System Architecture](#exploration-system-architecture)
2. [Galaxy Structure](#galaxy-structure)
3. [Exploration Fleet Mechanics](#exploration-fleet-mechanics)
4. [System Discovery Process](#system-discovery-process)
5. [Planet Detection and Classification](#planet-detection-and-classification)
6. [Exploration Rewards](#exploration-rewards)
7. [Test Infrastructure Setup](#test-infrastructure-setup)
8. [Detailed Test Plan](#detailed-test-plan)

---

## Exploration System Architecture

### Core Components

#### 1. Exploration Service
```python
class ExplorationService:
    @staticmethod
    def validate_exploration_fleet(fleet):
        """Validate fleet composition for exploration"""

    @staticmethod
    def calculate_exploration_range(fleet, user):
        """Calculate maximum exploration distance"""

    @staticmethod
    def generate_system_content(coordinates):
        """Generate planets and resources for discovered system"""

    @staticmethod
    def process_exploration_completion(fleet, discovered_system):
        """Process exploration results and update user knowledge"""
```

#### 2. Galaxy Map Service
```python
class GalaxyMapService:
    @staticmethod
    def get_explored_systems(user):
        """Get all systems explored by user"""

    @staticmethod
    def get_system_details(coordinates, user):
        """Get detailed information about a system"""

    @staticmethod
    def calculate_system_value(system):
        """Calculate economic value of a system"""
```

#### 3. Coordinate System
```python
class CoordinateSystem:
    @staticmethod
    def parse_coordinates(coord_string):
        """Parse coordinate string (x:y:z)"""

    @staticmethod
    def format_coordinates(x, y, z):
        """Format coordinates as string"""

    @staticmethod
    def calculate_distance(coord1, coord2):
        """Calculate 3D distance between coordinates"""

    @staticmethod
    def generate_random_coordinates(max_distance):
        """Generate random coordinates within range"""
```

---

## Galaxy Structure

### Galaxy Dimensions
```python
GALAXY_CONFIG = {
    'max_x': 10000,
    'max_y': 10000,
    'max_z': 10000,
    'min_distance_between_systems': 50,
    'systems_per_sector': 100,
    'planets_per_system': {'min': 1, 'max': 12}
}
```

### System Types
```python
SYSTEM_TYPES = {
    'empty': {'probability': 0.3, 'planets': 0},
    'sparse': {'probability': 0.4, 'planets': {'min': 1, 'max': 3}},
    'normal': {'probability': 0.2, 'planets': {'min': 4, 'max': 8}},
    'dense': {'probability': 0.08, 'planets': {'min': 9, 'max': 12}},
    'rich': {'probability': 0.02, 'planets': {'min': 10, 'max': 12}}
}
```

### Planet Distribution
```python
PLANET_ORBITS = {
    1: {'distance': 50, 'probability': 0.9},   # Close orbit
    2: {'distance': 100, 'probability': 0.8},  # Habitable zone
    3: {'distance': 150, 'probability': 0.7},  # Outer planets
    4: {'distance': 200, 'probability': 0.6},
    5: {'distance': 300, 'probability': 0.5},
    6: {'distance': 400, 'probability': 0.4},
    7: {'distance': 500, 'probability': 0.3},
    8: {'distance': 600, 'probability': 0.2},
    9: {'distance': 700, 'probability': 0.1},
    10: {'distance': 800, 'probability': 0.05},
    11: {'distance': 900, 'probability': 0.02},
    12: {'distance': 1000, 'probability': 0.01}  # Extreme outer planets
}
```

---

## Exploration Fleet Mechanics

### Fleet Requirements
```python
EXPLORATION_FLEET_REQUIREMENTS = {
    'min_ships': 1,
    'max_ships': 10,
    'allowed_ship_types': ['small_cargo', 'large_cargo'],
    'forbidden_ship_types': ['colony_ship', 'recycler'],
    'max_fleet_speed': 10000  # Exploration fleets should be fast
}
```

### Exploration Range Calculation
```python
def calculate_exploration_range(fleet, user):
    """Calculate maximum exploration distance based on fleet and research"""
    base_range = 1000  # Base exploration range

    # Fleet composition bonus
    ship_bonus = len(fleet.get_ship_list()) * 50

    # Research bonus
    research_level = get_exploration_tech_level(user)
    research_bonus = research_level * 200

    # Technology bonuses
    tech_bonuses = calculate_technology_bonuses(user)

    total_range = base_range + ship_bonus + research_bonus + tech_bonuses

    return min(total_range, GALAXY_CONFIG['max_x'])  # Galaxy boundary
```

### Exploration Time Calculation
```python
def calculate_exploration_time(distance, fleet_speed):
    """Calculate time required for exploration"""
    base_time = distance / fleet_speed  # Basic travel time

    # Exploration activities add time
    scanning_time = 300  # 5 minutes for system scanning
    analysis_time = 600  # 10 minutes for data analysis

    total_time = base_time + scanning_time + analysis_time

    return int(total_time)
```

---

## System Discovery Process

### Exploration Mission Flow
```python
def process_exploration_mission(fleet, target_coordinates):
    """Complete exploration mission processing"""

    # 1. Validate exploration requirements
    validate_exploration_fleet(fleet)

    # 2. Check exploration range
    distance = calculate_distance(fleet.current_coordinates, target_coordinates)
    max_range = calculate_exploration_range(fleet, fleet.user)

    if distance > max_range:
        raise ValueError(f"Target coordinates too far. Max range: {max_range}")

    # 3. Set exploration status
    fleet.status = f"exploring:{target_coordinates}"
    fleet.mission = 'explore'
    fleet.arrival_time = calculate_exploration_time(distance, fleet.speed)

    # 4. Process exploration on arrival
    discovered_system = generate_system_content(target_coordinates)

    # 5. Update user exploration data
    update_user_exploration_data(fleet.user, discovered_system)

    # 6. Return fleet to stationed
    fleet.status = 'stationed'
    fleet.mission = 'completed'

    return discovered_system
```

### System Content Generation
```python
def generate_system_content(coordinates):
    """Generate planets and resources for a newly discovered system"""

    # Determine system type
    system_type = determine_system_type()

    # Generate planets based on system type
    planets = []
    planet_count = random.randint(
        SYSTEM_TYPES[system_type]['planets']['min'],
        SYSTEM_TYPES[system_type]['planets']['max']
    )

    for i in range(planet_count):
        planet = generate_planet(coordinates, i + 1, system_type)
        planets.append(planet)

    system = {
        'coordinates': coordinates,
        'type': system_type,
        'planets': planets,
        'discovered_at': datetime.utcnow(),
        'economic_value': calculate_system_value(planets)
    }

    return system
```

---

## Planet Detection and Classification

### Planet Types
```python
PLANET_TYPES = {
    'terrestrial': {
        'probability': 0.4,
        'size_range': {'min': 4000, 'max': 12000},
        'temperature_range': {'min': -50, 'max': 50},
        'resources': {'metal': 1.0, 'crystal': 0.8, 'deuterium': 0.3}
    },
    'gas_giant': {
        'probability': 0.15,
        'size_range': {'min': 50000, 'max': 150000},
        'temperature_range': {'min': -200, 'max': -100},
        'resources': {'metal': 0.1, 'crystal': 0.05, 'deuterium': 2.0}
    },
    'ice_world': {
        'probability': 0.2,
        'size_range': {'min': 2000, 'max': 8000},
        'temperature_range': {'min': -250, 'max': -150},
        'resources': {'metal': 0.3, 'crystal': 0.1, 'deuterium': 1.5}
    },
    'desert': {
        'probability': 0.15,
        'size_range': {'min': 3000, 'max': 10000},
        'temperature_range': {'min': 50, 'max': 150},
        'resources': {'metal': 1.5, 'crystal': 0.5, 'deuterium': 0.1}
    },
    'ocean': {
        'probability': 0.08,
        'size_range': {'min': 5000, 'max': 14000},
        'temperature_range': {'min': -10, 'max': 30},
        'resources': {'metal': 0.8, 'crystal': 1.2, 'deuterium': 0.8}
    },
    'volcanic': {
        'probability': 0.02,
        'size_range': {'min': 6000, 'max': 18000},
        'temperature_range': {'min': 200, 'max': 800},
        'resources': {'metal': 2.0, 'crystal': 0.3, 'deuterium': 0.2}
    }
}
```

### Planet Generation
```python
def generate_planet(system_coordinates, orbit_number, system_type):
    """Generate a single planet with realistic properties"""

    # Select planet type based on probabilities
    planet_type = select_planet_type()

    # Calculate planet properties
    size = random.randint(
        PLANET_TYPES[planet_type]['size_range']['min'],
        PLANET_TYPES[planet_type]['size_range']['max']
    )

    temperature = random.randint(
        PLANET_TYPES[planet_type]['temperature_range']['min'],
        PLANET_TYPES[planet_type]['temperature_range']['max']
    )

    # Calculate planet coordinates
    orbit_distance = PLANET_ORBITS[orbit_number]['distance']
    angle = random.uniform(0, 2 * math.pi)

    planet_x = system_coordinates[0] + orbit_distance * math.cos(angle)
    planet_y = system_coordinates[1] + orbit_distance * math.sin(angle)
    planet_z = system_coordinates[2]  # Same z-plane as system

    # Generate resource deposits
    resources = generate_resource_deposits(planet_type, size)

    planet = {
        'coordinates': (int(planet_x), int(planet_y), int(planet_z)),
        'type': planet_type,
        'size': size,
        'temperature': temperature,
        'resources': resources,
        'orbit': orbit_number,
        'habitability': calculate_habitability(planet_type, temperature),
        'colonization_difficulty': calculate_colonization_difficulty(planet_type)
    }

    return planet
```

### Resource Deposit Generation
```python
def generate_resource_deposits(planet_type, size):
    """Generate resource deposits based on planet characteristics"""

    base_multipliers = PLANET_TYPES[planet_type]['resources']

    # Size affects resource abundance
    size_multiplier = size / 10000  # Normalize to 10000km baseline

    # Add randomness
    metal_deposit = base_multipliers['metal'] * size_multiplier * random.uniform(0.5, 1.5)
    crystal_deposit = base_multipliers['crystal'] * size_multiplier * random.uniform(0.5, 1.5)
    deuterium_deposit = base_multipliers['deuterium'] * size_multiplier * random.uniform(0.5, 1.5)

    return {
        'metal': int(metal_deposit * 1000),      # Base metal deposit
        'crystal': int(crystal_deposit * 1000),  # Base crystal deposit
        'deuterium': int(deuterium_deposit * 1000)  # Base deuterium deposit
    }
```

---

## Exploration Rewards

### Discovery Bonuses
```python
EXPLORATION_REWARDS = {
    'first_discovery': {
        'experience': 100,
        'bonus_resources': {'metal': 500, 'crystal': 300, 'deuterium': 100}
    },
    'system_value_bonus': {
        'high_value_threshold': 10000,
        'bonus_multiplier': 1.5
    },
    'planet_count_bonus': {
        'min_planets': 5,
        'bonus_per_planet': 50
    }
}
```

### Experience and Reputation
```python
def calculate_exploration_experience(user, discovered_system):
    """Calculate experience gained from exploration"""

    base_experience = 50

    # System type bonus
    system_multipliers = {
        'empty': 0.5,
        'sparse': 1.0,
        'normal': 1.5,
        'dense': 2.0,
        'rich': 3.0
    }

    system_bonus = system_multipliers.get(discovered_system['type'], 1.0)

    # Planet count bonus
    planet_bonus = len(discovered_system['planets']) * 10

    # Distance bonus (further = more experience)
    distance = calculate_distance_from_origin(discovered_system['coordinates'])
    distance_bonus = min(distance / 1000, 2.0)  # Max 2x bonus

    total_experience = base_experience * system_bonus * (1 + distance_bonus) + planet_bonus

    return int(total_experience)
```

### Economic Value Calculation
```python
def calculate_system_value(system):
    """Calculate the economic value of a discovered system"""

    total_value = 0

    for planet in system['planets']:
        planet_value = 0

        # Resource value
        planet_value += planet['resources']['metal'] * 1.0
        planet_value += planet['resources']['crystal'] * 1.5
        planet_value += planet['resources']['deuterium'] * 2.0

        # Size bonus
        size_bonus = planet['size'] / 10000
        planet_value *= size_bonus

        # Habitability bonus
        habitability_bonus = planet['habitability'] / 100
        planet_value *= (0.5 + habitability_bonus)

        total_value += planet_value

    return int(total_value)
```

---

## Test Infrastructure Setup

### SQLAlchemy Mocking Patterns (Following systemPatterns.md)

#### 1. Exploration Service Mocking
```python
from unittest.mock import Mock, patch
from backend.services.exploration_service import ExplorationService

# ✅ CORRECT: Mock service methods with proper return values
@patch.object(ExplorationService, 'validate_exploration_fleet')
@patch.object(ExplorationService, 'generate_system_content')
def test_exploration_process(mock_generate, mock_validate):
    mock_validate.return_value = True
    mock_generate.return_value = {'type': 'normal', 'planets': []}

    # Test exploration logic
    result = process_exploration(fleet, coordinates)

    mock_validate.assert_called_once()
    mock_generate.assert_called_once()
    assert result['type'] == 'normal'
```

#### 2. Coordinate System Mocking
```python
from backend.services.coordinate_system import CoordinateSystem

# ✅ CORRECT: Mock coordinate calculations
@patch.object(CoordinateSystem, 'calculate_distance')
def test_coordinate_distance(mock_distance):
    mock_distance.return_value = 500.0

    distance = CoordinateSystem.calculate_distance(coord1, coord2)
    assert distance == 500.0
    mock_distance.assert_called_once()
```

#### 3. Galaxy Map Service Mocking
```python
@patch('backend.services.galaxy_map_service.get_explored_systems')
def test_explored_systems(mock_get_systems):
    mock_get_systems.return_value = [{'coordinates': '100:200:300'}]

    systems = get_explored_systems(user)
    assert len(systems) == 1
    assert systems[0]['coordinates'] == '100:200:300'
```

### Test Data Creation Patterns

#### 1. Exploration Fleet Creation
```python
def create_test_exploration_fleet(db_session, user_id, planet_id):
    """Create fleet suitable for exploration testing"""
    fleet = Fleet(
        user_id=user_id,
        start_planet_id=planet_id,
        target_planet_id=planet_id,
        mission='stationed',
        status='stationed',
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow(),
        small_cargo=5,  # Exploration ships
        large_cargo=2
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet
```

#### 2. Test System Generation
```python
def create_test_system(coordinates=None, system_type='normal'):
    """Create test system for exploration testing"""
    if coordinates is None:
        coordinates = (1000, 2000, 3000)

    planets = []
    for i in range(5):  # Generate 5 test planets
        planet = {
            'coordinates': (coordinates[0] + i*10, coordinates[1] + i*10, coordinates[2]),
            'type': 'terrestrial',
            'size': 8000,
            'temperature': 20,
            'resources': {'metal': 1000, 'crystal': 500, 'deuterium': 200},
            'orbit': i + 1,
            'habitability': 80,
            'colonization_difficulty': 2
        }
        planets.append(planet)

    return {
        'coordinates': coordinates,
        'type': system_type,
        'planets': planets,
        'discovered_at': datetime.utcnow(),
        'economic_value': 50000
    }
```

#### 3. User Exploration Data Setup
```python
def setup_test_exploration_data(db_session, user_id):
    """Setup exploration progress for testing"""
    exploration_data = ExplorationData(
        user_id=user_id,
        explored_systems=['100:200:300', '200:300:400'],
        total_experience=500,
        discovered_planets=15,
        exploration_range=1500
    )
    db_session.add(exploration_data)
    db_session.commit()
    return exploration_data
```

---

## Detailed Test Plan

### Unit Test Coverage

#### 1. Exploration Service Tests
```python
class TestExplorationService:
    def test_validate_exploration_fleet_success(self):
        """Test successful exploration fleet validation"""

    def test_validate_exploration_fleet_invalid_ships(self):
        """Test validation fails with invalid ship types"""

    def test_calculate_exploration_range_basic(self):
        """Test basic exploration range calculation"""

    def test_calculate_exploration_range_with_research(self):
        """Test exploration range with research bonuses"""

    def test_generate_system_content_normal_system(self):
        """Test system generation for normal system type"""

    def test_generate_system_content_empty_system(self):
        """Test system generation for empty system type"""
```

#### 2. Coordinate System Tests
```python
class TestCoordinateSystem:
    def test_parse_coordinates_valid(self):
        """Test parsing valid coordinate string"""

    def test_parse_coordinates_invalid(self):
        """Test parsing invalid coordinate string"""

    def test_format_coordinates_integers(self):
        """Test coordinate formatting returns integers"""

    def test_calculate_distance_same_point(self):
        """Test distance calculation for same coordinates"""

    def test_calculate_distance_different_points(self):
        """Test distance calculation for different coordinates"""
```

#### 3. Planet Generation Tests
```python
class TestPlanetGeneration:
    def test_generate_planet_terrestrial(self):
        """Test planet generation for terrestrial type"""

    def test_generate_planet_gas_giant(self):
        """Test planet generation for gas giant type"""

    def test_generate_resource_deposits_variability(self):
        """Test resource deposit generation has proper variability"""

    def test_calculate_habitability_extremes(self):
        """Test habitability calculation for extreme conditions"""
```

### Integration Test Coverage

#### 1. Exploration Workflow Tests
```python
class TestExplorationWorkflow:
    def test_complete_exploration_process(self, client, exploration_fleet):
        """Test complete exploration workflow"""

    def test_exploration_fleet_departure(self, client, exploration_fleet):
        """Test exploration fleet departure"""

    def test_exploration_fleet_arrival_processing(self, client, exploration_fleet):
        """Test exploration fleet arrival processing"""

    def test_system_discovery_and_recording(self, client, exploration_fleet):
        """Test system discovery and user data updates"""
```

#### 2. System Content Tests
```python
class TestSystemContent:
    def test_system_type_distribution(self, client):
        """Test system type generation follows probability distribution"""

    def test_planet_count_by_system_type(self, client):
        """Test planet count matches system type requirements"""

    def test_planet_orbit_distribution(self, client):
        """Test planet orbits follow realistic distribution"""

    def test_resource_deposit_realism(self, client):
        """Test resource deposits are realistic for planet types"""
```

#### 3. Exploration Rewards Tests
```python
class TestExplorationRewards:
    def test_experience_calculation_basic(self, client):
        """Test basic exploration experience calculation"""

    def test_experience_calculation_with_bonuses(self, client):
        """Test experience with system type and distance bonuses"""

    def test_economic_value_calculation(self, client):
        """Test system economic value calculation"""

    def test_first_discovery_bonuses(self, client):
        """Test first discovery bonus rewards"""
```

### End-to-End Test Coverage

#### 1. Complete Exploration Journey
```javascript
test('should complete full exploration workflow', async ({ page }) => {
  // Login and navigate to galaxy map
  // Select unexplored coordinates
  // Create exploration fleet
  // Send exploration mission
  // Wait for exploration completion
  // Verify system discovery
  // Check exploration rewards
  // Validate user exploration data updates
});
```

#### 2. Multi-System Exploration
```javascript
test('should handle multiple system explorations', async ({ page }) => {
  // Explore multiple systems
  // Verify exploration range limitations
  // Check experience accumulation
  // Validate system data persistence
});
```

#### 3. Exploration Fleet Management
```javascript
test('should manage exploration fleets effectively', async ({ page }) => {
  // Create multiple exploration fleets
  // Send to different coordinates
  // Monitor exploration progress
  // Handle fleet returns and rewards
});
```

### Performance Test Coverage

#### 1. Large-Scale Exploration
```python
def test_massive_exploration_operations():
    """Test exploration with many simultaneous operations"""

def test_system_generation_performance():
    """Test system content generation performance"""
```

#### 2. Coordinate Calculation Performance
```python
def test_distance_calculation_performance():
    """Test distance calculations for many coordinate pairs"""

def test_coordinate_parsing_performance():
    """Test coordinate parsing performance"""
```

### Edge Case Test Coverage

#### 1. Boundary Conditions
```python
def test_exploration_at_range_limit():
    """Test exploration exactly at range limit"""

def test_exploration_beyond_range():
    """Test exploration attempt beyond range limit"""

def test_coordinate_boundary_values():
    """Test coordinate calculations at galaxy boundaries"""
```

#### 2. Error Conditions
```python
def test_exploration_without_proper_fleet():
    """Test exploration attempt without proper fleet composition"""

def test_exploration_of_already_discovered_system():
    """Test exploration of already discovered coordinates"""

def test_exploration_during_fleet_travel():
    """Test exploration attempts during fleet travel"""
```

#### 3. Race Conditions
```python
def test_simultaneous_exploration_same_coordinates():
    """Test multiple users exploring same coordinates"""

def test_exploration_fleet_interference():
    """Test exploration fleets interfering with each other"""
```

### Test Execution Strategy

#### 1. Unit Tests
```bash
# Run exploration unit tests
pytest tests/unit/ -k "exploration" -v

# Run specific test class
pytest tests/unit/test_exploration_service.py::TestExplorationService -v
```

#### 2. Integration Tests
```bash
# Run exploration integration tests
pytest tests/integration/ -k "exploration" -v

# Run with coverage
pytest tests/integration/test_exploration_workflow.py --cov=backend.services.exploration_service --cov-report=html
```

#### 3. E2E Tests
```bash
# Run exploration E2E tests
npx playwright test tests/e2e/exploration.spec.js

# Run with debugging
npx playwright test tests/e2e/exploration.spec.js --headed --debug
```

### Test Data Management

#### 1. Test Database Setup
```python
@pytest.fixture
def exploration_fleet(db_session, sample_user, sample_planet):
    """Create exploration fleet for testing"""
    return create_test_exploration_fleet(db_session, sample_user.id, sample_planet.id)

@pytest.fixture
def test_system():
    """Create test system for exploration testing"""
    return create_test_system(coordinates=(1000, 2000, 3000), system_type='normal')

@pytest.fixture
def user_with_exploration_data(db_session, sample_user):
    """Create user with exploration progress"""
    return setup_test_exploration_data(db_session, sample_user.id)
```

#### 2. Test Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_exploration_data(db_session):
    """Clean up exploration data after each test"""
    yield
    # Reset exploration data
    db_session.query(ExplorationData).delete()
    db_session.query(DiscoveredSystem).delete()
    db_session.query(Fleet).filter(Fleet.mission == 'explore').delete()
    db_session.commit()
```

### Continuous Integration

#### 1. Test Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Exploration Unit Tests
  run: pytest tests/unit/ -k "exploration" --cov=backend.services.exploration_service --cov-fail-under=90

- name: Run Exploration Integration Tests
  run: pytest tests/integration/ -k "exploration"

- name: Run Exploration E2E Tests
  run: npx playwright test tests/e2e/exploration.spec.js
```

#### 2. Test Reporting
```python
# Generate coverage reports
pytest tests/ -k "exploration" --cov=backend --cov-report=html --cov-report=xml

# Generate test reports
pytest tests/ -k "exploration" --junitxml=test-results.xml
```

This comprehensive test plan ensures complete coverage of exploration mechanics from fleet validation through system discovery and reward processing, with proper SQLAlchemy mocking patterns and robust error handling.
