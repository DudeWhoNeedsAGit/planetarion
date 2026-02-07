# Fleet / Combat / Colonization — Alignment Specification (Trackable)

Status: **Draft v0.1 (baseline)**  
Last updated: 2026-01-29  
Owner: (TBD)  

This document is intended to become the **single source of truth** for the Fleet → Combat → Colonization gameplay loop, and to **align 1:1**:
- Backend mechanics + persistence (Flask/SQLAlchemy)
- Frontend UX + rendering (React)
- Automated tests (pytest integration/unit + Playwright E2E)

It is written to be *trackable*: every requirement is testable, and every mismatch is listed as an explicit task.

---

## 0) Scope

### In scope (this spec defines)
- Fleet creation, sending, travel, arrival/return, recall
- Combat resolution for attack missions and resulting state changes
- Colonization loop(s): “unowned planet colonization” and “post-combat colonization opportunity”
- Tick/time model (how missions progress)
- API contracts and payload shapes required by the UI/tests
- Test matrix (E2E + integration) that must match mechanics

### Out of scope (tracked separately)
- Alliance mechanics, chat, research balancing (except colonization gating)
- Galaxy exploration UX beyond marker rendering
- Economic balancing (exact costs/rates) beyond what is required for determinism

---

## 1) Canonical Terminology

- **Planet**: A `Planet` row (x,y,z), possibly owned (`user_id != null`).
- **System**: A grouping by identical `x:y:z` in current code (note: multiple planets in same system is partially supported).
- **Fleet**: A `Fleet` row containing ship counts and mission state.
- **Mission**: Fleet intent, stored in `Fleet.mission` (e.g. `attack`, `colonize`, `return`).
- **Status**: Fleet runtime state, stored in `Fleet.status` (e.g. `stationed`, `traveling`, `returning`, `colonizing:<x>:<y>:<z>`, `exploring:<x>:<y>:<z>`).
- **ETA**: Remaining travel time in seconds (stored in `Fleet.eta`, but also derivable from times).
- **Tick**: Server-side periodic processing of resources + mission arrivals.

Implementation references:
- `game-server/src/backend/models.py`
- `game-server/src/backend/services/tick.py`
- `game-server/src/backend/services/fleet_arrival.py`
- `game-server/src/backend/routes/fleet.py`

---

## 2) Data Model Requirements (Backend)

### 2.1 Fleet row fields (required)
Source: `game-server/src/backend/models.py`

| Field | Type | Meaning | Notes |
|---|---|---|---|
| `id` | int | Primary key | |
| `user_id` | int | Owning user | JWT identity |
| `mission` | string | Intent (`attack`, `colonize`, `return`, …) | Must be consistent with `status` |
| `status` | string | Runtime state (`stationed`, `traveling`, …) | **Must support coordinate-based status** |
| `start_planet_id` | int | Origin planet id | Changes only when explicitly moved |
| `target_planet_id` | int | Target planet id | For coord missions, points to placeholder planet row |
| `departure_time` | datetime | Travel start time | Required for travel interpolation |
| `arrival_time` | datetime | Travel end time | Must be updated on mission stage changes |
| `eta` | int | Remaining seconds | Can be redundant; must stay consistent |
| `target_coordinates` | string | `"x:y:z"` | For colonize/explore arrivals (backup to parsing from status) |

#### Hard requirement: `Fleet.status` length
Current: `Fleet.status = db.Column(db.String(20))`  
Problem: values like `colonizing:500:600:700` exceed 20 characters.

**Spec requirement**: `Fleet.status` MUST be able to store the full coordinate-based status (recommend `String(64)` or `Text`).  
Tracking: `ALIGN-FLEET-001`

### 2.2 Planet row fields (required)
Source: `game-server/src/backend/models.py`

Planet ownership is `Planet.user_id` (nullable).

Colonization requires:
- `Planet.colonized_at` set on successful colonization
- `Planet.is_home_planet` false for colonies
- Starter resources/buildings set by a defined rule (see §6.5)

---

## 3) Time / Tick Model (Canonical)

### 3.1 Canonical rule: server is authoritative
- **Fleet status transitions** are authoritative on the backend, not inferred client-side.
- Frontend may compute display-only values (countdowns), but must not invent state changes.

