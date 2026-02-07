# Pirate AI (Per-Player) — Specification (MVP)

Date: 2026-02-02  
Status: Draft (MVP-focused; implementation-ready)

## 0) Goals

Create a lightweight, server-driven Pirate AI that:
- Spawns **per-player** pirate encounters near each player (not a global shared pirate faction).
- Acts on an **hourly cadence** (not per tick), with **peak time intensity** (18:00–20:00 server time).
- Produces gameplay through **combat → ship losses → debris fields**.
- Is deterministic enough to test, cheap to run, and safe (caps, cooldowns, protection windows).

Non-goals (MVP):
- Pirate economy (pirates accumulating stolen resources).
- Pirate diplomacy / persistence beyond “camps/outposts near player”.
- Complex tactical AI (micro/targeting per combat round).

## 1) High-Level Design

### 1.1 Encounter Director pattern (recommended)
Pirates are implemented as an **Encounter Director**:
- Periodically evaluates each player’s current state.
- Decides whether to create a pirate action (raid) for that player.
- Spawns a pirate fleet on a nearby pirate camp/outpost planet and sends it on an `attack` mission.
- On combat resolution, a combat report + debris are produced using existing combat/debris mechanics.

This avoids per-player spam, reduces CPU cost, improves testability, and makes the system “content-like” (events).

### 1.2 Cadence
- Runs **once per hour** per player (effective).
- Peak time window: **18:00–20:00 (server time)**.
  - In peak window, increase probability and/or strength of raids.

Rationale:
- Keeps server load low and predictable.
- Aligns with “mostly threat” and peak-time pressure design.

## 2) Entities / Data Model

### 2.1 Pirates user
- A dedicated `User` with `username="pirates"` exists (already used in populate).
- Pirate planets/camps are planets owned by this user.

### 2.2 Per-player Pirate AI State (new)
Persist one state record per player.

Minimum fields (MVP):
- `user_id` (FK)
- `last_action_at` (datetime)
- `cooldown_until` (datetime)
- `threat_level` (0..100 float/int) — optional but recommended (allows smoothing)
- `raids_last_24h` (int) — for caps
- `last_target_planet_id` (int nullable) — to prevent immediate repeat targeting

Storage options:
- Option A: new `pirate_ai_state` table.
- Option B: JSON column on `users` (faster to ship but harder to query).

Recommendation: **Table** (clear, queryable, no JSON parsing in hot path).

### 2.3 Pirate camps/outposts per player
In MVP, pirate camps are placed “near” each player. Placement options:
- Created at test-data populate time (already exists).
- Created/ensured at runtime (director creates a camp if none exists near that player).

MVP requirement:
- A player always has at least **1 pirate camp/outpost** within the galaxy range slice used by the UI.

## 3) Inputs / Signals

For each player, the director derives a cheap “player power” score:
- `planet_count`
- `production_total` (metal+crystal+deut per hour, if available)
- `fleet_power` (sum of ships across all fleets including inventory fleets)
- Optional: building total levels

This must be:
- inexpensive to compute
- stable enough for tests (deterministic input → deterministic output)

## 4) Decision Logic (Hourly)

### 4.1 Eligibility checks (hard safety)
Skip creating a pirate raid if any of the following are true:
- Player is currently protected (e.g., `protection_until > now`).
- Player has 0 planets (eliminated/respawn loop).
- Player is in cooldown (`cooldown_until > now`).
- Player exceeded daily cap: `raids_last_24h >= MAX_RAIDS_PER_24H`.

### 4.2 Peak-time multiplier
Define:
- `PEAK_START_HOUR=18`
- `PEAK_END_HOUR=20` (exclusive or inclusive — choose and document)

If server time is within peak window:
- `probability_multiplier` (e.g. 1.5x)
- `power_multiplier` (e.g. 1.25x)

### 4.3 Probability of raid
Compute base probability from player power and threat level:
- New players: low or near-zero.
- Mid players: moderate.
- High players: higher, but capped.

Example (MVP-friendly) structure:
- `p = clamp(base + power_factor + threat_factor, 0, p_max)`
- Multiply by peak modifier in peak hours.

