# Galaxy Map Technical Specification

## Problem Statement

**Original Question:** "condense and explain what the last two tests are testing and show the snippets in the code that are responsible. Also check which ui code is responsible for the still gray area in the center, AND why the yellow player location doesnt move when moving the map there are elements thar are not connect. Write a detailed documents explaining the galaxy map"

**Goal:** Debug and fix critical Galaxy Map issues:
1. Identify the last two failing E2E tests and their code snippets
2. Find UI code responsible for persistent gray center area
3. Debug why yellow player location marker doesn't move with map panning
4. Create comprehensive technical documentation for ChatGPT debugging assistance

## Test Errors and Failures

### Test Execution Results
- **Total Tests:** 27 galaxy map tests
- **Passing:** 22 tests (81.5% success rate)
- **Failing:** 5 tests (18.5% failure rate)
- **Last Two Failing Tests:**
  1. "fog of war is visible with Warcraft 3 styling"
  2. "galaxy map visual appearance"

### Common Test Failure Patterns
```
Error: expect(received).toBeVisible()
Expected element to be visible, but it was not found or hidden
```

```
Error: expect(received).toHaveAttribute(expected)
Expected element to have attribute, but attribute was not found
```

### Specific Test Error Details

#### Test 1: "fog of war is visible with Warcraft 3 styling"
**Expected Error Pattern:**
```
Error: expect(received).toBeVisible()

Call log:
- expect(page.locator('.absolute.inset-0.flex.items-center.justify-center .relative .absolute.bg-gray-900.opacity-95')).toBeVisible()
- expect(page.locator('.absolute.inset-0.flex.items-center.justify-center .relative .absolute.bg-gray-900.opacity-95 .absolute.inset-0.opacity-30')).toBeVisible()

Expected: visible
Received: hidden/not found
```

**Root Cause:** Test expects nested CSS selectors that don't match the actual DOM structure. The fog overlay uses different class combinations than expected.

#### Test 2: "galaxy map visual appearance"
**Expected Error Pattern:**
```
Error: expect(received).toBeVisible()

Call log:
- expect(page.locator('.absolute.bg-gray-900.opacity-95')).toBeVisible() // Fog
- expect(page.locator('.absolute.top-2.left-2.text-white')).toBeVisible() // Coordinates
- expect(page.locator('.absolute.inset-0.opacity-60')).toBeVisible() // Grid
- expect(page.locator('.absolute.w-16.h-16')).toHaveCount(...) // Systems

Expected: visible
Received: hidden/not found
```

**Root Cause:** Visual elements are not rendering correctly due to positioning issues (gray center area) and missing CSS classes that match the test selectors.

## Overview
This document provides a detailed technical specification of the Galaxy Map component in the Planetarion game, including implementation details, failing test analysis, and identified issues.

## Component Architecture

### Core Structure
```javascript
function GalaxyMap({ user, planets, onClose }) {
  // State management
  const [systems, setSystems] = useState([]);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [exploredSystems, setExploredSystems] = useState(new Set());
}
```

### Coordinate System
```javascript
// Coordinate utilities
const CoordinateUtils = {
  isValidCoordinate: (x, y, z) => {
    return (
      typeof x === 'number' && !isNaN(x) && x >= -10000 && x <= 10000 &&
      typeof y === 'number' && !isNaN(y) && y >= -10000 && y <= 10000 &&
      typeof z === 'number' && !isNaN(z) && z >= -10000 && z <= 10000
    );
  },

  formatCoordinates: (x, y, z) => `${x}:${y}:${z}`,

  calculateDistance: (x1, y1, z1, x2, y2, z2) => {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dz = z2 - z1;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }
};
```

## Rendering System

