## ⚔️ __Combat System Implementation Plan__

### __Overview__

Implement a complete player vs player combat system with fleet battles, debris fields, battle reports, and strategic depth. This will be the core conflict mechanic that drives player engagement and empire growth.

---

## 📋 __Phase 1: Combat Models & Infrastructure__

### __1.1 Extend Fleet Model for Combat__

```python
# Add to Fleet model
combat_experience = db.Column(db.Integer, default=0)
last_combat_time = db.Column(db.DateTime)
combat_victories = db.Column(db.Integer, default=0)
combat_defeats = db.Column(db.Integer, default=0)
```

### __1.2 Create Combat Models__

```python
class CombatReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attacker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    defender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rounds = db.Column(db.Text)  # JSON of combat rounds
    attacker_losses = db.Column(db.Text)  # JSON of ship losses
    defender_losses = db.Column(db.Text)  # JSON of ship losses
    debris_metal = db.Column(db.BigInteger, default=0)
    debris_crystal = db.Column(db.BigInteger, default=0)

class DebrisField(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'))
    metal = db.Column(db.BigInteger, default=0)
    crystal = db.Column(db.BigInteger, default=0)
    deuterium = db.Column(db.BigInteger, default=0)
    recycler_fleet_id = db.Column(db.Integer, db.ForeignKey('fleets.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### __1.3 Ship Combat Stats__

```python
# Add to existing ship definitions
SHIP_STATS = {
    'small_cargo': {
        'hull': 4000, 'shield': 10, 'weapon': 5, 'speed': 5000,
        'cargo': 5000, 'fuel': 10
    },
    'large_cargo': {
        'hull': 12000, 'shield': 25, 'weapon': 5, 'speed': 7500,
        'cargo': 25000, 'fuel': 50
    },
    'light_fighter': {
        'hull': 4000, 'shield': 10, 'weapon': 50, 'speed': 12500,
        'cargo': 50, 'fuel': 20
    },
    'heavy_fighter': {
        'hull': 10000, 'shield': 25, 'weapon': 150, 'speed': 10000,
        'cargo': 100, 'fuel': 75
    },
    'cruiser': {
        'hull': 27000, 'shield': 50, 'weapon': 400, 'speed': 15000,
        'cargo': 800, 'fuel': 300
    },
    'battleship': {
        'hull': 60000, 'shield': 200, 'weapon': 1000, 'speed': 10000,
        'cargo': 1500, 'fuel': 500
    },
    'colony_ship': {
        'hull': 30000, 'shield': 100, 'weapon': 50, 'speed': 2500,
        'cargo': 7500, 'fuel': 1000
    }
}
```

---

## 🧮 __Phase 2: Combat Engine Service__

### __2.1 Core Combat Calculator__

```python
class CombatEngine:
    @staticmethod
    def calculate_battle(attacker_fleet, defender_fleet, defender_planet=None):
        """Main battle calculation engine"""
        rounds = []
        attacker_ships = CombatEngine._fleet_to_combat_ships(attacker_fleet)
        defender_ships = CombatEngine._fleet_to_combat_ships(defender_fleet)
        
        # Add planetary defenses if defending planet
        if defender_planet:
            defender_ships.update(CombatEngine._planet_defenses_to_ships(defender_planet))
        
        round_num = 1
        while CombatEngine._has_ships(attacker_ships) and CombatEngine._has_ships(defender_ships) and round_num <= 6:
            round_result = CombatEngine._calculate_round(attacker_ships, defender_ships)
            rounds.append(round_result)
            round_num += 1
        
        # Determine winner and calculate losses
        winner = 'attacker' if CombatEngine._has_ships(attacker_ships) else 'defender'
        
        return {
            'winner': winner,
            'rounds': rounds,
            'attacker_losses': CombatEngine._calculate_losses(attacker_fleet, attacker_ships),
            'defender_losses': CombatEngine._calculate_losses(defender_fleet, defender_ships),
            'debris': CombatEngine._calculate_debris(attacker_fleet, defender_fleet)
        }
