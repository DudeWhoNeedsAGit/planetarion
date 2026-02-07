# Planetarion — Implementation-Ready Specs (Selected ROI Pack)
Date: 2026-02-07
Status: Active
Source: `top-10-roi-improvements-spec.md` candidate selection

Selected items:
- #1 Tick/Arrival Truth Contract Everywhere (`P0`)
- #2 Idle Catch-up Contract Completion (`P0`)
- #4 Galaxy Target Readability v2 (`P0`)
- #3 Fleet Templates MVP (`P0`)
- #5 Combat Outcome CTA Cards (`P1`)
- #7 New Player Guided Arc + Quest Helper (`P1`)

## Global Delivery Rules
- No contradictory fleet state wording across Fleet, Galaxy, and Overview.
- Prefer incremental rollout with test additions per milestone.
- Keep backend schema changes optional unless unavoidable.
- Any frontend-only persistence should use namespaced localStorage keys.

---

## 1) #1 Tick/Arrival Truth Contract Everywhere (`P0`)

### Current state
- Fleet UI already exposes `Arrived (pending tick)` and a pending banner.
- Travel vectors for `returning` in `FleetTravelService` are flipped to be truthful.
- Galaxy overlay and other surfaces do not consistently expose pending-processing semantics.

### Goal
A fleet has one consistent truth state everywhere:
- `traveling` (countdown in progress)
- `arrived_pending_processing` (ETA elapsed but server transition pending)
- `resolved` (stationed or mission-complete)

### GAP
- Truth labels are implemented in Fleet UI but not fully unified as a cross-surface contract.
- No shared helper to prevent wording drift.

### Implementation scope
Backend:
- Keep API states unchanged for now (no schema/API breaking changes).
- Ensure travel info for returning fleets remains route-correct.

Frontend:
- Add shared helper for deriving display-state from `status + arrival_time`.
- Use it in Fleet tiles and Galaxy overlay annotations.
- Keep existing `data-testid` contracts.

### Milestones
M1. Shared display-state helper
- [ ] Add helper: `traveling | arrived_pending_processing | resolved`.
- [ ] Replace ad-hoc checks in Fleet UI.

M2. Galaxy parity
- [ ] Mark pending fleets distinctly in map overlay tooltip/class.
- [ ] Ensure returning route remains visually reversed (`B→A`).

M3. Coverage
- [ ] Extend e2e for pending state in Fleet UI.
- [ ] Add/extend unit test for returning travel vector.

### Files
- `game-server/src/frontend/src/FleetManagement.js`
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/tests/unit/test_fleet_travel_service.py`
- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`

### Open questions
- None blocking for phase 1.

---

## 2) #2 Idle Catch-up Contract Completion (`P0`)

### Current state
- `apply_idle_catchup` is implemented with 4-week cap, storage clamp, RP gain, arrivals processing, and anti-double-award behavior.
- Integration coverage exists in `tests/integration/test_idle_catchup.py`.
- UI shows gains but does not explicitly signal when the cap was applied.

### Goal
Idle catch-up must be deterministic, bounded, and transparent to player.

### GAP
- Missing explicit cap indicator in API/UI.
- Needs explicit test coverage for cap indicator contract.

### Implementation scope
Backend:
- Add `was_capped` and optional `raw_duration_seconds` to idle summary payload.

Frontend:
- Show concise cap notice in Overview and header idle summary when capped.

Tests:
- Integration assertion that >4-week idle sets `was_capped=true`.

### Milestones
M1. API contract
- [ ] Extend `IdleCatchupResult` with cap metadata.
- [ ] Return new fields in `/api/auth/me` `idle_gains`.

M2. UX disclosure
- [ ] Add “window capped at 4 weeks” note in Overview/header summary.

M3. Coverage
- [ ] Update integration tests for cap metadata.

### Files
- `game-server/src/backend/services/idle_catchup.py`
- `game-server/src/backend/routes/auth.py`
- `game-server/src/frontend/src/Overview.js`
- `game-server/src/frontend/src/Dashboard.js`
- `game-server/tests/integration/test_idle_catchup.py`

### Open questions
- None blocking.

---

## 3) #4 Galaxy Target Readability v2 (`P0`)

### Current state
- Marker shape differentiation, fleet lane variants, empire links toggles, and zoom tiers are already present.
- Overlay toggles are persisted in localStorage.
- Missing quick-focus controls requested in spec (`Home`, `Nearest Pirate`, `Debris Hotspot`).

### Goal
Make tactical scanning faster without API changes.

### GAP
- Quick-focus wayfinding controls absent.
- No test coverage for quick-focus actions.

### Implementation scope
Frontend only:
- Add quick-focus chips/buttons:
  - `Home`: camera to home coordinates.
  - `Nearest Pirate`: focus nearest pirate-like system from current center or home.
  - `Debris Hotspot`: focus highest visible debris total.

### Milestones
M1. Focus actions
- [ ] Compute candidates from loaded `systems`.
- [ ] Add buttons near map controls.

M2. UX safety
- [ ] Disabled state and fallback text when no candidate exists.

M3. Coverage
- [ ] Add/extend galaxy e2e to assert quick-focus buttons render and update center text.