### 3.2 Required invariant: no “traveling + arrived” mismatch
If `now >= fleet.arrival_time` and `fleet.status` indicates a traveling stage, then within **one tick interval** the backend must advance the mission stage.

This prevents the UI from showing:
- Status: `traveling`
- ETA: `Arrived`

### 3.3 Tick execution environments
Source: `game-server/src/backend/app.py`
- Scheduler runs automatically only when `FLASK_ENV == development`.
- In `testing`, the scheduler does not run; a manual tick endpoint exists: `POST /api/tick`.

**Spec requirement**:
- Manual gameplay environments must have *either* auto ticks *or* an explicit UI control/workflow to advance ticks.
- E2E test environments must be deterministic; if auto ticks are enabled, tests must control time/ticks.

Tracking:
- `ALIGN-TICK-001`: Decide the “manual dev” environment: enable scheduler in `test-env` OR provide a “Run tick” button used during manual QA.

Current implementation (manual QA):
- `make test-env` starts the frontend with `REACT_APP_SHOW_TICK_BUTTON=true`, which shows a header button `data-testid="run-tick-button"` that calls `POST /api/tick` and refreshes planets.

---

## 4) Fleet State Machine (Canonical)

Backend source of truth (validation + helpers):
- `game-server/src/backend/services/fleet_state_machine.py`

### 4.1 Allowed statuses
Backend must treat these as first-class:
- `stationed`
- `traveling`
- `returning`
- `defending` (if supported)
- `colonizing:<x>:<y>:<z>`
- `exploring:<x>:<y>:<z>`

### 4.2 Allowed missions
- `stationed`
- `attack`
- `colonize`
- `explore`
- `recycle`
- `return`
- `transport` / `deploy` / `defend` (only if fully implemented)

### 4.3 State transitions (high level)

Implementation rule:
- All fleet status/mission mutations in API endpoints + arrival processing must be validated through the state machine helpers to prevent drift.

**Create fleet**
- `mission=stationed`, `status=stationed`, `target_planet_id=start_planet_id`

**Send fleet (planet-target missions: attack, recycle, transport, deploy, defend)**
- Precondition: `status == stationed`
- Transition: `status=traveling`, `mission=<mission>`, set `target_planet_id`, compute times (`departure_time`, `arrival_time`, `eta`)

**Send fleet (coordinate-based missions: colonize/explore)**
- Precondition: `status == stationed`
- Transition: `status=colonizing:<x>:<y>:<z>` or `exploring:<x>:<y>:<z>`, set `mission`, set `target_coordinates`
- `target_planet_id` MUST reference a real `Planet` row at those coords (existing or placeholder)

**Arrival processing**
- Trigger: `arrival_time <= now` and status indicates a traveling stage
- Handler: `FleetArrivalService.process_arrived_fleets()` in `game-server/src/backend/services/fleet_arrival.py`

**Recall**
- Allowed when `status` in traveling/returning or coordinate-based statuses.
- Transition to `returning` with updated times.

---

## 5) API Contracts (Backend ↔ Frontend)

### 5.1 `GET /api/planet` (owned planets)
Source: `game-server/src/backend/routes/planet_user.py`

Spec: each planet entry MUST include:
- identity: `id`, `user_id`, `name`
- coordinates: `x`, `y`, `z`, `coordinates`
- economy: `resources`, `structures`, `production_rates`
- local ships: `ships` (planet-stored counts, not fleet counts)

### 5.2 `GET /api/planets` (all planets)
Source: `game-server/src/backend/routes/planets.py`

Used by Fleet send modal to populate targets beyond owned planets.
Spec: must include `id`, `user_id`, `name`, `coordinates` at minimum.

### 5.3 `GET /api/fleet` (user fleets)
Source: `game-server/src/backend/routes/fleet.py`

Spec response for each fleet MUST include:
- `id`, `mission`, `status`
- `start_planet_id`, `target_planet_id`
- `departure_time`, `arrival_time`, `eta`
- `ships` dictionary (ship counts)
- `travel_info` (nullable; required for traveling/returning/coord missions)
- `start_planet` (name+coords)
- `target_planet` (name+coords) when applicable

