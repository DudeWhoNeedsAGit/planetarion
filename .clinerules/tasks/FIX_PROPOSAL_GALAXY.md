````markdown
# Galaxy Map Debugging & Fixes

## 🎯 Task Overview
The Galaxy Map component has **critical UX and test failures**.  
This task focuses on fixing **fog overlay**, **player marker**, **coordinate display**, and **test selectors**.

---

## ✅ Objectives
1. **Fix Failing Tests**
   - `fog of war is visible with Warcraft 3 styling`
   - `galaxy map visual appearance`

2. **Resolve UI Bugs**
   - Remove persistent **gray center area** (fog overlay moves with map).
   - Make **yellow player marker** move consistently with map panning.
   - Correct **coordinate display calculations**.

3. **Improve Test Reliability**
   - Update Playwright locators to match DOM.
   - Introduce `data-test` attributes for stable selectors.

---

## 🔍 Analysis

### Failing Tests
| Test | Intent | Current Issue |
|------|--------|---------------|
| `fog of war is visible with Warcraft 3 styling` | Check fog overlay + texture layer | Test expects Tailwind selectors (`.absolute.bg-gray-900.opacity-95`), but DOM uses `.fog-overlay` |
| `galaxy map visual appearance` | Verify fog, coordinates, grid, system markers | Selectors mismatch + fog overlay is static, player marker fixed |

### UI Bugs
- **Gray center area** → Fog overlay statically positioned:
  ```jsx
  left: '50%', top: '50%', transform: 'translate(-50%, -50%)'
````

* **Player marker stuck** → Fixed at `(200,150)` px instead of using `viewOffset`.
* **Coordinates wrong** → `viewOffset` treated as galaxy coords, but it’s pixels.

---

## 🛠 Proposed Fixes

### 1. Fog Overlay Positioning

```jsx
<div className="fog-overlay absolute" style={{
  width: `${400 / zoom}px`,
  height: `${300 / zoom}px`,
  left: `${200 + viewOffset.x}px`,
  top:  `${150 + viewOffset.y}px`,
  transform: 'translate(-50%, -50%) scale(${1/zoom})',
  background: 'rgba(64,64,64,0.95)',
  pointerEvents: 'none'
}} />
```

### 2. Player Marker Positioning

```jsx
<div data-test="player-marker"
  className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
  style={{
    left: `${200 + viewOffset.x}px`,
    top:  `${150 + viewOffset.y}px`,
    transform: 'translate(-50%, -50%)',
    zIndex: 15
  }}
  title="Your home system"
/>
```

### 3. Correct Coordinate Calculation

```js
const displayedCenterX = centerX - viewOffset.x / zoom;
const displayedCenterY = centerY - viewOffset.y / zoom;
```

### 4. Update Test Selectors

```javascript
// Fog test
await expect(page.locator('[data-test="fog-overlay"]')).toBeVisible();
await expect(page.locator('[data-test="fog-overlay"] .absolute.inset-0.opacity-30')).toBeVisible();

// Visual appearance test
await expect(page.locator('[data-test="fog-overlay"]')).toBeVisible();
await expect(page.locator('[data-test="coords"]')).toBeVisible();
await expect(page.locator('[data-test="grid"]')).toBeVisible();
await expect(page.locator('[data-test="system-marker"]').first()).toBeVisible();
```

---

## 📋 Implementation Steps

1. **Code Changes**

   * Refactor `fog-overlay` and `player-marker` to move with `viewOffset`.
   * Fix coordinate display math.
   * Add `data-test` attributes:

     * `fog-overlay`
     * `coords`
     * `grid`
     * `system-marker`
     * `player-marker`

2. **Test Updates**

   * Update Playwright locators to use `data-test` attributes.
   * Remove fragile chained Tailwind selectors.

3. **Validation**

   * Run manual panning → ensure fog and player marker move with map.
   * Verify coordinates update correctly.
   * Run `pnpm test:e2e -- galaxy-map` → confirm all pass.

---

## ⚡ Performance Notes

* Consider wrapping markers/fog in a parent container with `transform: translate/scale` (GPU-friendly).
* Use `React.memo` for system markers.
* Virtualize/cull offscreen systems to avoid DOM bloat.

---

## 📌 Deliverables

* [ ] Refactored `GalaxyMap` component (fog + marker dynamic positioning)
* [ ] Fixed coordinate calculation
* [ ] Updated Playwright tests with `data-test` selectors
* [ ] Verified passing test suite & visual regression snapshot

```
```
