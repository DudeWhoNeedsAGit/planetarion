# Galaxy Map Debugging & Refactor Task

## 🎯 Task Overview
The Galaxy Map component currently has **critical visual and interaction issues**.  
This task focuses on refactoring to align with **Space 4X (Master of Orion, Stellaris, Endless Space)** and optionally **roguelike exploration (FTL, Everspace)** fog-of-war behavior.

---

## ✅ Objectives
1. **Fix Failing Tests**
   - `fog of war is visible with Warcraft 3 styling`
   - `galaxy map visual appearance`

2. **Resolve UI Bugs**
   - Remove persistent **gray center area** (fog overlay moves with map).
   - Make **yellow player marker** move correctly with map panning.
   - Correct **coordinate display calculations**.

3. **Improve Test Reliability**
   - Update Playwright locators to match DOM.
   - Introduce `data-test` attributes for stable selectors.

---

## 🔍 Analysis & Current Issues

### 1. Fog Overlay
**Current Code:**
```jsx
<div className="fog-overlay absolute" style={{
  left: '50%',
  top: '50%',
  transform: 'translate(-50%, -50%)',
  background: 'rgba(64,64,64,0.95)'
}}>
  <div className="absolute inset-0 opacity-30" style={{ backgroundImage: `radial-gradient(...)` }} />
</div>
````

**Issue:** Fixed to screen center; fog holes for explored systems do **not move** with panning/zoom.

**Fix:** Move fog overlay in map-space relative to `viewOffset` and scale with `zoom`.

```jsx
<div className="fog-overlay absolute" style={{
  width: `${400 / zoom}px`,
  height: `${300 / zoom}px`,
  left: `${200 + viewOffset.x}px`,
  top:  `${150 + viewOffset.y}px`,
  transform: `translate(-50%, -50%) scale(${1/zoom})`,
  background: 'rgba(64,64,64,0.95)',
  pointerEvents: 'none'
}}>
```

---

### 2. Player Marker

**Current Code:**

```jsx
<div className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
  style={{ left: '200px', top: '150px' }}
  title="Your home system"
/>
```

**Issue:** Fixed screen coordinates; does **not move** with map panning.

**Fix:** Position relative to `viewOffset` like system markers:

```jsx
<div className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
  style={{
    left: `${200 + viewOffset.x}px`,
    top:  `${150 + viewOffset.y}px`,
    transform: 'translate(-50%, -50%)',
    zIndex: 15
  }}
  title="Your home system"
/>
```

---

### 3. Coordinate Display

**Current Code:**

```jsx
<div className="text-yellow-300">X: {Math.round(centerX + viewOffset.x/zoom)}</div>
<div className="text-green-300">Y: {Math.round(centerY + viewOffset.y/zoom)}</div>
<div className="text-purple-300">Z: {centerZ}</div>
```

**Issue:** Treats pixel offsets as galaxy coordinates; updates incorrectly when panning.

**Fix:** Convert pixel offsets to galaxy coordinates:

```js
const displayedCenterX = centerX - viewOffset.x / zoom;
const displayedCenterY = centerY - viewOffset.y / zoom;
<div className="text-yellow-300">X: {Math.round(displayedCenterX)}</div>
<div className="text-green-300">Y: {Math.round(displayedCenterY)}</div>
<div className="text-purple-300">Z: {centerZ}</div>
```

---

### 4. System Markers

**Current:** Uses `getSystemPosition(system)`:

```js
const getSystemPosition = (system) => ({
  x: (system.x - centerX) * zoom + viewOffset.x,
  y: (system.y - centerY) * zoom + viewOffset.y
});
```

**Issue:** Correct for markers, but **fog overlay and player marker were not using this**, causing misalignment.

**Fix:** Align all map-space elements using same positioning logic.

---

## 🔹 Summary of Required Changes

| Component          | Issue                                       | Fix                                                    |
| ------------------ | ------------------------------------------- | ------------------------------------------------------ |
| Fog Overlay        | Screen-fixed, gray center                   | Anchor to map-space with `viewOffset` and `zoom`       |
| Player Marker      | Screen-fixed                                | Anchor to map-space with `viewOffset` and `zoom`       |
| Coordinate Display | Pixel offsets treated as galaxy coordinates | Correct calculation: `center - viewOffset / zoom`      |
| System Markers     | Mostly OK                                   | Ensure fog and player marker layers align consistently |

---

## 🛠 Test Updates

### Playwright Locators

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

## ⚡ Notes

* Aligns behavior with **Space 4X games**: fog tied to galaxy coordinates, marker moves with map, coordinates reflect viewport.
* Preserves **progressive reveal** for roguelike-style exploration.
* All map-space elements (`fog`, `player marker`, `system markers`) now move consistently with panning and zoom.

---

## 📌 Deliverables

* [ ] Refactored `GalaxyMap` component with map-space fog, player marker, and coordinates
* [ ] Updated Playwright tests with `data-test` selectors
* [ ] Verified passing test suite & visual regression