IMPORTANT: `target_planet` MUST be present even if the target is not owned by the user.
Current backend behavior:
- It caches only user-owned planets, but falls back to DB query in `get_planet_info()`. ✅

### 5.4 `POST /api/fleet/send`
Source: `game-server/src/backend/routes/fleet.py`

#### Request (common)
```json
{
  "fleet_id": 123,
  "mission": "attack|colonize|explore|recycle|transport|deploy|defend",
  "target_planet_id": 456,
  "target_x": 100,
  "target_y": 200,
  "target_z": 300
}
```
Rules:
- Some missions require `target_planet_id`; some allow coordinates.
- Backend must validate mission-specific preconditions (ownership, colony ship presence, research, fuel).

#### Response
```json
{
  "message": "Fleet sent successfully",
  "fleet": {
    "id": 123,
    "mission": "attack",
    "start_planet_id": 1,
    "target_planet_id": 456,
    "status": "traveling",
    "departure_time": "2026-01-29T00:00:00Z",
    "arrival_time": "2026-01-29T00:00:30Z",
    "eta": 30,
    "ships": { "small_cargo": 0 },
    "travel_info": {},
    "start_planet": { "id": 1, "name": "Home", "coordinates": "1:1:1" },
    "target_planet": { "id": 456, "name": "Enemy", "coordinates": "2:2:2" }
  }
}
```

Note: Implementation returns the same serialized shape as `GET /api/fleet` to keep frontend state consistent without forcing a refetch.

### 5.5 `POST /api/fleet/recall/<id>`
Source: `game-server/src/backend/routes/fleet.py`

Spec:
- Must be allowed for `traveling`, `returning`, `exploring:*`, `colonizing:*`
- Must result in `status=returning`, `mission=return`, and a consistent `arrival_time`/`eta`

---

## 6) Mechanics

## 6.0 Colonization gameplay loops (canonical sequences)

### Loop A — Standard colonization of an unowned planet
Goal: Player expands to an unowned target.

1. Player builds at least `1x colony_ship` on a planet (shipyard).
2. Player creates a fleet containing `colony_ship >= 1`.
3. Player opens **Send Fleet** for that fleet and selects:
   - Mission: `colonize`
   - Target: either an unowned planet (by id) OR manual coordinates (x,y,z)
4. Frontend calls `POST /api/fleet/send` with `mission=colonize`.
5. Backend validates:
   - colony ship presence
   - target unowned
   - research gate (difficulty)
   - colony limit
   - fuel availability; deducts deuterium on launch
6. Backend updates fleet:
   - `mission=colonize`
   - `status=colonizing:<x>:<y>:<z>`
   - `target_planet_id` points at a real `Planet` row at those coords (existing or placeholder)
   - sets `departure_time`, `arrival_time`, `eta`
7. On tick (or manual tick), when `arrival_time <= now`:
   - backend runs `FleetArrivalService._process_colonization`
   - backend assigns `Planet.user_id=fleet.user_id`, sets `colonized_at`, initializes resources/buildings
   - fleet returns to `stationed` (spec: `mission=stationed`, `status=stationed`, `eta=0`)
8. Frontend refreshes planet list and fleet list:
   - new colony appears in planet selector
   - colonizing fleet is now stationed

### Loop B — Conquest (attack → capture)
Goal: Player conquers enemy territory via attack missions (no “defenseless colonization window”).

1. Player sends an `attack` mission against an enemy-owned planet.
2. Fleet travels (`status=traveling`) and arrives on tick.
3. Combat resolves:
   - If defender has a stationed/defending fleet, resolve fleet-vs-fleet combat and generate a combat report (+ debris if applicable).
   - If no defending fleet exists, resolve undefended capture (current simplified mechanic).
4. If attacker wins the engagement (definition: attacker victory and defender fleet eliminated), the target planet ownership transfers:
   - `Planet.user_id = attacker_user_id`
5. Attacking fleet progresses to next stage (recommended: `returning`), with consistent `departure_time`, `arrival_time`, and `eta`.

### 6.1 Travel time & speed
Source: `game-server/src/backend/routes/fleet.py`, `game-server/src/backend/config.py`

