{
  "milestones": [
    {
      "phase": 1,
      "name": "Interactive Map + Exploration",
      "note": "CURRENT STATUS: Galaxy map is fully implemented with no fog of war - all systems visible by default for simplified gameplay",
      "tasks": [
        { "id": "1.1", "description": "Implement galaxy map (2D grid, zoomable)", "status": "pending", "note": "COMPLETED: GalaxyMap.js with zoom, pan, and grid display" },
        { "id": "1.2", "description": "Add coordinate system (galaxy, system, position)", "status": "pending", "note": "COMPLETED: 3D coordinates (x,y,z) with proper scaling and display" },
        { "id": "1.3", "description": "Implement fog of war for unexplored stars", "status": "pending", "note": "DEFERRED: No fog of war implemented - all systems visible for gameplay simplicity" },
        { "id": "1.4", "description": "Fleet mission: explore → reveal system contents", "status": "pending", "note": "DEFERRED: Exploration mechanics not needed since no fog of war" },
        { "id": "1.5", "description": "System view with planets & placeholder black holes", "status": "pending", "note": "COMPLETED: System details view with planet information and black hole placeholders" }
      ]
    },
    {
      "phase": 2,
      "name": "Colonization Mechanics",
      "tasks": [
        { "id": "2.1", "description": "Assign random traits to planets (yield bonuses, caps)", "status": "pending" },
        { "id": "2.2", "description": "Fleet mission: colonize → establish new colony", "status": "pending" },
        { "id": "2.3", "description": "Implement colonization soft cap via research level", "status": "pending" },
        { "id": "2.4", "description": "Show colonized planets on map", "status": "pending" }
      ]
    },
    {
      "phase": 3,
      "name": "Black Hole Introduction",
      "tasks": [
        { "id": "3.1", "description": "Reveal black holes during exploration", "status": "pending" },
        { "id": "3.2", "description": "Black hole UI with mass, radius, stage, progress", "status": "pending" },
        { "id": "3.3", "description": "Fleet mission: feed → send resources/ships", "status": "pending" },
        { "id": "3.4", "description": "Implement feed cooldowns and combo streak bonuses", "status": "pending" },
        { "id": "3.5", "description": "Immediate loot feedback (shards, salvage, artifacts)", "status": "pending" }
      ]
    },
    {
      "phase": 4,
      "name": "Black Hole Growth & Swallow Events",
      "tasks": [
        { "id": "4.1", "description": "Implement radius scaling (k * mass^(1/3))", "status": "pending" },
        { "id": "4.2", "description": "Trigger swallow countdown for planets within radius", "status": "pending" },
        { "id": "4.3", "description": "Add evacuate/stabilizer player actions", "status": "pending" },
        { "id": "4.4", "description": "Swallow event: destroy planet, increase mass, generate loot", "status": "pending" },
        { "id": "4.5", "description": "Visual/audio feedback for swallow events", "status": "pending" }
      ]
    },
    {
      "phase": 5,
      "name": "Balancing & Feedback Polish",
      "tasks": [
        { "id": "5.1", "description": "Tune loot table probabilities", "status": "pending" },
        { "id": "5.2", "description": "Configure mass thresholds for stage progression", "status": "pending" },
        { "id": "5.3", "description": "Protective spawn rules for new players", "status": "pending" },
        { "id": "5.4", "description": "Polish UI: progress bars, feed animations, swallow cinematics", "status": "pending" },
        { "id": "5.5", "description": "Telemetry: feeds per session, swallow events, artifact drops", "status": "pending" }
      ]
    }
  ]
}

Review for phase 1:
## 🎯 __Current System Status Analysis__

### ✅ __Already Implemented (Surprisingly Complete):__

- __Planet ownership system__: `Planet.user_id` field exists
- __Colonization fleet missions__: Fleet system supports 'colonize' mission type
- __Research requirements__: `Research.colonization_tech` levels implemented
- __Galaxy map ownership display__: Different markers for owned/enemy systems
- __API endpoints__: `/api/fleet/send` with colonization validation
- __Distance calculations__: Fleet travel time based on 3D coordinates
- __UI components__: GalaxyMap with colonization buttons and planet details

### ❌ __Missing Components for Complete Colonization:__

1. __Fleet Arrival Processing__ - No logic to actually create colonies when fleets arrive
2. __Planet Transfer Logic__ - No mechanism to assign ownership after successful colonization
3. __Colony Initialization__ - New colonies need starting resources/buildings
4. __Home Planet Logic__ - Need to distinguish home planets from colonies
5. __Colony Limits__ - Research-based limits not enforced in UI
6. __Real-time Updates__ - Galaxy map doesn't refresh after colonization

## 🚀 __Detailed Phase 1 Implementation Plan__

### __1. Backend: Fleet Arrival Processing Service__

__File__: `game-server/src/backend/services/fleet_arrival.py` (new)

```python
class FleetArrivalService:
    @staticmethod
    def process_arrived_fleets():
        """Process all fleets that have arrived at their destinations"""
        arrived_fleets = Fleet.query.filter(
            Fleet.arrival_time <= datetime.utcnow(),
            Fleet.status.in_(['traveling', 'returning'])
        ).all()
        
        for fleet in arrived_fleets:
            if fleet.mission == 'colonize':
                FleetArrivalService._process_colonization(fleet)
            elif fleet.mission == 'return':
                FleetArrivalService._process_return(fleet)
            # ... other mission types
    
    @staticmethod
    def _process_colonization(fleet):
        """Handle colonization fleet arrival"""
        target_planet = Planet.query.filter_by(
            x=fleet.target_planet_id,  # This needs to be updated to use coordinates
            y=fleet.target_planet_id,
            z=fleet.target_planet_id
        ).first()
        
        if target_planet and not target_planet.user_id:
            # Successful colonization
            target_planet.user_id = fleet.user_id
            target_planet.metal = 1000  # Starting resources
            target_planet.crystal = 500
            target_planet.deuterium = 0
            
            # Create tick log entry
            tick_log = TickLog(
                planet_id=target_planet.id,
                event_type='colonization',
                event_description=f'Planet {target_planet.name} colonized by {fleet.user.username}'
            )
            db.session.add(tick_log)
        
        # Return fleet to stationed status
        fleet.status = 'stationed'
        fleet.mission = 'stationed'
        db.session.commit()
```

