# Planetarion Gameplay Reliability + Pirate AI Spec (v2)
Date: 2026-02-07
Status: Active
Owner: Product + Backend + Frontend

## 0) Purpose
This spec replaces the previous idea backlog with an implementation-grounded plan.
It records:
- what is implemented and test-verified,
- what exists but is under-tested,
- what remains backlog,
- exact milestones with trackable checklists.

This document is the operational source for "do we get cake tier reliability + loop quality".

## 1) North Star (unchanged intent, now measurable)
In a 20-30 minute active session, player should reliably complete:
- 1-3 meaningful decisions,
- 1-2 payoff moments,
- 1 obvious next action.

In idle return, player should reliably get:
- resource progression,
- resolved arrivals,
- useful event context.

## 2) Current Verified State (as of 2026-02-07)

### 2.1 Pirate AI MVP
Implemented:
- Per-player Pirate Encounter Director with hourly cadence and peak multipliers.
- Per-player `pirate_ai_state` persistence.
- Pirate raid spawn with non-zero ETA + `pirate_raid_spawned` log.
- Combat resolution path producing combat report + debris.
- Pirate raids do not capture player planets.

Verified by tests:
- `game-server/tests/integration/test_pirate_ai.py`

### 2.2 Tick reliability and truthful fleet states
Implemented:
- Auto tick scheduler service.
- Fleet UI explicitly shows "Arrived (pending tick)" and a warning banner.

Verified by tests:
- `game-server/tests/integration/test_autotick_scheduler.py`
- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`

### 2.3 Offline catch-up
Implemented:
- Delta-based catch-up on `GET /api/auth/me` with:
- 4-week cap,
- storage caps respected,
- per-user arrived fleet processing,
- research point accrual and queue completion support,
- idle summary payload in response.

Verification gap:
- No dedicated automated tests currently assert these behaviors end-to-end.

## 3) GOAL / GAP Summary

### 3.1 GOAL A - Reliability foundation
Goal:
- Tick and catch-up behaviors are deterministic, idempotent where required, and fully test-covered.

Gap:
- Idle catch-up has implementation but no dedicated test suite.
- Replay safety and edge windows (clock skew, repeated calls) are not contract-tested.

### 3.2 GOAL B - Pirate AI quality gate
Goal:
- Pirate AI decision logic is provably safe and deterministic under protection, cooldown, cap, and peak scenarios.

Gap:
- Existing tests cover forced spawn and resolve flow only.
- Missing unit tests for decision and eligibility logic.

### 3.3 GOAL C - Spec clarity and economy rules
Goal:
- No ambiguity in pirate economy and reward rules.

Gap:
- Current behavior includes loot transfer when players attack pirate planets.
- Contract now set to: pirate-initiated raids never transfer resources; player-initiated pirate attacks may loot.

### 3.4 GOAL D - Cake-tier acceptance hardening
Goal:
- Cake tier is measurable through concrete pass/fail acceptance checks.

Gap:
- Current acceptance language is outcome-oriented but not test-contract-oriented.

## 4) Scope by Delivery Track

### 4.1 Track R (Reliability, must-have)
In scope:
- Tick confidence + catch-up contract tests.
- Pending-tick UX contract consistency.

Out of scope:
- New major mechanics.

### 4.2 Track P (Pirate AI hardening)
In scope:
- Decision-path unit tests.
- Peak window verification.
- Safety/cap/cooldown verification.

Out of scope:
- Pirate tier ladder, buffs, advanced tactics.

### 4.3 Track G (Gameplay expansion backlog)
In scope (later):
- Intel levels,
- overlays,
- templates/rebalance UX,
- combat summary cards,
- suggestions rail,
- social layer.

## 5) Milestones and Checklists (Trackable)

## M1 - Contract lock (spec + behavior)
Definition of done:
- Pirate economy rule is explicitly documented.
- "No manual babysitting" is split by environment mode.
- Cake acceptance criteria rewritten into measurable checks.

Checklist:
- [x] Pirate economy policy fixed: no transfer for pirate raids; player-vs-pirate loot allowed.
- [x] Environment expectations documented:
- Dev/test: pending-tick states allowed and explicit.
- Production-like mode: auto-processing expected without manual `/api/tick`.
- [x] Acceptance metrics table finalized (Section 7).

## M2 - Idle catch-up verification
Definition of done:
- Catch-up behavior is covered by integration tests with deterministic assertions.

Checklist:
- [ ] Add test: resources accrue for elapsed window and respect storage caps.
- [ ] Add test: elapsed window is capped at 4 weeks.
- [ ] Add test: arrived fleets for authenticated user are processed.
- [ ] Add test: research points accrue and due queue item completes.
- [ ] Add test: repeated `/api/auth/me` calls in short interval do not double-award.
- [ ] Add test: future `last_seen_at` (clock skew) safely resets without payout.

## M3 - Pirate AI decision verification
Definition of done:
- Decision logic has unit coverage and deterministic behavior contract.

Checklist:
- [ ] Add unit tests for `_is_eligible`:
- protected user,
- zero planets,
- cooldown active,
- daily cap reached.
- [ ] Add unit tests for `_is_peak_hour` boundaries (start inclusive, end exclusive).
- [ ] Add unit tests for deterministic RNG outcome stability for same hour and salt.
- [ ] Add unit tests for probability clamp and threat growth/decay behavior.
- [ ] Add unit tests for target selection avoiding immediate repeats.
- [ ] Add integration test for cap/cooldown enforcement over multiple hourly runs.

## M4 - UX truthfulness and observability
Definition of done:
- UI states and event copy are explicit and test-backed.

Checklist:
- [ ] Assert pending-tick banner wording remains accurate and actionable.
- [ ] Add UI assertion for pirate peak activity messaging (if feature added).
- [ ] Add admin/dev telemetry endpoint or summary for:
- last tick time,
- scheduler status,
- pirate AI last run summary.

## 6) Backlog After Reliability Gate
These stay backlog until M1-M4 pass:
- Pirate ladder tiers I-V.
- Tactical overlays (heat, debris visibility tiers, range rings).
- Fleet templates/rebalance/split flows beyond dissolve.
- Combat summary cards and recommendation rail.
- Alliance + shared intel.

## 7) Cake-Tier Acceptance Criteria (Measurable)
All must pass in automated test environment:

### 7.1 Loop completion
- [ ] New player can complete:
- build ships -> attack pirates -> receive combat report -> recycle debris -> colonize -> rename.
- [ ] Flow succeeds without manual DB intervention.

### 7.2 Reliability
- [ ] Auto-ticks process arrivals within configured scheduler interval in production-like mode.
- [ ] Idle catch-up returns bounded deterministic summary and no double-credit on immediate re-open.

### 7.3 UX clarity
- [ ] Fleet state always communicates one of:
- traveling countdown,
- arrived pending processing,
- resolved/stationed.
- [ ] No silent state transitions that hide required player action.

### 7.4 Pirate AI safety
- [ ] Protected players are not raided.
- [ ] Daily cap is enforced.
- [ ] Cooldown is enforced.
- [ ] Pirate raids produce event + report + debris path when combat occurs.

## 8) Open Decisions (must close in M1)
- [x] Pirate economy wording finalized (raid-only restriction).
- [x] Production-like behavior finalized: no manual babysitting expected; auto-processing required.
- [x] Peak-time player-facing banner deferred (optional until explicit product requirement).

## 9) Execution Order
1. M1 Contract lock
2. M2 Idle catch-up verification
3. M3 Pirate AI decision verification
4. M4 UX truthfulness and observability
5. Resume feature backlog tracks

## 10) Autonomous Implementation Protocol
This section makes the spec executable by autonomous coding agents.

### 10.1 Preconditions
- Baseline tests must pass before new work:
- `game-server/tests/integration/test_pirate_ai.py`
- `game-server/tests/integration/test_autotick_scheduler.py`
- `game-server/tests/integration/test_auth.py`
- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`

