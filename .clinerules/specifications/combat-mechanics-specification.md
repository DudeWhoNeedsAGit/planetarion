# Combat Mechanics Specification & Test Plan

## Overview

This document provides a comprehensive specification for the combat mechanics system, including fleet vs fleet battles, planetary defense, battle calculations, debris fields, and combat resolution. The combat system enables player vs player conflict and strategic warfare.

## Table of Contents

1. [Combat System Architecture](#combat-system-architecture)
2. [Ship Combat Statistics](#ship-combat-statistics)
3. [Battle Calculation Engine](#battle-calculation-engine)
4. [Combat Resolution Process](#combat-resolution-process)
5. [Debris Field Mechanics](#debris-field-mechanics)
6. [Planetary Defense](#planetary-defense)
7. [Test Infrastructure Setup](#test-infrastructure-setup)
8. [Detailed Test Plan](#detailed-test-plan)

---

## Combat System Architecture

### Core Components

#### 1. Combat Engine Service
```python
class CombatEngine:
    @staticmethod
    def calculate_battle(attacker_fleet, defender_fleet, defender_planet=None):
        """Main battle calculation engine"""

    @staticmethod
    def simulate_round(attacker_ships, defender_ships):
        """Simulate a single round of combat"""

    @staticmethod
    def apply_damage(ships, damage, shield_strength):
        """Apply damage to ships with shield absorption"""

    @staticmethod
    def calculate_rapid_fire(attacker_ship, defender_ship):
        """Calculate rapid fire bonus damage"""
```

#### 2. Battle Report Service
```python
class BattleReportService:
    @staticmethod
    def generate_battle_report(attacker, defender, rounds, final_losses, debris):
        """Generate detailed battle report"""

    @staticmethod
    def store_battle_report(report_data):
        """Store battle report in database"""

    @staticmethod
    def get_user_battle_reports(user_id, limit=50):
        """Retrieve user's battle history"""
```

#### 3. Fleet Combat Service
```python
class FleetCombatService:
    @staticmethod
    def validate_attack_mission(attacker_fleet, target_planet):
        """Validate attack mission requirements"""

    @staticmethod
    def process_attack_arrival(attacker_fleet, target_planet):
        """Process attacking fleet arrival and initiate combat"""

    @staticmethod
    def resolve_battle_outcome(attacker_fleet, defender_fleet, battle_result):
        """Process battle results and update fleets"""
```

---

## Ship Combat Statistics

### Combat Value System
```python
SHIP_COMBAT_STATS = {
    'light_fighter': {
        'hull': 4000,
        'shield': 10,
        'weapon': 50,
        'cargo': 50,
        'speed': 12500
    },
    'heavy_fighter': {
        'hull': 10000,
        'shield': 25,
        'weapon': 150,
        'cargo': 100,
        'speed': 10000
    },
    'cruiser': {
        'hull': 27000,
        'shield': 50,
        'weapon': 400,
        'cargo': 800,
        'speed': 15000
    },
    'battleship': {
        'hull': 60000,
        'shield': 200,
        'weapon': 1000,
        'cargo': 1500,
        'speed': 10000
    },
    'colony_ship': {
        'hull': 30000,
        'shield': 100,
        'weapon': 50,
        'cargo': 7500,
        'speed': 2500
    },
    'recycler': {
        'hull': 16000,
        'shield': 10,
        'weapon': 1,
        'cargo': 20000,
        'speed': 2000
    },
    'espionage_probe': {
        'hull': 100,
        'shield': 0.01,
        'weapon': 0.01,
        'cargo': 0,
        'speed': 100000000
    },
    'bomber': {
        'hull': 75000,
        'shield': 500,
        'weapon': 1000,
        'cargo': 500,
        'speed': 4000
    },
    'destroyer': {
        'hull': 110000,
        'shield': 500,
        'weapon': 2000,
        'cargo': 2000,
        'speed': 5000
    },
    'deathstar': {
        'hull': 9000000,
        'shield': 50000,
        'weapon': 200000,
        'cargo': 1000000,
        'speed': 100
    },
    'battlecruiser': {
        'hull': 70000,
        'shield': 400,
        'weapon': 700,
        'cargo': 750,
        'speed': 10000
    }
}
```

### Rapid Fire System
```python
RAPID_FIRE = {
    'light_fighter': {
        'heavy_fighter': 2,
        'cruiser': 6,
        'battleship': 3
    },
    'heavy_fighter': {
        'small_cargo': 3,
        'large_cargo': 4,
        'cruiser': 4,
        'battleship': 7
    },
    'cruiser': {
        'light_fighter': 6,
        'heavy_fighter': 4,
        'battleship': 7
    },
    'battleship': {
        'small_cargo': 3,
        'large_cargo': 4
    },
    'battlecruiser': {
        'small_cargo': 3,
        'large_cargo': 4,
        'light_fighter': 3,
        'heavy_fighter': 4,
        'cruiser': 4
    },
    'destroyer': {
        'espionage_probe': 1000,
        'light_fighter': 2
    },
    'deathstar': {
        'small_cargo': 250,
        'large_cargo': 250,
        'light_fighter': 200,
        'heavy_fighter': 100,
        'cruiser': 33,
        'battleship': 30,
        'colony_ship': 250,
        'recycler': 250,
        'espionage_probe': 1250,
        'bomber': 25,
        'destroyer': 5,
        'battlecruiser': 15
    }
}
```

---

## Battle Calculation Engine

### Combat Round Simulation
```python
def simulate_combat_round(attacker_fleet, defender_fleet):
    """Simulate a single round of combat"""

    # Calculate total firepower for each side
    attacker_firepower = calculate_fleet_firepower(attacker_fleet)
    defender_firepower = calculate_fleet_firepower(defender_fleet)

    # Apply rapid fire bonuses
    attacker_firepower = apply_rapid_fire(attacker_firepower, attacker_fleet, defender_fleet)
    defender_firepower = apply_rapid_fire(defender_firepower, defender_fleet, attacker_fleet)

    # Calculate damage absorption
    attacker_damage = calculate_damage(attacker_firepower, defender_fleet)
    defender_damage = calculate_damage(defender_firepower, attacker_fleet)

    # Apply damage to ships
    apply_damage_to_fleet(attacker_fleet, defender_damage)
    apply_damage_to_fleet(defender_fleet, attacker_damage)

    return {
        'attacker_firepower': attacker_firepower,
        'defender_firepower': defender_firepower,
        'attacker_damage': attacker_damage,
        'defender_damage': defender_damage,
        'attacker_losses': calculate_round_losses(attacker_fleet),
        'defender_losses': calculate_round_losses(defender_fleet)
    }
```

### Fleet Firepower Calculation
```python
def calculate_fleet_firepower(fleet):
    """Calculate total firepower of a fleet"""
    total_firepower = 0

    for ship_type, count in fleet.get_ship_counts().items():
        if count > 0:
            ship_stats = SHIP_COMBAT_STATS.get(ship_type, {})
            weapon_power = ship_stats.get('weapon', 0)
            total_firepower += weapon_power * count

    return total_firepower
```

### Damage Application
```python
def apply_damage_to_fleet(fleet, damage):
    """Apply damage to fleet with shield absorption"""
    remaining_damage = damage

    # First, damage shields
    remaining_damage = damage_shields(fleet, remaining_damage)

    # Then, damage hulls
    if remaining_damage > 0:
        damage_hulls(fleet, remaining_damage)

    return remaining_damage
```

### Shield Absorption
```python
def damage_shields(fleet, damage):
    """Apply damage to shields first"""
    total_shield_strength = 0

    # Calculate total shield strength
    for ship_type, count in fleet.get_ship_counts().items():
        if count > 0:
            ship_stats = SHIP_COMBAT_STATS.get(ship_type, {})
            shield_strength = ship_stats.get('shield', 0)
            total_shield_strength += shield_strength * count

    # Absorb damage with shields
    if total_shield_strength >= damage:
        # All damage absorbed by shields
        return 0
    else:
        # Shields depleted, return remaining damage
        return damage - total_shield_strength
```

---

## Combat Resolution Process

### Battle Flow
```python
def resolve_battle(attacker_fleet, defender_fleet, max_rounds=6):
    """Resolve complete battle between two fleets"""

    rounds = []
    round_number = 1

    while round_number <= max_rounds:
        # Check if battle should continue
        if not has_surviving_ships(attacker_fleet) or not has_surviving_ships(defender_fleet):
            break

        # Simulate combat round
        round_result = simulate_combat_round(attacker_fleet, defender_fleet)
        rounds.append(round_result)

        round_number += 1

    # Determine winner
    if has_surviving_ships(attacker_fleet) and not has_surviving_ships(defender_fleet):
        winner = 'attacker'
    elif not has_surviving_ships(attacker_fleet) and has_surviving_ships(defender_fleet):
        winner = 'defender'
    else:
        winner = 'draw'

    # Calculate final results
    final_result = {
        'winner': winner,
        'rounds': rounds,
        'attacker_losses': calculate_total_losses(attacker_fleet),
        'defender_losses': calculate_total_losses(defender_fleet),
        'debris': calculate_debris_field(attacker_fleet, defender_fleet)
    }

    return final_result
```

### Victory Conditions
```python
def has_surviving_ships(fleet):
    """Check if fleet has any surviving ships"""
    for ship_type, count in fleet.get_ship_counts().items():
        if count > 0:
            return True
    return False
```

### Loss Calculation
```python
def calculate_total_losses(fleet):
    """Calculate total losses for battle report"""
    losses = {}

    for ship_type in SHIP_COMBAT_STATS.keys():
        original_count = getattr(fleet, f'original_{ship_type}', 0)
        current_count = getattr(fleet, ship_type, 0)
        lost_count = original_count - current_count

        if lost_count > 0:
            losses[ship_type] = lost_count

    return losses
```

---

## Debris Field Mechanics

### Debris Generation
```python
def calculate_debris_field(attacker_fleet, defender_fleet):
    """Calculate debris field from destroyed ships"""
    debris = {'metal': 0, 'crystal': 0}

    # Calculate debris from both fleets
    for fleet in [attacker_fleet, defender_fleet]:
        for ship_type, lost_count in calculate_total_losses(fleet).items():
            if lost_count > 0:
                ship_cost = get_ship_cost(ship_type)
                # 30% of ship cost becomes debris
                debris['metal'] += int(ship_cost['metal'] * 0.3 * lost_count)
                debris['crystal'] += int(ship_cost['crystal'] * 0.3 * lost_count)

    return debris
```

### Debris Collection
```python
def collect_debris(recycler_fleet, debris_field):
    """Calculate debris collection by recycler fleet"""
    recycler_capacity = calculate_recycler_capacity(recycler_fleet)

    # Calculate collection amounts
    metal_collected = min(debris_field['metal'], recycler_capacity // 2)
    crystal_collected = min(debris_field['crystal'], recycler_capacity // 2)

    # Update debris field
    debris_field['metal'] -= metal_collected
    debris_field['crystal'] -= crystal_collected

    return {
        'metal_collected': metal_collected,
        'crystal_collected': crystal_collected,
        'remaining_metal': debris_field['metal'],
        'remaining_crystal': debris_field['crystal']
    }
```

### Recycler Capacity
```python
def calculate_recycler_capacity(fleet):
    """Calculate total recycler capacity"""
    recycler_count = getattr(fleet, 'recycler', 0)
    recycler_stats = SHIP_COMBAT_STATS.get('recycler', {})
    base_capacity = recycler_stats.get('cargo', 20000)

    return recycler_count * base_capacity
```

---

## Planetary Defense

### Defense Structure Combat Values
```python
DEFENSE_COMBAT_STATS = {
    'rocket_launcher': {
        'hull': 2000,
        'shield': 20,
        'weapon': 80
    },
    'light_laser': {
        'hull': 2000,
        'shield': 25,
        'weapon': 100
    },
    'heavy_laser': {
        'hull': 8000,
        'shield': 100,
        'weapon': 250
    },
    'gauss_cannon': {
        'hull': 35000,
        'shield': 200,
        'weapon': 1100
    },
    'ion_cannon': {
        'hull': 8000,
        'shield': 500,
        'weapon': 150
    },
    'plasma_turret': {
        'hull': 100000,
        'shield': 300,
        'weapon': 3000
    },
    'small_shield_dome': {
        'hull': 20000,
        'shield': 2000,
        'weapon': 1
    },
    'large_shield_dome': {
        'hull': 100000,
        'shield': 10000,
        'weapon': 1
    }
}
```

### Planetary Combat Integration
```python
def include_planetary_defenses(planet, defender_fleet):
    """Include planetary defenses in battle calculations"""

    # Add defense structures to fleet
    for defense_type, count in planet.get_defense_counts().items():
        if count > 0:
            defense_stats = DEFENSE_COMBAT_STATS.get(defense_type, {})
            # Add defense structures as additional ships
            defender_fleet.add_defense_ships(defense_type, count, defense_stats)

    return defender_fleet
```

### Shield Dome Effects
```python
def apply_shield_dome_bonus(fleet, planet):
    """Apply shield dome bonuses to fleet"""
    small_domes = getattr(planet, 'small_shield_dome', 0)
    large_domes = getattr(planet, 'large_shield_dome', 0)

    # Calculate shield bonus
    shield_bonus = (small_domes * 2000) + (large_domes * 10000)

    # Apply bonus to all ships in fleet
    for ship_type in fleet.get_ship_counts().keys():
        ship_stats = SHIP_COMBAT_STATS.get(ship_type, {})
        base_shield = ship_stats.get('shield', 0)
        # Shield domes provide percentage bonus
        bonus_multiplier = 1 + (shield_bonus / (base_shield * fleet.get_ship_count(ship_type)))
        fleet.apply_shield_bonus(ship_type, bonus_multiplier)

    return fleet
```

---

## Test Infrastructure Setup

### SQLAlchemy Mocking Patterns (Following systemPatterns.md)

#### 1. Combat Engine Mocking
```python
from unittest.mock import Mock, patch
from backend.services.combat_engine import CombatEngine

# ✅ CORRECT: Mock service methods with proper return values
@patch.object(CombatEngine, 'calculate_battle')
@patch.object(CombatEngine, 'resolve_battle_outcome')
def test_combat_resolution(mock_resolve, mock_calculate):
    mock_calculate.return_value = {
        'winner': 'attacker',
        'rounds': [],
        'attacker_losses': {},
        'defender_losses': {'light_fighter': 5},
        'debris': {'metal': 1000, 'crystal': 500}
    }

    # Test combat logic
    result = resolve_combat(attacker_fleet, defender_fleet)

    mock_calculate.assert_called_once()
    assert result['winner'] == 'attacker'
```

#### 2. Fleet Mocking for Combat
```python
from backend.models import Fleet

# ✅ CORRECT: Use real Fleet objects for combat calculations
def create_mock_combat_fleet():
    fleet = Fleet(
        user_id=1,
        start_planet_id=1,
        target_planet_id=2,
        mission='attack',
        status='traveling',
        light_fighter=10,
        heavy_fighter=5,
        cruiser=2
    )
    return fleet
```

#### 3. Battle Report Service Mocking
```python
@patch('backend.services.battle_report_service.generate_battle_report')
def test_battle_report_generation(mock_generate):
    mock_generate.return_value = {
        'id': 1,
        'attacker_id': 1,
        'defender_id': 2,
        'winner': 'attacker',
        'rounds': 3
    }

    # Test battle report logic
    report = generate_battle_report(attacker, defender, battle_result)
    assert report['winner'] == 'attacker'
```

### Test Data Creation Patterns

#### 1. Combat Fleet Creation
```python
def create_test_combat_fleet(db_session, user_id, planet_id, **kwargs):
    """Create fleet suitable for combat testing"""
    fleet = Fleet(
        user_id=user_id,
        start_planet_id=planet_id,
        target_planet_id=kwargs.get('target_planet_id', planet_id),
        mission=kwargs.get('mission', 'stationed'),
        status=kwargs.get('status', 'stationed'),
        departure_time=datetime.utcnow(),
        arrival_time=datetime.utcnow(),
        # Combat ships
        light_fighter=kwargs.get('light_fighter', 10),
        heavy_fighter=kwargs.get('heavy_fighter', 5),
        cruiser=kwargs.get('cruiser', 2),
        battleship=kwargs.get('battleship', 1)
    )
    db_session.add(fleet)
    db_session.commit()
    return fleet
```

#### 2. Planet with Defenses Creation
```python
def create_test_planet_with_defenses(db_session, user_id=None, **kwargs):
    """Create planet with defensive structures"""
    planet = Planet(
        name=kwargs.get('name', 'Fortress Planet'),
        x=kwargs.get('x', 1000),
        y=kwargs.get('y', 2000),
        z=kwargs.get('z', 3000),
        user_id=user_id,
        # Defense structures
        rocket_launcher=kwargs.get('rocket_launcher', 10),
        light_laser=kwargs.get('light_laser', 5),
        heavy_laser=kwargs.get('heavy_laser', 2),
        gauss_cannon=kwargs.get('gauss_cannon', 1),
        small_shield_dome=kwargs.get('small_shield_dome', 1)
    )
    db_session.add(planet)
    db_session.commit()
    return planet
```

#### 3. Battle Scenario Setup
```python
def setup_test_battle_scenario(db_session):
    """Setup complete battle scenario for testing"""
    # Create attacker
    attacker_user = create_test_user_with_hashed_password(db_session, 'attacker')
    attacker_planet = create_test_planet(db_session, attacker_user.id)
    attacker_fleet = create_test_combat_fleet(db_session, attacker_user.id, attacker_planet.id,
                                            light_fighter=20, cruiser=5)

    # Create defender
    defender_user = create_test_user_with_hashed_password(db_session, 'defender')
    defender_planet = create_test_planet_with_defenses(db_session, defender_user.id,
                                                      rocket_launcher=15, light_laser=8)
    defender_fleet = create_test_combat_fleet(db_session, defender_user.id, defender_planet.id,
                                            light_fighter=15, heavy_fighter=3)

    return {
        'attacker': attacker_fleet,
        'defender': defender_fleet,
        'attacker_planet': attacker_planet,
        'defender_planet': defender_planet
    }
```

---

## Detailed Test Plan

### Unit Test Coverage

#### 1. Combat Engine Tests
```python
class TestCombatEngine:
    def test_calculate_battle_attacker_wins(self):
        """Test battle calculation where attacker wins"""

    def test_calculate_battle_defender_wins(self):
        """Test battle calculation where defender wins"""

    def test_calculate_battle_draw(self):
        """Test battle calculation resulting in draw"""

    def test_simulate_combat_round_damage_calculation(self):
        """Test damage calculation in combat round"""

    def test_apply_rapid_fire_bonus(self):
        """Test rapid fire bonus application"""

    def test_shield_absorption_calculation(self):
        """Test shield damage absorption"""
```

#### 2. Fleet Combat Service Tests
```python
class TestFleetCombatService:
    def test_validate_attack_mission_success(self):
        """Test successful attack mission validation"""

    def test_validate_attack_mission_invalid_target(self):
        """Test attack mission validation with invalid target"""

    def test_process_attack_arrival_initiates_combat(self):
        """Test attack arrival triggers combat"""

    def test_resolve_battle_outcome_updates_fleets(self):
        """Test battle outcome resolution updates fleets correctly"""
```

#### 3. Debris Field Tests
```python
class TestDebrisFieldMechanics:
    def test_calculate_debris_field_from_battle(self):
        """Test debris field calculation from battle losses"""

    def test_collect_debris_with_recyclers(self):
        """Test debris collection by recycler fleet"""

    def test_recycler_capacity_calculation(self):
        """Test recycler fleet capacity calculation"""

    def test_partial_debris_collection(self):
        """Test partial debris collection when capacity exceeded"""
```

### Integration Test Coverage

#### 1. Combat Workflow Tests
```python
class TestCombatWorkflow:
    def test_complete_combat_process(self, client, battle_scenario):
        """Test complete combat workflow from attack to resolution"""

    def test_fleet_vs_fleet_combat(self, client, combat_fleets):
        """Test fleet vs fleet combat without planetary defenses"""

    def test_fleet_vs_planetary_defense(self, client, fleet_vs_planet):
        """Test fleet attacking planet with defensive structures"""

    def test_combat_with_shield_domes(self, client, shielded_planet):
        """Test combat with shield dome bonuses"""
```

#### 2. Battle Report Tests
```python
class TestBattleReports:
    def test_battle_report_generation(self, client, completed_battle):
        """Test battle report generation after combat"""

    def test_battle_report_storage(self, client, battle_report):
        """Test battle report storage in database"""

    def test_user_battle_history_retrieval(self, client, user_battles):
        """Test retrieving user's battle history"""

    def test_battle_report_detail_accuracy(self, client, detailed_report):
        """Test battle report contains accurate combat details"""
```

#### 3. Debris Collection Tests
```python
class TestDebrisCollection:
    def test_debris_field_creation_after_battle(self, client, battle_with_debris):
        """Test debris field creation after battle"""

    def test_recycler_fleet_debris_collection(self, client, recycler_fleet):
        """Test debris collection by recycler fleet"""

    def test_multiple_recycler_collection(self, client, multiple_recyclers):
        """Test debris collection with multiple recycler fleets"""

    def test_debris_field_depletion(self, client, depleted_debris):
        """Test behavior when debris field is depleted"""
```

### End-to-End Test Coverage

#### 1. Complete Combat Journey
```javascript
test('should complete full combat workflow', async ({ page }) => {
  // Login and navigate to galaxy map
  // Find enemy planet
  // Create attack fleet
  // Send attack mission
  // Wait for combat resolution
  // Verify battle report
  // Check debris field creation
  // Test debris collection
});
```

#### 2. Multi-Fleet Combat
```javascript
test('should handle multiple fleet combat', async ({ page }) => {
  // Create multiple attack fleets
  // Send simultaneous attacks
  // Verify combat resolution for all fleets
  // Check combined debris fields
  // Test recycler fleet coordination
});
```

#### 3. Planetary Defense Testing
```javascript
test('should test planetary defense effectiveness', async ({ page }) => {
  // Build defensive structures on planet
  // Create attack fleet
  // Send attack and monitor combat
  // Verify defense structure damage
  // Test shield dome effectiveness
  // Check repair mechanics
});
```

### Performance Test Coverage

#### 1. Large-Scale Combat
```python
def test_massive_fleet_combat():
    """Test combat with maximum fleet sizes"""

def test_multiple_simultaneous_battles():
    """Test multiple battles occurring simultaneously"""
```

#### 2. Combat Calculation Performance
```python
def test_combat_round_calculation_performance():
    """Test performance of combat round calculations"""

def test_battle_report_generation_performance():
    """Test performance of battle report generation"""
```

### Edge Case Test Coverage

#### 1. Boundary Conditions
```python
def test_combat_with_minimum_fleets():
    """Test combat with single ship fleets"""

def test_combat_with_maximum_fleets():
    """Test combat with maximum ship counts"""

def test_combat_round_limit():
    """Test combat reaching maximum round limit"""
```

#### 2. Error Conditions
```python
def test_combat_without_attacker_fleet():
    """Test combat attempt without attacking fleet"""

def test_combat_without_defender():
    """Test combat against undefended planet"""

def test_combat_during_fleet_travel():
    """Test combat attempts during fleet travel"""
```

#### 3. Race Conditions
```python
def test_simultaneous_attacks_same_target():
    """Test multiple fleets attacking same target"""

def test_combat_interruption():
    """Test combat interruption scenarios"""

def test_debris_collection_race_condition():
    """Test multiple recyclers collecting same debris field"""
```

### Test Execution Strategy

#### 1. Unit Tests
```bash
# Run combat unit tests
pytest tests/unit/ -k "combat" -v

# Run specific test class
pytest tests/unit/test_combat_engine.py::TestCombatEngine -v
```

#### 2. Integration Tests
```bash
# Run combat integration tests
pytest tests/integration/ -k "combat" -v

# Run with coverage
pytest tests/integration/test_combat_workflow.py --cov=backend.services.combat_engine --cov-report=html
```

#### 3. E2E Tests
```bash
# Run combat E2E tests
npx playwright test tests/e2e/combat.spec.js

# Run with debugging
npx playwright test tests/e2e/combat.spec.js --headed --debug
```

### Test Data Management

#### 1. Test Database Setup
```python
@pytest.fixture
def battle_scenario(db_session):
    """Create complete battle scenario for testing"""
    return setup_test_battle_scenario(db_session)

@pytest.fixture
def combat_fleets(db_session, sample_user, sample_planet):
    """Create fleets for combat testing"""
    attacker = create_test_combat_fleet(db_session, sample_user.id, sample_planet.id,
                                      light_fighter=20, cruiser=5)
    defender = create_test_combat_fleet(db_session, sample_user.id + 1, sample_planet.id + 1,
                                      light_fighter=15, heavy_fighter=3)
    return {'attacker': attacker, 'defender': defender}

@pytest.fixture
def recycler_fleet(db_session, sample_user, sample_planet):
    """Create recycler fleet for debris testing"""
    return create_test_fleet_with_constraints(
        db_session, sample_user.id, sample_planet.id,
        recycler=5, small_cargo=2
    )
```

#### 2. Test Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_combat_data(db_session):
    """Clean up combat-related data after each test"""
    yield
    # Reset fleet states
    db_session.query(Fleet).filter(Fleet.status.in_(['traveling', 'returning'])).update({
        'status': 'stationed',
        'mission': 'stationed'
    })
    # Remove debris fields
    db_session.query(DebrisField).delete()
    # Remove battle reports
    db_session.query(BattleReport).delete()
    db_session.commit()
```

### Continuous Integration

#### 1. Test Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Combat Unit Tests
  run: pytest tests/unit/ -k "combat" --cov=backend.services.combat_engine --cov-fail-under=90

- name: Run Combat Integration Tests
  run: pytest tests/integration/ -k "combat"

- name: Run Combat E2E Tests
  run: npx playwright test tests/e2e/combat.spec.js
```

#### 2. Test Reporting
```python
# Generate coverage reports
pytest tests/ -k "combat" --cov=backend --cov-report=html --cov-report=xml

# Generate test reports
pytest tests/ -k "combat" --junitxml=test-results.xml
```

This comprehensive test plan ensures complete coverage of combat mechanics from battle initiation through resolution and debris collection, with proper SQLAlchemy mocking patterns and robust error handling.
