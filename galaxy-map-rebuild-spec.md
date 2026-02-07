# Planetarion — Galaxy Map Evolution Spec (v2)
Date: 2026-02-07
Status: Active
Scope: Frontend visual/UX evolution on top of current map architecture

## 0) Why this update
Current map functionality is solid (pan/zoom, minimap, intel panel, fleet overlay), but visual differentiation is weak:
- systems are primarily ring-color encoded,
- scanning the map is functional but not emotionally engaging,
- zooming does not yet reveal richer spatial storytelling.

Goal: make the map enjoyable to navigate while preserving current performance and data contracts.

## 1) Current State (code-grounded)
Current implementation strengths:
- SVG world-space rendering with smooth pan/zoom.
- Moving fleet overlay already exists and is map-anchored.
- Minimap with camera window + click-to-focus.
- Intel panel action bridge to fleets.
- SSE-driven refresh + debounced fetching.

Current visual limitations:
- Marker identity relies mostly on stroke color.
- Fleet lines are readable but stylistically flat.
- Home-planet connection storytelling is missing.
- Map atmosphere is mostly static gradient + grid.

## 2) Design Goals
1. Strong visual identity per system type without relying on color alone.
2. “Pleasure to zoom” experience: more structure appears at deeper zoom levels.
3. Preserve readability and tactical clarity under high marker density.
4. Keep current API contracts; evolve mostly in UI layer.
5. Incremental rollout with measurable acceptance checks.

## 3) Visual Language System

### 3.1 Marker taxonomy (shape + icon + motion)
Each marker uses three channels:
- silhouette/frame style,
- center glyph/texture hint,
- motion treatment.

Relation mapping:
- `self`: blue command ring + subtle home pulse + inner star/garrison glyph.
- `players/enemy`: amber/orange tactical ring + segmented frame.
- `pirates`: red jagged ring + hazard ticks + faint scan sweep.
- `unknown/unowned`: slate ring + dim center core.

Optional state adorners:
- debris: orbiting shard ring.
- selection: clean bright ring + soft outer bloom.
- explored: crisp core.
- unexplored: softened core + lower contrast.

### 3.2 Zoom-tier behavior (progressive detail)
Tier A (far zoom):
- simplified dots/frames only,
- low-noise fleet lanes.

Tier B (mid zoom):
- marker frames + relation glyph,
- debris and pirate hazard adorners.

Tier C (near zoom):
- richer frame texture,
- micro labels (optional toggle),
- clearer lane direction indicators.

### 3.3 Atmosphere and depth
Map should feel alive but never noisy:
- low-contrast starfield base layer,
- faint nebula plumes in corners (not center),
- grid overlay with controlled opacity,
- subtle parallax shimmer (very slow).

## 4) Fleet Overlay Evolution

## 4.1 Keep what works
Keep:
- route lines,
- moving dots/blips,
- mission-based colors.

## 4.2 Refine route readability
Enhancements:
- lane style by mission:
  - attack: sharper dashed lane, red pulse.
  - recycle: rounded dashed lane, green pulse.
  - espionage/explore: thinner line, stealth glow.
  - colonize: teal lane with calm cadence.
- directional chevrons/arrowheads along route (lightweight).
- slight opacity fade near endpoints to reduce clutter.

## 4.3 Improve moving fleet cues
Enhancements:
- moving blip uses mission-specific halo,
- optional tiny heading tick to imply direction,
- hover tooltip remains concise.

## 4.4 Planet connection network (your request)
Add optional overlay: “Empire links”.
- Draw subtle connection lines between your planets (minimum spanning network or nearest-neighbor graph).
- Style: calm blue-cyan low-opacity lines.
- Purpose: give spatial ownership feel and wayfinding anchors.

Controls:
- toggle `Empire Links` in HUD (default ON).
- toggle `Fleet Lanes` (default ON).

## 5) UX Flow Evolution

### 5.1 Primary workflow
1. Open map.
2. Identify target cluster quickly by marker identity.
3. Click system -> intel panel.
4. Launch action (attack/spy/recycle/colonize) through fleet preset bridge.
5. Observe route and live movement.

### 5.2 Interaction polish
- Keep drag/pan and wheel zoom behavior.
- Add optional quick-focus chips:
  - `Home`
  - `Nearest Pirate`
  - `Debris Hotspot`
- Keep minimap click-to-focus; add relation color legend parity with main map.

## 6) Asset-Driven Plan (with prompt generation)
Generated assets should focus on reusable layers:
- marker frames by relation/state,
- selection/debris rings,
- fleet arrowheads and blips,
- minimap frame + dots style,
- atmospheric overlays and panel skins.

Implementation approach:
- Use PNG/WebP assets for frames/rings.
- Compose in SVG/HTML with CSS blend/opacity.
- Keep fallback to plain vector circles for low-end mode.

## 7) Phased Delivery

## Phase 1: Marker identity uplift (low risk)
- Introduce frame assets for self/player/pirate/unknown.
- Keep current data and click behavior.
- Add debris + selection asset rings.

Acceptance:
- marker type can be identified by shape alone in grayscale screenshot.

