# 🚀 __Planetarion Combat System UI - Complete Specification Draft__

## 📋 __Overview__

This specification outlines the complete UI implementation for the Planetarion combat system, including enhanced colonization mechanics and comprehensive battle reporting. The system transforms combat from pure destruction into strategic territorial warfare.

---

## 🎯 __Core Objectives__

### __Enhanced Colonization__

- Allow colonization of planets that have lost their defending fleets
- Create time-sensitive strategic opportunities
- Balance risk/reward for aggressive expansion

### __Combat Reports UI__

- Comprehensive battle history visualization
- Real-time combat updates
- Detailed round-by-round analysis
- Strategic combat intelligence

---

## ⚔️ __Enhanced Colonization Mechanics__

### __1. Defenseless Planet Detection__

#### __Backend Logic__

```python
def is_planet_defenseless(planet, exclude_user_id=None):
    """Check if a planet has no active defending fleets"""
    defending_fleets = Fleet.query.filter(
        Fleet.user_id == planet.user_id,
        Fleet.start_planet_id == planet.id,
        Fleet.status.in_(['stationed', 'defending']),
        Fleet.user_id != exclude_user_id  # Allow self-colonization
    ).all()
    
    return len(defending_fleets) == 0
```

#### __Colonization Window System__

```python
class ColonizationWindow:
    def __init__(self, planet, defeated_at):
        self.planet = planet
        self.defeated_at = defeated_at
        self.expires_at = defeated_at + timedelta(hours=24)  # 24-hour window
        self.attempts_used = 0
        self.max_attempts = 3  # Limited colonization attempts
```

### __2. Fleet Mission Types__

#### __Enhanced Attack Mission__

```javascript
// Fleet sending with colonization intent
const sendAttackFleet = async (fleetId, targetPlanetId, colonizationIntent = false) => {
  const response = await fetch('/api/fleet/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fleet_id: fleetId,
      mission: 'attack',
      target_planet_id: targetPlanetId,
      colonization_intent: colonizationIntent  // New flag
    })
  });
  return response.json();
};
```

#### __Rapid Colonization Mission__

```javascript
// Immediate colonization of defenseless planets
const colonizeDefenselessPlanet = async (fleetId, targetPlanetId) => {
  const response = await fetch('/api/fleet/colonize-defenseless', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fleet_id: fleetId,
      target_planet_id: targetPlanetId
    })
  });
  return response.json();
};
```

---

## 🎨 __UI Component Architecture__

### __1. Main Combat Dashboard__

#### __Component Structure__

```javascript
CombatDashboard/
├── CombatOverview.js          # Main combat statistics
├── ActiveCombats.js           # Current fleet engagements
├── ColonizationOpportunities.js # Available defenseless planets
├── RecentBattles.js           # Quick battle summaries
└── CombatNavigation.js        # Combat section navigation
```

#### __CombatOverview Component__

```javascript
const CombatOverview = ({ user }) => {
  const [stats, setStats] = useState({
    totalVictories: 0,
    totalDefeats: 0,
    planetsConquered: 0,
    planetsLost: 0,
    debrisCollected: 0,
    activeFleets: 0
  });

  useEffect(() => {
    fetchCombatStats();
    const interval = setInterval(fetchCombatStats, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="combat-overview grid grid-cols-1 md:grid-cols-3 gap-6">
      <StatCard title="Combat Record" value={`${stats.totalVictories}W - ${stats.totalDefeats}L`} />
      <StatCard title="Territorial Control" value={`${stats.planetsConquered} conquered`} />
      <StatCard title="Active Fleets" value={stats.activeFleets} />
    </div>
  );
};
```

### __2. Galaxy Map Integration__

#### __Enhanced Planet Markers__

```javascript
const PlanetMarker = ({ planet, user, onColonizeClick }) => {
  const isDefenseless = planet.isDefenseless && planet.user_id !== user.id;
  const canColonize = isDefenseless && planet.colonizationWindow?.isActive;
  
  return (
    <div className={`planet-marker ${planet.ownerClass}`}>
      {canColonize && (
        <div className="colonization-indicator animate-pulse">
          <button 
            onClick={() => onColonizeClick(planet)}
            className="colonize-button"
          >
            ⚠️ Colonize Opportunity
          </button>
        </div>
      )}
      
      {planet.hasDebris && (
        <div className="debris-indicator">
          <span className="debris-amount">{planet.debrisMetal + planet.debrisCrystal}</span>
        </div>
      )}
    </div>
  );
};
```

#### __Interactive Combat Actions__