### 4.4 Target selection
Choose a target planet owned by the player:
- Prefer highest-value planet (production or stored resources).
- Avoid the same planet as `last_target_planet_id` if possible.
- Optional: add per-planet cooldown.

### 4.5 Pirate spawn location
Choose a pirate camp planet:
- Nearest pirate planet within a radius on the same Z slice.
- If none exist, create one near the player (optional MVP).

### 4.6 Spawn composition
Define a pirate fleet composition algorithm:
- Determine `pirate_power = clamp(player_power * difficulty_factor, min, max)`
- Convert `pirate_power` to ship mix (fighters/cruisers/battleships etc.)

MVP approach:
- Use a simple mapping table: `pirate_power → ship counts`.
- Ensure “threat” bias: pirates should sometimes be stronger than casual defenses, especially in peak window.

### 4.7 Create raid fleet
Spawn a `Fleet` with:
- `user_id = pirates_user_id`
- `mission = 'attack'`
- `status = 'traveling'`
- `start_planet_id = pirate_camp_planet_id`
- `target_planet_id = chosen_player_planet_id`
- `departure_time = now`
- `arrival_time = now + eta`
- `eta` computed using existing travel-time logic (do not set to 0)

Add an event log entry (TickLog):
- Event type: `pirate_raid_spawned`
- Description: includes target and ETA

## 5) Resolution (Combat → Debris)

On arrival, use existing fleet arrival / combat pipeline:
- Combat report produced (attacker=pirates, defender=player).
- Debris field created at the target planet location.

MVP rule:
- **Pirate-initiated raids do not transfer resources** (no theft on pirate attack events).
- **Player-initiated attacks on pirate planets may transfer loot** as a separate gameplay loop.

Optional extensions:
- Add “structure damage” or “resource burn” later.

## 6) Player Experience (UX)

Minimum UX requirements:
- Player can see:
  - Pirate camps on galaxy map (relation `pirates`).
  - Incoming pirate raids in an event feed (tick logs / overview).
  - Combat report after raid resolves.
  - Debris field in combat/debris UI.

Peak time behavior:
- Raids are more frequent/stronger between 18:00–20:00 server time.
- Communicate this (tooltips or a “pirate activity high” banner).

## 7) Configuration

Add config knobs (env / config):
- `PIRATE_AI_ENABLED` (default false in prod until tuned; true in testing if desired)
- `PIRATE_AI_INTERVAL_SECONDS` (default 3600)
- `PIRATE_AI_MAX_RAIDS_PER_24H` (default 2)
- `PIRATE_AI_COOLDOWN_SECONDS` (default 6h)
- `PIRATE_AI_PEAK_START_HOUR=18`
- `PIRATE_AI_PEAK_END_HOUR=20`
- `PIRATE_AI_PEAK_PROB_MULT=1.5`
- `PIRATE_AI_PEAK_POWER_MULT=1.25`
- `PIRATE_AI_DIFFICULTY_FACTOR` (default 0.6–1.0; tune)

## 8) Testing Strategy

### 8.1 Determinism
- Use a deterministic RNG seed for each hourly run:
  - seed = hash(`user_id`, `current_hour_timestamp`, `server_secret_salt`)
- This makes “same inputs → same output” for tests.

### 8.2 Unit tests (pure decision)
- Given a mocked player state, verify:
  - eligibility checks
  - peak multiplier behavior
  - raid probability and selected action
  - target selection chooses the expected planet

### 8.3 Integration tests (DB + services)
Scenario:
- Create player with planet(s), create pirate camp planet near player, ensure no cooldown.
- Run `pirate_ai_hourly()` once.
- Assert:
  - one pirate fleet created with `mission='attack'`, `status='traveling'`, non-zero ETA
  - TickLog event created (`pirate_raid_spawned`)
- Advance time (or set arrival_time <= now) and run tick:
  - Assert combat report created + debris field created.

### 8.4 E2E (optional)
- In test env, trigger a “force pirate raid” endpoint for deterministic UI flows:
  - open galaxy map, see pirate marker
  - see “raid inbound”
  - run tick to resolve
  - see combat report + debris

## 9) Implementation Plan (MVP)

1) Add `PirateAIDirector` service:
   - `run_hourly(now)` iterates players and applies decision logic.
