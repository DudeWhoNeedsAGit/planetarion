# Planetarion — 20–30 Minute Active Play Loop (Spec + Progress Tracker)

Date: 2026-02-02  
Status: Draft (implementation-oriented)  
Owner: Gameplay / Systems

## 0) Purpose

This document defines a **20–30 minute active play** target experience and provides a **trackable implementation checklist** to align backend, frontend, ticks, fleets, combat, debris/recycling, colonization, research, galaxy map, and tests.

Primary outcome: a player can log in and repeatedly make meaningful decisions, receive frequent feedback/rewards, and reliably close the loop:

**Target → Send → Travel → Resolve (Combat) → Debris → Recycle → Return → Payout → Expand/Repeat**

## 1) North Star Outcomes (Measurable)

In a single **30-minute** session (starting from a seeded test account):
- Player can perform **5–10 fleet actions** (send/recall/recycle/colonize/transport).
- Player sees **2–4 combat resolutions** (pirates + optional PvP).
- Player experiences **≥1 “big moment”**:
  - planet capture/colonization, or
  - major tech unlock that changes decisions.
- **0 manual intervention** required for normal play:
  - no “Arrived (pending tick)” for extended periods,
  - no manual tick button required (dev-only).

Reliability:
- Fleet status, ETA, destination (“To”), and state transitions remain **truthful** and **stable** (no flicker/reset) across refreshes/ticks.

## 2) Session Cadence Targets (Pacing)

### 2.1 Fleet travel time bands
These targets define how fast the loop cycles during active play.

- **Nearby targets:** 30–120s  
  (enables several ops per session)
- **Mid-range targets:** 3–6 min  
  (keeps anticipation without stalling)
- **Far targets:** 10–20 min  
  (one “long mission” per session)

### 2.2 “Decision frequency”
- Player should encounter a meaningful choice **every 1–3 minutes**:
  - build ships/building
  - reroute/recall fleet
  - choose target
  - research choice
  - recycler dispatch
  - colonize choice

To avoid “What do I do now?” stalls, the UI provides a lightweight “next step” rail:
- **Commander Suggestions** widget (contextual recommendations)
- optional **session missions** (daily/weekly) that align with the loop

### 2.3 Tick model
- Normal gameplay uses **auto ticks** (scheduler enabled in non-test environments).
- Manual tick exists only as a **dev/admin tool** and for deterministic tests.

## 2.4 Open Gaps (Highest ROI)

- **Tick catch-up / idle progression:** make “time passes” feel real even if the server was down.
- **Event coherence:** “Recent Activity / Fleet Events” should be purely append-only + event-driven (SSE now helps, but backend should also avoid writing spammy per-tick logs).
- **Galaxy intel loop:** exploration/fog rules + scouting + “why can I attack this” tooltips (partially there, still needs gameplay rules).
- **Fleet UX:** dissolve/rebalance fleets + templates + “max/add all per ship” everywhere.
- **Recycler loop polish:** one-click “send recyclers” + clear source-planet selection + payout celebration.

## 2.5 Idle Progression Proposal (Server Catch-Up Ticks)

Goal: when the server restarts after downtime, we “fast-forward” the world by simulating the ticks that would have happened.

### Persist a canonical time marker
- Store `last_tick_processed_at` (UTC) in DB (single-row `server_state` table or reuse an existing table if you have one).
- On every successful tick commit, update that timestamp.

### On server startup, compute backlog
- `downtime_seconds = now - last_tick_processed_at`
- `tick_interval = TICK_SCHEDULER_INTERVAL_SECONDS` (e.g. 5s)
- `catchup_ticks = floor(downtime_seconds / tick_interval)`
- Cap it:
  - **Hard cap:** maximum catch-up is **4 weeks** (requested).
  - **Performance cap:** apply a safe `MAX_CATCHUP_TICKS` for the “loop ticks” approach (Option A) so startup doesn’t take minutes. Anything beyond that must use an optimized delta approach (Option B).

### Apply catch-up ticks efficiently