Canonical:
- `distance` is Euclidean in 3D.
- `fleet_speed` is the speed of the slowest ship present (after global multiplier).
- `travel_time_seconds = max(distance / fleet_speed * 3600, MIN_TRAVEL_TIME_SECONDS)`

Spec requirement:
- `MIN_TRAVEL_TIME_SECONDS` is a **published constant** for UI/tests (currently 30s).
Tracking: `ALIGN-TRAVEL-001`

### 6.2 Fuel
Source: `backend/config.py:calculate_fuel_consumption`, used by colonize flow.

Spec:
- Fuel is charged in **deuterium** from the origin planet at launch time.
- Fuel formula uses `distance` and per-ship `FUEL_RATES`.

### 6.3 Attack mission (fleet arrival)
Source:
- `game-server/src/backend/services/fleet_arrival.py:_process_attack`
- `game-server/src/backend/services/combat_engine.py`

Required behavior:
1. If defender has a stationed/defending fleet at the target, perform fleet-vs-fleet combat and create a `CombatReport` and potentially a `DebrisField`.
2. If no defending fleet exists, resolve “planet attack” (currently implemented as immediate capture).
3. After resolution, the attacker fleet MUST advance to its next stage (typically `returning`), updating `departure_time`, `arrival_time`, `eta`.

Tracking:
- `ALIGN-COMBAT-001`: Decide whether conquest triggers on attacker win always, or only when defender fleet is eliminated (recommended for v1: eliminated).

### 6.5 Standard colonization (unowned planet)
Source:
- Send validation in `game-server/src/backend/routes/fleet.py` (mission == `colonize`)
- Arrival processing in `game-server/src/backend/services/fleet_arrival.py:_process_colonization`

Canonical rules:
- Fleet must contain `colony_ship >= 1`.
- Target planet must be unowned at launch time and at arrival time.
- Research gate: `colonization_tech >= difficulty(target coords)`.
- Colony limit: base + research-derived.
- On success:
  - Set `Planet.user_id = fleet.user_id`
  - Set `Planet.is_home_planet = False`
  - Set `Planet.colonized_at = now`
  - Initialize starting resources/buildings (currently in `_complete_colonization()`).

---

## 7) Frontend UX / Rendering Requirements

### 7.1 Fleet Management screen
Source: `game-server/src/frontend/src/FleetManagement.js`

Spec:
- Planet selector lists user-owned planets.
- Fleet list shows, per fleet:
  - Mission, status
  - Ships total + composition
  - From planet name
  - To planet name (or coordinates for coordinate-based)
  - ETA countdown based on `arrival_time`

Important display rules:
- For `traveling` outbound missions, `To` must resolve via API-provided `fleet.target_planet` if not in owned planet list.
- For `returning`/`return` missions, `To` should display the origin/start planet (homeward destination).
- If `arrival_time` is in the past but status is still `traveling`/`returning` (tick not yet processed), UI should show `ETA = "Arrived (pending tick)"` to avoid confusing “traveling + arrived”.

Test hooks (required by Playwright):
- `data-testid="fleet-tile"`
- `data-testid="fleet-from-value"`
- `data-testid="fleet-to-value"`
- `data-testid="fleet-eta-value"`

### 7.2 Send Fleet modal
Source: `game-server/src/frontend/src/FleetManagement.js` (`SendFleetModal`)

Spec:
- Attack: list enemy-owned planets (exclude user-owned + unowned)
- Colonize: list unowned planets; allow manual coordinates
- Transport/deploy: list user-owned planets

### 7.3 Colonization Opportunities screen (removed by design)
Option A removes “Colonization Opportunities”. Colonization happens via `mission=colonize` only (Loop A),
and conquest happens via `mission=attack` (Loop B).

---

## 8) Test Matrix (must map 1:1 to spec)

### 8.1 Playwright E2E (frontend)
Location: `game-server/src/frontend/tests/e2e/*.spec.js`

Minimum required coverage:
- Fleet management renders and can create a fleet
- Sending an attack fleet shows a non-`N/A` destination (`fleet-to-value`)
- Galaxy map renders at least one system marker (smoke)