2) Add `pirate_ai_state` persistence.
3) Add scheduler job (hourly) OR tick-guarded “once per hour” call.
4) Add event logs + minimal UI surfacing if missing.
5) Add tests for spawn + resolution pipeline.

## 10) Open Questions (to finalize before implementation)

1) Peak time: currently specified as **server time 18:00–20:00**. Confirm this (vs player-local time).
2) Daily raid cap: confirm desired cap (suggest: 1–2 per 24h).
3) Do we allow pirate raids against players with 1 planet and very low fleet power (or keep a grace threshold)?

---

## 11) Phase 2 Spec — Autonomous Pirate Simulation (Implementation-Ready)

Date: 2026-02-07  
Status: Draft for implementation

### 11.1 GOAL

Turn pirates into a visible, bounded galaxy simulation:
- Pirates can colonize unowned planets and build up locally.
- Pirate factions can attack other pirate factions, producing combat reports + debris.
- Galaxy map feels alive (moving fleets, changing ownership), but remains fair and readable.
- Hard anti-snowball limits prevent runaway pirate empires.

### 11.2 GAP (Current vs Target)

Current state (implemented):
- Per-player pirate raid director exists (`PirateAIDirector.run_hourly`).
- Single canonical NPC user (`username="pirates"`).
- Pirate raids on players are supported and tested.
- Debris generation from pirate-vs-player combat is supported and tested.

Missing for the new goal:
- No pirate colonization loop.
- No pirate-vs-pirate combat loop (single pirate owner cannot self-attack).
- No pirate faction economy/build budget with hard growth caps.
- Multiple services hardcode `username == "pirates"` and must be generalized.

### 11.3 Scope

In scope:
- Pirate faction model (multiple pirate NPC users).
- Colonization behavior for pirate factions.
- Pirate-vs-pirate skirmish behavior.
- Growth caps: structures, fleet power, planets.
- New logs/events and map-visible state changes.
- Automated tests for all new behavior.

Out of scope (Phase 2):
- Pirate diplomacy/alliances.
- Pirate trading/transport economy.
- Complex tactical AI beyond current combat engine.

### 11.4 Core Design

#### A) Pirate faction model

Introduce multiple pirate NPC users:
- Keep existing `pirates` user for backward compatibility.
- Add additional factions, default:
  - `pirates_red`
  - `pirates_black`

Implementation rule:
- Add helper `is_pirate_username(name: str) -> bool` in backend services.
- Replace hardcoded checks `username == "pirates"` with `is_pirate_username(...)` where appropriate.

Required touchpoints:
- `backend/services/pirate_ai.py`
- `backend/services/fleet_arrival.py` (pirate attacker special path)
- `backend/services/tick.py` (NPC processing exclusions)
- `backend/services/idle_catchup.py`
- `backend/services/commander_xp.py` (exclude all pirate NPCs from XP systems)
- `backend/routes/fleet.py` (PvP protection exceptions for pirate targets)
- map relation derivation in API/frontend where pirate ownership is inferred

#### B) Pirate faction state (new table)

Add `pirate_faction_state` table (one row per pirate NPC user):
- `user_id` (unique FK users.id)
- `expansion_cooldown_until` (datetime)
- `build_cooldown_until` (datetime)
- `skirmish_cooldown_until` (datetime)
- `expansion_points` (int)
- `fleet_points` (int)
- `planet_cap` (int)
- `fleet_cap` (int)
- `last_target_faction_user_id` (nullable int FK users.id)
- `created_at`, `updated_at`

Purpose:
- deterministic throttling + anti-snowball controls without overloading `PirateAIState`.

#### C) Simulation loops (cadence)

Keep existing raid loop. Add two loops:
- `run_expansion_cycle(now)` every 2h
- `run_skirmish_cycle(now)` every 20m

Orchestration entrypoint:
- `PirateAIDirector.run_simulation(now)` calls:
  - raids (existing)
  - expansion
  - skirmish

Cadence config:
- env-gated and independently toggleable.

### 11.5 Behavior Spec

#### 1) Pirate colonization

Eligibility:
- Faction has fewer owned planets than `planet_cap`.
- Faction has at least one valid colony fleet source (camp/outpost with colony ships).
- Expansion cooldown elapsed.

