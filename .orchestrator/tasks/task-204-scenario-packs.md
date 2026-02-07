# Task Brief

## Context
- Related spec(s): `top-10-roi-improvements-spec.md` (#10), `implementation-ready-remaining-roi-specs.md`
- User goal: one-click deterministic scenario resets for iteration speed.
- Constraints: stable payload schema and reproducible setup.

## Scope
- In scope:
  - named scenario reset endpoints
  - common response contract for harnesses
  - e2e helper integration
- Out of scope:
  - dynamic scenario designer UI

## Implementation Targets
- Files likely touched:
  - `game-server/src/backend/routes/admin.py`
  - `game-server/src/backend/routes/populate.py`
  - `game-server/src/frontend/tests/e2e/helpers/testSession.js`
- Required tests:
  - new `tests/integration/test_scenario_packs.py`

## Acceptance Criteria
- [ ] all named scenarios reset successfully
- [ ] response payload is normalized and deterministic
- [ ] at least one e2e flow uses named scenario helper

## Notes / Open Questions
- explicit snapshot write behavior should remain opt-in