### Files
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/tests/e2e/galaxy-map.smoke.spec.js`

### Open questions
- None blocking.

---

## 4) #3 Fleet Templates MVP (`P0`)

### Current state
- Cross-screen one-shot presets already exist via `fleetSendPreset` and event dispatch.
- No reusable named templates library in Fleet screen.

### Goal
Enable repeatable mission setup in <=2 interactions for common missions.

### GAP
- No save/apply template UI.
- No per-planet template persistence.

### MVP implementation scope (frontend-only)
- Local templates per user+planet in localStorage.
- Template payload includes:
  - `name`
  - `mission`
  - `target_planet_id` or `target_x/y/z`
  - `recycle_focus` (optional)
  - `preferred_fleet_id` (optional)
- Fleet screen widget:
  - Save current send-form configuration as template.
  - Apply template to reopen send modal with preset.

### Milestones
M1. Template storage
- [ ] Add parser/serializer with versioned key.
- [ ] User+planet key strategy.

M2. Template UI
- [ ] Add list in Fleet screen for selected planet.
- [ ] Add `Apply`, `Rename`, `Delete`, `Save current` actions.

M3. Coverage
- [ ] Add e2e: save template -> apply -> send.

### Files
- `game-server/src/frontend/src/FleetManagement.js`
- `game-server/src/frontend/tests/e2e/fleet.spec.js` (or new dedicated spec)

### Open questions
- Whether templates should sync server-side (deferred, out of MVP).

---

## 5) #5 Combat Outcome CTA Cards (`P1`)

### Current state
- Combat overview already supports “Send recyclers” flow.
- Battle report modal lacks immediate post-result action buttons.

### Goal
Reduce post-battle friction by 1-click transition to next action.

### GAP
- No direct CTA from report detail modal.

### Implementation scope
Frontend:
- Add CTA row in battle report detail:
  - `Send recyclers`
  - `Attack again`
  - `Open target in Galaxy`
- Use existing preset handoff (`fleetSendPreset`) for fleet actions.
- For `Open target in Galaxy`, pass a navigation intent payload via localStorage/event.

### Milestones
M1. CTA UI
- [ ] Add compact CTA card to detail modal.

M2. CTA wiring
- [ ] Reuse fleet preset flow for recycle/attack.
- [ ] Add optional navigate-to-galaxy focus intent.

M3. Coverage
- [ ] Add e2e for battle report -> recycle CTA -> fleets prefilled.

### Files
- `game-server/src/frontend/src/BattleReports.js`
- `game-server/src/frontend/src/CombatDashboard.js`
- `game-server/src/frontend/tests/e2e/recycle-from-debris.spec.js` (extend) or new spec

### Open questions
- Galaxy deep-link focus intent schema (simple coordinate payload is acceptable MVP).

---

## 6) #7 New Player Guided Arc + Quest Helper (`P1`)

### Product direction
Use existing Commander Suggestions as compact input and build a quest-helper rail ("addon-like") that tracks completion and points to next action.

### Current state
- Overview has Commander Suggestions based on debris/research context.
- No explicit quest progression or completion tracking for first-session arc.

### Goal
First 20-minute arc with visible progress:
1. Build ships
2. Attack pirates
3. Recycle debris
4. Colonize planet
5. Rename planet

### GAP
- No quest state machine or progress persistence.
- Suggestions are informative but not structured as actionable progression.

### MVP implementation scope
Frontend-first quest helper (no backend schema changes):
- Derive completion from existing signals:
  - ships built: fleet inventory or non-zero combat-capable ships
  - attack done: combat report exists
  - recycle done: recycle event in activity
  - colonize done: planet count > 1
  - rename done: rename event in activity
- Persist dismissal/completion checkpoints in localStorage per user.
- Show rail in Overview:
  - current quest
  - completion checklist
  - “Go now” CTA -> navigate to relevant section

### Milestones
M1. Quest model
- [ ] Implement deterministic derived-state evaluator.
- [ ] Add localStorage checkpoints for collapse/dismiss.

M2. Quest helper UI
- [ ] Add compact rail near Commander Suggestions.
- [ ] Add per-step CTA routing.

M3. Coverage
- [ ] Add e2e: quest helper visible for fresh user and advances after actions.

### Files
- `game-server/src/frontend/src/Overview.js`
- `game-server/src/frontend/src/Dashboard.js` (navigation hooks)
- `game-server/src/frontend/tests/e2e/dashboard.spec.js` (extend) or new onboarding spec

### Open questions
- None blocking for derived-state MVP.

---

## Execution order (this batch)
1. #2 Idle catch-up cap metadata + UI disclosure
2. #4 Galaxy quick-focus controls
3. #5 Combat outcome CTA card (recycle/attack first)
4. #7 Quest helper rail from commander suggestions
5. #1 Cross-surface truth-state helper cleanup
6. #3 Fleet templates MVP (frontend-local)

## Done definition for this execution cycle
- [ ] Spec accepted (this file)
- [ ] Implemented all no-open-question milestones
- [ ] Targeted tests pass for changed areas
- [ ] Remaining open questions listed with concrete decision proposals