**Option A (simple, safe): loop ticks using existing tick code**
- Loop `catchup_ticks` times calling existing tick logic (same code path as manual tick), but:
  - disable/aggregate verbose `TickLog` spam during catch-up,
  - batch commit every N ticks (e.g. 10–25) if safe for your tick implementation.

**Option B (recommended long-term): “delta tick”**
- Compute resources with `production_per_tick * catchup_ticks` in one go per planet.
- Process fleet arrivals by comparing `arrival_time <= now` and resolving the state machine once per fleet (no per-tick iteration).
- Same for research queue: consume `research_points_per_tick * catchup_ticks`, pop completed items.

### Make the UI reflect it instantly
- After catch-up, broadcast a single SSE event like:
  - `event_type = server_catchup`
  - payload `{ ticksApplied, from, to }`
  - so clients refresh once (and don’t flicker).

### Next implementation steps
- Add a tiny `ServerState` model/table and migrate.
- Update tick runner to write `last_tick_processed_at`.
- Add startup hook: run catch-up before enabling scheduler.
- Add tests:
  - simulate `last_tick_processed_at` in the past, start app, assert resources/fleet state advanced and `ticksApplied` is capped,
  - ensure catch-up does not create thousands of `TickLog` rows.

## 3) Gameplay Loop Definition (Happy Path)

### 3.1 Discovery → Targeting
Player uses the galaxy map to:
- identify nearby pirate camps/outposts and potential targets
- understand risk/reward quickly (tooltip/overlay)
- choose a target and mission

### 3.2 Fleet send (low friction)
From Fleets or Galaxy:
- select **source planet**
- select **target planet**
- choose **mission** (attack / recycle / colonize / transport / spy if enabled)
- pick ships quickly (templates, “add all per ship”, numeric input)
- confirm send → fleet appears in a clear “in-flight” list with ETA

### 3.3 Travel
While traveling:
- player can build 1–2 things
- player can start/continue 1 research
- event feed reflects significant changes without spam

### 3.4 Arrival → Resolution
When a fleet arrives:
- status becomes **arrived/resolving** momentarily, then **resolved** without requiring manual tick
- combat generates a **battle summary** and (if applicable) **debris field intel**
- the UI “celebrates” the outcome with a clear **summary card** and a **call-to-action** (e.g., “Send recyclers”, “Colonize”, “Rename planet”)
- outcomes are written to:
  - combat reports
  - debris fields (if ships destroyed)
  - activity feed events

### 3.5 Salvage / Recycling
From combat/debris UI:
- one-click **“Send recyclers”** opens fleet send modal prefilled:
  - mission = recycle
  - target = debris location
  - source planet explicitly chosen (not implicit)
- recycler fleet travels, arrives, loads resources, returns, deposits payout.

### 3.6 Expansion
After repeated victories:
- colonization/capture loop yields a new planet
- player can **rename** a captured/colonized planet once (and later again if desired)
- new planet is usable for build/shipyard (source selection must be explicit)

## 4) Critical Consistency Rules (Must-Haves)

### 4.1 Fleet UI truth table
At all times:
- `Status` reflects actual server state (stationed / traveling / arrived / resolving / returning / destroyed).
- `ETA`:
  - if traveling: shows remaining time (counts down)
  - if arrived and resolving: shows “Arrived” and resolution time if applicable
  - if stationed: shows “—”
- `To`:
  - never `N/A` for traveling/returning fleets
  - always includes planet name + coordinates for missions that target planets
  - for debris: “Debris @ (x:y:z)” or associated planet/cell name
- Fleets are visible in the relevant lists:
  - stationed fleets per planet
  - in-flight fleets (global + filterable)
  - recent fleet events (deduplicated; append-only)

### 4.2 Events/feeds
- “Recent Activity” and “Recent Fleet Events” are:
  - **append-only** for a session view (no disappearing/reappearing items),
  - **deduplicated** (no “pollution” from periodic ticks),
  - show only significant events (combat resolved, fleet sent/returned, planet captured, debris created/recycled).

