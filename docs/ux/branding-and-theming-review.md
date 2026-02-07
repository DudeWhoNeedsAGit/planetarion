# Planetarion — Branding & Theming Review (Sci‑Fi Browser Game)

Date: 2026-02-04  
Status: Draft → Implemented foundation (Phase 1)

## Goals

- Cohesive “Planetarion” look across **Login → Dashboard → all tabs**.
- Clear hierarchy: primary actions pop, secondary actions are calm, destructive actions are unmistakable.
- Readable at long sessions: low glare, high contrast, consistent spacing.
- UI feels “alive” through subtle motion/lighting, **without** flicker or distracting animation.
- Asset pipeline friendly: large batches of icons/banners can be generated and swapped in progressively.

## Current Observations (what’s inconsistent today)

- Visual language varies per screen (some screens are “flat gray”, others are rich sci‑fi).
- Components reimplement ad-hoc styling (buttons, inputs, panels), which makes it hard to keep consistent.
- Emoji icons in navigation are functional but not “premium”.
- Toasts are very bright; they read more like dev notifications than in-world UI.
- Too many arbitrary shades of gray; palette doesn’t feel intentional.

## Brand Direction (recommended)

### Tone & identity
- “Military sci‑fi ops room”: dark, clean, precise, subtle glow, strong *system status* feel.
- Color story: deep navy base + slate surfaces + one primary blue accent + secondary teal + warnings amber + danger red + “science” purple.

### Design principles
- **Clarity > decoration**: all decoration must reinforce affordance or hierarchy.
- **One surface system**: Background → Surface → Elevated Surface → Modal.
- **One button system**: Primary/Secondary/Ghost/Danger with consistent sizing & focus rings.
- **Status is color + shape**: colors are consistent across the app (pirates red, yours blue, other players amber, ally purple, debris purple ring, success green).

## Design Tokens (Phase 1)

### Palette (strict base + accents)
- Base: `#0B1B3A` (deep navy), `#1E293B` (slate), `#334155` (slate mid), `#E5E7EB` (text)
- Accents:
  - Primary: `#2563EB` (blue)
  - Secondary: `#14B8A6` (teal)
  - Warning: `#F59E0B` (amber)
  - Danger: `#EF4444` (red)
  - Science: `#A855F7` (purple)
  - Success: `#22C55E` (green)

### Typography
- Keep system font for now (fast). Later: add a single headline font (optional).
- Scale:
  - H1 24–28, H2 18–22, H3 16–18, Body 14–16, Meta 11–12.

### Spacing & radius
- Radius: 12px panels, 10px inputs/buttons, 16px modals.
- Spacing: 8/12/16/24 grid.

## Layout Rules

### App Shell
- Background: subtle gradient + vignette; no harsh black.
- Content container: consistent padding (`px-6`, `py-6`) across tabs.
- Navigation:
  - Tab row reads like a “control bar”.
  - Active tab: clear, consistent highlight (border + subtle glow).

### Panels
- Panels always:
  - have a border with low alpha,
  - have a subtle highlight gradient,
  - avoid full‑bright backgrounds.

## Interaction Guidelines

- Hover: small lift or highlight, not big color jumps.
- Focus: visible ring using primary blue.
- Loading: spinner + “Updating…” text; don’t blank content unless first-load.
- Errors: inline and actionable, plus toast.

## Asset Plan (batch generation)

All prompts live in `docs/assets/prompts/userscript_prompts.js`.  
All generated images should be saved under `docs/assets/images/<category>/` and referenced from the app later.

Priority assets for “premium feel”:
- App logo/wordmark (top-left)
- Navigation icon set (Overview/Planets/Galaxy/Fleets/Combat/Wheel/Shipyard/Research/Alliance/Messages)
- Panel background textures (subtle)
- Button/icon set (small UI glyphs)

## Implementation Plan

### Phase 1 (now): Foundation + quick wins
- Add global theme tokens + reusable component classes in `src/index.css` (`pa-*` classes).
- Update Login/Register shell to match theme.
- Update Navigation to consistent active/hover states.
- Update Toast styling to match in-world UI.

### Phase 2: Apply across all tabs
- Convert each tab to use `pa-panel`, `pa-card`, `pa-btn*`, `pa-input`.
- Remove bespoke “one-off” grays.

### Phase 3: Swap emoji → icon assets
- Replace emoji in nav with generated icons (SVG preferred).
- Add a tiny icon registry component.
- If generated icons come with a solid background (common with PNG exports), use `rembg` to remove the background and add a proper alpha channel:
  - Install once in the game-server venv: `game-server/venv/bin/pip install "rembg[cpu]"`
  - Batch process a folder (creates backups, overwrites in-place): `game-server/venv/bin/python game-server/scripts/rembg_batch.py game-server/src/frontend/src/assets/icons/nav`
  - Optional flags:
    - `--pattern "*.png"` (default), `--recursive` (include subfolders)
    - `--out-dir <dir>` (write outputs elsewhere; leaves originals unchanged)
    - `--dry-run` (preview)
  - Note: first run downloads a segmentation model file (~176MB) into your home directory (used by rembg).

### Phase 4: “Dopamine moments”
- Add banners/animations for combat victory/defeat, capture, research completion.
