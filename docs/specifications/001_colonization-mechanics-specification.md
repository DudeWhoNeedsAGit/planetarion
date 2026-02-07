# Colonization Mechanics Specification

## User Action Steps (Simple Format)

### Basic Colonization Flow
1. **Build colony ship** in Shipyard (requires: 2,500 Metal, 2,000 Crystal, 500 Deuterium)
2. **Go to Fleet Management** page
3. **Create fleet** with colony ship + optional escort ships
4. **Click "Send"** on the fleet
5. **Select target planet** from dropdown OR enter coordinates manually
6. **Choose "Colonize" mission**
7. **Click "Send"** to launch mission
8. **Monitor travel** in Fleet Management (shows ETA)
9. **Wait for arrival** (fleet status changes to "arrived")
10. **New colony appears** in planet selector

### Fleet Recall Process
1. **Go to Fleet Management**
2. **Find colonizing fleet** (shows "colonizing:X:Y:Z" status)
3. **Click "Recall"** button
4. **Confirm recall** (optional)
5. **Fleet returns** to origin planet
6. **ETA shows return time** (same as original travel time)

**Expected ETA after return**: Same duration as outbound journey (round trip = 2x distance)

---

## Core Mechanics

### Ship Requirements
- **Minimum**: 1 Colony Ship
- **Recommended**: Colony Ship + Light Fighters (5-10) for basic protection
- **Optional**: Cruisers/Battleships for heavy defense
- **Fuel**: Automatic calculation based on distance + ship types

### Target Selection
- **Planet Dropdown**: Shows unowned planets within range
- **Manual Coordinates**: Enter X:Y:Z directly
- **Range Limit**: Determined by research level + fuel capacity
- **Validation**: System checks ownership + research requirements

### Mission Parameters
- **Mission Type**: "colonize" (coordinate-based)
- **Travel Time**: `distance / fleet_speed` hours
- **Fleet Speed**: Determined by slowest ship (colony_ship = 2500 units/hour)
- **Fuel Cost**: Calculated automatically, deducted on launch

---

## Technical Calculations

### Distance Formula
```
distance = sqrt((x2-x1)² + (y2-y1)² + (z2-z1)²)
```

### Colonization Difficulty
```
difficulty = min(5, max(1, floor(distance_from_origin / 200)))
distance_from_origin = (abs(x) + abs(y) + abs(z)) / 3
```

### Travel Time
```
travel_time_hours = distance / slowest_ship_speed
slowest_ship_speed = min(ship_speeds_in_fleet)
colony_ship_speed = 2500
```

### Fuel Consumption
```
fuel_needed = distance * fuel_per_unit_distance * num_ships
fuel_per_unit_distance = ship_type_fuel_consumption / ship_speed
```

---

## Validation Rules

### Pre-Launch Validation
- ✅ **Colony Ship Present**: At least 1 colony ship required
- ✅ **Research Level**: `user.colonization_tech >= target_difficulty`
- ✅ **Colony Limit**: `user.colony_count < max_colonies`
- ✅ **Fuel Available**: Sufficient deuterium on origin planet
- ✅ **Target Valid**: Coordinates unoccupied, within range

### Runtime Validation
- ✅ **Arrival Check**: Target coordinates still unoccupied
- ✅ **Ownership Transfer**: Planet assigned to player
- ✅ **Resource Allocation**: Starting resources added

---

## Error Conditions

### Launch Failures
- **400 Error**: "Fleet must contain at least one colony ship"
- **400 Error**: "Colonization difficulty X requires research level X"
- **409 Error**: "Coordinates already occupied"
- **400 Error**: "Colony limit reached (X/X)"
- **400 Error**: "Insufficient fuel"

### Arrival Failures
- **409 Error**: "Planet already colonized during travel"
- **Fleet Lost**: If destroyed en route (future PvP feature)

---

## UI/UX Details

### Fleet Management Interface
- **Fleet List**: Shows all fleets with status, mission, ETA
- **Send Button**: Available for "stationed" fleets
- **Mission Dropdown**: attack, defend, transport, colonize, explore
- **Target Input**: Planet dropdown OR coordinate fields
- **Travel Info**: Distance, time, fuel cost preview

### Galaxy Map Integration
- **Planet Markers**: Different colors for owned/enemy/unowned
- **Click Actions**: View planet details, initiate colonization
- **Coordinate Display**: X:Y:Z format
- **Range Indicators**: Visual feedback for colonization range

### Real-time Updates
- **Fleet Status**: Updates every 30 seconds
- **Position Tracking**: Shows current location during travel
- **ETA Countdown**: Live timer in fleet details
- **Arrival Notifications**: Toast messages + UI updates

---

## Backend Processing

### Fleet Creation
```python
fleet = Fleet(
    user_id=user.id,
    start_planet_id=planet.id,
    target_planet_id=target_id,
    mission='colonize',
    status='stationed',
    colony_ship=ships['colony_ship'],
    departure_time=datetime.utcnow(),
    arrival_time=datetime.utcnow()
)
```

### Mission Launch
```python
# Calculate travel time
distance = calculate_distance(start_planet, target_planet)
travel_time = distance / fleet_speed

# Update fleet
fleet.status = f'colonizing:{target_x}:{target_y}:{target_z}'
fleet.arrival_time = datetime.utcnow() + timedelta(hours=travel_time)
fleet.eta = int(travel_time * 3600)  # seconds
```

