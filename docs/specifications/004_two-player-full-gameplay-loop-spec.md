# Two-Player “Full Gameplay Loop” Spec (Combat + Colonization + Reset)

Objective: define a **closed, testable gameplay loop** for *two human players* plus *pirate NPCs*, from fresh start to multi-battle war and eventual conquest, with fast iteration support (snapshot/restore).

This spec is written for **Planetarion’s current implementation** (SQLite, server-side tick), and calls out **gaps** explicitly.

## Status / What’s Missing (High Level)

This spec is **not fully implemented** yet. The biggest gaps are:

- **Exploration as a real loop**: discovery + persistent intel + UI that differentiates “unknown/known/scanned”.
- **Espionage as a real loop**: report format + UI + counterplay/detection + retention rules.
- **War arc as a campaign**: repeatable fights with consistent battle summaries and deterministic rules under test.
- **Defeat → respawn loop**: if a player loses all planets, they must be respawned with protection and a starter kit.
- **End-to-end UI coverage**: Playwright tests exist for key screens, but there is no single “runs the whole spec” test.

## Actors

- **Player A** (“alpha”)
- **Player B** (“beta”)
- **Pirates** (NPC user `"pirates"` with pirate camp planets + defensive fleets)

## Core Loop Overview

1. **Bootstrap**: upgrade economy buildings; build starter ships.
2. **Explore**: discover nearby systems/planets from Galaxy Map.
3. **Pirate raiding loop**: attack pirate camp → combat report + debris/loot → recycle debris → profit.
4. **Player discovery**: find each other via Galaxy Map; run espionage to get intel.
5. **Fleet scaling**: build fleets sized for multiple engagements.
6. **War arc**: 5 battles (raids/counters/decisive engagement).
7. **Conquest**: winner captures at least one planet of the loser.
8. **Loser restart**: loser receives a new home planet (respawn) and re-enters the loop.

## Non-goals (for this spec)

- Real-time PvP or twitch combat (this is a tick-based strategy loop).
- Diplomacy/alliance mechanics beyond “a second player exists”.
- Full economy/balance tuning (we optimize for a playable, testable loop first).

## Definitions / State

### Fleets (status + mission)

Source of truth: `fleet-state-map.md`.

Important derived UI state:
- “Arrived (pending tick)” = `arrival_time <= now` while still “in-flight” status.

**Invariant**
- Fleets must never be “lost”: every fleet is always queryable (either shown under the owning planet, or in a global “in-flight/returning” view).

**Acceptance**
- Fleet screen must show:
  - stationed fleets (by selected planet)
  - in-flight/returning fleets (global section, or per planet section but visible)
- After sending a fleet away, the player can still find it and see where it is going and when it returns.

### Tick processing model

Planetarion runs server-side “ticks” which:
- generate resources
- process arrived fleets (combat, recycle, espionage, explore, colonize, etc.)

For manual play, auto-tick should be enabled via scheduler; for tests, tick can be invoked deterministically.

**Tick modes**
- **Manual**: user clicks “Run tick” (debug/admin convenience).
- **Auto (scheduler)**: server runs ticks at an interval (required for “real play feel”).

**Invariant**
- UI labels must reflect server truth:
  - `status=traveling` must not show “ETA: Arrived” unless explicitly “Arrived (pending tick)”.
  - If `arrival_time <= now` and status is in-flight, the UI must show the pending-tick banner and explain what it means.

## State Maps (MVP)

This spec assumes these additional state concepts exist (even if currently implicit):

- **Planet owner type**: `player_owned | pirate_owned | neutral`
- **Player state**: `active | defeated | protected_respawn`
  - `defeated` is defined as “0 planets”.
  - `protected_respawn` blocks attacks for a short duration and is clearly visible in UI.
- **Combat outcome**: `attacker_win | defender_win | draw | retreat` (retreat optional for MVP, but must be decided)

## Phase Spec (with API hooks)

### Phase 0 — Scenario Reset (deterministic)

**Requirement**: a fast way to get back to a known baseline.

- Use admin snapshot/restore endpoints:
  - `POST /api/admin/db/snapshot`
  - `POST /api/admin/db/restore`

**Acceptance**
- Reset takes < 1s on local machine.

**Open questions**
- Do we want multiple named baselines (e.g. “two-player”, “pirate-rich”, “late-game”) or just one snapshot per dev?