```javascript
const CombatActions = ({ planet, userFleets, onAttack, onColonize }) => {
  const [selectedFleet, setSelectedFleet] = useState(null);
  const [missionType, setMissionType] = useState('attack');
  
  const availableFleets = userFleets.filter(fleet => 
    fleet.status === 'stationed' && 
    fleet.start_planet_id !== planet.id
  );
  
  return (
    <div className="combat-actions">
      <select 
        value={selectedFleet?.id || ''} 
        onChange={(e) => setSelectedFleet(availableFleets.find(f => f.id === e.target.value))}
      >
        <option value="">Select Fleet</option>
        {availableFleets.map(fleet => (
          <option key={fleet.id} value={fleet.id}>
            Fleet {fleet.id} ({fleet.totalShips} ships)
          </option>
        ))}
      </select>
      
      <div className="mission-buttons">
        <button 
          onClick={() => onAttack(selectedFleet, planet, false)}
          disabled={!selectedFleet}
        >
          Attack
        </button>
        
        <button 
          onClick={() => onAttack(selectedFleet, planet, true)}
          disabled={!selectedFleet}
        >
          Attack & Colonize
        </button>
        
        {planet.isDefenseless && (
          <button 
            onClick={() => onColonize(selectedFleet, planet)}
            disabled={!selectedFleet}
            className="colonize-button"
          >
            Colonize Now
          </button>
        )}
      </div>
    </div>
  );
};
```

### __3. Battle Reports System__

#### __BattleReports Component__

```javascript
const BattleReports = ({ user }) => {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [filter, setFilter] = useState('all'); // all, victories, defeats, recent
  
  useEffect(() => {
    fetchBattleReports();
    // Real-time updates
    const interval = setInterval(fetchBattleReports, 10000);
    return () => clearInterval(interval);
  }, [filter]);
  
  const fetchBattleReports = async () => {
    const response = await fetch(`/api/combat/reports?filter=${filter}`);
    const data = await response.json();
    setReports(data);
  };
  
  return (
    <div className="battle-reports">
      <div className="reports-header">
        <h2>Battle History</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All Battles</option>
          <option value="victories">Victories</option>
          <option value="defeats">Defeats</option>
          <option value="recent">Last 24 Hours</option>
        </select>
      </div>
      
      <div className="reports-list">
        {reports.map(report => (
          <BattleReportCard 
            key={report.id} 
            report={report} 
            onClick={() => setSelectedReport(report)}
          />
        ))}
      </div>
      
      {selectedReport && (
        <BattleReportDetail 
          report={selectedReport} 
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
};
```

#### __BattleReportCard Component__

```javascript
const BattleReportCard = ({ report, onClick }) => {
  const isVictory = report.winner_id === report.attacker_id;
  const timeAgo = formatTimeAgo(report.timestamp);
  
  return (
    <div 
      className={`battle-report-card ${isVictory ? 'victory' : 'defeat'}`}
      onClick={onClick}
    >
      <div className="report-header">
        <div className="outcome-indicator">
          {isVictory ? '🏆' : '💀'}
        </div>
        <div className="battle-info">
          <h3>{report.planet_name}</h3>
          <p>{report.attacker_name} vs {report.defender_name}</p>
          <span className="timestamp">{timeAgo}</span>
        </div>
      </div>
      
      <div className="casualties-summary">
        <div className="attacker-losses">
          Attacker: {calculateTotalLosses(report.attacker_losses)} ships lost
        </div>
        <div className="defender-losses">
          Defender: {calculateTotalLosses(report.defender_losses)} ships lost
        </div>
      </div>
      
      {report.debris_metal > 0 && (
        <div className="debris-info">
          Debris: {report.debris_metal} Metal, {report.debris_crystal} Crystal
        </div>
      )}
    </div>
  );
};
```

#### __BattleReportDetail Component__

```javascript
const BattleReportDetail = ({ report, onClose }) => {
  const [roundDetails, setRoundDetails] = useState([]);
  
  useEffect(() => {
    if (report.rounds) {
      setRoundDetails(JSON.parse(report.rounds));
    }
  }, [report]);
  
  return (
    <div className="battle-report-detail modal">
      <div className="modal-header">
        <h2>Detailed Battle Report</h2>
        <button onClick={onClose}>×</button>
      </div>
      
      <div className="battle-summary">
        <div className="participants">
          <div className="attacker">
            <h3>{report.attacker_name}</h3>
            <p>Attacker</p>
          </div>
          <div className="vs">VS</div>
          <div className="defender">
            <h3>{report.defender_name}</h3>
            <p>Defender</p>
          </div>
        </div>
        
        <div className="outcome">
          <h3>{report.winner_name} Wins!</h3>
        </div>
      </div>
      
      <div className="combat-rounds">
        <h3>Combat Rounds</h3>
        {roundDetails.map((round, index) => (
          <CombatRound 
            key={index} 
            round={round} 
            roundNumber={index + 1}
          />
        ))}
      </div>
      
      <div className="final-results">
        <div className="final-losses">
          <h4>Final Losses</h4>
          <div className="losses-breakdown">
            <ShipLosses losses={JSON.parse(report.attacker_losses)} label="Attacker" />
            <ShipLosses losses={JSON.parse(report.defender_losses)} label="Defender" />
          </div>
        </div>
        
        <div className="debris-field">
          <h4>Debris Field</h4>
          <p>{report.debris_metal} Metal, {report.debris_crystal} Crystal</p>
          {report.debris_recycled && (
            <p className="recycled-notice">Already collected</p>
          )}
        </div>
      </div>
    </div>
  );
};
```