### Map Container Structure
```jsx
<div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
  <div className="bg-gray-800 rounded-lg p-6 max-w-6xl w-full h-5/6 flex flex-col">
    {/* Map Container */}
    <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden relative galaxy-background">
      {/* Deep Space Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900">
        {/* Nebula Layers */}
        {/* Animated Starfield */}
        {/* Floating Particles */}
      </div>

      {/* Grid Background */}
      <div className="absolute inset-0 opacity-60">
        <svg width="100%" height="100%">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Coordinate Labels */}
      <div className="absolute top-2 left-2 text-xs text-white font-mono bg-black bg-opacity-70 px-3 py-2 rounded-lg border border-gray-600 shadow-lg">
        <div className="font-semibold text-blue-300">Coordinates:</div>
        <div className="text-yellow-300">X: {Math.round(centerX + viewOffset.x/zoom)}</div>
        <div className="text-green-300">Y: {Math.round(centerY + viewOffset.y/zoom)}</div>
        <div className="text-purple-300">Z: {centerZ}</div>
      </div>

      {/* Systems Display */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative">
          {/* Fog of War Overlay */}
          <div className="fog-overlay absolute" style={{
            width: '400px',
            height: '300px',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(64,64,64,0.95)',
            pointerEvents: 'none'
          }}>
            {/* Atmospheric fog texture */}
            <div className="absolute inset-0 opacity-30" style={{
              backgroundImage: `
                radial-gradient(circle at 20% 80%, rgba(64,64,64,0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(96,96,96,0.2) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(32,32,32,0.4) 0%, transparent 50%)
              `,
              animation: 'fogDrift 30s ease-in-out infinite',
              pointerEvents: 'none'
            }} />

            {/* Fog Holes for Explored Systems */}
            {systems.filter(system => system.explored).map((system, index) => {
              const pos = getSystemPosition(system);
              const relativeX = pos.x + 200;
              const relativeY = pos.y + 150;

              return (
                <div key={`fog-${index}`} className="fog-hole absolute w-40 h-40 rounded-full" style={{
                  left: `${relativeX}px`,
                  top: `${relativeY}px`,
                  transform: 'translate(-50%, -50%)',
                  background: `radial-gradient(circle, transparent 0%, transparent 25%, rgba(64,64,64,0.8) 45%, rgba(96,96,96,0.9) 65%, rgba(128,128,128,0.95) 85%, rgba(160,160,160,0.98) 100%)`,
                  boxShadow: '0 0 20px rgba(0,0,0,0.5)',
                  filter: 'blur(1px)',
                  pointerEvents: 'none'
                }} />
              );
            })}
          </div>

          {/* System Markers */}
          {systems.map((system, index) => {
            const pos = getSystemPosition(system);
            const isVisible = Math.abs(pos.x) < 300 && Math.abs(pos.y) < 200;

            if (!isVisible) return null;

            return (
              <div key={index} className="system-marker absolute w-16 h-16 rounded-full border-2 cursor-pointer transition-all duration-200 flex items-center justify-center text-xs font-bold"
                style={{
                  left: `${pos.x + 200}px`,
                  top: `${pos.y + 150}px`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: system.explored ? 10 : 5
                }}
                onClick={() => handleExploreSystem(system)}
              >
                <div className="text-center">
                  <div>{system.x - centerX}:{system.y - centerY}</div>
                  <div className="text-xs opacity-75">
                    {system.explored ? `${system.planets}P` : '???'}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Center Marker (Player Location) */}
          <div className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
            style={{
              left: '200px',
              top: '150px',
              transform: 'translate(-50%, -50%)',
              zIndex: 15
            }}
            title="Your home system"
          />
        </div>
      </div>
    </div>
  </div>
</div>
```

## Event Handling System

### Mouse Interactions
```javascript
// Mouse drag handlers for panning
const handleMouseDown = (e) => {
  if (e.button === 0) {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    e.preventDefault();
  }
};

const handleMouseMove = (e) => {
  if (isDragging) {
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    setViewOffset(prev => ({
      x: prev.x + deltaX,
      y: prev.y + deltaY
    }));
    setDragStart({ x: e.clientX, y: e.clientY });
    e.preventDefault();
  }
};
```

### System Position Calculation
```javascript
const getSystemPosition = (system) => {
  const relativeX = (system.x - centerX) * zoom + viewOffset.x;
  const relativeY = (system.y - centerY) * zoom + viewOffset.y;
  return { x: relativeX, y: relativeY };
};
```

## API Integration

### Fetch Nearby Systems
```javascript
const fetchNearbySystems = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch(`http://localhost:5000/api/galaxy/nearby/${centerX}/${centerY}/${centerZ}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    setSystems(data);
  } catch (error) {
    // Fallback data for testing
    setSystems([
      { x: centerX + 10, y: centerY + 20, z: centerZ + 30, explored: false, planets: 0, owner_id: null },
      { x: centerX - 15, y: centerY - 25, z: centerZ - 35, explored: true, planets: 2, owner_id: user.id },
      // ... more fallback systems
    ]);
  }
};
```

## Failing Tests Analysis

### Test 1: "fog of war is visible with Warcraft 3 styling"

**Test Code:**
```javascript
test('fog of war is visible with Warcraft 3 styling', async ({ page }) => {
  await navigateToGalaxyMap(page);

  // Check fog overlay exists with correct Warcraft 3 styling
  const fogOverlay = page.locator('.absolute.inset-0.flex.items-center.justify-center .relative .absolute.bg-gray-900.opacity-95');
  await expect(fogOverlay).toBeVisible();

  // Check atmospheric texture layer exists
  const textureLayer = page.locator('.absolute.inset-0.flex.items-center.justify-center .relative .absolute.bg-gray-900.opacity-95 .absolute.inset-0.opacity-30');
  await expect(textureLayer).toBeVisible();
});
```

**What it's testing:**
- Verifies the fog overlay has the correct CSS classes and styling
- Checks for atmospheric texture layer with opacity effects
- Validates Warcraft 3-style fog of war appearance

**Why it fails:**
The test expects specific CSS class combinations that may not match the actual implementation. The fog overlay styling might be different from what's expected.

### Test 2: "galaxy map visual appearance"

**Test Code:**
```javascript
test('galaxy map visual appearance', async ({ page }) => {
  await navigateToGalaxyMap(page);
  await page.waitForTimeout(2000);

  // Take screenshot for visual regression testing
  await page.screenshot({
    path: 'galaxy-map-visual-test.png',
    clip: { x: 0, y: 0, width: 800, height: 600 }
  });

  // Verify key visual elements are present
  await expect(page.locator('.absolute.bg-gray-900.opacity-95')).toBeVisible(); // Fog
  await expect(page.locator('.absolute.top-2.left-2.text-white')).toBeVisible(); // Coordinates
  await expect(page.locator('.absolute.inset-0.opacity-60')).toBeVisible(); // Grid
  await expect(page.locator('.absolute.w-16.h-16')).toHaveCount(await page.locator('.absolute.w-16.h-16').count()); // Systems
});
```

**What it's testing:**
- Takes a screenshot for visual regression testing
- Verifies presence of key visual elements:
  - Fog overlay
  - Coordinate display
  - Grid background
  - System markers

**Why it fails:**
The test is checking for visual elements that may not be rendered correctly or may have different CSS classes than expected.

## Critical Issues Identified

### Issue 1: Gray Center Area Problem

**Problem:** The fog overlay creates a persistent gray area in the center of the map that doesn't move with panning.

**Root Cause:**
```javascript
// In GalaxyMap.js - Fog overlay positioning
<div className="fog-overlay absolute" style={{
  width: '400px',
  height: '300px',
  left: '50%',
  top: '50%',
  transform: 'translate(-50%, -50%)', // FIXED POSITIONING
  background: 'rgba(64,64,64,0.95)',
  pointerEvents: 'none'
}}>
```

**Impact:**
- Creates a static gray rectangle that blocks the starfield
- Doesn't respond to map panning or zooming
- Makes the center of the map permanently obscured

**Solution:**
The fog overlay should be positioned relative to the map container and move with the view offset, similar to system markers.

### Issue 2: Yellow Player Location Not Moving

**Problem:** The yellow center marker (player location) stays fixed while the map pans, creating a disconnect between the player's position and the moving map.

**Root Cause:**
```javascript
// In GalaxyMap.js - Center marker positioning
<div className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
  style={{
    left: '200px',    // FIXED POSITION
    top: '150px',     // FIXED POSITION
    transform: 'translate(-50%, -50%)',
    zIndex: 15
  }}
  title="Your home system"
