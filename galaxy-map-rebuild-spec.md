# Planetarion — Galaxy Map Rebuild (Spec + Plan)

Date: 2026-02-03  
Status: Draft (implementation-oriented)  
Scope: Frontend-first refactor + small backend contract tightenings

## 0) Purpose

The Galaxy Map is the player’s **decision surface**:
- find targets
- understand risk/reward at a glance
- take action (attack / spy / recycle / colonize)
- track outcomes (ETA, arrivals, combat, debris, capture)

This spec defines the gameplay requirements, UX rules, and an implementation plan to rebuild the Galaxy Map with:
- **stable rendering** (no flicker/reset)
- **event-driven updates** (SSE)
- **clear intel model** (contact vs scouted vs full)
- **scalable visuals** (assets + icons)

## 1) Gameplay Requirements (North Star)

### 1.1 What a player should be able to do (20–30 min session)
- See nearby pirate targets and pick one within 10–20 seconds.
- From a target: choose source planet + mission + fleet template and launch.
- See an accurate ETA (or a clear “unknown”).
- On resolution: get a clear follow-up CTA (send recyclers / colonize / rename).

### 1.2 Map should feel “alive” without being spammy
- World changes appear as **additive events** (no lists clearing, no full-map resets).
- Only “meaningful” changes trigger UI refresh:
  - planet ownership changes
  - exploration completion
  - debris created/cleared
  - pirate camp spawned/destroyed

## 2) Visibility / Intel Model (Fog-of-war rules)

We split **visibility** and **intel detail**:
- **Visibility**: contacts are visible on the map so the player can plan.
- **Intel detail**: names, owner, garrison estimates, loot estimates are gated by exploration/spy.

### 2.1 Contact levels
- `contact`: marker visible + coordinates; minimal info (type hint only).
- `scouted`: owner/type visible + basic risk/reward.
- `full`: detailed planet list + detailed tooltip + action constraints.

### 2.2 Current constraints (2D Z-slice)
- GalaxyMap operates on the player’s Z-slice (2D X/Y).  
- Backend queries default to `z_band=0`.

## 3) UX: Layout + Interactions

### 3.1 3-pane structure
- **Center Canvas**: pan/zoom + markers.
- **Corner Minimap**: large overview radius; click to focus camera; shows camera window.
- **Right Intel Panel**: selected contact/system; actions; source planet selector.

### 3.2 Marker density
- Default view should show ~3–6 meaningful targets.
- Zooming in reveals more. Zooming out simplifies/aggregates.
- Avoid hard caps like “only render 4”.

### 3.3 Actions (CTA)
From a selected contact:
- Attack
- Spy (if enabled)
- Recycle (if debris known)
- Colonize (if eligible)

All actions must support:
- explicit **source planet** selection (never implicit)
- prefilled mission + target + ETA preview

## 4) Data Contracts (Frontend-facing)

### 4.1 `/api/galaxy/nearby/:x/:y/:z`
Returns “system summaries / contacts”:
- key, x,y,z
- relation (`self|pirates|ally|enemy|unowned|contested`)
- owner_id + owner_name (when known)
- explored boolean (intel, not visibility)
- flags: has_debris, has_pirates
- meta: center, range, z_band

### 4.2 `/api/galaxy/system/:x/:y/:z`
Returns planet list, gated by intel rules (backend enforced).

## 5) Update Model (no polling)

### 5.1 Event-driven refresh
- Subscribe to SSE (`/api/events/stream`) and refresh galaxy datasets only for relevant events.
- Debounce updates (e.g. 500–1000ms) to avoid burst refreshes.

### 5.2 Cache behavior
- Keep last good datasets and update incrementally (no clearing lists to empty).
- Show “updating…” indicator without blanking the map.

## 6) Asset plan (batch prompt workflow)

Generate assets in batches (see `docs/assets/prompts/planetarion-ui-assets.ahk` and the global palette rules in the gameplay spec):
- Map markers: pirates / players / yours / unknown
- Minimap frame + background
- Tooltip card background
- Optional: planet thumbnails later (not required for MVP)

## 7) Implementation Plan (phased)

### Phase 1 — Refactor for maintainability (no gameplay changes)
- Split `GalaxyMap.js` into:
  - container/state (fetch + SSE + derived data)
  - `GalaxyCanvas` (render + pan/zoom)
  - `GalaxyMinimap` (overview + camera window)
  - `GalaxyIntelPanel` (selected system + actions)
- Keep current API usage.

### Phase 2 — Correctness + consistency
- Make minimap anchored to home center; camera window moves with pan.
- Remove visibility “fog” (opacity) from markers; keep intel gating for details only.
- Ensure minimap shows a larger radius than main view.

### Phase 3 — Gameplay loop polish
- Source planet selection integrated into intel panel and action flows.
- Tooltip shows risk/reward (pirates strength estimate, debris, capture).

### Phase 4 — Tests
- Playwright: open galaxy map, click pirate, attack, see fleet in-flight + ETA.
- Playwright: after combat, debris shows; click “send recyclers” opens fleet modal prefilled.

## 8) Acceptance Criteria
- No periodic polling for galaxy data.
- Main map and minimap are consistent: minimap shows larger radius and clearly indicates camera window; main map shows targets within camera/selection rules.
- “Fog” does not hide contacts; only reduces intel detail.
- Clicking a minimap dot always results in a visible focus/selection on the main map (or an explicit “out of view” hint).