### Phase 1 — Bootstrap Economy

**Player actions**
- Upgrade mines/energy.
- Build initial ships (cargo + fighters, plus probes/recyclers as needed).

**Existing APIs**
- Building upgrades: `PUT /api/planet/buildings`
- Ship builds: `POST /api/shipyard/build`

**Acceptance**
- Player can build: fighters + recyclers + probes.
- Fleet screen reflects ship availability correctly.

**Also required for UI stability**
- `GET /api/shipyard/roles` must never 500 (fleet send/build UIs depend on it).

**Missing / unclear**
- Building upgrade cost/time rules (and whether ticks impact build time) are not specified here; we currently prioritize “fast play” settings.

### Phase 2 — Explore (Galaxy Map)

**Player actions**
- Open Galaxy Map.
- Explore a nearby system (reveals planets).

**Existing APIs**
- Planet list (with relationship markers): `GET /api/planets`
- Explore mission:
  - Create a fleet: `POST /api/fleet`
  - Send explore: `POST /api/fleet/send` with `mission="explore"` and `target_x/y/z`
  - Tick processes exploration results.

**Acceptance**
- System becomes “discovered” (planets appear via `/api/planets`).

**Missing / required detail**
- What does “discovered” mean?
  - MVP proposal: a `(user_id, system_coords)` discovery record that unlocks:
    - system marker visibility
    - planet list + ownership class (pirate/neutral/player-known)
- Does exploration create a report in the UI (like combat/espionage reports)?
- Do we allow “instant discovery” by just opening Galaxy Map (arcade), or does discovery require an explore mission (4X)?

### Phase 3 — Pirate raid loop (combat + debris + recycle)

**Player actions**
- Select pirate planet from Galaxy Map.
- Send attack fleet.
- After combat, see combat report (and debris if created).
- Build recyclers and send recycle mission to the debris target.
- Recyclers return and deposit resources.

**Existing APIs**
- Attack: `POST /api/fleet/send mission="attack" target_planet_id=<pirate planet>`
- Debris listing: `GET /api/combat/debris`
- Recycle: `POST /api/fleet/send mission="recycle" target_planet_id=<planet with debris>`
- Tick log feed (for UI timeline): `GET /api/planet/ticks`

**Acceptance**
- Combat report exists (winner/loser).
- Debris field is created for combats that generate debris.
- Recycle reduces debris and increases the attacker’s resources on return.

**Missing / required detail**
- Debris rules:
  - how much debris is created (by ship losses? by fixed %?)
  - debris lifetime / decay
- Recycler UX:
  - one-click “Send recyclers” from the battle report/debris list should preselect mission + target + available recycler fleet.

### Phase 4 — Player discovery + espionage

**Player actions**
- Find opponent planet on Galaxy Map.
- Send espionage.

**Existing APIs**
- Espionage: `POST /api/fleet/send mission="espionage" target_planet_id=<enemy planet>`
- Spy reports are persisted as `EspionageReport` (backend model).

**Acceptance**
- At least one espionage report exists for the mission.

**Missing / required detail**
- Espionage report schema (MVP):
  - attacker user, defender planet, timestamp/tick
  - defender resources snapshot, ships snapshot, key buildings, defenses
  - detection chance and outcome (detected/not detected; probe losses)
- UI rules:
  - reports list + report detail screen
  - retention (how many reports kept)

### Phase 5 — War arc (5 battles)

**Player actions**
- A attacks B, B counters, repeat until “decisive” battle.

**Mechanics**
- Each battle produces:
  - `CombatReport`
  - `DebrisField` increments
  - Tick log entry
- After each engagement:
  - the attacker fleet returns (mission becomes `return`)
  - the defender either loses ships or, if undefended, loses planet ownership.

**Acceptance**
- 5 `CombatReport`s exist between alpha/beta (or alpha/pirates + alpha/beta depending on pacing).

**Missing / required detail**
- Define what counts as “a battle”:
  - is each tick-resolved engagement one report?
  - do we support multi-round battles and store per-round losses?
- Determinism requirement for tests:
  - the war arc needs stable outcomes under a fixed seed or fixed formulas.

### Phase 6 — Conquest (capture)

**Current implementation**
- `CombatEngine.calculate_planet_attack()` captures **undefended** planets.

**Rule (MVP)**
- A planet is “capturable” when **no defending fleet exists** at that planet.

