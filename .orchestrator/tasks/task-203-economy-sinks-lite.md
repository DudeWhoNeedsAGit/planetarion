# Task Brief

## Context
- Related spec(s): `top-10-roi-improvements-spec.md` (#9), `implementation-ready-remaining-roi-specs.md`
- User goal: introduce lightweight economic pressure without destabilizing loop.
- Constraints: feature-flagged, safe rollback.

## Scope
- In scope:
  - upkeep sink integrated into tick loop (config gated)
  - minimal UX transparency in overview/fleet
- Out of scope:
  - deep economy rebalance

## Implementation Targets
- Files likely touched:
  - `game-server/src/backend/services/tick.py`
  - `game-server/src/backend/config.py`
  - `game-server/src/frontend/src/Overview.js`
- Required tests:
  - new `tests/integration/test_economy_sinks.py`

## Acceptance Criteria
- [ ] upkeep applies deterministically when flag enabled
- [ ] resources never underflow below zero
- [ ] UI shows clear upkeep impact

## Notes / Open Questions
- upkeep resource target (recommend deuterium-first)