### 4.3 Source planet is always explicit
Any action that sends ships must clearly state “From”:
- galaxy map “attack”
- combat debris “send recyclers”
- fleet send modal
- colonization

No hidden “currently selected planet” behavior for gameplay-critical actions.

## 5) Feature Plan (Trackable Milestones)

Each milestone below has acceptance criteria and recommended tests.

### Milestone A — Tick & Fleet State Truth (Backbone)
Goal: remove ambiguity (“Arrived (pending tick)”) from normal play.

Acceptance:
- Auto-tick mode processes arrivals/combat within a bounded delay (e.g., ≤5s).
- UI never shows “arrived” while status is “traveling” for more than one refresh cycle.
- ETA is non-zero for non-trivial distances (except local dev overrides).

Tests:
- Unit: fleet state transitions (state map coverage)
- Integration: create fleet, advance time/ticks, assert state transitions + combat resolution
- E2E: send fleet, wait for traveling ETA, observe resolution and report

Status checklist:
- [ ] Auto-tick enabled for active play environments
- [ ] Fleet status/ETA computation correct (non-zero travel)
- [ ] Arrival/resolution pipeline idempotent (no double resolve)
- [ ] UI renders truthful state and does not hide traveling fleets

### Milestone B — Combat Summary → Debris → Recycle Funnel (Dopamine core)
Goal: immediate post-combat action that reliably yields payout.

Acceptance:
- Combat report shows readable summary (win/loss, losses, debris created) and a clear **next action CTA**.
- Debris list shows only “known” debris (created by fights or discovered).
- “Send recyclers” one-click opens prefilled fleet modal.
- Recycler mission completes end-to-end and awards resources on return.
- Capture outcomes (if any) surface a “big moment” UI (banner/prompt) and link to rename/manage the new planet.

Tests:
- Integration: combat produces debris; recycler fleet collects; payout applied.
- E2E: fight pirates → click “Send recyclers” → confirm send → verify payout or resource increase.

Status checklist:
- [ ] Debris is generated and persisted on combat
- [ ] Debris visibility respects “known” rules
- [ ] Prefilled recycler flow works with explicit source planet
- [ ] Payout on return is correct and audited in events

### Milestone C — Fleet + Shipyard UX (Reduce friction)
Goal: make building ships and composing fleets fast at scale.

Acceptance:
- Per ship type controls:
  - “Add all” per ship class
  - numeric input (free text) with sane clamps
- Shipyard quantity UX supports late-game scale:
  - free-text numeric input
  - “Max” button (based on resources / limits)
- Fleet dissolve/reassign:
  - dissolve returns ships to “inventory” (or stationed pool)
  - players can restructure fleets for different compositions
- No duplicate ship entries (e.g., recyclers shown twice).

Tests:
- Unit: dissolve/merge logic
- E2E: build ships → create fleet → send → dissolve → verify ships restored

Status checklist:
- [ ] Per-ship “Add all” / numeric input
- [ ] Shipyard “Max” + free-text quantity input
- [ ] Fleet dissolve endpoint + UI wiring
- [ ] Inventory fleet semantics documented and explained in UI
- [ ] No duplicate ship types in UI

### Milestone D — Galaxy Map as Planning Tool (Targets + Minimap)
Goal: turn the map into a consistent decision surface.

Acceptance:
- Map shows an appropriate density (≈3–4 planets per screen at default zoom).
- Stable background (no flicker) while panning.
- Minimap:
  - red dots = pirates
  - yellow dots = other players
  - blue dots = your planets
  - much larger scale than main view (context, not redundancy)
- Backend populates only the player’s Z slice (2D galaxy plane) for cost control.

Tests:
- Integration: galaxy query returns planets on same Z slice; marker types tagged.
- E2E: galaxy loads, markers render, minimap displays all three categories.

Status checklist:
- [ ] Density/spacing algorithm tuned
- [ ] Minimap overlay + legend
- [ ] Marker colors/types consistent with ownership
- [ ] Backend ensures slice population is sufficient near player