**Acceptance**
- After final battle, at least one beta planet has `user_id` switched to alpha.

**Missing / required detail**
- What happens to:
  - defender buildings (keep? degrade? destroy?)
  - stationed fleets (deleted? transferred? forced return?)
  - debris/resources on the captured planet
- Captured planet UX:
  - planet list updates immediately (or after tick) and ownership is clear in UI.

### Phase 7 — Loser “respawn” / new home planet

**Missing today**
- There is no implemented “respawn” system when a player is eliminated or loses a home planet.

**Proposed MVP**
- If a user has **0 planets** after capture:
  - create a new home planet at a safe coordinate range
  - grant starter resources + 1–2 starter fleets
  - grant a temporary protection status (no attacks for N minutes)

**Acceptance**
- After conquest eliminates the loser, loser has a new home planet within 1 tick.

**Missing / required detail**
- Define “eliminated”:
  - 0 planets (MVP) vs “lost home planet” (harder; may still have colonies).
- Define protection rules:
  - what actions are blocked while protected (being attacked, spying, etc.)
  - how the UI shows protection and expiry time.
- Define starter kit (ships/resources/buildings) to avoid “dead-on-arrival”.

## Data / Report Contracts (MVP)

These are the contracts the UI and tests depend on. If these are wrong/incomplete, E2E tests will flake or gameplay will feel inconsistent.

### Combat report (minimum fields)
- battle id
- attacker user + defender user (or pirates)
- attacker fleet id + defender planet id
- outcome (attacker_won/defender_won/draw)
- ship losses by side (by ship type)
- debris created (metal/crystal)
- loot (metal/crystal/deuterium) if applicable
- timestamps / tick number

### Debris field (minimum fields)
- planet id
- remaining metal/crystal
- created_at, expires_at (if decay exists)
- last_collected_at

### Espionage report (minimum fields)
- attacker user id, defender planet id
- timestamp / tick number
- visibility level (what was revealed)
- snapshots (resources, ships, buildings/defenses)
- detection outcome

## API / Contract Notes (MVP)

- **Auth**: all player actions require a valid JWT (Playwright should login and set token consistently).
- **Error shape**: error responses should be JSON with `{ "error": "..." }` (so UI can display useful messages).
- **Fleet list**: `GET /api/fleet` must include *all* fleets owned by the user, including traveling/returning, and include enough fields to render:
  - `status`, `mission`, `arrival_time`, `start_planet_id`, `target_planet_id` or target coords (explore), and ship counts.
- **Tick execution**:
  - Manual tick endpoint (debug) should return a clear summary of what changed (at least fleet arrivals processed).
  - Auto tick should not be enabled in unit/integration tests unless explicitly requested (determinism).
- **Admin DB reset** (dev/test only):
  - snapshot/restore must not require restarting the server, and must be safe while the scheduler is running (pause tick job during restore).

## Testing Strategy

### A) Backend golden-path integration test (deterministic)

One test that:
- creates alpha/beta/pirates scenario
- performs: pirate raid → recycle → espionage → repeated player fights → final capture
- asserts: ownership flips, reports exist, debris recycled

### B) Minimal UI E2E tests (Playwright)

Small number of stable UI tests:
- Galaxy map renders and shows at least one pirate marker.
- Clicking a target and choosing Attack opens Fleet Send modal and successfully sends.
- Fleet page shows pending tick banner when applicable and clears after tick/auto tick.

### C) Full-spec UI E2E (eventual)

One long Playwright test that runs the entire spec (two users, 5 fights, capture, respawn).

**Non-goal (for now)**: making this test “fast” is secondary to making it “deterministic and stable”.

## Dev Workflow / Fast Iteration

- Start env once: `make test-env TICK=1`
- After you “break” the world during manual play: `make test-env-reset`
- If you intentionally changed baseline and want to save it: `make test-env-snapshot`

## Open Questions / Decisions Needed

- Exploration:
  - does Galaxy Map show everything immediately (arcade), or only discovered systems (4X)?
- Combat:
  - do we need per-round combat logs, or only aggregate losses?
  - do we allow “retreat” and how does that affect conquest?
- Conquest:
  - do we require “deploy/occupy” after winning, or is “attack” enough to capture undefended planets?
- Respawn:
  - should respawn be instant or “next tick”?
  - should respawn protection block espionage or only block attacks?
