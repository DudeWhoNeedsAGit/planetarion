# Autonomous Implementation Task Board
Date: 2026-02-07
Source Specs:
- `do_i_get_cake_for_this.spec`
- `galaxy-map-rebuild-spec.md`

Use this board as execution tickets. Complete in order unless blocked.

## Global Rules
- Run tasks milestone-by-milestone.
- Do not start backlog features before reliability gates pass.
- If a milestone fails and causes unrelated regressions, rollback only that milestone.

## Environment Setup (one-time)
1. Backend deps and frontend deps
```bash
cd game-server
pip install -r src/backend/requirements.txt
cd src/frontend && npm ci
```
2. Quick baseline smoke
```bash
cd game-server
pytest -q tests/integration/test_pirate_ai.py tests/integration/test_autotick_scheduler.py tests/integration/test_auth.py
```

---

## M1 - Contract Lock (Reliability Spec)
Issue title: `M1: finalize reliability and pirate-economy contracts`

Scope:
- Eliminate wording contradictions across specs.

Files:
- `do_i_get_cake_for_this.spec`
- `pirate-ai-spec.md`
- optional: `README.md`, `game-server/README.md`

Checklist:
- [ ] Finalize pirate economy policy wording (raid-only vs all pirate interactions).
- [ ] Finalize environment semantics for pending tick (dev/test vs production-like).
- [ ] Freeze measurable acceptance language.

Commands:
```bash
cd /home/yves/repos/planetarion
rg -n "no transfer|no stealing|pending tick|manual babysitting|SLA" do_i_get_cake_for_this.spec pirate-ai-spec.md README.md game-server/README.md
```

Exit criteria:
- No conflicting statements remain.

---

## M2 - Idle Catch-up Verification
Issue title: `M2: add integration tests for idle catch-up contracts`

Scope:
- Test `GET /api/auth/me` catch-up behavior and edge cases.

Primary files:
- `game-server/tests/integration/test_auth.py` or new `game-server/tests/integration/test_idle_catchup.py`
- (only if defects) `game-server/src/backend/services/idle_catchup.py`
- (only if defects) `game-server/src/backend/routes/auth.py`

Checklist:
- [ ] Resource accrual honors storage caps.
- [ ] 4-week cap is enforced.
- [ ] Arrived fleets process for authenticated user only.
- [ ] Research queue due item completes.
- [ ] Repeated `/api/auth/me` calls do not double-award.
- [ ] Future `last_seen_at` clock skew handled safely.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server
pytest -q tests/integration/test_auth.py
# after adding tests
pytest -q tests/integration/test_auth.py tests/integration/test_autotick_scheduler.py
```

Exit criteria:
- All added catch-up tests pass reliably.

---

## M3 - Pirate AI Decision Verification
Issue title: `M3: unit + integration tests for pirate decision logic`

Scope:
- Add deterministic and safety-path coverage for PirateAIDirector.

Primary files:
- new: `game-server/tests/unit/test_pirate_ai_decision.py`
- extend: `game-server/tests/integration/test_pirate_ai.py`
- (only if defects) `game-server/src/backend/services/pirate_ai.py`

Checklist:
- [ ] `_is_eligible`: protected/no_planets/cooldown/daily_cap.
- [ ] `_is_peak_hour` boundary behavior validated.
- [ ] deterministic RNG behavior validated.
- [ ] probability clamping + threat adjustments validated.
- [ ] target repeat-avoidance validated.
- [ ] cap/cooldown enforcement integration scenario added.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server
pytest -q tests/unit/test_pirate_ai_decision.py tests/integration/test_pirate_ai.py
```

Exit criteria:
- Decision-path regressions are protected by automated tests.

---

## M4 - UX Truthfulness + Observability
Issue title: `M4: lock pending-tick UX contract and observability`

Scope:
- Keep fleet state communication explicit and test-backed.