NOTE: E2E currently does not validate mission completion due to tick model (see §3).

### 8.2 Pytest integration (backend)
Location: `game-server/tests/integration`

Existing coverage to keep aligned:
- Colonization mission send creates `status=colonizing:x:y:z`
- Arrival processing claims the planet and sets `colonized_at`
- Fleet API includes `travel_info`, `start_planet`, `target_planet`
- Attack/combat workflow tests exist but currently assume “defeated planet becomes unowned” (may conflict with capture logic)

Tracking:
- `ALIGN-COMBAT-TEST-001`: Align integration tests with the chosen rule in `ALIGN-COMBAT-001`.

### 8.3 Requirement → test mapping (initial)
This is the start of a traceability matrix. Expand as we lock decisions.

| Requirement / invariant | Test(s) that should cover it |
|---|---|
| Fleet UI destination is not `N/A` after sending | `game-server/src/frontend/tests/e2e/fleet.spec.js` |
| Colonize send sets `status=colonizing:x:y:z` | `game-server/tests/integration/test_colonization_workflow.py` |
| Colonize arrival assigns ownership + `colonized_at` | `game-server/tests/integration/test_colonization_workflow.py` |
| Fleet API includes `travel_info` and planet info | `game-server/tests/integration/test_enhanced_fleet_api.py` |
| Combat produces report/debris (when enabled) | `game-server/tests/integration/test_combat_api.py` (plus workflow test once aligned) |

---

## 9) Alignment Backlog (Trackable)

| ID | Area | Current behavior | Target behavior | Status |
|---|---|---|---|---|
| ALIGN-FLEET-001 | DB | `Fleet.status` is `String(20)` | Must store `colonizing:x:y:z` safely | DONE |
| ALIGN-FLEET-API-001 | Fleet API | `POST /api/fleet/send` returns partial fleet | Return same serialized fleet shape as `GET /api/fleet` | DONE |
| ALIGN-FLEET-UI-ETA-001 | Fleet UI | “traveling + Arrived” can happen pre-tick | Display `Arrived (pending tick)` | DONE |
| ALIGN-TICK-001 | Tick model | Manual QA requires mission progression | Provide manual `/api/tick` trigger in UI | DONE |
| ALIGN-TRAVEL-001 | Travel constants | min travel time exists but not documented | Publish constants for UI/tests | TODO |
| ALIGN-COMBAT-001 | Combat outcome | Mixed (capture only on undefended) | Conquest: attacker win + defender wiped captures planet | DONE |
| ALIGN-COMBAT-TEST-001 | Tests | Integration tests assume “defender planet becomes unowned” | Match chosen combat rule | DONE |
| ALIGN-SHIP-STATS-001 | Source of truth | `CombatEngine.SHIP_STATS` duplicates `backend/config.py` | Single canonical stats source | TODO |

---

## 10) Open Questions (to resolve in v0.2)

1. Should conquest trigger on attacker win always, or only when the defender fleet is eliminated?
2. Do coordinate-based missions store coordinates in `status`, `target_coordinates`, or both? (Spec recommends `target_coordinates` as canonical storage and `status` as a small enum.)
3. Should the backend expose an explicit “fleet arrived” status (separate from tick processing), or keep “Arrived” purely as derived display text?

---

## 11) Appendix: Implementation Map (current files)

Backend:
- Fleet routes: `game-server/src/backend/routes/fleet.py`
- Fleet arrivals: `game-server/src/backend/services/fleet_arrival.py`
- Fleet travel info: `game-server/src/backend/services/fleet_travel.py`
- Combat engine: `game-server/src/backend/services/combat_engine.py`
- Tick processing: `game-server/src/backend/services/tick.py`
- Planets: `game-server/src/backend/routes/planet_user.py`, `game-server/src/backend/routes/planets.py`

Frontend:
- Fleet UI: `game-server/src/frontend/src/FleetManagement.js`

Tests:
- Playwright: `game-server/src/frontend/tests/e2e/fleet.spec.js`
- Pytest integration: `game-server/tests/integration/test_colonization_workflow.py`, `game-server/tests/integration/test_attack_combat_colonization_workflow.py`
