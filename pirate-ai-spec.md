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