### Arrival Processing
```python
# Check success conditions
if planet_available(target_coords):
    # Create new planet
    new_planet = Planet(
        x=target_x, y=target_y, z=target_z,
        user_id=fleet.user_id,
        metal=500, crystal=300, deuterium=100
    )
    # Transfer ownership
    db.session.add(new_planet)
    # Return fleet to stationed
    fleet.status = 'stationed'
    fleet.mission = 'stationed'
```

---

## Edge Cases & Special Scenarios

### Multiple Colony Ships
- **Behavior**: Only first successful colonization counts
- **Subsequent Fleets**: Automatically return to origin
- **Resource Waste**: Extra colony ships provide no benefit

### Simultaneous Colonization
- **Race Condition**: First fleet to arrive claims planet
- **Timing**: Exact arrival time determines winner
- **Notification**: Losing players notified of failed colonization

### Research Level Changes
- **During Travel**: Research upgrades don't affect en route fleets
- **Post-Arrival**: New colonies use current research levels
- **Validation**: Checked at launch time, not arrival

### Fuel Shortages
- **Launch Prevention**: Insufficient fuel blocks mission
- **Partial Fuel**: System calculates maximum range possible
- **Emergency Return**: Future feature for stranded fleets

---

## Strategic Considerations

### Early Game
- **Priority**: Research colonization tech to level 1
- **Targets**: Nearby planets (difficulty 1-2)
- **Defense**: Minimal escort ships needed
- **Timing**: Colonize before other players

### Mid Game
- **Expansion**: Target resource-rich planets
- **Defense**: Add cruisers for protection
- **Positioning**: Consider mutual support between colonies
- **Research**: Upgrade to access distant planets

### Late Game
- **Specialization**: Dedicate colonies to specific resources
- **Networks**: Create defensive constellations
- **Forward Bases**: Use colonies as expansion hubs
- **Risk Management**: Balance expansion speed vs defense

---

## Performance & Scaling

### Database Impact
- **Fleet Queries**: Indexed by user_id for fast retrieval
- **Planet Creation**: Minimal impact, planets are lightweight
- **Travel Updates**: Position calculations every 30 seconds
- **Concurrent Colonization**: Race condition handling

### Frontend Performance
- **Real-time Updates**: Polling every 30 seconds for fleet status
- **Map Rendering**: Efficient for 1000+ planets
- **UI Responsiveness**: Instant feedback for user actions
- **Memory Usage**: Minimal state for fleet tracking

---

## Future Enhancements

### Planned Features
- **Fleet Interception**: PvP combat during colonization
- **Colony Evacuation**: Emergency return capabilities
- **Advanced Scouting**: Detailed planet information
- **Colony Templates**: Pre-configured building queues
- **Alliance Coordination**: Shared colonization intelligence

### Technical Debt
- **Coordinate Validation**: More robust range checking
- **Fuel Optimization**: Dynamic fuel calculations
- **Travel Prediction**: More accurate ETA calculations
- **Error Recovery**: Better handling of failed missions

---

## Testing Scenarios

### Unit Tests
- ✅ Distance calculations
- ✅ Difficulty formulas
- ✅ Fuel consumption
- ✅ Travel time calculations

### Integration Tests
- ✅ Full colonization workflow
- ✅ Error condition handling
- ✅ Concurrent colonization
- ✅ Research level validation

### E2E Tests
- ✅ User interface flow
- ✅ Real-time updates
- ✅ Error message display
- ✅ Multi-planet management

---

## API Endpoints

### Fleet Management
```
GET  /api/fleet          # List user fleets
POST /api/fleet          # Create new fleet
POST /api/fleet/send     # Send fleet on mission
POST /api/fleet/recall/:id # Recall traveling fleet
```

### Planet Information
```
GET  /api/planets        # List user planets
GET  /api/planets/:id    # Planet details
POST /api/planets/scan   # Scan target coordinates
```

### Research Status
```
GET  /api/research       # Current research levels
POST /api/research       # Start research project
```

---

## Configuration Constants

```python
# Ship specifications
COLONY_SHIP_COST = {'metal': 2500, 'crystal': 2000, 'deuterium': 500}
COLONY_SHIP_SPEED = 2500
COLONY_SHIP_FUEL = 1000

# Game constants
BASE_COLONY_LIMIT = 5
RESEARCH_COLONY_BONUS = 2  # per astrophysics level
DIFFICULTY_DIVISOR = 200
MAX_DIFFICULTY = 5
MIN_DIFFICULTY = 1

# Starting resources for new colonies
COLONY_STARTING_RESOURCES = {
    'metal': 500,
    'crystal': 300,
    'deuterium': 100
}
```

---

## Monitoring & Analytics

### Key Metrics
- **Colonization Success Rate**: Successful vs failed attempts
- **Average Travel Time**: Distance vs time correlation
- **Research Level Distribution**: Player progression tracking
- **Colony Distribution**: Empire expansion patterns

### Error Tracking
- **Failed Launches**: Most common failure reasons
- **Travel Interruptions**: Fleet loss incidents
- **Race Conditions**: Simultaneous colonization conflicts
- **Performance Issues**: Slow query identification

---

This specification provides complete coverage of the colonization mechanics for LLM ingestion, with concise user steps and comprehensive technical details.