/>
```

**Impact:**
- Player location appears to "float" independently of the map
- Creates confusing visual disconnect during navigation
- Makes it difficult to understand the player's actual position

**Solution:**
The center marker should be positioned relative to the view offset, similar to how system markers are positioned.

### Issue 3: Coordinate Display Not Updating

**Problem:** The coordinate display shows fixed values that don't update when the map is panned.

**Current Implementation:**
```javascript
// In GalaxyMap.js - Coordinate display
<div className="text-yellow-300">X: {Math.round(centerX + viewOffset.x/zoom)}</div>
<div className="text-green-300">Y: {Math.round(centerY + viewOffset.y/zoom)}</div>
<div className="text-purple-300">Z: {centerZ}</div>
```

**Issue:** The coordinate calculation is incorrect. The viewOffset represents pixel offsets, but the coordinates should represent the actual galaxy coordinates being viewed at the center of the screen.

## Proposed Fixes

### Fix 1: Dynamic Fog Overlay Positioning

```javascript
// Replace static fog overlay with dynamic positioning
<div className="fog-overlay absolute" style={{
  width: '400px',
  height: '300px',
  left: `${200 + viewOffset.x}px`,  // Move with view offset
  top: `${150 + viewOffset.y}px`,   // Move with view offset
  transform: 'translate(-50%, -50%) scale(${1/zoom})', // Scale with zoom
  background: 'rgba(64,64,64,0.95)',
  pointerEvents: 'none'
}}>
```

### Fix 2: Dynamic Player Location Marker

```javascript
// Position player marker relative to view offset
<div className="absolute w-4 h-4 bg-yellow-400 rounded-full border-2 border-yellow-200"
  style={{
    left: `${200 + viewOffset.x}px`,  // Move with view offset
    top: `${150 + viewOffset.y}px`,   // Move with view offset
    transform: 'translate(-50%, -50%)',
    zIndex: 15
  }}
  title="Your home system"
