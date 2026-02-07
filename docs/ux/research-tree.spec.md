# Planetarion — Research Tree (Economy / Combat / Expansion) (Spec)

Date: 2026-02-05  
Status: Draft  
Scope: Game design + UI/API contract (phased rollout)

## Problem

The current research set is too small and the semantics are unclear:
- Players expect “Colonization” to be unlocked by research and then “just work”.
- In practice, colonization requires **colony ships**, **tick processing**, and **Colonization Tech ≥ target difficulty**.
- There’s no visible structure (economy vs combat vs expansion), so progression feels arbitrary.

## Goals

- Provide a clear, expandable research tree with 3 primary branches:
  1) **Economy** (income, storage, efficiency)
  2) **Combat** (damage, defense, ship performance)
  3) **Expansion** (colonization, travel, logistics, intel)
- Make early progression obvious:
  - “What do I research first to expand?”
  - “What do I research first to fight?”
- Make colonization feel like an intentional loop:
  - Unlock → build colony ship → send colonize mission → resolve (tick) → new colony.

## Definitions / Current Behavior (for alignment)

### Colonization “works” only if

- You have at least one `colony_ship` in the fleet.
- You send mission `colonize` to empty coordinates.
- A tick (auto scheduler or manual tick) processes arrivals.
- Your `colonization_tech` is high enough for the target’s **colonization difficulty**.

### Colonization difficulty

Difficulty is deterministic and coordinate-based (1–5). Higher difficulty requires higher Colonization Tech.

## Proposed Research Structure (v1)

Each research item has:
- key (stable id)
- name
- max level (or soft cap)
- cost curve (RP)
- time curve (optional; could remain tick-based for now)
- effect per level

### 1) Expansion branch

**Colonization Tech** (`colonization_tech`)
- L1: unlock colonization loop (send colonize mission succeeds on difficulty-1 targets)
- L2–L5: unlock difficulty 2–5 targets
- UI should show: “Target requires Colonization Tech L{n}”

**Astrophysics** (`astrophysics`)
- Travel time reduction per level (already exists).
- Colony cap increase per level (already exists: `+2 colonies / level`).

**Interstellar Communication** (`interstellar_communication`)
- Unlocks alliance/shared intel later
- In MVP: could expand activity feed retention or allow basic “pings”

**Logistics** (new)
- Reduced fuel costs / increased cargo efficiency for long trips

**Espionage** (new)
- Unlock espionage probe effectiveness / report detail

### 2) Economy branch

**Mining Optimization** (new)
- +% metal/crystal/deut production per level

**Energy Efficiency** (new)
- +% energy production or -% energy usage

**Storage Engineering** (new)
- +% storage capacity or reduced overflow loss (if introduced)

**Recycling Efficiency** (new, referenced by UI suggestions already)
- +% recycler capacity or improved debris yield

### 3) Combat branch

**Weapons Tech** (new/exists as placeholder in backend model)
- +% damage per level

**Armor Tech** (new)
- +% hull/HP per level

**Shield Tech** (new)
- +% shields per level

**Drive Tech** (new; combustion/impulse/hyperspace exist in backend model)
- unlock faster ships / speed multipliers, impacts travel time by ship class

## UI Requirements (MVP)

### Research screen

- Group by branch with clear headings.
- Each card shows:
  - current level
  - next level cost
  - primary effect summary
  - “Unlocks” bullet(s) (e.g., “Colonize difficulty-2 planets”)

### Fleet send / colonize UX

- When mission is `colonize`, show a small “requirements” line:
  - required colonization tech for entered coordinates
  - show current tech level (from `/api/research` or `/api/auth/me`)
- Error messages include required/current levels (even if the UI doesn’t parse fields).

## Backend/API Requirements (phased)

### Phase A (clarity + unblock colonization)

- Ensure local test/unowned planets include low-difficulty targets near players (difficulty 1–2) so Colonization Tech L1–L2 is meaningful.
- Return helpful error strings for colonization failures (required/current levels).

### Phase B (tree expansion)

- Expand `/api/research` to include new keys and effect metadata:
  - `branches` array with items
  - `effects` summary for each key
  - `unlocks` array per level

## Acceptance Criteria (v1)

- A player with `colonization_tech = 2` can reliably find and colonize at least one nearby target.
- UI makes it obvious *why* colonization fails (missing colony ship vs insufficient tech vs occupied).
- Research UI clearly communicates branches and what each research does.

