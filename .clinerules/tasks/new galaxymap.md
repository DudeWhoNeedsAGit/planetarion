# Task: Refactor `GalaxyMap.js` — Remove Fog of War & Simplify Map (Cline task.md)

## Summary

Remove the Fog-of-War implementation and all related rendering logic so the **space background is always visible**. Keep system markers, zoom/pan, grid, and UI controls intact. Remove unused fog state and cleanup unused imports. Deliver a clean, functional `GalaxyMap.js` ready for E2E tests that expect visible background and system markers.

---

## Files to edit

* `src/components/GalaxyMap.js` (or the path where your component lives)

---

## Preconditions

* Ensure you have a working branch for changes (do not commit directly to `main`).
* Run tests before/after change: `pnpm test` / `pnpm test:e2e` (or your project commands).

---

## Changes (step-by-step, actionable)

### 1) Remove Fog overlay render block

**What to remove:** the block that renders per-system fog (the `systems.map(...)` that outputs fog `<div>`s). In your current file this is the first `systems.map` block inside the Map Container (look for comment or code that contains `/* Fog Overlay for systems */` or `key={`fog-\${index}`}`).

**Search token:** `key={`fog-\${index}`}` or `/* Fog Overlay for systems */`

**Delete this whole block.**
(Example of the block to remove — remove exactly this construct from your file)

```jsx
{systems.map((system, index) => {
  const pos = getSystemPosition(system);
  const containerWidth = containerDimensions.width || 800;
  const containerHeight = containerDimensions.height || 600;

  return (
    <div
      key={`fog-${index}`}
      className="absolute rounded-full transition-opacity duration-700 ease-out"
      style={{
        left: `${pos.x + containerWidth/2}px`,
        top: `${pos.y + containerHeight/2}px`,
        width: '80px',
        height: '80px',
        transform: 'translate(-50%, -50%)',
        background: `radial-gradient(... )`,
        opacity: system.explored ? 0 : 1,
      }}
    />
  );
})}
```

> After deletion there must be no duplicates of this block elsewhere.

---

### 2) Remove fog-related state & helper usage

* Remove `exploredSystems` state if unused:

  ```js
  // remove
  const [exploredSystems, setExploredSystems] = useState(new Set());
  ```
* Remove any code that only served to compute / update fog (e.g., code that set sector/state purely for fog rendering). Keep `system.explored` only if still used for gameplay (e.g., subtle UI differences or enabling colonize).

Search tokens:

* `exploredSystems`
* `opacity: system.explored`
* `system.explored ? 0 : 1` (remove or refactor)

If you need `system.explored` for game logic (not rendering), keep it in `systems` but **do not use it to hide background**.

---

### 3) Keep background always visible (ensure nothing hides it)

Locate the Deep Space Background block:

```jsx
<div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900">
  {/* nebula layers */}
  {/* animated starfield */}
  {/* floating particles */}
</div>
```

**Ensure:**

* This block remains **before** system markers in DOM order (background underneath).
* No parent element or overlay sets a full-screen opaque layer above it (we removed that).
* `z-index` ordering: background `z` lower than markers (default absolute ordering is OK if no custom z-index is applied above).

---

### 4) Keep & verify System markers block

Ensure the system marker block (the second `systems.map(...)` in your file) remains, with proper positioning and z-index above the background. Typical snippet to keep:

```jsx
{systems.map((system, index) => {
  const pos = getSystemPosition(system);
  const containerWidth = containerDimensions.width || 800;
  const containerHeight = containerDimensions.height || 600;
  const isVisible = Math.abs(pos.x) < containerWidth/2 && Math.abs(pos.y) < containerHeight/2;

  if (!isVisible) return null;

  return (
    <div
      key={index}
      ref={(el) => el && EventHandlingSystem.setupSystemMarkerEvents(el)}
      className={`system-marker absolute w-16 h-16 rounded-full ... ${markerClass}`}
      style={{
        left: `${pos.x + containerWidth/2}px`,
        top: `${pos.y + containerHeight/2}px`,
        transform: 'translate(-50%, -50%)',
        zIndex: system.explored ? 10 : 5
      }}
      onClick={() => handleExploreSystem(system)}
    >
      {/* marker content */}
    </div>
  );
})}
```

**Action:** Keep this intact. Remove only fog-related conditional classes (if any).

---

### 5) Remove imports/usages not needed anymore

* Remove `axios` import if unused.
* Remove any CSS classes or helper functions used exclusively for fog (e.g., mask-building helpers).

Search tokens:

* `import axios`
* `fog-overlay`
* `fog-hole`

---

### 6) Update `handleExploreSystem` logic (simplify)

Keep exploration API and state updates but **do not** try to update fog. Example minimal flow:

```js
const handleExploreSystem = async (system) => {
  if (system.explored) {
    setSelectedSystem(system);
    return;
  }
  setLoading(true);
  try {
    // API call (optional)
    // mark system explored for gameplay
    setSystems(prev => prev.map(s => s.x===system.x && s.y===system.y && s.z===system.z ? { ...s, explored: true } : s));
  } finally {
    setLoading(false);
  }
};
```

---

### 7) Run tests and visual checks

* Run unit/E2E:

  * `pnpm test`
  * `pnpm test:e2e --grep 'galaxy map'` (or relevant test command)
* Manual check:

  * Background visible on load.
  * System markers are clickable and render in correct positions.
  * Grid toggle works.
  * Zoom/pan unaffected.

---

## Acceptance Criteria (Checklist)

* [ ] Fog overlay block removed from `GalaxyMap.js`.
* [ ] No full-screen opaque overlay above background.
* [ ] Background (nebula/starfield) visible on initial load.
* [ ] System markers render and remain clickable.
* [ ] `handleExploreSystem` updates `systems` state but does not toggle any fog rendering.
* [ ] No unused imports (`axios`, fog helpers) remain.
* [ ] E2E tests that check visual presence of background and system elements pass.

---

## Example small diff (conceptual)

* **Delete** the entire `systems.map` that renders fog `<div>`s.
* **Keep** the system markers `systems.map`.
* **Remove** `exploredSystems` state if it only fed the fog.

---

## Implementation notes for Cline

* Use the in-file comment markers (if present) to locate fog block (`/* Fog Overlay for systems */`).
* If multiple fog blocks exist, search for `fog-hole`, `fog-overlay`, `key={'fog-'`.
* Keep changes atomic and create a single PR with the above edits.
* Add a short PR description: "Remove fog-of-war overlay — keep background always visible and simplify exploration logic."