#### __CombatRound Component__

```javascript
const CombatRound = ({ round, roundNumber }) => {
  return (
    <div className="combat-round">
      <h4>Round {roundNumber}</h4>
      
      <div className="round-stats">
        <div className="firepower">
          <div className="attacker-fire">
            Attacker Firepower: {round.attacker_fire}
          </div>
          <div className="defender-fire">
            Defender Firepower: {round.defender_fire}
          </div>
        </div>
        
        <div className="damage">
          <div className="attacker-damage">
            Attacker Damage Dealt: {round.attacker_damage}
          </div>
          <div className="defender-damage">
            Defender Damage Dealt: {round.defender_damage}
          </div>
        </div>
      </div>
      
      <div className="round-visualization">
        <CombatVisualization 
          attackerFire={round.attacker_fire}
          defenderFire={round.defender_fire}
          attackerDamage={round.attacker_damage}
          defenderDamage={round.defender_damage}
        />
      </div>
    </div>
  );
};
```

### __4. Colonization Opportunities Panel__

#### __ColonizationOpportunities Component__

```javascript
const ColonizationOpportunities = ({ user }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  
  useEffect(() => {
    fetchColonizationOpportunities();
    const interval = setInterval(fetchColonizationOpportunities, 15000); // Update every 15s
    return () => clearInterval(interval);
  }, []);
  
  const fetchColonizationOpportunities = async () => {
    const response = await fetch('/api/combat/colonization-opportunities');
    const data = await response.json();
    setOpportunities(data);
  };
  
  return (
    <div className="colonization-opportunities">
      <h3>Colonization Opportunities</h3>
      
      {opportunities.length === 0 ? (
        <p className="no-opportunities">No defenseless planets available</p>
      ) : (
        <div className="opportunities-list">
          {opportunities.map(planet => (
            <ColonizationCard 
              key={planet.id}
              planet={planet}
              onColonize={() => setSelectedOpportunity(planet)}
            />
          ))}
        </div>
      )}
      
      {selectedOpportunity && (
        <ColonizationDialog 
          planet={selectedOpportunity}
          userFleets={userFleets}
          onClose={() => setSelectedOpportunity(null)}
          onColonize={handleColonize}
        />
      )}
    </div>
  );
};
```

#### __ColonizationCard Component__

```javascript
const ColonizationCard = ({ planet, onColonize }) => {
  const timeRemaining = calculateTimeRemaining(planet.colonizationWindow.expiresAt);
  const isExpiringSoon = timeRemaining.hours < 1;
  
  return (
    <div className={`colonization-card ${isExpiringSoon ? 'urgent' : ''}`}>
      <div className="planet-info">
        <h4>{planet.name}</h4>
        <p>Coordinates: {planet.x}:{planet.y}:{planet.z}</p>
        <p>Previous Owner: {planet.previousOwner}</p>
      </div>
      
      <div className="colonization-details">
        <div className="time-remaining">
          <span className="timer">{formatTimeRemaining(timeRemaining)}</span>
          <span className="label">remaining</span>
        </div>
        
        <div className="planet-resources">
          <p>Metal: {planet.metal}</p>
          <p>Crystal: {planet.crystal}</p>
          <p>Deuterium: {planet.deuterium}</p>
        </div>
        
        <div className="buildings-present">
          {planet.buildings.map(building => (
            <span key={building.type} className="building-tag">
              {building.type} L{building.level}
            </span>
          ))}
        </div>
      </div>
      
      <button 
        onClick={onColonize}
        className="colonize-button"
        disabled={timeRemaining.expired}
      >
        {timeRemaining.expired ? 'Expired' : 'Colonize Now'}
      </button>
    </div>
  );
};
```

---

## 🔄 __User Interaction Flows__

### __1. Combat Initiation Flow__

