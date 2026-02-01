# 🔗 **API ENDPOINTS SPECIFICATION**

## **Authentication Endpoints** (`/api/auth`)

### `POST /api/auth/register`
**Purpose**: User registration with automatic starting planet creation
**Auth**: None
**Request Body**:
```json
{
  "username": "string (required)",
  "email": "string (required, email format)",
  "password": "string (required, min 8 chars)"
}
```
**Response 201**:
```json
{
  "message": "User registered successfully",
  "access_token": "string",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string"
  }
}
```
**Errors**: 400 (missing fields/invalid email), 409 (username/email exists), 500 (server error)

### `POST /api/auth/login`
**Purpose**: User authentication with JWT token generation
**Auth**: None
**Request Body**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```
**Response 200**:
```json
{
  "message": "Login successful",
  "token": "string (backward compatibility)",
  "access_token": "string (JWT token)",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string"
  }
}
```
**Errors**: 400 (missing fields), 401 (invalid credentials), 500 (server error)

### `GET /api/auth/me`
**Purpose**: Get current authenticated user profile
**Auth**: JWT required
**Response 200**:
```json
{
  "id": "integer",
  "username": "string",
  "email": "string",
  "created_at": "ISO datetime string"
}
```
**Errors**: 401 (unauthorized), 404 (user not found)

## **Fleet Management Endpoints** (`/api/fleet`)

### `GET /api/fleet`
**Purpose**: Retrieve all fleets for authenticated user
**Auth**: JWT required
**Query Params**: None
**Response 200**:
```json
[
  {
    "id": "integer",
    "mission": "string (stationed/traveling/returning/exploring/colonizing)",
    "start_planet_id": "integer",
    "target_planet_id": "integer",
    "status": "string",
    "ships": {
      "small_cargo": "integer",
      "large_cargo": "integer",
      "light_fighter": "integer",
      "heavy_fighter": "integer",
      "cruiser": "integer",
      "battleship": "integer",
      "colony_ship": "integer",
      "recycler": "integer",
      "espionage_probe": "integer",
      "bomber": "integer",
      "destroyer": "integer",
      "deathstar": "integer",
      "battlecruiser": "integer"
    },
    "departure_time": "ISO datetime string | null",
    "arrival_time": "ISO datetime string | null",
    "eta": "integer (seconds remaining)",
    "travel_info": {
      "distance": "float",
      "speed": "float",
      "travel_time_hours": "float"
    },
    "start_planet": {
      "id": "integer",
      "name": "string",
      "coordinates": "string (x:y:z)"
    },
    "target_planet": {
      "id": "integer",
      "name": "string",
      "coordinates": "string (x:y:z)"
    } | null
  }
]
```
**Errors**: 401 (unauthorized), 500 (server error)

### `POST /api/fleet`
**Purpose**: Create new fleet with ship composition
**Auth**: JWT required
**Request Body**:
```json
{
  "start_planet_id": "integer (required)",
  "ships": {
    "small_cargo": "integer (optional)",
    "large_cargo": "integer (optional)",
    "light_fighter": "integer (optional)",
    "heavy_fighter": "integer (optional)",
    "cruiser": "integer (optional)",
    "battleship": "integer (optional)",
    "colony_ship": "integer (optional)",
    "recycler": "integer (optional)",
    "espionage_probe": "integer (optional)",
    "bomber": "integer (optional)",
    "destroyer": "integer (optional)",
    "deathstar": "integer (optional)",
    "battlecruiser": "integer (optional)"
  }
}
```
**Response 201**:
```json
{
  "message": "Fleet created successfully",
  "fleet": {
    "id": "integer",
    "mission": "string",
    "start_planet_id": "integer",
    "target_planet_id": "integer",
    "status": "string",
    "ships": { /* same as request */ }
  }
}
```
**Errors**: 400 (missing fields/invalid planet/no ships), 401 (unauthorized), 404 (planet not found), 500 (server error)

### `POST /api/fleet/send`
**Purpose**: Send fleet on mission with travel calculations
**Auth**: JWT required
**Request Body**:
```json
{
  "fleet_id": "integer (required)",
  "mission": "string (required: attack/defend/recycle/colonize/explore)",
  "target_planet_id": "integer (optional, for planet-based missions)",
  "target_x": "integer (optional, for exploration)",
  "target_y": "integer (optional, for exploration)",
  "target_z": "integer (optional, for exploration)"
}
```
**Response 200**:
```json
{
  "message": "Fleet sent successfully",
  "fleet": {
    "id": "integer",
    "mission": "string",
    "target_planet_id": "integer",
    "status": "string",
    "departure_time": "ISO datetime string",
    "arrival_time": "ISO datetime string",
    "eta": "integer (seconds)"
  }
}
```
**Errors**: 400 (missing fields/invalid mission/fleet not available), 401 (unauthorized), 404 (fleet/planet not found), 500 (server error)

### `POST /api/fleet/recall/<fleet_id>`
**Purpose**: Recall traveling fleet to origin
**Auth**: JWT required
**URL Params**: `fleet_id` (integer)
**Request Body**: None
**Response 200**:
```json
{
  "message": "Fleet recalled successfully",
  "fleet": {
    "id": "integer",
    "status": "string (returning)",
    "mission": "string (return)",
    "arrival_time": "ISO datetime string",
    "eta": "integer (seconds)",
    "ships": { /* ship counts */ }
  }
}
```
**Errors**: 400 (fleet cannot be recalled), 401 (unauthorized), 404 (fleet not found), 500 (server error)

### `DELETE /api/fleet/clear-all`
**Purpose**: Clear all fleets for authenticated user (testing/debug)
**Auth**: JWT required
**Response 200**:
```json
{
  "message": "Cleared X fleets successfully",
  "deleted_count": "integer"
}
```
**Errors**: 401 (unauthorized), 500 (server error)

## **Planet Management Endpoints** (`/api/planet`)

### `GET /api/planet`
**Purpose**: Get all planets owned by authenticated user
**Auth**: JWT required
**Response 200**:
```json
[
  {
    "id": "integer",
    "name": "string",
    "coordinates": "string (x:y:z)",
    "resources": {
      "metal": "integer",
      "crystal": "integer",
      "deuterium": "integer"
    },
    "structures": {
      "metal_mine": "integer",
      "crystal_mine": "integer",
      "deuterium_synthesizer": "integer",
      "solar_plant": "integer",
      "fusion_reactor": "integer"
    },
    "production_rates": {
      "metal_per_hour": "integer",
      "crystal_per_hour": "integer",
      "deuterium_per_hour": "integer",
      "energy_production": "integer",
      "energy_consumption": "integer"
    }
  }
]
```
**Errors**: 401 (unauthorized), 500 (server error)

### `GET /api/planet/<planet_id>`
**Purpose**: Get detailed information for specific planet
**Auth**: JWT required
**URL Params**: `planet_id` (integer)
**Response 200**: Same structure as single planet in array above
**Errors**: 401 (unauthorized), 404 (planet not found), 500 (server error)

### `PUT /api/planet/buildings`
**Purpose**: Upgrade buildings on planet
**Auth**: JWT required
**Request Body**:
```json
{
  "planet_id": "integer (required)",
  "buildings": {
    "metal_mine": "integer (new level)",
    "crystal_mine": "integer (new level)",
    "deuterium_synthesizer": "integer (new level)",
    "solar_plant": "integer (new level)",
    "fusion_reactor": "integer (new level)"
  }
}
```
**Response 200**:
```json
{
  "message": "Buildings updated successfully",
  "resources": {
    "metal": "integer (remaining)",
    "crystal": "integer (remaining)",
    "deuterium": "integer (remaining)"
  },
  "structures": { /* updated building levels */ }
}
```
**Errors**: 400 (missing fields/insufficient resources), 401 (unauthorized), 404 (planet not found), 500 (server error)

## **Public Planet Endpoints** (`/api`)

### `GET /api/planets`
**Purpose**: Get all planets (public/admin access)
**Auth**: None
**Response 200**:
```json
[
  {
    "id": "integer",
    "name": "string",
    "coordinates": "string (x:y:z)",
    "user_id": "integer | null",
    "resources": {
      "metal": "integer",
      "crystal": "integer",
      "deuterium": "integer"
    },
    "structures": { /* building levels */ }
  }
]
```
**Errors**: 500 (server error)

### `GET /api/planets/<planet_id>`
**Purpose**: Get specific planet details (public)
**Auth**: None
**URL Params**: `planet_id` (integer)
**Response 200**: Same structure as single planet in array above
**Errors**: 404 (planet not found), 500 (server error)

### `GET /api/galaxy/system/<x>/<y>/<z>`
**Purpose**: Get all planets in specific system coordinates
**Auth**: None
**URL Params**: `x`, `y`, `z` (integers)
**Response 200**:
```json
[
  {
    "id": "integer",
    "name": "string",
    "coordinates": "string (x:y:z)",
    "user_id": "integer | null",
    "owner_name": "string | null"
  }
]
```
**Errors**: 500 (server error)

### `GET /api/galaxy/nearby/<center_x>/<center_y>/<center_z>`
**Purpose**: Get nearby systems for exploration
**Auth**: None (currently, TODO: add JWT)
**URL Params**: `center_x`, `center_y`, `center_z` (integers)
**Response 200**:
```json
[
  {
    "x": "integer",
    "y": "integer",
    "z": "integer",
    "planets": "integer",
    "explored": "boolean",
    "owner_id": "integer | null"
  }
]
```
**Errors**: 500 (server error)

### `POST /api/planets`
**Purpose**: Create new planet (admin/setup)
**Auth**: None
**Request Body**:
```json
{
  "name": "string (required)",
  "x": "integer (required)",
  "y": "integer (required)",
  "z": "integer (required)",
  "user_id": "integer (required)"
}
```
**Response 201**:
```json
{
  "id": "integer",
  "name": "string",
  "coordinates": "string (x:y:z)",
  "user_id": "integer"
}
```
**Errors**: 400 (missing fields), 404 (user not found), 409 (coordinates occupied), 500 (server error)

## **Shipyard Endpoints** (`/api/shipyard`)

### `POST /api/shipyard/build`
**Purpose**: Build ships on planet
**Auth**: JWT required
**Request Body**:
```json
{
  "planet_id": "integer (required)",
  "ship_type": "string (required)",
  "quantity": "integer (required, > 0)"
}
```
**Response 200**:
```json
{
  "message": "Successfully built X ship_type(s)",
  "planet_resources": {
    "metal": "integer",
    "crystal": "integer",
    "deuterium": "integer"
  },
  "fleet": {
    "id": "integer",
    /* ship counts */
  }
}
```
**Errors**: 400 (missing fields/invalid ship type/insufficient resources), 401 (unauthorized), 404 (planet not found), 500 (server error)

### `GET /api/shipyard/costs`
**Purpose**: Get construction costs for all ship types
**Auth**: None
**Response 200**:
```json
{
  "small_cargo": {
    "metal": 2000,
    "crystal": 2000,
    "deuterium": 0
  },
  "large_cargo": {
    "metal": 6000,
    "crystal": 6000,
    "deuterium": 0
  },
  /* ... all ship types */
}
```
**Errors**: 500 (server error)

### `GET /api/shipyard/stats`
**Purpose**: Get comprehensive ship statistics
**Auth**: None
**Response 200**: Array of ship stat objects
**Errors**: 500 (server error)

### `GET /api/shipyard/stats/<ship_type>`
**Purpose**: Get statistics for specific ship type
**Auth**: None
**URL Params**: `ship_type` (string)
**Response 200**: Ship statistics object
**Errors**: 404 (ship type not found), 500 (server error)

### `GET /api/shipyard/roles`
**Purpose**: Get ship roles and ships by role
**Auth**: None
**Response 200**:
```json
{
  "roles": ["cargo", "fighter", "capital", "special"],
  "ships_by_role": {
    "cargo": ["small_cargo", "large_cargo"],
    "fighter": ["light_fighter", "heavy_fighter"],
    "capital": ["cruiser", "battleship"],
    "special": ["colony_ship", "recycler"]
  }
}
```
**Errors**: 500 (server error)

### `GET /api/shipyard/roles/<role>`
**Purpose**: Get all ships of specific role
**Auth**: None
**URL Params**: `role` (string)
**Response 200**: Array of ship type strings
**Errors**: 404 (role not found), 500 (server error)

## **Research Endpoints** (`/api/research`)

### `GET /api/research`
**Purpose**: Get user's current research status
**Auth**: JWT required
**Response 200**:
```json
{
  "research_points": "integer",
  "levels": {
    "colonization_tech": "integer",
    "astrophysics": "integer",
    "interstellar_communication": "integer"
  },
  "next_level_costs": {
    "colonization_tech": "integer",
    "astrophysics": "integer",
    "interstellar_communication": "integer"
  }
}
```
**Errors**: 401 (unauthorized), 500 (server error)

### `POST /api/research/upgrade/<research_type>`
**Purpose**: Upgrade specific research technology
**Auth**: JWT required
**URL Params**: `research_type` (string)
**Response 200**:
```json
{
  "message": "research_type upgraded to level X",
  "new_level": "integer",
  "research_points_remaining": "integer",
  "next_upgrade_cost": "integer"
}
```
**Errors**: 400 (invalid research type/insufficient points), 401 (unauthorized), 500 (server error)

### `GET /api/research/points`
**Purpose**: Get current research points (real-time)
**Auth**: JWT required
**Response 200**:
```json
{
  "research_points": "integer",
  "last_updated": "ISO datetime string"
}
```
**Errors**: 401 (unauthorized), 500 (server error)

### `GET /api/research/info/<research_type>`
**Purpose**: Get detailed research information
**Auth**: JWT required
**URL Params**: `research_type` (string)
**Response 200**:
```json
{
  "name": "string",
  "description": "string",
  "benefits": ["string"],
  "max_level": "integer"
}
```
**Errors**: 401 (unauthorized), 404 (research type not found), 500 (server error)

## **Combat Endpoints** (`/api/combat`)

### `GET /api/combat/reports`
**Purpose**: Get combat reports for authenticated user
**Auth**: JWT required
**Query Params**:
- `limit` (integer, default 20, max 100)
- `offset` (integer, default 0)
**Response 200**:
```json
{
  "reports": [
    {
      "id": "integer",
      "timestamp": "ISO datetime string",
      "attacker": {
        "id": "integer",
        "username": "string"
      },
      "defender": {
        "id": "integer",
        "username": "string"
      },
      "planet": {
        "id": "integer",
        "name": "string",
        "coordinates": "string (x:y:z)"
      },
      "winner": {
        "id": "integer",
        "username": "string"
      },
      "rounds": "string (JSON)",
      "attacker_losses": "string (JSON)",
      "defender_losses": "string (JSON)",
      "debris_metal": "integer",
      "debris_crystal": "integer",
      "debris_deuterium": "integer"
    }
  ],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```
**Errors**: 401 (unauthorized), 500 (server error)

### `GET /api/combat/reports/<report_id>`
**Purpose**: Get detailed combat report by ID
**Auth**: JWT required
**URL Params**: `report_id` (integer)
**Response 200**: Single report object (same structure as above)
**Errors**: 401 (unauthorized), 403 (access denied), 404 (report not found), 500 (server error)

### `GET /api/combat/debris`
**Purpose**: Get debris fields visible to user
**Auth**: JWT required
**Response 200**:
```json
{
  "debris_fields": [
    {
      "id": "integer",
      "planet": {
        "id": "integer",
        "name": "string",
        "coordinates": "string (x:y:z)",
        "owner": "string | null"
      },
      "resources": {
        "metal": "integer",
        "crystal": "integer",
        "deuterium": "integer"
      },
      "created_at": "ISO datetime string",
      "recycler_fleet_id": "integer | null"
    }
  ],
  "total": "integer"
}
```
**Errors**: 401 (unauthorized), 500 (server error)

### `GET /api/combat/debris/<planet_id>`
**Purpose**: Get debris field for specific planet
**Auth**: JWT required
**URL Params**: `planet_id` (integer)
**Response 200**: Single debris field object
**Errors**: 401 (unauthorized), 404 (no debris found), 500 (server error)

### `GET /api/combat/statistics`
**Purpose**: Get combat statistics for authenticated user
**Auth**: JWT required
**Response 200**:
```json
{
  "fleet_statistics": {
    "total_victories": "integer",
    "total_defeats": "integer",
    "total_experience": "integer",
    "win_rate": "float"
  },
  "battle_statistics": {
    "total_battles": "integer",
    "battles_won": "integer",
    "battles_lost": "integer",
    "win_rate": "float"
  }
}
```
**Errors**: 401 (unauthorized), 500 (server error)

## **Chat Endpoints** (`/api/chat`)

### `GET /api/chat/messages`
**Purpose**: Get recent chat messages
**Auth**: JWT required
**Query Params**: `limit` (integer, default 50, max 100)
**Response 200**:
```json
{
  "messages": [
    {
      "id": "integer",
      "user_id": "integer",
      "username": "string",
      "message": "string",
      "timestamp": "ISO datetime string",
      "is_system": "boolean"
    }
  ],
  "count": "integer"
}
```
**Errors**: 401 (unauthorized), 500 (server error)

### `POST /api/chat/messages`
**Purpose**: Send new chat message
**Auth**: JWT required
**Request Body**:
```json
{
  "message": "string (required, max 500 chars)"
}
```
**Response 201**:
```json
{
  "message": "Message sent successfully",
  "id": "integer",
  "timestamp": "ISO datetime string"
}
```
**Errors**: 400 (missing message/empty after sanitization), 401 (unauthorized), 429 (rate limit), 500 (server error)

### `POST /api/chat/messages/system`
**Purpose**: Send system message (admin/debug)
**Auth**: JWT required
**Request Body**:
```json
{
  "message": "string (required)"
}
```
**Response 201**:
```json
{
  "message": "System message sent successfully",
  "id": "integer"
}
```
**Errors**: 400 (missing message), 401 (unauthorized), 500 (server error)

## **Population Endpoints** (`/api/populate`)

### `POST /api/populate`
**Purpose**: Populate database with realistic test data
**Auth**: None
**Query Params**:
- `deterministic` (boolean, default false)
- `minimal` (boolean, default false)
**Response 200**:
```json
{
  "message": "Database populated successfully",
  "users": "integer",
  "planets": "integer",
  "fleets": "integer",
  "alliances": "integer",
  "tick_logs": "integer"
}
```
**Errors**: 500 (server error)

---

## 📋 **API CONTRACT SUMMARY**

### **Authentication Flow**
1. `POST /api/auth/register` → Get JWT token
2. `POST /api/auth/login` → Get JWT token
3. Include `Authorization: Bearer <token>` in all subsequent requests

### **Common Patterns**
- **JWT Authentication**: Required for user-specific operations
- **Resource Ownership**: Users can only access their own resources
- **Error Handling**: Consistent error response format
- **Pagination**: `limit` and `offset` for large result sets
- **Rate Limiting**: 5 messages per 10 seconds for chat
- **Input Validation**: Required fields, data types, business rules

### **Data Types**
- **Coordinates**: Always `string` format `"x:y:z"`
- **Timestamps**: ISO 8601 format `"2025-01-09T23:30:00"`
- **Resources**: `integer` values (metal, crystal, deuterium)
- **Ship Counts**: `integer` values for all ship types
- **IDs**: `integer` primary keys

### **Business Rules**
- **Fleet Speed**: Determined by slowest ship type
- **Travel Time**: Based on 3D distance and fleet speed
- **Resource Costs**: Exponential scaling for building upgrades
- **Research Requirements**: Technology level prerequisites
- **Planet Ownership**: Users can only modify their own planets
- **Combat Resolution**: Automatic battle calculation on fleet arrival

This specification provides complete API contracts for all endpoints in the Planetarion game server, optimized for LLM ingestion with minimal token usage while maintaining full technical accuracy.
