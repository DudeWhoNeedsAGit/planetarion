# Research System Proposal (MVP → Iterative Expansion)

This document proposes a **simple, testable Research system** that fits Planetarion’s current tick-based gameplay and unlocks meaningful choices without requiring a massive tech tree up front.

## Goals

- Provide a **long-term progression loop** that complements fleets/combat/colonization.
- Keep mechanics **deterministic and testable** (works with manual ticks and auto-ticks).
- Avoid “dead tab”: Research should always show *something to do* (queue, points, unlocks).

## Core Concepts (MVP)

### Research Points (RP)

- RP is a per-user currency.
- RP accrues automatically from **Research Labs** on owned planets.
- RP accrual is processed during ticks.

**Formula (MVP)**

- Per planet:
  - `rp_per_hour = research_lab_level * 10`
  - Apply energy efficiency multiplier (same concept as production), so research ties into economy.
- Per tick:
  - `rp_gain = rp_per_hour / 720` for 5s ticks.

### Research Queue (one active project per user)

- User can start exactly **one** research project at a time (MVP).
- Starting a project:
  - checks RP >= cost
  - spends RP immediately
  - sets `research_in_progress = { key, level_to, started_at, completes_at }`
- Completing a project:
  - increments the appropriate research level
  - emits activity/log entry

### Research Tree (MVP set)

Start with the tech that already influences core loops:

| Key | Description | Gameplay impact |
|---|---|---|
| `colonization_tech` | Colonization difficulty gate | Higher level allows colonizing harder planets |
| `astrophysics` | Travel optimization | Reduces travel time multiplier |
| `interstellar_communication` | Intel range | Increases galaxy visibility/range |

## UI/UX (MVP)

### Research Tab

- Show:
  - Current RP balance
  - RP/hour and RP/tick estimate
  - Current research levels
  - A “Start research” panel with:
    - research selection dropdown
    - target level (+1)
    - cost preview + ETA
    - start button
- If a research is running:
  - progress bar (time-based)
  - cancel button (optional; refund policy defined below)

### Feedback / Events

When a research completes:
- Add a toast in UI (“Research completed: Astrophysics → Level 2”)
- Add an activity entry in `/api/tick/logs` (so Overview shows it)

## Backend/API (MVP)

### Data model (minimal)

Reuse existing `Research` table (already present) and add a “queue” concept:

- Option A (recommended for speed): store queue on `User` as JSON string:
  - `user.research_queue` (JSON)
- Option B: create `research_queue` table (cleaner, but requires migrations)

Queue JSON example:
```json
{
  "key": "astrophysics",
  "target_level": 2,
  "started_at": "2026-02-01T12:00:00Z",
  "completes_at": "2026-02-01T12:10:00Z"
}
```

### Endpoints

- `GET /api/research` → current RP, levels, queue status, production estimate
- `POST /api/research/start` `{ key }` → starts next level
- `POST /api/research/cancel` → cancels active project

### Tick integration

During each tick:
1) Add RP gains based on each planet’s `research_lab` level (and energy ratio)
2) If queue exists and `now >= completes_at`, complete it:
   - increment research level
   - clear queue
   - emit `TickLog` event_type `research_complete`

## Economy & Balancing (first pass)

### Costs

Use exponential RP cost per level:
- `cost(level_to) = base_cost[key] * (1.6 ** (level_to - 1))`

Suggested base costs:
- `colonization_tech`: 200
- `astrophysics`: 150
- `interstellar_communication`: 150

### Duration

Time-based research keeps the tab engaging even if RP is abundant:
- `duration_seconds = 60 * level_to` (1 min per target level) as a starting point

## Design decisions to lock in (so implementation is consistent)

1) **Refund policy on cancel**
   - MVP: no cancel (simplest)
   - or 100% refund (dev-friendly)
   - or partial refund (adds complexity)
2) **RP cap**
   - MVP: no cap
3) **Multiple queues**
   - MVP: one per user

## Testing Strategy

### Backend (pytest)
- Starting research spends RP and sets queue.
- Tick accrues RP.
- Tick completes research exactly once and increments level.
- Emits `TickLog` entry that is visible via `/api/tick/logs`.

### Frontend (Playwright)
- Research tab renders RP + levels.
- Start a research (mock RP high in test scenario).
- Run tick until completion → verify level increases + activity entry visible on Overview.

## Next Iteration (after MVP)

- Planet-specific research specialization (different planets produce different RP multipliers).
- Spy counter-tech, combat tech, recycler efficiency tech.
- Alliance research bonuses.
- “Research lab building” costs and build times (if we add build queues).