Primary files:
- `game-server/src/frontend/src/FleetManagement.js`
- `game-server/src/frontend/tests/e2e/tick-processing.spec.js`
- optional backend admin observability route

Checklist:
- [ ] Pending-tick message remains explicit and actionable.
- [ ] E2E verifies transitions (traveling -> pending -> stationed/resolved).
- [ ] Optional runtime status summary available for diagnostics.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server/src/frontend
npx playwright test tests/e2e/tick-processing.spec.js
```

Exit criteria:
- Truthful UI state model is enforced by E2E.

---

## P1 - Galaxy Marker Identity Uplift
Issue title: `P1: marker silhouette differentiation (shape-first)`

Scope:
- Move from color-only identity to layered marker visuals.

Primary files:
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`

Checklist:
- [ ] Self/player/pirate/unknown are distinguishable by shape.
- [ ] Debris/selected adorners integrated.
- [ ] Marker click contract preserved (`data-test-marker="system-marker"`).

Commands:
```bash
cd /home/yves/repos/planetarion/game-server/src/frontend
npx playwright test tests/e2e/galaxy.smoke.spec.js tests/e2e/galaxy-map.smoke.spec.js
```

Exit criteria:
- Marker identity readable in grayscale screenshot.

---

## P2 - Fleet Lane Polish
Issue title: `P2: mission-styled lanes and directional cues`

Scope:
- Enhance route readability while preserving current overlay behavior.

Primary files:
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`

Checklist:
- [ ] Mission-specific line style variants.
- [ ] Directional chevrons/arrow hints.
- [ ] Existing moving-dot test IDs preserved.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server/src/frontend
npx playwright test tests/e2e/galaxy.fleet-overlay.spec.js
```

Exit criteria:
- Direction and mission class are readable at a glance.

---

## P3 - Empire Links + Overlay Toggles
Issue title: `P3: own-planet connection network and map overlay controls`

Scope:
- Add optional `Empire Links` overlay and persistence for map layer toggles.

Primary files:
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`

Checklist:
- [ ] Overlay toggles exist (`Grid`, `Fleet Lanes`, `Empire Links`).
- [ ] Toggle states persist for session.
- [ ] Empire links do not block marker interactions.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server/src/frontend
npx playwright test tests/e2e/galaxy.smoke.spec.js tests/e2e/galaxy-map.smoke.spec.js
```

Exit criteria:
- All overlays are independently controllable without regressions.

---

## P4 - Zoom-Tier Refinement + Atmosphere
Issue title: `P4: progressive detail by zoom and atmosphere polish`

Scope:
- Tiered visual detail for far/mid/near zoom while maintaining legibility.

Primary files:
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`
- optional: `game-server/src/frontend/src/galaxy/GalaxyBackground.js`

Checklist:
- [ ] Far zoom is clean and low-noise.
- [ ] Mid/near zoom adds useful visual richness.
- [ ] No performance cliff under high marker count.

Commands:
```bash
cd /home/yves/repos/planetarion/game-server/src/frontend
npx playwright test tests/e2e/galaxy.smoke.spec.js tests/e2e/galaxy-map.smoke.spec.js tests/e2e/galaxy.fleet-overlay.spec.js
```

Exit criteria:
- Zooming feels richer without reducing tactical readability.

---

## Final Release Gate
Run full targeted suite before merge:
```bash
cd /home/yves/repos/planetarion/game-server
pytest -q tests/integration/test_pirate_ai.py tests/integration/test_autotick_scheduler.py tests/integration/test_auth.py
cd src/frontend
npx playwright test tests/e2e/tick-processing.spec.js tests/e2e/galaxy.smoke.spec.js tests/e2e/galaxy-map.smoke.spec.js tests/e2e/galaxy.fleet-overlay.spec.js
```

Definition of done:
- [ ] M1-M4 complete
- [ ] P1-P4 complete
- [ ] Existing smoke tests pass
- [ ] No unresolved spec contradictions