## Phase 2: Fleet lane polish
- Add directional chevrons and mission-specific lane style.
- Upgrade moving blip visuals.
- Preserve current ETA/tooltip logic.

Acceptance:
- route direction is readable at glance without opening panel.

## Phase 3: Empire links + overlay controls
- Add optional own-planet network lines.
- Add overlay toggles (`Grid`, `Fleet Lanes`, `Empire Links`).

Acceptance:
- player can disable overlays independently; state persists per session.

## Phase 4: Zoom-tier refinement and atmosphere polish
- Progressive detail by zoom tier.
- Atmospheric layer tuning to avoid clutter.

Acceptance:
- zooming in feels richer without reducing tactical readability.

## 8) Technical Constraints
- No backend schema changes required for Phases 1-3.
- Maintain current fetch/SSE cadence.
- Preserve existing e2e map smoke tests.
- Ensure asset fallbacks exist for missing files.

## 9) Testing Additions
Add/extend e2e checks:
- markers still render and are clickable.
- fleet overlay still displays moving blips.
- overlay toggles change rendered layers.
- minimap remains functional after visual changes.

Add visual regression snapshots:
- far zoom, mid zoom, near zoom.
- with and without overlays.

## 10) Non-goals for this cycle
- full fog-of-war redesign.
- backend intel model changes.
- 3D galaxy rendering.
- heavy particle effects that impact interaction latency.

## 11) Autonomous Implementation Protocol
This section is the execution contract for autonomous coding agents.

### 11.1 Preconditions
- Frontend map tests are green before changes:
- `game-server/src/frontend/tests/e2e/galaxy.smoke.spec.js`
- `game-server/src/frontend/tests/e2e/galaxy-map.smoke.spec.js`
- `game-server/src/frontend/tests/e2e/galaxy.fleet-overlay.spec.js`
- Existing functional parity must be preserved for:
- marker click -> intel panel,
- minimap click focus,
- fleet overlay movement.

### 11.2 Task Matrix by Phase

#### P1 Marker identity uplift
Files:
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`

Tasks:
- Add marker rendering model with layered parts:
- base core,
- relation frame,
- optional adorners (debris, pirate hazard, selected, hover).
- Keep color mapping but add shape/glyph differentiation.
- Keep existing `data-test-marker="system-marker"` marker contract.

Done when:
- markers are distinguishable without color.
- no regression in marker click behavior.

#### P2 Fleet lane polish
Files:
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`

Tasks:
- Extend overlay model to include:
- mission lane style,
- directional chevron repetition,
- mission blip style classes.
- Keep current mission color semantics.

Done when:
- direction is visually obvious on moving and static routes.
- fleet dots continue to render with current test ids (`galaxy-fleet-dot-*`).

#### P3 Empire links + overlay toggles
Files:
- `game-server/src/frontend/src/GalaxyMap.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`

Tasks:
- Derive own-planet graph from `planets` prop.
- Render low-opacity connection network.
- Add toggles:
- `Grid`,
- `Fleet Lanes`,
- `Empire Links`.
- Persist toggle choices in local storage.

Done when:
- overlays are independently switchable.
- toggle states survive modal reopen.

#### P4 Zoom-tier refinement + atmosphere
Files:
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.js`
- `game-server/src/frontend/src/galaxy/GalaxyCanvas.module.css`
- `game-server/src/frontend/src/galaxy/GalaxyMap.module.css`
- optional: `game-server/src/frontend/src/galaxy/GalaxyBackground.js`

Tasks:
- Add zoom-tier class logic (far/mid/near).
- Reduce visual noise at far zoom.
- increase semantic richness at near zoom.
- Keep performance stable under high marker counts.

Done when:
- zoom transitions feel progressive and remain readable.

### 11.3 Asset Integration Contract
Prompt source:
- `docs/assets/prompts/userscript_prompts.js`

Asset path convention:
- `game-server/src/frontend/public/assets/galaxy/map-v2/*`

Rules:
- every asset has a vector or CSS fallback path.
- do not block rendering on missing assets.
- use transparent backgrounds and non-destructive blending.

### 11.4 Test Gates (must run per phase)
- `game-server/src/frontend/tests/e2e/galaxy.smoke.spec.js`
- `game-server/src/frontend/tests/e2e/galaxy-map.smoke.spec.js`
- `game-server/src/frontend/tests/e2e/galaxy.fleet-overlay.spec.js`
- Any newly added overlay tests for toggles and minimap focus.

### 11.5 Rollback Rule
- If a phase breaks marker clickability, minimap focus, or fleet overlay visibility, revert only that phase’s UI changes and keep prior phases intact.

## 12) Autonomous Acceptance Checklist
- [ ] Marker relation is identifiable by silhouette and not just color.
- [ ] Fleet lanes preserve mission semantics and show clear direction.
- [ ] Empire links can be toggled without affecting gameplay actions.
- [ ] Zoomed-out view is cleaner; zoomed-in view is richer.
- [ ] Existing galaxy and fleet overlay e2e tests remain green.
- [ ] Added assets degrade gracefully when unavailable.