### Milestone E — Planet Capture/Colonization Polish (Big moments)
Goal: capture feels rewarding and makes sense.

Acceptance:
- Captured pirate planets have normal names (not “enemy base near …”).
- Rename action exists (at least once) with validation and persistence.
- Shipyard/build actions respect the selected planet explicitly.
- Activity feed includes capture/colonization events.

Tests:
- Integration: capture updates owner, names appropriately, creates event, enables shipyard.
- E2E: capture pirate planet → rename → build on new planet.

Status checklist:
- [ ] Capture naming rules + rename endpoint/UI
- [ ] Build-on-selected-planet is consistent
- [ ] Capture events in overview feed

### Milestone F — Research MVP → “Choices that matter”
Goal: research affects the loop within one session.

Acceptance:
- At least 3–5 techs with clear impacts:
  - travel speed
  - recycler efficiency/capacity
  - colonization success or target tier
  - scanning/visibility (if scouting exists)
- Research progress ties to ticks/time and is visible.

Tests:
- Unit: research queue processing
- E2E: start research → observe completion → verify effect applied.

### Milestone G — Action Clarity (“Next step” rail)
Goal: players always have an obvious, rewarding next action during active play.

Acceptance:
- A “Commander Suggestions” widget is visible on Overview (or another always-visited screen).
- Suggestions are derived from current state (simple heuristics are fine):
  - “Attack nearby pirates” (if a pirate target exists)
  - “Send recyclers to known debris” (if debris exists and recyclers are available)
  - “Start/continue research” (if queue empty and RP available)
  - “Build ships” (if resources are high / fleet power low)
  - “Colonize/capture follow-up” (if a capture was just earned)
- Optional: add 3–5 missions that match the loop (daily/weekly), e.g.:
  - “Win 2 pirate fights”
  - “Recycle 50k debris”
  - “Colonize 1 planet”

Tests:
- Unit: suggestion rule engine returns stable recommendations for fixtures
- E2E: after combat, UI shows a “Send recyclers” suggestion/CTA and the flow works

## 6) Test Strategy (Fast Iteration)

Principles:
- Keep deterministic core logic in unit/integration tests (seed RNG where needed).
- Use E2E for “happy path” smoke tests that validate the loop closes.
- Prefer DB snapshot/restore for test-env speed (avoid full repopulate each run).

Minimum recommended E2E set (stable):
1) Login → build ships → create fleet → send attack → see combat report  
2) From report: “Send recyclers” → arrive → return → payout  
3) Capture/colonize → rename → build on new planet  
4) Galaxy loads + minimap markers visible

## 7) Open Design Choices (Need explicit decision)

- Peak time window semantics (server time vs player-local time).
- Debris collection: proportional always vs resource type selection.
- “Inventory” fleet concept: rename in UI (“Docked ships” / “Garrison”) or keep as-is.
- PvP discovery: when do other players appear (always in range vs explored only).

## 7.1 Asset Batch (AHK Image-Gen Prompts)

Asset generation prompts live in `docs/assets/prompts/planetarion-ui-assets.ahk`, and generated images should be placed under `docs/assets/images/` (ships/buildings/research/galaxy/combat/planets).

## 8) Progress Tracking (Fill in as you implement)

Legend: ✅ done, 🟡 partial, ❌ not started

- A Tick & Fleet State Truth: ✅
- B Combat → Debris → Recycle Funnel: 🟡 (CTA flow exists; continue polishing battle report CTA + payout celebration)
- C Fleet + Shipyard UX: 🟡 (per-ship max + shipyard max exist; continue with templates + advanced fleet reorganize)
- D Galaxy Map Planning + Minimap: 🟡 (minimap + single-Z density exist; continue tuning clustering + stability)
- E Capture/Colonization Polish: 🟡 (rename endpoint/UI exists; continue with capture naming + stronger “big moment” UX)
- F Research “Choices that matter”: 🟡 (MVP exists; expand to 3–5 impactful techs)
- G Action Clarity (“Next step” rail): ✅
