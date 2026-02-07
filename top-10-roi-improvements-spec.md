# Planetarion — Top 10 Highest ROI Improvements (Spec)
Date: 2026-02-07
Status: Draft for prioritization
Purpose: Identify the 10 changes with best payoff-to-effort based on the current codebase and test posture.

## 0) Scoring Model
Each item is ranked by:
- `Impact`: player retention + session quality + reduced confusion
- `Effort`: implementation complexity and cross-system risk
- `Confidence`: how clearly current code indicates a gap/opportunity

Priority tiers:
- `P0`: immediate ROI, low-medium effort
- `P1`: high ROI, medium effort
- `P2`: strategic ROI, medium-high effort

## 1) #1 — Tick/Arrival Truth Contract Everywhere (`P0`)
Goal:
- Remove state ambiguity around fleet movement/arrival in all relevant surfaces (Fleet, Overview, Galaxy).

Why high ROI:
- The core loop is fleet timing. Confusion here undermines all gameplay.
- Existing work already improved this in Fleet UI; extending consistently is cheap.

Scope:
- Standardize messaging states: `traveling`, `arrived pending processing`, `resolved`.
- Ensure same semantics in Fleet timeline, Overview event feed, Galaxy overlays.

Acceptance:
- No screen shows contradictory state for same fleet.
- E2E test verifies synchronized state on at least two pages.

## 2) #2 — Idle Catch-up Contract Completion (`P0`)
Goal:
- Guarantee offline return always feels fair, bounded, and understandable.

Why high ROI:
- Idle progression is core for browser strategy retention.
- Backend implementation exists; adding robust UX/coverage is efficient.

Scope:
- Expose concise idle summary in Overview with drill-down.
- Add explicit “window capped” indicator when 4-week cap applies.

Acceptance:
- Return flow shows deterministic gains and cap explanation.
- Integration tests cover edge windows and no double-award.

## 3) #3 — Fleet Templates MVP (`P0`)
Goal:
- One-click mission presets to reduce repetitive setup friction.

Why high ROI:
- Repeated fleet composition is high-frequency player pain.
- Existing fleet send preset infrastructure already exists (intel panel -> fleet section).

Scope:
- Add template save/apply per planet (Raid, Recycle, Colonize, Spy).
- Prepopulate ship quantities and mission type.

Acceptance:
- Player can launch common mission in <= 2 interactions from Fleet screen.
- Template E2E test covers save + apply + send.

## 4) #4 — Galaxy Target Readability v2 (`P0`)
Goal:
- Make target scanning fast and satisfying via marker identity and overlays.

Why high ROI:
- Map is strategic surface; readability directly affects decision velocity.
- Recent map architecture is ready for iterative visual gains.

Scope:
- Complete marker differentiation (shape-first), mission lane styles, empire links toggles.
- Add quick-focus chips (`Home`, `Nearest Pirate`, `Debris Hotspot`).

Acceptance:
- Player can identify pirates/self/enemy without relying solely on color.
- Galaxy smoke + overlay tests remain green.

## 5) #5 — Combat Outcome CTA Cards (`P1`)
Goal:
- Convert battle results into immediate next actions.

Why high ROI:
- Combat is high emotion; fast follow-up increases session momentum.
- Recycle/colonize actions already exist and can be wired from reports.

Scope:
- Add compact post-combat card: result, losses, debris, buttons (`Send recyclers`, `Attack again`, `Open target`).

Acceptance:
- At least one-click action from combat report to next mission setup.
- E2E covers battle -> CTA -> mission prefill.

## 6) #6 — Pirate AI Live Ops Tuning Layer (`P1`)
Goal:
- Make pirate pressure feel intentional and tunable without code edits.

Why high ROI:
- Pirate AI is implemented; tuning quality now drives perceived game pacing.

Scope:
- Add admin-visible runtime summary (last run, spawned count, blocked reasons).
- Add safe env/config knobs dashboard for difficulty/peak tuning (dev/test first).

Acceptance:
- Operators can verify pirate behavior using telemetry, not guesswork.
- Integration test verifies summary payload shape.

## 7) #7 — New Player Guided Arc (First 20 Minutes) (`P1`)
Goal:
- Remove early “what do I do now?” drop-off.

Why high ROI:
- First-session clarity is biggest multiplier for retention.
- Game systems exist; missing orchestration and guidance.

Scope:
- Add mission rail: build ships -> attack pirates -> recycle -> colonize -> rename.
- Show completion ticks and next actionable CTA.

Acceptance:
- Fresh account can complete guided arc without docs/admin help.
- E2E “golden onboarding” flow passes.

## 8) #8 — Fleet Rebalance Toolkit (Split/Transfer) (`P1`)
Goal:
- Let players iterate strategy without destructive rebuild loops.

Why high ROI:
- Dissolve exists; split/transfer is natural next step with high tactical value.

Scope:
- Split fleet into two at same planet.
- Transfer ships between stationed fleets on same planet.

Acceptance:
- No ship duplication/loss under repeated operations.
- Integration tests enforce conservation invariants.

## 9) #9 — Economy Pressure + Sinks Lite (`P2`)
Goal:
- Prevent late-game resource saturation and decision flattening.

Why high ROI:
- Long-term pacing requires sinks; otherwise economy becomes idle inflation.

Scope:
- Add small recurring sinks (repair/rearm tax or fleet upkeep lite).
- Add optional booster spend choices (non-pay-to-win).

Acceptance:
- Mid/late game has at least 2 meaningful spend options beyond pure ship spam.
- Economy telemetry shows reduced resource hoarding slope.

## 10) #10 — Scenario Packs for Fast Iteration (`P2`)
Goal:
- Cut design/test cycle time with one-click deterministic states.

Why high ROI:
- Faster iteration compounds all feature delivery quality.
- Existing reset/snapshot foundations already present.

Scope:
- Add scenario presets: `Pirate Pressure`, `Debris Rich`, `Colonization Race`, `Returning Fleets Stress`.
- Standardize setup API outputs for test harness reuse.

Acceptance:
- Scenario reset < 10 seconds locally.
- Playwright specs can boot into named scenario deterministically.

## 11) Recommended Execution Order
1. Tick/Arrival Truth Contract Everywhere
2. Idle Catch-up Contract Completion
3. Fleet Templates MVP
4. Galaxy Target Readability v2
5. Combat Outcome CTA Cards
6. Pirate AI Live Ops Tuning Layer
7. New Player Guided Arc
8. Fleet Rebalance Toolkit
9. Scenario Packs for Fast Iteration
10. Economy Pressure + Sinks Lite

## 12) Candidate Selection Template (for next step)
When selecting 2-4 items for implementation-ready specs, record:
- Chosen item(s)
- Why now (release objective)
- Success metric
- Risk constraints
- Out-of-scope boundaries
