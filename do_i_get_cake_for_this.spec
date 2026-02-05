# Planetarion — “Highest ROI” Ideas Backlog (v1)
Date: 2026-02-04  
Owner: You  
Purpose: A curated list of **highest ROI** additions to make Planetarion feel “alive”, strategic, and addictive, with minimal engineering waste.

---

## North Star (what “fun” should feel like)

**20–30 min active session** yields:
- 1–3 meaningful decisions (target selection, fleet composition, tech choice)
- 1–2 “moments” (combat result, capture, research completion, debris payout)
- 1 clear next step (suggestions rail / missions)

**Idle time** yields:
- resources progressed
- fleets resolved
- news/events to react to

---

## 1) “Close the Loop” Reliability (must-have)

### 1.1 Tick confidence
- **Auto tick by default** in “real play” mode; manual tick only as dev/admin tool.
- Every system that depends on ticks must have:
  - stable state machine transitions
  - deterministic ordering
  - idempotent “re-run tick” behavior (no double credit)

**ROI**: Removes frustration; makes every other feature feel better.

### 1.2 Offline catch-up (idle progression)
- On server start, fast-forward up to 4 weeks (cap) using delta-based catch-up:
  - resource accrual = prod_rate * elapsed
  - fleets: resolve by `arrival_time <= now`
  - research: consume RP budget, pop queue items

**ROI**: Makes game viable with intermittent hosting; creates “return dopamine”.

### 1.3 “Truthful UI”
- No “Arrived (pending tick)” surprises without a clear timer/state.
- Consistent ETA semantics:
  - traveling: real countdown
  - arrived: resolved immediately if auto ticks on; otherwise explicit “awaiting server tick”

---

## 2) Galaxy as a Decision Surface (best long-term retention)

### 2.1 Intel loop (fog-of-war as gameplay, not UX bug)
Define clear intel levels:
- `contact`: marker + coords + type hint
- `scouted`: owner/type + basic risk
- `full`: garrison estimate + loot/debris estimate + action constraints

How to gain intel:
- explore mission
- spy mission
- alliance shared intel (later)

**ROI**: Turns “map browsing” into meaningful planning.

### 2.2 Map overlays (strategic)
Overlays toggles:
- Pirates density / threat
- Player activity heat (recent fights/raids)
- Debris fields known
- Fleet movements (already started)
- Range rings from selected planet (travel time preview)

**ROI**: Makes the map the core tool for play.

### 2.3 “Why can I attack this?” + “What do I gain?”
Every target tooltip shows:
- estimated difficulty (pirate level / defender estimate)
- expected loot/debris range
- travel time
- recommended fleet template

---

## 3) Fleet UX = Fun Multiplier

### 3.1 Fleet templates (one-click)
Templates per planet:
- Raid (fast fighters + cargo)
- Recycle (recyclers + cargo)
- Colonize (colony + escorts + cargo)
- Spy (probes)

**ROI**: Converts “micromanagement” into “fast decisions”.

### 3.2 Dissolve / rebalance fleets
Allow:
- dissolve fleet back to inventory
- move ships between fleets on same planet
- split fleet into two

**ROI**: Lets players iterate strategies quickly.

### 3.3 Batch actions
- “Send recyclers” from combat report (already)
- “Send raid fleet” from map tooltip
- “Recall all” for selected planet
- “Repair / rebuild” CTA after heavy losses

---

## 4) Pirate AI (farmable, escalating, time-boxed)

### 4.1 Per-player pirate ladder near home
- Spawn pirate camps near each player on their Z-slice.
- Camps have tiers (I–V) with scaling rewards.
- Players progress by defeating camps → unlock next tier.

**ROI**: Reliable content pipeline; solo fun; testing target.

### 4.2 “Peak time threat” windows
Given your note:
- Pirates act hourly
- higher threat 18:00–20:00 local server time

Implement:
- hourly pirate “raids” that generate:
  - debris events
  - defense prompts
  - temporary buffs if defended successfully

**ROI**: Creates predictable “events” that players log in for.

---

## 5) Rewards You Can Feel (Dopamine UX)

### 5.1 Combat summary cards (shareable)
After each fight:
- Win/Loss
- ships lost (both sides)
- debris created
- loot gained
- CTA: “Send recyclers”, “Attack again”, “Colonize”

**ROI**: Converts raw numbers into satisfying moments.

### 5.2 Milestones + achievements
Lightweight achievements:
- first capture
- first recycler payout
- first fleet template
- research level milestones

**ROI**: Tiny effort, big retention.

### 5.3 Commander Suggestions widget
Small “next step” rail:
- “Attack nearby pirate camp (Tier II)”
- “Recycle debris at X”
- “Start Astrophysics L2”

**ROI**: Prevents “what do I do now?” drop-off.

---

## 6) Social Layer (only after core loop is solid)

### 6.1 Alliance MVP
- alliance roster + basic chat + shared intel toggle
- alliance “pings” on targets

### 6.2 Player vs player arcs
- scouting → raid → counter-raid → conquest window
- clear rules to prevent grief spirals

**ROI**: Social adds retention, but only if loop is stable.

---

## 7) Economy / Scaling QoL

### 7.1 Shipyard scale controls
- numeric text input + “max” + multipliers

### 7.2 Resource sinks
- fleet upkeep (optional)
- research boosters (late game)
- defense structures (planet investment)

**ROI**: Prevents runaway numbers and “infinite accumulation”.

---

## 8) Observability for Fast Iteration (dev ROI)

### 8.1 Scenario reset buttons (admin/dev)
- “Two player loop”
- “Pirate ladder tier III”
- “Debris-rich battle”

### 8.2 In-game debug overlay (dev only)
- tick status
- scheduler on/off
- last tick time
- event stream status (SSE)

**ROI**: Cuts iteration time dramatically.

---

## Proposed Next 5 (if you want “real game” quickest)

1) Auto-ticks + offline catch-up (cap 4 weeks)  
2) Fleet templates + dissolve/rebalance  
3) Pirate ladder near player + tiered rewards  
4) Combat summary + CTA moments (recycle/colonize)  
5) Galaxy overlays + intel levels (contact/scouted/full)

---

## Acceptance criteria for “cake tier”

- New player can: build ships → raid pirates → see clear win summary → send recyclers → get payout → colonize → rename → repeat.
- No manual babysitting required (ticks, ETAs, arrivals).
- Galaxy map answers: where to go, why, and what reward.