### 10.2 Milestone-to-File Mapping

#### M1 Contract lock
Files:
- `pirate-ai-spec.md`
- `do_i_get_cake_for_this.spec`
- optional docs references in `README.md` or `game-server/README.md`

Tasks:
- finalize pirate economy wording.
- finalize environment expectations for pending tick states.
- freeze measurable acceptance criteria wording.

Done when:
- no contradictory language remains between specs.

#### M2 Idle catch-up verification
Files:
- `game-server/tests/integration/test_auth.py` (or new `test_idle_catchup.py`)
- `game-server/src/backend/services/idle_catchup.py` (only if defects found)
- `game-server/src/backend/routes/auth.py` (only if defects found)

Tests to implement:
- elapsed resource accrual + storage cap clamp.
- 4-week cap enforcement.
- per-user arrived-fleet resolution.
- research queue completion when due.
- repeated `/api/auth/me` no immediate double-credit.
- future `last_seen_at` skew safety.

Done when:
- all idle catch-up contracts are asserted by automated tests.

#### M3 Pirate AI decision verification
Files:
- new `game-server/tests/unit/test_pirate_ai_decision.py`
- optional `game-server/tests/integration/test_pirate_ai.py` additions
- `game-server/src/backend/services/pirate_ai.py` (only if bugs found)

Tests to implement:
- eligibility checks (protected/no_planets/cooldown/daily_cap).
- peak-hour boundary behavior.
- deterministic RNG for same user/hour/salt.
- probability clamp and threat adjustment behavior.
- target selection repeat-avoidance.
- integration for cap/cooldown over successive runs.

Done when:
- decision logic has both unit and integration protection.

#### M4 UX truthfulness and observability
Files:
- `game-server/src/frontend/src/FleetManagement.js`
- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`
- optional backend admin route additions for scheduler/pirate runtime summaries

Tasks:
- lock pending-tick messaging contract.
- add tests for truthful state transitions.
- add lightweight observability endpoint/fields if needed.

Done when:
- player-visible state copy and behavior match test assertions.

### 10.3 Autonomous Execution Rules
- Do not implement backlog mechanics before M1-M4 pass.
- For each milestone:
- write tests first when feasible.
- run targeted tests.
- only then refactor/extend behavior.
- Preserve existing API contracts unless explicitly updated in spec.
- Any behavior change must include test updates in the same milestone.

### 10.4 Test Gate by Milestone
- M1: docs-only consistency checks, no regressions.
- M2: all idle-catchup tests pass.
- M3: new pirate decision tests pass + existing pirate integration tests pass.
- M4: fleet/tick e2e truthfulness tests pass.

### 10.5 Rollback Rule
- If a milestone introduces regressions outside its scope, revert only that milestone’s code changes and keep prior completed milestones intact.

## 11) Autonomous Done Definition
- [ ] M1 through M4 checklists fully completed.
- [ ] No unresolved contradictions between gameplay and pirate specs.
- [ ] Reliability contracts are enforced by automated tests.
- [ ] Cake-tier criteria are measurable and test-backed.
