# Populate Improvements (Draft)

Date: 2026-02-05  
Owner: Planetarion  
File(s): `game-server/src/backend/routes/populate.py`

## 1) Avoid row-by-row inserts (use batch inserts)

### Problem
`db.session.add(obj)` inside large loops eventually results in individual INSERTs per row at flush/commit time. For populate runs with hundreds/thousands of rows (fleets, tick logs, extra planets), this is slow and noisy.

### Proposal
- For “large, independent rows” that don’t need ORM relationship mechanics:
  - Use `db.session.bulk_save_objects([...])` in batches (e.g. chunk size 500–2000).
  - Or use Core executemany: `db.session.execute(Model.__table__.insert(), list_of_dicts)`.
- Keep classic ORM `add()` only for:
  - rows where you need an ID mid-function,
  - rows where relationships/defaults/events matter.

### Acceptance
- Populate time scales roughly linearly (not “death by 1000 inserts”).
- No behavior changes to game logic; only faster seeding.

## 2) Spiral-shaped galaxy distribution (instead of “rectangle clusters”)

### Problem
The legacy cluster generator distributed planets uniformly in a **square** around a center (`x = cx + randint(-r, r)`), which visually looks like a rectangle blob in the GalaxyMap.

### Proposal: cluster shape modes
Add a configurable “cluster shape” mode:

- `square` (legacy): uniform in a square.
- `disk`: uniform in a circle:
  - sample `angle ~ U(0, 2π)`
  - sample `r = R * sqrt(U(0,1))`
  - convert via `x=cx+r*cos(angle)`, `y=cy+r*sin(angle)`
- `spiral`: galaxy-like spiral arms within a disk:
  - pick `t ~ U(0,1)` from center → edge
  - pick `arm_index` in `[0..arms-1]`
  - `theta = t * turns * 2π + arm_index * (2π/arms) + jitter`
  - `r = (t^p) * R` (p slightly < 1 concentrates points outwards)

### Acceptance
- In the 2D GalaxyMap, the “local neighborhood” looks organic (arms and gaps), not a hard-edged square.
- Deterministic mode remains deterministic (seed → same shape).

## Optional next steps

- Generate **cluster centers** themselves along a larger, global spiral (so the entire galaxy has arms, not only per-cluster arms).
- Add a `--shape` query param to `/populate` for quick visual experiments:
  - `/populate?shape=spiral|disk|square`
- Batch insert planets too, but only after ensuring IDs are still available where needed (`return_defaults=True` or “insert then query”).