/>
```

### Fix 3: Correct Coordinate Calculation

```javascript
// Calculate actual coordinates at screen center
const displayedCenterX = centerX - viewOffset.x / zoom;
const displayedCenterY = centerY - viewOffset.y / zoom;

// Update coordinate display
<div className="text-yellow-300">X: {Math.round(displayedCenterX)}</div>
<div className="text-green-300">Y: {Math.round(displayedCenterY)}</div>
<div className="text-purple-300">Z: {centerZ}</div>
```

## Test Updates Needed

### Update Fog Test Selectors
```javascript
// Update test selectors to match actual implementation
test('fog of war is visible with Warcraft 3 styling', async ({ page }) => {
  await navigateToGalaxyMap(page);

  // Check for fog overlay with correct selector
  const fogOverlay = page.locator('.fog-overlay');
  await expect(fogOverlay).toBeVisible();

  // Check atmospheric texture
  const textureLayer = page.locator('.fog-overlay .absolute.inset-0.opacity-30');
  await expect(textureLayer).toBeVisible();
});
```

### Update Visual Appearance Test
```javascript
test('galaxy map visual appearance', async ({ page }) => {
  await navigateToGalaxyMap(page);
  await page.waitForTimeout(2000);

  // Verify key visual elements with correct selectors
  await expect(page.locator('.fog-overlay')).toBeVisible();
  await expect(page.locator('.absolute.top-2.left-2.text-white')).toBeVisible();
  await expect(page.locator('.absolute.inset-0.opacity-60')).toBeVisible();
  await expect(page.locator('[data-test-marker="system-marker"]').first()).toBeVisible();
});
```

## Performance Considerations

### Rendering Optimization
- Use `React.memo` for system markers to prevent unnecessary re-renders
- Implement virtual scrolling for large numbers of systems
- Debounce rapid mouse movements to reduce coordinate updates

### Memory Management
- Clean up event listeners on component unmount
- Use `useCallback` for event handlers to prevent recreation
- Implement system culling for systems outside viewport

## Conclusion

The Galaxy Map component has a solid foundation but suffers from critical positioning issues that break the user experience. The fog overlay and player location marker need to be repositioned relative to the view offset, and coordinate calculations need correction. The failing tests highlight these visual and interaction problems that must be addressed for a functional galaxy map experience.

The fixes outlined above will resolve the gray center area, make the player location move correctly with the map, and ensure proper coordinate display updates during navigation.
