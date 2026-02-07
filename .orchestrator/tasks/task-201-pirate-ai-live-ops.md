# Task Brief

## Context
- Related spec(s): `top-10-roi-improvements-spec.md` (#6), `implementation-ready-remaining-roi-specs.md`
- User goal: add live-ops visibility + safe runtime tuning for Pirate AI.
- Constraints: no risky prod mutation paths; dev/test safe defaults.

## Scope
- In scope:
  - admin status endpoint for Pirate AI runtime summary
  - admin config endpoint with allowlisted knobs
  - optional minimal admin UI card
- Out of scope:
  - new pirate combat mechanics or rebalance logic

## Implementation Targets
- Files likely touched:
  - `game-server/src/backend/routes/admin.py`
  - `game-server/src/backend/services/pirate_ai.py`
  - `game-server/src/backend/models.py` (if persistent overrides)
  - optional frontend admin surface
- Required tests:
  - `tests/integration/test_pirate_ai.py`
  - new `tests/integration/test_pirate_ai_admin_ops.py`

## Acceptance Criteria
- [ ] status endpoint returns actionable summary including blocked reasons
- [ ] config endpoint updates allowlisted knobs only and is test-covered
- [ ] no regressions in existing Pirate AI integration tests

## Notes / Open Questions
- Persist runtime overrides in DB vs in-memory only (prefer DB for restart stability)