```javascript
User clicks planet on galaxy map
→ Combat actions panel appears
→ User selects fleet and mission type
→ System validates fleet availability
→ Fleet sent with travel time calculation
→ Real-time fleet tracking begins
→ Combat resolves automatically on arrival
→ Battle report generated and displayed
```

### __2. Colonization Opportunity Flow__

```javascript
Combat results in planet becoming defenseless
→ System marks planet as colonization opportunity
→ Planet appears in colonization opportunities panel
→ Visual indicator on galaxy map
→ 24-hour countdown begins
→ User can send colonization fleet
→ Successful colonization transfers ownership
→ Opportunity expires or is claimed by another player
```

### __3. Battle Report Analysis Flow__

```javascript
User navigates to combat dashboard
→ Battle reports list loads
→ User can filter by outcome/time
→ Click report for detailed view
→ Round-by-round combat analysis
→ Debris field information
→ Strategic insights for future battles
```

---

## 📊 __Data Structures & API Requirements__

### __1. Enhanced Planet Model__

```javascript
const EnhancedPlanet = {
  id: number,
  name: string,
  x: number, y: number, z: number,
  user_id: number | null,
  previousOwner: string | null,
  isDefenseless: boolean,
  colonizationWindow: {
    isActive: boolean,
    expiresAt: Date,
    attemptsRemaining: number
  },
  hasDebris: boolean,
  debrisMetal: number,
  debrisCrystal: number,
  buildings: Building[],
  resources: Resources
};
```

### __2. Combat Report Model__

```javascript
const CombatReport = {
  id: number,
  timestamp: Date,
  planet_id: number,
  planet_name: string,
  attacker_id: number,
  attacker_name: string,
  defender_id: number,
  defender_name: string,
  winner_id: number,
  winner_name: string,
  rounds: CombatRound[],
  attacker_losses: ShipLosses,
  defender_losses: ShipLosses,
  debris_metal: number,
  debris_crystal: number,
  debris_recycled: boolean
};
```

### __3. API Endpoints__

#### __Combat Reports__

```javascript
GET /api/combat/reports?filter=all&limit=50
GET /api/combat/reports/:id
GET /api/combat/reports/recent
```

#### __Colonization Opportunities__

```javascript
GET /api/combat/colonization-opportunities
POST /api/fleet/colonize-defenseless
GET /api/combat/colonization-window/:planetId
```

#### __Combat Statistics__

```javascript
GET /api/combat/statistics
GET /api/combat/statistics/:userId
```

---

## 🎨 __UI/UX Design Specifications__

### __1. Color Scheme & Theming__

#### __Combat States__

```css
.combat-victory { background: linear-gradient(135deg, #4CAF50, #45a049); }
.combat-defeat { background: linear-gradient(135deg, #f44336, #d32f2f); }
.combat-active { background: linear-gradient(135deg, #FF9800, #F57C00); }

.colonization-opportunity { 
  border: 2px solid #FFD700;
  animation: pulse 2s infinite;
}

.debris-field {
  background: radial-gradient(circle, #FFA500, #FF8C00);
}
```

#### __Interactive Elements__

```css
.combat-button {
  background: #DC143C;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  transition: all 0.3s ease;
}

.combat-button:hover {
  background: #B22222;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.colonize-button {
  background: #FFD700;
  color: #000;
  animation: glow 1s ease-in-out infinite alternate;
}
```

### __2. Responsive Design__

#### __Mobile Layout__

```css
@media (max-width: 768px) {
  .combat-dashboard {
    flex-direction: column;
  }
  
  .battle-report-card {
    margin-bottom: 15px;
  }
  
  .combat-actions {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #1a1a1a;
    padding: 20px;
  }
}
```

#### __Tablet Layout__

```css
@media (min-width: 769px) and (max-width: 1024px) {
  .combat-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .battle-reports {
    max-height: 60vh;
    overflow-y: auto;
  }
}
```

---

## 🔧 __Technical Implementation__

### __1. State Management__

#### __Combat Context__

```javascript
const CombatContext = createContext();

const CombatProvider = ({ children }) => {
  const [activeCombats, setActiveCombats] = useState([]);
  const [colonizationOpportunities, setColonizationOpportunities] = useState([]);
  const [battleReports, setBattleReports] = useState([]);
  const [combatStats, setCombatStats] = useState({});
  
  // Real-time updates
  useEffect(() => {
    const ws = new WebSocket('/ws/combat');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleCombatUpdate(data);
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <CombatContext.Provider value={{
      activeCombats,
      colonizationOpportunities,
      battleReports,
      combatStats,
      sendAttackFleet,
      colonizePlanet,
      fetchBattleReports
    }}>
      {children}
    </CombatContext.Provider>
  );
```