```

### __2.2 Combat Round Logic__

```python
@staticmethod
def _calculate_round(attacker_ships, defender_ships):
    """Calculate a single round of combat"""
    # Rapid fire calculations
    attacker_fire = CombatEngine._calculate_firepower(attacker_ships, defender_ships, 'attacker')
    defender_fire = CombatEngine._calculate_firepower(defender_ships, attacker_ships, 'defender')
    
    # Shield absorption
    attacker_damage = CombatEngine._apply_shields(attacker_fire, defender_ships)
    defender_damage = CombatEngine._apply_shields(defender_fire, attacker_ships)
    
    # Hull damage
    CombatEngine._apply_hull_damage(attacker_damage, defender_ships)
    CombatEngine._apply_hull_damage(defender_damage, attacker_ships)
    
    return {
        'attacker_fire': attacker_fire,
        'defender_fire': defender_fire,
        'attacker_damage': attacker_damage,
        'defender_damage': defender_damage
    }
```

### __2.3 Rapid Fire & Weapon Systems__

```python
RAPID_FIRE = {
    'light_fighter': {'heavy_fighter': 2, 'cruiser': 6, 'battleship': 3},
    'heavy_fighter': {'small_cargo': 3, 'large_cargo': 4, 'cruiser': 4, 'battleship': 7},
    'cruiser': {'light_fighter': 6, 'heavy_fighter': 4, 'battleship': 7},
    'battleship': {'small_cargo': 3, 'large_cargo': 4}
}
```

---

## 🚀 __Phase 3: Combat Mission Types__

### __3.1 Attack Mission__

```python
# Extend fleet routes
elif data['mission'] == 'attack':
    # Validate target planet ownership
    target_planet = Planet.query.get(data['target_planet_id'])
    if not target_planet or target_planet.user_id == user_id:
        return jsonify({'error': 'Invalid attack target'}), 400
    
    # Check if target has defending fleet
    defending_fleet = Fleet.query.filter_by(
        user_id=target_planet.user_id,
        start_planet_id=data['target_planet_id'],
        status='stationed'
    ).first()
    
    if defending_fleet:
        # Fleet vs Fleet combat
        combat_result = CombatEngine.calculate_battle(fleet, defending_fleet)
    else:
        # Attack undefended planet (capture mechanics)
        combat_result = CombatEngine.calculate_planet_attack(fleet, target_planet)
```

### __3.2 Defend Mission__

```python
elif data['mission'] == 'defend':
    # Station fleet at planet for defense
    fleet.status = 'defending'
    fleet.mission = 'defend'
    # Fleet remains at planet until attacked or recalled
```

### __3.3 Espionage Mission__

```python
elif data['mission'] == 'espionage':
    # Spy on enemy planet/fleet
    # Requires espionage tech level
    # Reveals fleet composition, resources, defenses
```

---

## 🗂️ __Phase 4: Combat Resolution & Debris__

### __4.1 Fleet Arrival Combat Processing__

```python
# Extend FleetArrivalService
@staticmethod
def _process_attack(fleet):
    """Handle attack fleet arrival"""
    target_planet = Planet.query.get(fleet.target_planet_id)
    
    # Find defending fleet
    defending_fleet = Fleet.query.filter_by(
        user_id=target_planet.user_id,
        start_planet_id=fleet.target_planet_id,
        status__in=['stationed', 'defending']
    ).first()
    
    if defending_fleet:
        # Fleet vs Fleet combat
        combat_result = CombatEngine.calculate_battle(fleet, defending_fleet)
        CombatEngine.process_combat_result(combat_result, fleet, defending_fleet, target_planet)
    else:
        # Attack undefended planet
        combat_result = CombatEngine.calculate_planet_attack(fleet, target_planet)
        CombatEngine.process_planet_attack_result(combat_result, fleet, target_planet)
