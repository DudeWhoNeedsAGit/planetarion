# Planetarion — Header Portrait + Idle Gains + Suggestions UX (Spec)

Date: 2026-02-05  
Status: Draft  
Scope: Frontend + backend support (no account page)

## Summary / Why

The dashboard header should feel more “commander-centric” and should explain what happened while the player was away:

- Add a **commander portrait** in the top header, with a **level-dependent frame** and **level number**.
- Add an **idle gains / return summary** (“Since you were away…”) to create a strong re-entry moment and make offline progression visible.
- Make **Commander Suggestions** dismissible/toggleable and remove the redundant “Next Steps” block (or fold it into Suggestions).

This spec intentionally avoids a full account/profile page. The only “profile” element is level/achievements framing.

## Non-goals

- No avatar upload / custom images (yet).
- No editable account settings page.
- No deep achievements system beyond what’s needed to drive level + cosmetics.

## UX Requirements

### 1) Header portrait + level frame

Location: Dashboard header (left side), near the “Welcome, {username}” area.

Display:
- A portrait (default deterministic portrait if none selected).
- A frame around the portrait based on the user’s **commander level**.
- A visible level indicator (e.g. `L12`) inside the frame (badge or inset).

Interactions (MVP):
- Hover tooltip: `Commander Level {n}` and (optionally) “Next unlock: {frameName}”.
- Click opens a small **Commander Panel** popover/modal:
  - Level + progress to next level (if XP exists).
  - Unlocked frames list (read-only).
  - “Coming soon” for future profile features.

Accessibility:
- Portrait element has an accessible label like `Commander portrait, level 12`.

Assets:
- Frames live under a dedicated folder, e.g. `game-server/src/frontend/src/assets/avatars/frames/`.
- Frames are named by level tiers, e.g. `frame_01.png`, `frame_02.png`, … or semantic names like `cadet.png`, `captain.png`.

### 2) Idle gains / return summary (“Since you were away…”)

Location: Header area (right of the title/welcome), directly under/near the welcome line.

Text content (MVP):
- `Welcome back, {username}.`
- `While you were away ({duration}), you gained: +{metal} metal, +{crystal} crystal, +{deut} deuterium.`
- Optional second line if relevant:
  - `Fleets resolved: {n}` / `Research completed: {n}` / `Battles: {n}` (derived from event logs).

Rules:
- Show only if “away time” exceeds a small threshold (e.g. 2 minutes) to avoid noise.
- Cap the summary time window if needed (e.g. 4 weeks) to prevent huge catch-up summaries.

### 3) Commander Suggestions toggle + remove “Next Steps”

Commander Suggestions:
- Add a compact “hide/show” control in the Commander Suggestions card header:
  - Label: `Commander Suggestions` + toggle button `Hide` / `Show`.
- Persist preference (MVP: `localStorage`; later: server-side user settings).

Next Steps:
- Remove the standalone “Next Steps” card, or:
  - fold it into Suggestions as a “Learn / Next steps” collapsible panel.

## Backend Requirements

### A) Expose commander level + cosmetic state

Add to `User` model (or a dedicated table later):
- `commander_level` (int, default 1)
- `commander_xp` (int, default 0) — optional if we want progress bars
- `portrait_key` (string, nullable) — optional; for deterministic portraits we can omit this and derive from `user.id`
- `frame_key` (string, nullable) — optional; otherwise derive from level tier

Expose via:
- `GET /api/auth/me` includes:
  - `commander_level`
  - `commander_xp` (if used)
  - `portrait_key` / `frame_key` if present
  - `last_login` (or a new timestamp, see below)

### B) Track “last seen” cleanly (to compute idle duration)

Problem: the current `last_login` is updated at login time, so the server loses the “previous value” needed for an idle summary.

Add one of:
1) `User.last_seen_at` updated on authenticated requests (cheap, e.g. update on `/api/auth/me` only), OR
2) Update login to return both:
   - `previous_last_login`
   - `last_login` (new value after update)

Recommended:
- Add `last_seen_at` and update it in `GET /api/auth/me` (or a light `/api/ping`).
- Keep `last_login` as “last successful interactive login”.

### C) Idle gains summary endpoint

Add `GET /api/user/idle-summary?since=<iso8601>`

Response (example):
```json
{
  "since": "2026-02-05T18:20:00Z",
  "until": "2026-02-05T19:10:00Z",
  "duration_seconds": 3000,
  "resources": { "metal": 12345, "crystal": 6789, "deuterium": 1112 },
  "events": { "fleets_resolved": 2, "research_completed": 1, "combats": 0 }
}
```

Implementation guidance:
- Use existing `TickLog` rows:
  - Identify the player’s `planet_id`s and `fleet_id`s.
  - Sum `metal_change/crystal_change/deuterium_change` for logs within `[since, until]`.
  - Count event types for “fleets resolved / research completed / combat”.

Notes:
- This is **not** “session recording”. It is a server-side summary of game events that occurred while the player was away.

## Frontend Requirements

### Header UI changes

Dashboard header currently shows logo + `Planetarion` + welcome + buttons.

Add:
- `CommanderPortrait` component next to welcome line.
- Idle summary line(s) under welcome when applicable.

Data flow:
- Ensure `user` object includes `commander_level` and a timestamp (`last_seen_at` or `last_login_previous`).
- On Dashboard load, call `/api/user/idle-summary` when we can compute a `since`.

Testing hooks:
- Add `data-testid="commander-portrait"`, `data-testid="commander-level"`, `data-testid="idle-summary"`.

### Commander Suggestions toggle

- Add `data-testid="commander-suggestions-toggle"`.
- Persist to `localStorage` key, e.g. `pa:commanderSuggestionsHidden=true`.

## Acceptance Criteria (MVP)

- Header shows a portrait with a frame and visible level number for every logged-in user.
- Away/idle summary appears only when away time > threshold and shows resource gains at minimum.
- Commander Suggestions can be hidden/shown and the preference persists across refresh.
- “Next Steps” is removed or merged so we don’t show duplicated guidance blocks.

## Open Questions

- What is “commander level” derived from initially (pure XP? #planets? research milestones)? Suggested MVP:
  - Start at 1, increment via simple milestones (first planet colonized, first research completed, first battle won, etc.).
A: every ship killed / resource recycled / planet colonized gives a certain amount of xp

- Do we want multiple portrait styles (factions) or a single consistent portrait art style?
A: single consistent (put prompt for this in the usual space)

- Do we want frames per exact level, or per tier bands (1–5, 6–10, …)?
A: Tier bands 1-5, 6-10 etc.