Target selection:
- Unowned planets only.
- Same z-slice preference as faction core planet.
- Avoid player home planets and avoid protected buffer radius around each player home.
- Prefer unexplored/low-value neutral planets first.

Mission:
- Spawn `mission='colonize'` fleet (same mission contract as players).
- Use existing colonization arrival path.

Post-colonization bootstrap (bounded):
- New pirate colony starts with capped baseline structures only.
- Seed inventory fleet from faction budget (not from unlimited spawn).

#### 2) Pirate building growth

Each faction can perform at most one build action per owned pirate planet per build cycle.

Priority order:
1. `metal_mine`
2. `crystal_mine`
3. `deuterium_synthesizer`
4. `solar_plant`

Hard per-planet structure caps:
- `metal_mine <= 12`
- `crystal_mine <= 12`
- `deuterium_synthesizer <= 10`
- `solar_plant <= 12`
- storage/fusion/research stay at current values (no growth in Phase 2)

#### 3) Pirate fleet growth

Faction fleet budget is bounded by `fleet_cap` (power score, not raw hull count).

Hard ship caps per pirate planet (inventory + stationed combined):
- `light_fighter <= 250`
- `heavy_fighter <= 120`
- `cruiser <= 50`
- `battleship <= 20`
- `battlecruiser <= 10`
- `colony_ship <= 3`

If faction exceeds `fleet_cap`:
- no new ship growth
- optional attrition: remove 2% of combat ships per cycle until below cap

#### 4) Pirate-vs-pirate skirmish

Eligibility:
- At least two pirate factions exist with planets in same z-slice.
- Attacker and target are different pirate users.
- Cooldowns satisfied.

Target selection:
- Prefer nearest hostile pirate planet with highest pirate value score.
- Avoid repeating same target faction consecutively if alternatives exist.

Mission:
- Spawn `attack` fleet from attacker faction to target faction planet.
- Resolve through normal combat arrival pipeline.

Expected outcomes:
- Combat report generated.
- Debris field generated from losses.
- Planet ownership may change only if normal combat rules allow; if not, remain as is.

### 11.6 Anti-Snowball Guardrails (Mandatory)

Global caps:
- `PIRATE_SIM_PLANET_CAP_PER_FACTION` default `6`
- `PIRATE_SIM_PLANET_CAP_PER_Z_SLICE` default `3`
- `PIRATE_SIM_TOTAL_PLANET_CAP` default `18`

Growth throttles:
- `PIRATE_SIM_BUILD_COOLDOWN_SECONDS` default `7200`
- `PIRATE_SIM_EXPANSION_COOLDOWN_SECONDS` default `7200`
- `PIRATE_SIM_SKIRMISH_COOLDOWN_SECONDS` default `1200`

Fairness rules:
- Do not colonize within `PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE` (default `1200`) of any non-pirate home planet.
- If pirate-owned planets exceed `PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO` (default `0.20`) of total colonized planets, expansion halts.

Cleanup rule:
- If a pirate faction is reduced to 0 planets, auto-seed one camp with starter capped fleet (once per 24h max).

### 11.7 Events, Telemetry, and UX Surface

Add TickLog event types:
- `pirate_colonization_started`
- `pirate_colonization_completed`
- `pirate_build_applied`
- `pirate_skirmish_spawned`
- `pirate_skirmish_resolved`
- `pirate_growth_blocked_cap`

Admin status endpoint additions:
- per-faction planets, fleet score, cap utilization
- last expansion/skirmish action timestamps
- blocked reasons counters (cap, cooldown, buffer, ownership ratio)

Galaxy map UX expectations:
- multiple pirate owners still render as pirate relation
- skirmish/colonization fleets visible on travel lines
- debris appears after pirate-vs-pirate fights in intel/combat surfaces

### 11.8 Implementation Milestones and Checklists

#### Milestone M1 — Pirate Faction Foundation
- [ ] Add `is_pirate_username` helper and replace hardcoded checks.
- [ ] Add `pirate_faction_state` model + schema ensure migration.
- [ ] Seed additional pirate faction users (`pirates_red`, `pirates_black`) in scenario/bootstrap paths.
- [ ] Extend admin status payload with per-faction summary.

Exit criteria:
- backend starts cleanly; existing pirate AI tests remain green.

