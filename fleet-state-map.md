# Fleet State Map (Source of Truth)

This document describes the **fleet state machine** as it exists in Planetarion today, and the **expected transitions** for the core gameplay loops:

- attack
- recycle (debris)
- espionage
- explore
- colonize
- transport
- deploy
- defend
- recall

It’s written to be **testable**: each transition has a corresponding backend integration test.

## Vocabulary

### Status (`Fleet.status`)

`status` is the *high-level state* of the fleet:

- `stationed`
- `traveling`
- `returning`
- `defending`
- coordinate-based:
  - `exploring:x:y:z`
  - `colonizing:x:y:z`

### Mission (`Fleet.mission`)

`mission` is the *intent*:

- `stationed`, `return`
- `attack`, `recycle`, `espionage`
- `explore`, `colonize`
- `transport`, `deploy`, `defend`

### Derived UI state (not persisted)

The UI shows **Arrived (pending tick)** when:

- `arrival_time <= now`, and
- `status` is still “in-flight” (`traveling`, `returning`, `exploring:*`, `colonizing:*`)

That means: the fleet has arrived in real time, but **a tick has not been executed yet** to process the arrival.

## Invariants

These are relied on by the UI and tests:

### Stationary fleets

- `status` in: `stationed`, `defending`
- `eta == 0`
- `arrival_time ~= now`
- `target_planet_id == start_planet_id` (treated as “fleet current location”)

### In-flight fleets

- `status` in: `traveling`, `returning`, `exploring:*`, `colonizing:*`
- `eta >= 0`
- `departure_time <= arrival_time`

## State transitions (high level)

### Sending (API)

All sends happen through `POST /api/fleet/send`.

- `stationed` → `traveling` for: `attack`, `recycle`, `espionage`, `transport`, `deploy`, `defend`
- `stationed` → `exploring:x:y:z` for: `explore`
- `stationed` → `colonizing:x:y:z` for: `colonize`

### Arrivals (Tick processing)

Arrivals are processed inside a tick:

- `backend.services.tick.run_tick()` calls `FleetArrivalService.process_arrived_fleets()`

Arrival processing should cause one of:

- “finalize and return”
- “finalize and stay”
- “finalize and station”

## Mission-specific flows

### Attack

1. send: `stationed` → `traveling`
2. tick at arrival: combat runs, then `traveling` → `returning` (mission becomes `return`)
3. tick at return arrival: `returning` → `stationed`

### Recycle (Debris)

1. send: `stationed` → `traveling`
2. tick at arrival: collect into `cargo_*`, then `traveling` → `returning` (mission becomes `return`)
3. tick at return arrival: deposit `cargo_*` on origin planet, then `returning` → `stationed`

### Espionage

1. send: `stationed` → `traveling`
2. tick at arrival: create spy report, then `traveling` → `returning` (mission becomes `return`)
3. tick at return arrival: `returning` → `stationed`

### Explore

1. send: `stationed` → `exploring:x:y:z` (mission `explore`)
2. tick at arrival: create system planets + explored marker, then → `returning` (mission `return`)
3. tick at return arrival: `returning` → `stationed`

### Colonize

1. send: `stationed` → `colonizing:x:y:z` (mission `colonize`)
2. tick at arrival: claim planet, then fleet becomes `stationed`

### Transport

1. send: `stationed` → `traveling` (mission `transport`) and *optionally* load `cargo_*` from origin
2. tick at arrival: unload `cargo_*` to target, then `traveling` → `returning` (mission becomes `return`)
3. tick at return arrival: `returning` → `stationed`

### Deploy

1. send: `stationed` → `traveling` (mission `deploy`) and *optionally* load `cargo_*` from origin
2. tick at arrival: unload `cargo_*` to target, set fleet location to target, then → `stationed` (mission stays `deploy`)

### Defend

1. send: `stationed` → `traveling` (mission `defend`)
2. tick at arrival: set fleet location to target and → `defending` (mission `defend`)

### Recall

`POST /api/fleet/recall/<id>`:

- `traveling` → `returning`
- `exploring:*` → `returning`
- `colonizing:*` → `returning`

## Tests

Backend integration coverage:

- `game-server/tests/integration/test_fleet_state_map_transitions.py`

UI coverage for “pending tick”:

- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`

