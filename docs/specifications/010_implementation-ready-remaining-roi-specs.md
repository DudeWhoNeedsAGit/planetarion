# Planetarion — Implementation-Ready Specs (Remaining Top-10 ROI)
Date: 2026-02-07
Status: Active
Source: `top-10-roi-improvements-spec.md`
Scope: Remaining items not yet in selected implementation pack.

Items covered:
- #6 Pirate AI Live Ops Tuning Layer (`P1`)
- #8 Fleet Rebalance Toolkit (Split/Transfer) (`P1`)
- #9 Economy Pressure + Sinks Lite (`P2`)
- #10 Scenario Packs for Fast Iteration (`P2`)

## Global constraints
- Keep existing gameplay loops stable.
- Prefer backend-first contracts + thin UI for operations tooling.
- Every item must ship with tests proving invariants.

---

## #6 Pirate AI Live Ops Tuning Layer (`P1`)

### Goal
Expose pirate behavior visibility and safe tuning controls without code edits.

### Current gap
- Pirate decision engine exists, but runtime visibility is weak.
- Difficulty knobs are mostly env-only and opaque during runtime.

### Implementation scope
Backend:
- Add admin endpoint: `GET /api/admin/pirate-ai/status`
  - last run timestamp
  - spawned raids count (rolling 24h)
  - blocked reasons histogram (protected/cooldown/no_planets/cap)
  - effective config snapshot used by director
- Add admin endpoint: `POST /api/admin/pirate-ai/config` (dev/test only)
  - allowlist of safe knobs (difficulty factor, cap, cooldown, interval)
  - in-memory + persisted override (SQLite table or app config cache)

Frontend (admin/dev panel lite):
- Simple card in admin surface for status + knob edits.

### Milestones
M1 Status contract
- [ ] status endpoint payload + integration test

M2 Safe tuning contract
- [ ] config endpoint with allowlist validation + tests

M3 Admin UI
- [ ] read status + patch config + success/error toasts

### Tests
- `tests/integration/test_pirate_ai.py` extend for status/config contract
- new `tests/integration/test_pirate_ai_admin_ops.py`

### Open questions
- Persist override across restart (recommended: yes, SQLite table)

---

## #8 Fleet Rebalance Toolkit (Split/Transfer) (`P1`)

### Goal
Allow non-destructive fleet reconfiguration on same planet.

### Current gap
- Dissolve exists, but no split or transfer operations.

### Implementation scope
Backend API:
- `POST /api/fleet/<id>/split`
  - payload: ship counts to move into new fleet
  - source fleet and new fleet remain stationed on same planet
- `POST /api/fleet/transfer`
  - payload: `from_fleet_id`, `to_fleet_id`, ship counts
  - both fleets must be same owner, stationed, same planet

Rules/invariants:
- No negative ships, no overdraw
- No-op requests rejected
- Ship conservation strict

Frontend:
- Fleet tile actions: `Split`, `Transfer`
- Modal forms with max buttons and validation messages

### Milestones
M1 Backend split/transfer contracts
- [ ] routes + validation + invariant checks

M2 Frontend actions
- [ ] split modal + transfer modal

M3 Invariant tests
- [ ] repeated split/transfer operations maintain total ship counts

### Tests
- new `tests/integration/test_fleet_rebalance.py`
- extend `src/frontend/tests/e2e/fleet.spec.js`

### Open questions
- Transfer to inventory fleet allowed? (recommended: yes)

---

## #9 Economy Pressure + Sinks Lite (`P2`)

### Goal
Reduce late-game resource saturation with lightweight sinks.

### Current gap
- Resource accumulation dominates with few strategic sinks.

### Implementation scope (phase 1 minimal)
Backend:
- Add optional fleet upkeep tick sink (config gated, default low)
  - upkeep based on stationed + moving combat ship value
  - deducted per tick from metal/crystal (or deuterium-only, choose one)
- Add repair/rearm action sink after combat (optional button) as spend choice

Frontend:
- Overview card: upkeep summary (hourly estimate)
- Combat/fleet UI: show repair cost and action

### Milestones
M1 Upkeep engine (gated)
- [ ] config flags + calculation + tick integration

M2 UX transparency
- [ ] show upkeep in overview + fleet panels

M3 Safety
- [ ] no negative-resource underflow and sane floor behavior

### Tests
- new `tests/integration/test_economy_sinks.py`
- extend tick/economy related integration tests

### Open questions
- Which resource should upkeep consume first (recommended: deuterium)

---

## #10 Scenario Packs for Fast Iteration (`P2`)

### Goal
One-click deterministic scenario setup for design/testing speed.

### Current gap
- Some scenario/reset support exists but lacks named pack contracts and unified payload schema.

### Implementation scope
Backend admin:
- Named scenario endpoints:
  - `POST /api/admin/scenarios/pirate-pressure/reset`
  - `POST /api/admin/scenarios/debris-rich/reset`
  - `POST /api/admin/scenarios/colonization-race/reset`
  - `POST /api/admin/scenarios/returning-fleets-stress/reset`
- Standard response schema:
  - users/planets/fleets summary
  - deterministic seed/version marker
  - timestamps and key ids

Frontend/tests:
- helper utilities for Playwright to boot by scenario name

### Milestones
M1 Scenario contracts
- [ ] endpoint implementation + standard payload

M2 Harness integration
- [ ] add reusable test helper to call named reset

M3 Determinism checks
- [ ] repeated reset gives stable counts/markers

### Tests
- new `tests/integration/test_scenario_packs.py`
- extend `src/frontend/tests/e2e/helpers/testSession.js` + targeted e2e smoke usage

### Open questions
- Include snapshot auto-write on each scenario reset? (recommended: no; explicit)

---

## Suggested execution order
1. #10 Scenario Packs (foundation for fast iteration)
2. #6 Pirate AI Live Ops layer
3. #8 Fleet Rebalance toolkit
4. #9 Economy Pressure + Sinks Lite

## Done definition for this remaining pack
- [ ] all four items have implementation branches
- [ ] each item has passing targeted tests
- [ ] orchestrator validates integration compatibility before merge