### __2. Database Schema Updates__

__File__: `game-server/src/backend/models.py`

```python
class Planet(db.Model):
    # ... existing fields ...
    
    # Add home planet flag
    is_home_planet = db.Column(db.Boolean, default=False)
    
    # Add colony creation timestamp
    colonized_at = db.Column(db.DateTime)
```

### __3. Enhanced Fleet API__

__File__: `game-server/src/backend/routes/fleet.py`

__Current Issue__: Fleet uses `target_planet_id` for coordinates, but colonization needs coordinate-based targeting.

```python
@fleet_mgmt_bp.route('/send', methods=['POST'])
@jwt_required()
def send_fleet():
    # ... existing code ...
    
    elif data['mission'] == 'colonize':
        # Enhanced colonization with coordinate targeting
        target_x = data.get('target_x')
        target_y = data.get('target_y') 
        target_z = data.get('target_z')
        
        if not all([target_x, target_y, target_z]):
            return jsonify({'error': 'Target coordinates required'}), 400
        
        # Check coordinates are unoccupied
        existing_planet = Planet.query.filter_by(x=target_x, y=target_y, z=target_z).first()
        if existing_planet:
            return jsonify({'error': 'Coordinates already occupied'}), 409
        
        # Store coordinates in fleet for arrival processing
        fleet.target_coordinates = f"{target_x}:{target_y}:{target_z}"
        fleet.mission = 'colonize'
        fleet.status = f'colonizing:{target_x}:{target_y}:{target_z}'
```

### __4. Tick Service Integration__

__File__: `game-server/src/backend/services/tick.py`

```python
def process_tick():
    """Main tick processing function"""
    # ... existing resource generation ...
    
    # Process arrived fleets
    from .fleet_arrival import FleetArrivalService
    FleetArrivalService.process_arrived_fleets()
    
    # ... rest of tick processing ...
```

### __5. Frontend: Real-time Galaxy Updates__

__File__: `game-server/src/frontend/src/GalaxyMap.js`

__Current Issue__: Galaxy data is fetched once on mount, doesn't update after colonization.

```javascript
// Add polling for galaxy updates
useEffect(() => {
  const interval = setInterval(() => {
    if (!loading) {
      fetchNearbySystems();
    }
  }, 10000); // Poll every 10 seconds
  
  return () => clearInterval(interval);
}, [loading]);
```

### __6. Enhanced Colonization UI__

__File__: `game-server/src/frontend/src/GalaxyMap.js`

__Current Issue__: Colonization button doesn't show proper feedback or handle success states.

```javascript
const handleColonizePlanet = async (planet) => {
  // ... existing code ...
  
  const sendResponse = await fetch('http://localhost:5000/api/fleet/send', {
    // ... existing code ...
  });
  
  if (sendResponse.ok) {
    const result = await sendResponse.json();
    alert(`Colonization fleet sent! ETA: ${result.fleet.eta} seconds`);
    
    // Refresh galaxy data immediately
    await fetchNearbySystems();
  }
};
```

### __7. Colony Management UI__

__File__: `game-server/src/frontend/src/Dashboard.js`

__Enhancement__: Add colony-specific features to planet management.

```javascript
// In planet selection, distinguish home planets from colonies
{planets.map(planet => (
  <button
    key={planet.id}
    onClick={() => setSelectedPlanet(planet)}
    className={`px-4 py-2 rounded whitespace-nowrap ${
      selectedPlanet?.id === planet.id
        ? 'bg-blue-600 text-white'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
    }`}
  >
    {planet.is_home_planet ? '🏠' : '🌍'} {planet.name} ({planet.coordinates})
  </button>
))}
```

## 📋 __Implementation Dependencies__

### __Phase 1A: Core Colonization (Week 1)__

1. ✅ Fleet arrival processing service
2. ✅ Database schema updates
3. ✅ Enhanced fleet coordinate targeting
4. ✅ Tick service integration

### __Phase 1B: UI Polish (Week 1-2)__

1. ✅ Real-time galaxy updates
2. ✅ Enhanced colonization feedback
3. ✅ Colony management UI
4. ✅ Home planet indicators

## 🎯 __Success Criteria__

- __Functional__: Players can send colonization fleets and establish new colonies
- __Visual__: Galaxy map updates in real-time showing new colony ownership
- __Balanced__: Research requirements and colony limits are enforced
- __Integrated__: New colonies appear in dashboard planet selection
- __Persistent__: Colony ownership survives server restarts

## 💡 __Technical Approach__

- __Incremental__: Build on existing fleet/planet systems
- __Test-Driven__: Add unit tests for fleet arrival processing
- __API-First__: Backend APIs drive frontend implementation
- __Real-time__: Polling-based updates for galaxy state
- __Robust__: Comprehensive error handling and validation

The system is actually __80% complete__ for colonization - we just need to connect the existing pieces and add the missing arrival processing logic. This makes Phase 1 much more achievable than initially thought.

Would you like me to proceed with implementing this plan, or would you prefer to discuss any specific aspects in more detail?
