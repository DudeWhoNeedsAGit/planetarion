# Colonization Mechanics Specification & Test Plan

## Overview

This document provides a comprehensive specification for the colonization mechanics system, including colony ship operations, planet colonization, research requirements, and colony management. The colonization system enables player expansion and empire growth.

## Table of Contents

1. [Colonization System Architecture](#colonization-system-architecture)
2. [Colony Ship Mechanics](#colony-ship-mechanics)
3. [Planet Colonization Process](#planet-colonization-process)
4. [Research Requirements](#research-requirements)
5. [Colony Management](#colony-management)
6. [Test Infrastructure Setup](#test-infrastructure-setup)
7. [Detailed Test Plan](#detailed-test-plan)

---

## Colonization System Architecture

### Core Components

#### 1. Colony Ship Model Integration
```python
# Fleet model includes colony_ship field
class Fleet(db.Model):
    # ... existing fields ...
    colony_ship = db.Column(db.Integer, default=0)

    # Colonization-specific status
    # Status format: 'colonizing:X:Y:Z' for coordinate-based colonization
```

#### 2. Planet Colonization Service
```python
class ColonizationService:
    @staticmethod
    def validate_colonization_requirements(fleet, target_planet):
        """Validate all requirements for colonization"""

    @staticmethod
    def calculate_colonization_difficulty(distance):
        """Calculate colonization difficulty based on distance"""

    @staticmethod
    def initialize_new_colony(user, planet, fleet):
        """Initialize a new colony with starting resources"""

    @staticmethod
    def check_research_requirements(user, tech_level):
        """Check if user has required colonization technology"""
```

#### 3. Research System Integration
```python
class ResearchService:
    @staticmethod
    def get_colonization_tech_level(user):
        """Get user's colonization technology level"""

    @staticmethod
    def calculate_colony_limit(tech_level):
        """Calculate maximum colonies based on tech level"""
```

---

## Colony Ship Mechanics

### Ship Specifications

#### Colony Ship Statistics
```python
COLONY_SHIP_STATS = {
    'speed': 2500,           # Base speed (slowest ship)
    'cargo_capacity': 7500,  # Colony supplies capacity
    'fuel_consumption': 10.0, # High fuel consumption
    'hull': 30000,          # Strong hull for long journeys
    'shield': 100,          # Basic shield protection
    'weapon': 50            # Minimal weapon capability
}
```

### Fleet Composition Requirements

#### Minimum Fleet Requirements
```python
def validate_colony_fleet_composition(fleet):
    """Validate fleet has colony ship and escort"""
    requirements = {
        'colony_ship': {'min': 1, 'max': 1},  # Exactly 1 colony ship
        'escort_ships': {'min': 5, 'max': 50} # Escort ships for protection
    }

    colony_ships = fleet.colony_ship
    escort_count = (
        fleet.light_fighter + fleet.heavy_fighter +
        fleet.cruiser + fleet.battleship
    )

    if colony_ships != 1:
        raise ValueError("Fleet must contain exactly 1 colony ship")

    if escort_count < 5:
        raise ValueError("Fleet must contain at least 5 escort ships")

    if escort_count > 50:
        raise ValueError("Fleet cannot contain more than 50 escort ships")

    return True
```

### Travel Mechanics

#### Colonization Journey
```python
def calculate_colonization_travel_time(distance, fleet_speed):
    """Calculate colonization travel time with difficulty modifier"""
    base_travel_time = calculate_travel_time(distance, fleet_speed)

    # Colonization difficulty affects travel time
    difficulty = calculate_colonization_difficulty(distance)
    difficulty_modifier = 1.0 + (difficulty * 0.1)  # 10% increase per difficulty level

    return int(base_travel_time * difficulty_modifier)
```

---

## Planet Colonization Process

### Target Planet Validation

#### Planet Ownership Check
```python
def validate_target_planet(target_planet, user):
    """Validate planet can be colonized"""
    if target_planet.user_id is not None:
        raise ValueError("Planet is already owned")

    if target_planet.is_destroyed:
        raise ValueError("Planet is destroyed and cannot be colonized")

    # Check colonization distance limits
    home_planet = get_user_home_planet(user)
    distance = calculate_distance(home_planet, target_planet)

    max_distance = calculate_max_colonization_distance(user)
    if distance > max_distance:
        raise ValueError(f"Planet is too far to colonize (max: {max_distance})")

    return True
```

#### Planet Type Compatibility
```python
PLANET_COLONY_COMPATIBILITY = {
    'terrestrial': {'modifier': 1.0, 'base_resources': 1000},
    'gas_giant': {'modifier': 0.5, 'base_resources': 500},
    'ice_world': {'modifier': 0.8, 'base_resources': 800},
    'desert': {'modifier': 1.2, 'base_resources': 1200},
    'ocean': {'modifier': 1.1, 'base_resources': 1100}
}

def calculate_planet_colony_bonus(planet_type):
    """Calculate colonization bonus based on planet type"""
    compatibility = PLANET_COLONY_COMPATIBILITY.get(planet_type, {'modifier': 1.0})
    return compatibility
```

### Colonization Difficulty System

#### Distance-Based Difficulty
```python
def calculate_colonization_difficulty(distance):
    """Calculate colonization difficulty (1-5 scale)"""
    # Base distance from origin (0,0,0)
    origin_distance = distance

    # Difficulty increases with distance
    if origin_distance < 200:
        return 1  # Easy colonization
    elif origin_distance < 500:
        return 2  # Moderate difficulty
    elif origin_distance < 1000:
        return 3  # Challenging
    elif origin_distance < 2000:
        return 4  # Difficult
    else:
        return 5  # Extreme difficulty
```

#### Research-Based Difficulty Reduction
```python
def apply_research_difficulty_modifier(difficulty, tech_level):
    """Reduce difficulty based on colonization technology"""
    # Each tech level reduces difficulty by 0.5
    reduction = tech_level * 0.5
    return max(1, difficulty - reduction)
```

### Fleet Arrival and Colonization

#### Colonization Status Updates
```python
def process_colonization_arrival(fleet, target_planet):
    """Process fleet arrival for colonization mission"""
    # Update fleet status to colonizing
    fleet.status = f"colonizing:{target_planet.x}:{target_planet.y}:{target_planet.z}"
    fleet.arrival_time = datetime.utcnow() + timedelta(hours=24)  # 24 hours to colonize

    # Lock target planet during colonization
    target_planet.colonization_lock = True
    target_planet.locked_by_fleet = fleet.id

    db.session.commit()
    return fleet
```

#### Colony Initialization
```python
def initialize_new_colony(user, planet, fleet):
    """Initialize a new colony after successful colonization"""
    # Transfer planet ownership
    planet.user_id = user.id
    planet.is_home_planet = False
    planet.colonized_at = datetime.utcnow()

    # Set starting resources based on planet type
    compatibility = calculate_planet_colony_bonus(planet.planet_type)
    base_resources = compatibility['base_resources']

    planet.metal = base_resources
    planet.crystal = int(base_resources * 0.6)
    planet.deuterium = int(base_resources * 0.3)

    # Initialize buildings
    planet.metal_mine = 1
    planet.crystal_mine = 1
    planet.solar_plant = 1

    # Remove colonization lock
    planet.colonization_lock = False
    planet.locked_by_fleet = None

    # Update fleet status
    fleet.status = 'stationed'
    fleet.mission = 'completed'

    # Create colonization event log
    create_colonization_log(user, planet, fleet)

    db.session.commit()
    return planet
```

---

## Research Requirements

### Colonization Technology Tree

#### Technology Levels
```python
COLONIZATION_TECH_LEVELS = {
    0: {
        'name': 'Basic Colonization',
        'max_colonies': 3,
        'difficulty_reduction': 0,
        'special_abilities': []
    },
    1: {
        'name': 'Advanced Colonization',
        'max_colonies': 5,
        'difficulty_reduction': 0.5,
        'special_abilities': ['terraforming']
    },
    2: {
        'name': 'Expert Colonization',
        'max_colonies': 8,
        'difficulty_reduction': 1.0,
        'special_abilities': ['terraforming', 'atmosphere_processing']
    },
    3: {
        'name': 'Master Colonization',
        'max_colonies': 12,
        'difficulty_reduction': 1.5,
        'special_abilities': ['terraforming', 'atmosphere_processing', 'resource_enrichment']
    }
}
```

#### Research Requirements
```python
COLONIZATION_RESEARCH_REQUIREMENTS = {
    1: {
        'metal': 400,
        'crystal': 120,
        'deuterium': 200,
        'research_time': 3600,  # 1 hour
        'prerequisites': []
    },
    2: {
        'metal': 1000,
        'crystal': 300,
        'deuterium': 500,
        'research_time': 7200,  # 2 hours
        'prerequisites': ['colonization_tech_1']
    },
    3: {
        'metal': 2500,
        'crystal': 750,
        'deuterium': 1250,
        'research_time': 14400,  # 4 hours
        'prerequisites': ['colonization_tech_2', 'energy_tech_3']
    }
}
```

### Colony Limits

#### Technology-Based Limits
```python
def calculate_max_colonies(user):
    """Calculate maximum colonies based on research"""
    tech_level = get_colonization_tech_level(user)
    base_limit = COLONIZATION_TECH_LEVELS[tech_level]['max_colonies']

    # Additional colonies from special buildings/upgrades
    bonus_colonies = calculate_colony_bonuses(user)

    return base_limit + bonus_colonies
```

#### Distance-Based Limits
```python
def calculate_max_colonization_distance(user):
    """Calculate maximum colonization distance"""
    tech_level = get_colonization_tech_level(user)
    base_distance = 1000  # Base distance

    # Technology increases maximum distance
    distance_bonus = tech_level * 500

    return base_distance + distance_bonus
```

---

## Colony Management

### Colony Statistics

#### Colony Overview
```python
def get_colony_statistics(user):
    """Get comprehensive colony statistics"""
    colonies = get_user_colonies(user)

    stats = {
        'total_colonies': len(colonies),
        'total_population': sum(c.population for c in colonies),
        'total_production': {
            'metal': sum(c.metal_production for c in colonies),
            'crystal': sum(c.crystal_production for c in colonies),
            'deuterium': sum(c.deuterium_production for c in colonies)
        },
        'total_resources': {
            'metal': sum(c.metal for c in colonies),
            'crystal': sum(c.crystal for c in colonies),
            'deuterium': sum(c.deuterium for c in colonies)
        },
        'average_happiness': sum(c.happiness for c in colonies) / len(colonies) if colonies else 0
    }

    return stats
```

### Colony Development

#### Resource Production
```python
def calculate_colony_production(colony):
    """Calculate resource production for a colony"""
    production = {
        'metal': colony.metal_mine * calculate_metal_production_rate(colony.metal_mine),
        'crystal': colony.crystal_mine * calculate_crystal_production_rate(colony.crystal_mine),
        'deuterium': colony.deuterium_synthesizer * calculate_deuterium_production_rate(colony.deuterium_synthesizer)
    }

    # Apply energy efficiency
    energy_efficiency = calculate_energy_efficiency(colony)
    for resource in production:
        production[resource] *= energy_efficiency

    return production
```

#### Colony Happiness System
```python
def calculate_colony_happiness(colony):
    """Calculate colony happiness based on various factors"""
    happiness = 50  # Base happiness

    # Population factors
    if colony.population > colony.housing_capacity:
        happiness -= 20  # Overcrowding penalty

    # Resource factors
    if colony.metal < 100:
        happiness -= 10  # Low resources penalty

    # Building factors
    if colony.entertainment_complexes > 0:
        happiness += colony.entertainment_complexes * 5

    # Technology factors
    tech_level = get_colonization_tech_level(colony.user)
    happiness += tech_level * 2

    return max(0, min(100, happiness))
```

---

## Test Infrastructure Setup

### SQLAlchemy Mocking Patterns (Following systemPatterns.md)

#### 1. Colonization Service Mocking
```python
from unittest.mock import Mock, patch
from backend.services.colonization_service import ColonizationService

# ✅ CORRECT: Mock service methods with proper return values
@patch.object(ColonizationService, 'validate_colonization_requirements')
@patch.object(ColonizationService, 'calculate_colonization_difficulty')
def test_colonization_process(mock_difficulty, mock_validate):
    mock_validate.return_value = True
    mock_difficulty.return_value = 2

    # Test colonization logic
    result = process_colonization(fleet, planet)

    mock_validate.assert_called_once()
    mock_difficulty.assert_called_once()
    assert result['difficulty'] == 2
```

#### 2. Planet Model Mocking
```python
from backend.models import Planet

# ✅ CORRECT: Use real Planet objects for arithmetic operations
def create_mock_planet():
    planet = Planet(
        name='Test Colony',
        x=100, y=200, z=300,
        user_id=None,  # Unowned planet
        planet_type='terrestrial'
    )
    return planet
```

#### 3. Research Service Mocking
```python
@patch('backend.services.research_service.get_colonization_tech_level')
def test_tech_level_requirements(mock_tech_level):
    mock_tech_level.return_value = 2

    # Test with tech level 2
    can_colonize = check_colonization_requirements(user, planet)
    assert can_colonize == True
```

### Test Data Creation Patterns

#### 1. Colony Fleet Creation
```python
def create_test_colony_fleet(db_session, user_id, planet_id):
    """Create fleet with colony ship for testing"""
    fleet = Fleet(
        user_id=user_id,
        start_planet_id=planet_id,
        target_planet_id=planet_id,
        mission='stationed',
        status='stationed',
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow(),
        colony_ship=1,  # Required for colonization
        light_fighter=10,  # Escort ships
        cruiser=5
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet
```

#### 2. Unowned Planet Creation
```python
def create_test_unowned_planet(db_session, **kwargs):
    """Create unowned planet for colonization testing"""
    planet = Planet(
        name=kwargs.get('name', 'Unowned Planet'),
        x=kwargs.get('x', 100),
        y=kwargs.get('y', 200),
        z=kwargs.get('z', 300),
        user_id=None,  # Unowned
        planet_type=kwargs.get('planet_type', 'terrestrial'),
        metal=kwargs.get('metal', 1000),
        crystal=kwargs.get('crystal', 500),
        deuterium=kwargs.get('deuterium', 0)
    )
    db_session.add(planet)
    db_session.commit()
    return planet
```

#### 3. Research Setup for Testing
```python
def setup_test_research(db_session, user_id, tech_level):
    """Setup research levels for testing"""
    research = Research(
        user_id=user_id,
        colonization_tech=tech_level,
        energy_tech=max(tech_level, 1),  # Prerequisite
        # ... other research fields
    )
    db_session.add(research)
    db_session.commit()
    return research
```

---

## Detailed Test Plan

### Unit Test Coverage

#### 1. Colonization Service Tests
```python
class TestColonizationService:
    def test_validate_colonization_requirements_success(self):
        """Test successful colonization validation"""

    def test_validate_colonization_requirements_owned_planet(self):
        """Test validation fails for owned planet"""

    def test_calculate_colonization_difficulty_easy(self):
        """Test difficulty calculation for easy colonization"""

    def test_calculate_colonization_difficulty_extreme(self):
        """Test difficulty calculation for extreme colonization"""

    def test_initialize_new_colony_resources(self):
        """Test new colony gets correct starting resources"""

    def test_initialize_new_colony_ownership(self):
        """Test planet ownership transfer after colonization"""
```

#### 2. Colony Ship Tests
```python
class TestColonyShipMechanics:
    def test_validate_colony_fleet_composition_valid(self):
        """Test valid colony fleet composition"""

    def test_validate_colony_fleet_composition_no_colony_ship(self):
        """Test validation fails without colony ship"""

    def test_validate_colony_fleet_composition_insufficient_escort(self):
        """Test validation fails with insufficient escort"""

    def test_calculate_colonization_travel_time(self):
        """Test colonization travel time with difficulty modifier"""
```

#### 3. Research Requirement Tests
```python
class TestResearchRequirements:
    def test_check_research_requirements_sufficient(self):
        """Test research requirements met"""

    def test_check_research_requirements_insufficient(self):
        """Test research requirements not met"""

    def test_calculate_colony_limit_by_tech_level(self):
        """Test colony limits based on technology"""

    def test_calculate_max_colonization_distance(self):
        """Test maximum colonization distance"""
```

### Integration Test Coverage

#### 1. Colonization Workflow Tests
```python
class TestColonizationWorkflow:
    def test_complete_colonization_process(self, client, sample_user):
        """Test complete colonization workflow"""

    def test_colonization_fleet_departure(self, client, colony_fleet):
        """Test colony fleet departure"""

    def test_colonization_fleet_arrival(self, client, colony_fleet):
        """Test colony fleet arrival processing"""

    def test_colony_initialization(self, client, new_colony):
        """Test new colony initialization"""
```

#### 2. Planet Validation Tests
```python
class TestPlanetValidation:
    def test_validate_target_planet_unowned(self, client, unowned_planet):
        """Test validation passes for unowned planet"""

    def test_validate_target_planet_owned(self, client, owned_planet):
        """Test validation fails for owned planet"""

    def test_validate_target_planet_distance_limit(self, client, distant_planet):
        """Test validation fails for planets beyond distance limit"""
```

#### 3. Research Integration Tests
```python
class TestResearchIntegration:
    def test_colonization_with_research_bonus(self, client, user_with_research):
        """Test colonization with research difficulty reduction"""

    def test_colony_limit_enforcement(self, client, user_at_limit):
        """Test colony limit enforcement"""

    def test_technology_upgrade_effects(self, client, user_upgrading):
        """Test effects of technology upgrades"""
```

### End-to-End Test Coverage

#### 1. Complete Colonization Journey
```javascript
test('should complete full colonization workflow', async ({ page }) => {
  // Login and navigate to galaxy
  // Find unowned planet
  // Create colony fleet
  // Send colonization mission
  // Wait for arrival
  // Verify colony creation
  // Check colony resources and buildings
});
```

#### 2. Research Progression
```javascript
test('should handle research progression for colonization', async ({ page }) => {
  // Start with basic colonization tech
  // Research advanced colonization
  // Verify increased colony limits
  // Verify reduced colonization difficulty
  // Test new colonization abilities
});
```

#### 3. Multi-Colony Management
```javascript
test('should manage multiple colonies', async ({ page }) => {
  // Create multiple colonies
  // Switch between colonies
  // Verify resource production across colonies
  // Test colony-specific upgrades
  // Check colony happiness and population
});
```

### Performance Test Coverage

#### 1. Large-Scale Colonization
```python
def test_massive_colonization_operations():
    """Test colonization with many simultaneous operations"""

def test_colony_resource_calculation_performance():
    """Test resource calculations for many colonies"""
```

#### 2. Research Impact Testing
```python
def test_research_upgrade_performance():
    """Test research upgrade effects on colonization"""

def test_technology_tree_navigation():
    """Test navigation through colonization tech tree"""
```

### Edge Case Test Coverage

#### 1. Boundary Conditions
```python
def test_colonization_at_distance_limit():
    """Test colonization exactly at distance limit"""

def test_colony_limit_boundary():
    """Test attempting colonization at colony limit"""

def test_research_level_boundary():
    """Test research level boundary conditions"""
```

#### 2. Error Conditions
```python
def test_colonization_without_colony_ship():
    """Test colonization attempt without colony ship"""

def test_colonization_of_owned_planet():
    """Test attempting to colonize owned planet"""

def test_colonization_during_research():
    """Test colonization while research is in progress"""
```

#### 3. Race Conditions
```python
def test_simultaneous_colonization_attempts():
    """Test multiple users attempting same planet"""

def test_colonization_during_fleet_travel():
    """Test colonization attempts during fleet travel"""
```

### Test Execution Strategy

#### 1. Unit Tests
```bash
# Run colonization unit tests
pytest tests/unit/ -k "colonization" -v

# Run specific test class
pytest tests/unit/test_colonization_service.py::TestColonizationService -v
```

#### 2. Integration Tests
```bash
# Run colonization integration tests
pytest tests/integration/ -k "colonization" -v

# Run with coverage
pytest tests/integration/test_colonization_workflow.py --cov=backend.services.colonization_service --cov-report=html
```

#### 3. E2E Tests
```bash
# Run colonization E2E tests
npx playwright test tests/e2e/colonization.spec.js

# Run with debugging
npx playwright test tests/e2e/colonization.spec.js --headed --debug
```

### Test Data Management

#### 1. Test Database Setup
```python
@pytest.fixture
def colony_fleet(db_session, sample_user, sample_planet):
    """Create colony fleet for testing"""
    return create_test_colony_fleet(db_session, sample_user.id, sample_planet.id)

@pytest.fixture
def unowned_planet(db_session):
    """Create unowned planet for colonization testing"""
    return create_test_unowned_planet(db_session, x=500, y=600, z=700)

@pytest.fixture
def user_with_research(db_session, sample_user):
    """Create user with colonization research"""
    return setup_test_research(db_session, sample_user.id, tech_level=2)
```

#### 2. Test Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_colonies(db_session):
    """Clean up colonies after each test"""
    yield
    # Reset planet ownership and colony data
    db_session.query(Planet).filter(Planet.user_id.isnot(None)).update({
        'user_id': None,
        'colonization_lock': False,
        'locked_by_fleet': None
    })
    db_session.query(Fleet).filter(Fleet.mission == 'colonize').delete()
    db_session.commit()
```

### Continuous Integration

#### 1. Test Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Colonization Unit Tests
  run: pytest tests/unit/ -k "colonization" --cov=backend.services.colonization_service --cov-fail-under=90

- name: Run Colonization Integration Tests
  run: pytest tests/integration/ -k "colonization"

- name: Run Colonization E2E Tests
  run: npx playwright test tests/e2e/colonization.spec.js
```

#### 2. Test Reporting
```python
# Generate coverage reports
pytest tests/ -k "colonization" --cov=backend --cov-report=html --cov-report=xml

# Generate test reports
pytest tests/ -k "colonization" --junitxml=test-results.xml
```

This comprehensive test plan ensures complete coverage of colonization mechanics from colony ship validation through full colony management, with proper SQLAlchemy mocking patterns and robust error handling.