#### Milestone M2 — Colonization Loop
- [ ] Implement `run_expansion_cycle`.
- [ ] Spawn pirate colonization fleets with existing mission contracts.
- [ ] Add target filters (unowned only, home-buffer exclusion).
- [ ] Emit `pirate_colonization_started/completed` logs.

Exit criteria:
- deterministic integration test proves pirates colonize at least one neutral planet when eligible.

#### Milestone M3 — Capped Pirate Growth
- [ ] Implement build cycle with per-planet structure caps.
- [ ] Implement fleet growth with ship caps and faction `fleet_cap`.
- [ ] Implement over-cap block/attrition behavior.
- [ ] Emit `pirate_build_applied` and `pirate_growth_blocked_cap`.

Exit criteria:
- integration tests prove caps are never exceeded after repeated cycles.

#### Milestone M4 — Pirate-vs-Pirate Skirmishes
- [ ] Implement `run_skirmish_cycle`.
- [ ] Select rival pirate targets and spawn attack missions.
- [ ] Ensure combat/debris pipeline works for non-`pirates` pirate usernames.
- [ ] Emit `pirate_skirmish_spawned/resolved`.

Exit criteria:
- integration tests prove combat report + debris generated for pirate-vs-pirate battle.

#### Milestone M5 — Balance, Guardrails, and Observability
- [ ] Enforce global ownership ratio and total cap halts.
- [ ] Enforce z-slice caps and anti-home-buffer checks.
- [ ] Expose cap utilization + blocked reasons in admin status.
- [ ] Update docs for tuning values and operational playbook.

Exit criteria:
- long-run simulation test (multi-cycle) shows bounded growth and no runaway snowball.

### 11.9 Test Plan (Required)

Unit tests:
- `is_pirate_username` behavior (`pirates`, `pirates_red`, case handling).
- expansion eligibility and target filter logic.
- cap math and attrition behavior.
- skirmish target selection avoids same-faction and respects cooldown.

Integration tests:
- `test_pirate_sim_colonization.py`:
  - eligible faction colonizes neutral planet
  - blocked by home-buffer
- `test_pirate_sim_caps.py`:
  - repeated cycles never exceed structure/fleet caps
- `test_pirate_sim_skirmish.py`:
  - pirate-vs-pirate attack resolves with combat report + debris
- `test_pirate_sim_anti_snowball.py`:
  - ownership ratio cap halts expansion

Regression tests:
- Existing `test_pirate_ai.py` and `test_pirate_ai_admin_ops.py` must pass.
- Existing combat and colonization pipelines must pass unchanged.

### 11.10 Configuration Additions

Add env/config flags:
- `PIRATE_SIM_ENABLED` (default false)
- `PIRATE_SIM_EXPANSION_ENABLED` (default true)
- `PIRATE_SIM_SKIRMISH_ENABLED` (default true)
- `PIRATE_SIM_BUILD_ENABLED` (default true)
- `PIRATE_SIM_EXPANSION_INTERVAL_SECONDS` (default 7200)
- `PIRATE_SIM_SKIRMISH_INTERVAL_SECONDS` (default 1200)
- `PIRATE_SIM_BUILD_INTERVAL_SECONDS` (default 7200)
- `PIRATE_SIM_PLANET_CAP_PER_FACTION` (default 6)
- `PIRATE_SIM_PLANET_CAP_PER_Z_SLICE` (default 3)
- `PIRATE_SIM_TOTAL_PLANET_CAP` (default 18)
- `PIRATE_SIM_MAX_PIRATE_OWNERSHIP_RATIO` (default 0.20)
- `PIRATE_SIM_PLAYER_HOME_BUFFER_DISTANCE` (default 1200)
- `PIRATE_SIM_FLEET_CAP_SCORE` (default 6000)

### 11.11 Rollout Plan

Phase rollout:
1. Enable in staging with `PIRATE_SIM_ENABLED=false` (deploy code dark).
2. Enable only expansion in low cadence, monitor telemetry.
3. Enable skirmish with strict low caps.
4. Tune caps and intervals based on debris volume, planet ownership ratio, and player feedback.

Abort switches:
- `PIRATE_SIM_ENABLED=false` hard stop.
- per-loop toggles to disable expansion or skirmish independently.
