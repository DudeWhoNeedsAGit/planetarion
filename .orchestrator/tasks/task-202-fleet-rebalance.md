# Task Brief

## Context
- Related spec(s): `top-10-roi-improvements-spec.md` (#8), `implementation-ready-remaining-roi-specs.md`
- User goal: split/transfer ships between stationed fleets safely.
- Constraints: strict ship conservation invariant.

## Scope
- In scope:
  - split endpoint
  - transfer endpoint
  - fleet UI actions + modal forms
- Out of scope:
  - cross-planet transfer

## Implementation Targets
- Files likely touched:
  - `game-server/src/backend/routes/fleet.py`
  - `game-server/src/frontend/src/FleetManagement.js`
- Required tests:
  - new `tests/integration/test_fleet_rebalance.py`
  - extend `src/frontend/tests/e2e/fleet.spec.js`

## Acceptance Criteria
- [ ] split creates a new stationed fleet with requested ships
- [ ] transfer moves ships between same-planet fleets
- [ ] repeated operations preserve total ship counts exactly

## Notes / Open Questions
- transfer to inventory fleet should be allowed (recommended yes)