```

### __4.2 Debris Field Creation__

```python
@staticmethod
def _calculate_debris(attacker_fleet, defender_fleet):
    """Calculate debris from destroyed ships"""
    total_metal = 0
    total_crystal = 0
    
    # 30% of ship costs become debris
    for ship_type, count in attacker_fleet.get_ship_counts().items():
        if count <= 0:  # Ship type was destroyed
            ship_cost = SHIP_COSTS[ship_type]
            total_metal += int(ship_cost['metal'] * 0.3)
            total_crystal += int(ship_cost['crystal'] * 0.3)
    
    # Same for defender
    for ship_type, count in defender_fleet.get_ship_counts().items():
        if count <= 0:
            ship_cost = SHIP_COSTS[ship_type]
            total_metal += int(ship_cost['metal'] * 0.3)
            total_crystal += int(ship_cost['crystal'] * 0.3)
    
    return {'metal': total_metal, 'crystal': total_crystal}
```

### __4.3 Recycler Mission__

```python
elif data['mission'] == 'recycle':
    # Send recyclers to collect debris
    debris_field = DebrisField.query.filter_by(planet_id=data['target_planet_id']).first()
    if not debris_field:
        return jsonify({'error': 'No debris field at target'}), 404
    
    # Calculate collection capacity
    recycler_capacity = fleet.recycler * RECYCLER_CAPACITY
    collected_metal = min(debris_field.metal, recycler_capacity // 2)
    collected_crystal = min(debris_field.crystal, recycler_capacity // 2)
    
    # Update debris field
    debris_field.metal -= collected_metal
    debris_field.crystal -= collected_crystal
```

---

## 📊 __Phase 5: Battle Reports & UI__

### __5.1 Battle Report Generation__

```python
@staticmethod
def generate_battle_report(combat_result, attacker, defender, planet):
    """Create detailed battle report"""
    report = CombatReport(
        attacker_id=attacker.user_id,
        defender_id=defender.user_id,
        planet_id=planet.id,
        winner_id=attacker.user_id if combat_result['winner'] == 'attacker' else defender.user_id,
        rounds=json.dumps(combat_result['rounds']),
        attacker_losses=json.dumps(combat_result['attacker_losses']),
        defender_losses=json.dumps(combat_result['defender_losses']),
        debris_metal=combat_result['debris']['metal'],
        debris_crystal=combat_result['debris']['crystal']
    )
    
    db.session.add(report)
    return report
```

### __5.2 Frontend Combat UI__

```javascript
// GalaxyMap.js - Add attack buttons
const handleAttackPlanet = async (planet) => {
  if (planet.user_id === user.id) {
    alert('Cannot attack your own planet!');
    return;
  }
  
  // Similar to colonization but for attack
  const token = localStorage.getItem('token');
  const response = await fetch('http://localhost:5000/api/fleet/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      fleet_id: selectedFleet.id,
      mission: 'attack',
      target_planet_id: planet.id
    })
  });
  
  if (response.ok) {
    alert('Attack fleet sent!');
    await fetchNearbySystems();
  }
};
```

### __5.3 Battle Report Viewer__

```javascript
// New component: BattleReports.js
const BattleReports = ({ user }) => {
  const [reports, setReports] = useState([]);
  
  useEffect(() => {
    fetchBattleReports();
  }, []);
  
  const fetchBattleReports = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('http://localhost:5000/api/combat/reports', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const data = await response.json();
      setReports(data);
    }
  };
  
  return (
    <div className="battle-reports">
      {reports.map(report => (
        <div key={report.id} className="report-card">
          <h3>Battle at {report.planet_name}</h3>
          <p>Winner: {report.winner_username}</p>
          <p>Rounds: {report.rounds.length}</p>
          <div className="losses">
            <div>Attacker Losses: {JSON.parse(report.attacker_losses)}</div>
            <div>Defender Losses: {JSON.parse(report.defender_losses)}</div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 🧪 __Phase 6: Testing Strategy__

### __6.1 Unit Tests__

```python
# test_combat_engine.py
def test_basic_fleet_vs_fleet_combat():
    attacker = create_test_fleet('attacker', {'light_fighter': 100})
    defender = create_test_fleet('defender', {'light_fighter': 50})
    
    result = CombatEngine.calculate_battle(attacker, defender)
    
    assert result['winner'] == 'attacker'
    assert result['attacker_losses']['light_fighter'] < 100
    assert result['defender_losses']['light_fighter'] == 50

def test_rapid_fire_mechanics():
    attacker = create_test_fleet('attacker', {'cruiser': 10})
    defender = create_test_fleet('defender', {'light_fighter': 100})
    
    result = CombatEngine.calculate_battle(attacker, defender)
    
    # Cruiser has rapid fire 6 vs light fighters
    assert result['defender_losses']['light_fighter'] > 50
```

### __6.2 Integration Tests__

```python
# test_combat_api.py
def test_attack_mission_workflow(client, db_session):
    # Create attacker and defender
    attacker = create_test_user('attacker')
    defender = create_test_user('defender')
    
    # Create fleets
    attacker_fleet = create_test_fleet(attacker.id, {'light_fighter': 50})
    defender_fleet = create_test_fleet(defender.id, {'light_fighter': 25})
    
    # Send attack
    response = client.post('/api/fleet/send', 
        headers=get_auth_headers(attacker),
        json={
            'fleet_id': attacker_fleet.id,
            'mission': 'attack',
            'target_planet_id': defender_fleet.start_planet_id
        }
    )
    
    assert response.status_code == 200
    
    # Trigger tick to process combat
    trigger_manual_tick()
    
    # Verify battle report created
    reports = CombatReport.query.all()
    assert len(reports) == 1
```

### __6.3 E2E Tests__

```javascript
// test_combat_e2e.spec.js
test('should complete full combat workflow', async ({ page }) => {
  // Login as attacker
  await loginAsUser(page, 'attacker');
  
  // Create attack fleet
  await createCombatFleet(page, { light_fighter: 50 });
  
  // Navigate to galaxy and attack enemy planet
  await navigateToGalaxyMap(page);
  await initiateAttack(page, enemyPlanetId);
  
  // Verify attack fleet sent
  await expect(page.locator('text=Attack fleet sent')).toBeVisible();
  
  // Trigger combat processing
  await triggerTick(page);
  
  // Check battle reports
  await navigateToBattleReports(page);
  await expect(page.locator('.battle-report')).toBeVisible();
  
  // Verify debris field created
  await checkDebrisField(page, enemyPlanetId);
});
```

---

## 📈 __Implementation Timeline__

### __Week 1: Core Combat Engine__

- ✅ Combat models and database schema
- ✅ Ship stats and rapid fire system
- ✅ Basic battle calculation engine
- ✅ Unit tests for combat logic

### __Week 2: Mission Integration__

- ✅ Attack and defend mission types
- ✅ Fleet arrival combat processing
- ✅ Combat result application
- ✅ Integration tests for API endpoints

### __Week 3: Advanced Features__

- ✅ Debris fields and recycler missions
- ✅ Battle reports system
- ✅ Espionage mechanics
- ✅ Planet attack/capture logic

### __Week 4: UI & Polish__

- ✅ Frontend combat interface
- ✅ Battle report viewer
- ✅ Real-time combat updates
- ✅ E2E test coverage

---

## 🎯 __Success Criteria__

### __Functional Requirements__

- ✅ Fleet vs Fleet combat with realistic outcomes
- ✅ Ship-specific stats and rapid fire mechanics
- ✅ Debris field generation and recycling
- ✅ Detailed battle reports with round-by-round breakdown
- ✅ Planet attack and capture mechanics
- ✅ Espionage and intelligence gathering

### __Technical Requirements__

- ✅ Combat calculations complete within 100ms
- ✅ Battle reports stored efficiently (JSON compression)
- ✅ Real-time combat updates without page refresh
- ✅ Comprehensive test coverage (>90%)
- ✅ Error handling for edge cases

### __Balance Requirements__

- ✅ No single ship type overpowered
- ✅ Rapid fire provides strategic depth
- ✅ Debris collection incentivizes combat
- ✅ Research affects combat effectiveness
