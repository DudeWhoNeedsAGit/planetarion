# Fleet Tab Event Mechanics Specification

## Overview

This document provides a comprehensive analysis of the Fleet Management tab event mechanics, including event chains, component interactions, data flow, and debugging strategies.

## Table of Contents

1. [Event Flow Architecture](#event-flow-architecture)
2. [Component Data Contracts](#component-data-contracts)
3. [State Management Patterns](#state-management-patterns)
4. [Event Chain Analysis](#event-chain-analysis)
5. [Debugging Guide](#debugging-guide)
6. [Testing Strategies](#testing-strategies)
7. [Performance Considerations](#performance-considerations)

---

## Event Flow Architecture

### Primary Event Chains

#### 1. Planet Selection Flow

```mermaid
graph TD
    A[User Clicks Planet Button] --> B[onClick Handler]
    B --> C[setSelectedPlanet(planet)]
    C --> D[State Update Triggered]
    D --> E[Component Re-render]
    E --> F[PlanetOverviewCard Updates]
    E --> G[ShipAvailabilityDashboard Updates]
    E --> H[FleetTile Components Filter]
    F --> I[UI Shows Planet-Specific Data]
    G --> I
    H --> I
```

#### 2. Fleet Creation Flow

```mermaid
graph TD
    A[User Clicks Create Fleet] --> B[setShowCreateForm(true)]
    B --> C[CreateFleetModal Renders]
    C --> D[Modal Receives Props]
    D --> E[Planet Dropdown Populates]
    E --> F[User Selects Planet]
    F --> G[formData.start_planet_id Updates]
    G --> H[User Submits Form]
    H --> I[handleSubmit Executes]
    I --> J[API Call: POST /api/fleet]
    J --> K[Fleet Created Successfully]
    K --> L[UI Updates with New Fleet]
```

#### 3. Fleet Sending Flow

```mermaid
graph TD
    A[User Clicks Send Fleet] --> B[setSelectedFleet(fleet)]
    B --> C[setShowSendForm(true)]
    C --> D[SendFleetModal Renders]
    D --> E[User Selects Target]
    E --> F[User Sets Mission]
    F --> G[User Submits Form]
    G --> H[handleSendFleet Executes]
    H --> I[API Call: POST /api/fleet/send]
    I --> J[Fleet Status Updates]
    J --> K[UI Updates Fleet Status]
```

### Secondary Event Chains

#### Data Fetching Flow

```mermaid
graph TD
    A[Component Mounts] --> B[useEffect Triggers]
    B --> C[fetchFleets() Called]
    C --> D[API Call: GET /api/fleet]
    D --> E[Response Received]
    E --> F[setFleets(data) Updates State]
    F --> G[Component Re-renders]
    G --> H[UI Shows Fleet Data]
```

#### Error Handling Flow

```mermaid
graph TD
    A[API Call Fails] --> B[Error Caught]
    B --> C[showError() Called]
    C --> D[Toast Notification Shown]
    D --> E[User Sees Error Message]
    E --> F[User Can Retry Action]
```

---

## Component Data Contracts

### FleetManagement Component

#### Props Received
```typescript
interface FleetManagementProps {
  user: {
    id: number;
    username: string;
    // ... other user properties
  };
  planets: Planet[];
}

interface Planet {
  id: number;
  name: string;
  x: number;
  y: number;
  z: number;
  coordinates?: string; // May be missing
  user_id: number;
  is_home_planet: boolean;
  metal?: number;
  crystal?: number;
  deuterium?: number;
  small_cargo?: number;
  large_cargo?: number;
  light_fighter?: number;
  heavy_fighter?: number;
  cruiser?: number;
  battleship?: number;
  colony_ship?: number;
  recycler?: number;
  // ... other planet properties
}
```

#### State Managed
```typescript
interface FleetManagementState {
  fleets: Fleet[];
  selectedPlanet: Planet | null;
  showCreateForm: boolean;
  showSendForm: boolean;
  selectedFleet: Fleet | null;
  loading: boolean;
}

interface Fleet {
  id: number;
  mission: string;
  status: string;
  start_planet_id: number;
  target_planet_id: number;
  arrival_time?: string;
  departure_time?: string;
  eta?: number;
  ships?: {
    small_cargo?: number;
    large_cargo?: number;
    light_fighter?: number;
    heavy_fighter?: number;
    cruiser?: number;
    battleship?: number;
    colony_ship?: number;
    recycler?: number;
  };
}
```

#### Data Transformations
```javascript
// Group fleets by planet
const fleetsByPlanet = fleets.reduce((acc, fleet) => {
  const planetId = fleet.start_planet_id;
  if (!acc[planetId]) {
    acc[planetId] = [];
  }
  acc[planetId].push(fleet);
  return acc;
}, {});

// Filter user's planets
const userPlanets = planets.filter(planet => planet.user_id === user?.id);
```

### PlanetOverviewCard Component

#### Props Expected
```typescript
interface PlanetOverviewCardProps {
  planet: Planet;
  fleets: Fleet[];
  onCreateFleet: () => void;
}
```

#### Data Dependencies
```javascript
// Required planet properties
const requiredPlanetProps = [
  'metal', 'crystal', 'deuterium',  // Resources
  'small_cargo', 'large_cargo',     // Ship counts
  'light_fighter', 'heavy_fighter',
  'cruiser', 'battleship',
  'colony_ship', 'recycler'
];

// Required fleet properties
const requiredFleetProps = [
  'ships',  // Ship composition object
  'status'  // Fleet status
];
```

### ShipAvailabilityDashboard Component

#### Props Expected
```typescript
interface ShipAvailabilityDashboardProps {
  planet: Planet;
  fleets: Fleet[];
}
```

#### Calculations Performed
```javascript
// Calculate available ships
const availableShips = {
  small_cargo: planet.small_cargo || 0,
  large_cargo: planet.large_cargo || 0,
  // ... other ship types
};

// Subtract ships in active fleets
fleets.forEach(fleet => {
  if (fleet.status === 'traveling' || fleet.status === 'returning') {
    const ships = fleet.ships || {};
    Object.keys(availableShips).forEach(shipType => {
      availableShips[shipType] -= ships[shipType] || 0;
    });
  }
});
```

### FleetTile Component

#### Props Expected
```typescript
interface FleetTileProps {
  fleet: Fleet;
  planets: Planet[];
  onSend: (fleet: Fleet) => void;
  onRecall: (fleetId: number) => void;
  formatTimeRemaining: (time: string) => string;
}
```

#### Data Lookups
```javascript
// Find planet names
const startPlanet = planets.find(p => p.id === fleet.start_planet_id);
const targetPlanet = planets.find(p => p.id === fleet.target_planet_id);

const startPlanetName = startPlanet?.name || 'Unknown';
const targetPlanetName = targetPlanet?.name || 'N/A';
```

---

## State Management Patterns

### Local State Management

#### State Initialization
```javascript
const [fleets, setFleets] = useState([]);
const [selectedPlanet, setSelectedPlanet] = useState(null);
const [showCreateForm, setShowCreateForm] = useState(false);
const [showSendForm, setShowSendForm] = useState(false);
const [selectedFleet, setSelectedFleet] = useState(null);
const [loading, setLoading] = useState(true);
```

#### State Updates
```javascript
// Atomic state updates
setFleets(prev => [...prev, response.data.fleet]);
setSelectedPlanet(planet);
setShowCreateForm(true);
```

### Derived State

#### Computed Values
```javascript
// Group fleets by planet (computed on every render)
const fleetsByPlanet = fleets.reduce((acc, fleet) => {
  const planetId = fleet.start_planet_id;
  if (!acc[planetId]) {
    acc[planetId] = [];
  }
  acc[planetId].push(fleet);
  return acc;
}, {});

// Filter user's planets (computed on every render)
const userPlanets = planets.filter(planet => planet.user_id === user?.id);
```

#### Memoized Computations
```javascript
// For expensive computations, consider useMemo
const planetStats = useMemo(() => {
  return userPlanets.map(planet => ({
    ...planet,
    fleetCount: fleetsByPlanet[planet.id]?.length || 0,
    activeFleets: fleetsByPlanet[planet.id]?.filter(f =>
      f.status === 'traveling' || f.status === 'returning'
    ).length || 0
  }));
}, [userPlanets, fleetsByPlanet]);
```

### Side Effects

#### Data Fetching
```javascript
useEffect(() => {
  fetchFleets();
}, []); // Empty dependency array = run once on mount
```

#### Planet Selection Effects
```javascript
useEffect(() => {
  if (planets.length > 0 && !selectedPlanet) {
    setSelectedPlanet(planets[0]);
  }
}, [planets, selectedPlanet]);
```

---

## Event Chain Analysis

### Planet Selection Issues

#### Current Implementation
```javascript
// Planet selection buttons
{userPlanets.map(planet => (
  <button
    key={planet.id}
    onClick={() => setSelectedPlanet(planet)}
    className={`px-4 py-2 rounded whitespace-nowrap ${
      selectedPlanet?.id === planet.id
        ? 'bg-blue-600 text-white'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
    }`}
  >
    {planet.is_home_planet ? '🏠' : '🌍'} {planet.name} ({planet.x}:{planet.y}:{planet.z})
  </button>
))}
```

#### Potential Issues
1. **userPlanets is empty**: No planets returned from API or filtering failed
2. **Planet objects malformed**: Missing required properties (id, name, etc.)
3. **State update not triggering re-render**: React not detecting state change
4. **Event handler not bound**: onClick not properly attached

### Create Fleet Modal Issues

#### Current Implementation
```javascript
<CreateFleetModal
  planets={userPlanets}
  selectedPlanet={selectedPlanet}
  onCreate={handleCreateFleet}
  onClose={() => setShowCreateForm(false)}
/>
```

#### Modal Component
```javascript
function CreateFleetModal({ planets, onCreate, onClose }) {
  const [formData, setFormData] = useState({
    start_planet_id: '',
    ships: { /* ... */ }
  });

  // Planet dropdown
  <select
    value={formData.start_planet_id}
    onChange={(e) => setFormData(prev => ({ ...prev, start_planet_id: e.target.value }))}
  >
    <option value="">Select a planet</option>
    {planets.map(planet => (
      <option key={planet.id} value={planet.id}>
        {planet.name} ({planet.coordinates})
      </option>
    ))}
  </select>
}
```

#### Potential Issues
1. **planets prop is empty**: userPlanets not passed correctly
2. **Planet missing coordinates**: planet.coordinates property undefined
3. **Form data not updating**: onChange handler not working
4. **Modal not receiving props**: Component props not passed correctly

---

## Debugging Guide

### Step-by-Step Debugging Process

#### Step 1: Verify Data Flow
```javascript
// Add logging in FleetManagement component
console.log('=== FleetManagement Debug ===');
console.log('Props received:', { user, planets });
console.log('State:', { fleets, selectedPlanet, loading });
console.log('Computed values:', { userPlanets, fleetsByPlanet });
```

#### Step 2: Check Planet Selection
```javascript
// Add logging to planet selection
const handlePlanetSelect = (planet) => {
  console.log('Planet selection triggered:', planet);
  console.log('Previous selectedPlanet:', selectedPlanet);
  setSelectedPlanet(planet);
  console.log('New selectedPlanet set:', planet);
};

// Use in JSX
<button onClick={() => handlePlanetSelect(planet)}>
```

#### Step 3: Verify Component Re-renders
```javascript
// Add useEffect to track re-renders
useEffect(() => {
  console.log('FleetManagement re-rendered with selectedPlanet:', selectedPlanet);
}, [selectedPlanet]);
```

#### Step 4: Check Modal Props
```javascript
// Add logging in CreateFleetModal
function CreateFleetModal({ planets, selectedPlanet, onCreate, onClose }) {
  console.log('=== CreateFleetModal Debug ===');
  console.log('Props received:', { planets, selectedPlanet, onCreate, onClose });

  // Log planets array details
  console.log('Planets array:', planets?.map(p => ({
    id: p.id,
    name: p.name,
    coordinates: p.coordinates
  })));
}
```

### Common Issues and Solutions

#### Issue: Planet Selection Not Working
```javascript
// Solution: Add defensive checks
const handlePlanetSelect = (planet) => {
  if (!planet || !planet.id) {
    console.error('Invalid planet object:', planet);
    return;
  }
  setSelectedPlanet(planet);
};
```

#### Issue: Create Fleet Dropdown Empty
```javascript
// Solution: Add fallback for missing coordinates
{planets.map(planet => (
  <option key={planet.id} value={planet.id}>
    {planet.name} ({planet.coordinates || `${planet.x}:${planet.y}:${planet.z}`})
  </option>
))}
```

#### Issue: Component Not Re-rendering
```javascript
// Solution: Ensure state updates trigger re-renders
setSelectedPlanet(prev => {
  if (prev?.id === planet.id) return prev; // No change needed
  return planet; // Trigger re-render
});
```

---

## Testing Strategies

### Unit Testing

#### Component Testing
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import FleetManagement from './FleetManagement';

const mockProps = {
  user: { id: 1, username: 'testuser' },
  planets: [
    {
      id: 1,
      name: 'Test Planet',
      x: 100,
      y: 200,
      z: 300,
      user_id: 1,
      is_home_planet: true
    }
  ]
};

test('renders planet selection buttons', () => {
  render(<FleetManagement {...mockProps} />);
  expect(screen.getByText('🏠 Test Planet (100:200:300)')).toBeInTheDocument();
});

test('planet selection updates state', () => {
  render(<FleetManagement {...mockProps} />);
  const planetButton = screen.getByText('🏠 Test Planet (100:200:300)');
  fireEvent.click(planetButton);
  // Verify selectedPlanet state updated
});
```

#### Event Handler Testing
```javascript
test('create fleet button opens modal', () => {
  render(<FleetManagement {...mockProps} />);
  const createButton = screen.getByText('Create Fleet');
  fireEvent.click(createButton);
  expect(screen.getByText('Create New Fleet')).toBeInTheDocument();
});
```

### Integration Testing

#### API Integration Testing
```javascript
import axios from 'axios';
jest.mock('axios');

test('fetches fleets on mount', async () => {
  const mockFleets = [{ id: 1, mission: 'stationed' }];
  axios.get.mockResolvedValue({ data: mockFleets });

  render(<FleetManagement {...mockProps} />);
  await waitFor(() => {
    expect(axios.get).toHaveBeenCalledWith('/api/fleet');
  });
});
```

#### Form Submission Testing
```javascript
test('create fleet form submission', async () => {
  axios.post.mockResolvedValue({ data: { fleet: { id: 2 } } });

  render(<FleetManagement {...mockProps} />);

  // Open modal
  fireEvent.click(screen.getByText('Create Fleet'));

  // Fill form
  fireEvent.change(screen.getByLabelText('Starting Planet'), {
    target: { value: '1' }
  });

  // Submit form
  fireEvent.click(screen.getByText('Create Fleet'));

  await waitFor(() => {
    expect(axios.post).toHaveBeenCalledWith('/api/fleet', expect.any(Object));
  });
});
```

### End-to-End Testing

#### Playwright Test Example
```javascript
import { test, expect } from '@playwright/test';

test('fleet management planet selection', async ({ page }) => {
  await page.goto('/dashboard');

  // Navigate to fleet tab
  await page.click('text=Fleets');

  // Check planet selection buttons exist
  await expect(page.locator('text=🏠')).toBeVisible();

  // Click planet selection
  await page.click('text=🏠 Test Planet');

  // Verify planet overview appears
  await expect(page.locator('text=Planet Overview')).toBeVisible();

  // Test create fleet functionality
  await page.click('text=Create Fleet');
  await expect(page.locator('text=Create New Fleet')).toBeVisible();

  // Select planet in dropdown
  await page.selectOption('select[name="start_planet_id"]', '1');

  // Submit form
  await page.click('text=Create Fleet');

  // Verify success message
  await expect(page.locator('text=Fleet created successfully')).toBeVisible();
});
```

---

## Performance Considerations

### Optimization Strategies

#### Memoization
```javascript
// Memoize expensive computations
const planetStats = useMemo(() => {
  return userPlanets.map(planet => calculatePlanetStats(planet));
}, [userPlanets]);
```

#### Debounced Updates
```javascript
// Debounce rapid state updates
const debouncedUpdate = useCallback(
  debounce((newFleets) => setFleets(newFleets), 300),
  []
);
```

#### Virtual Scrolling
```javascript
// For large fleet lists, implement virtual scrolling
// Only render visible fleet tiles
const VirtualizedFleetList = ({ fleets }) => {
  // Implementation using react-window or similar
};
```

### Memory Management

#### Cleanup Event Listeners
```javascript
useEffect(() => {
  const interval = setInterval(fetchFleets, 10000);
  return () => clearInterval(interval); // Cleanup on unmount
}, []);
```

#### State Cleanup
```javascript
// Clear modal state when closing
const handleCloseModal = () => {
  setShowCreateForm(false);
  setSelectedFleet(null);
  setFormData(initialFormData);
};
```

### Network Optimization

#### Request Deduplication
```javascript
// Prevent duplicate API calls
const [fetching, setFetching] = useState(false);

const fetchFleets = async () => {
  if (fetching) return; // Prevent duplicate requests

  setFetching(true);
  try {
    const response = await axios.get('/api/fleet');
    setFleets(response.data);
  } finally {
    setFetching(false);
  }
};
```

#### Response Caching
```javascript
// Cache planet data
const [planetCache, setPlanetCache] = useState(new Map());

const getCachedPlanets = async () => {
  const cacheKey = 'planets';
  const cached = planetCache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < 30000) { // 30s cache
    return cached.data;
  }

  const response = await axios.get('/api/planets');
  setPlanetCache(prev => new Map(prev).set(cacheKey, {
    data: response.data,
    timestamp: Date.now()
  }));

  return response.data;
};
```

---

## Error Handling Strategies

### Graceful Degradation

#### Fallback UI States
```javascript
// Show fallback when no planets available
if (userPlanets.length === 0) {
  return (
    <div className="text-center text-gray-400 py-8">
      No planets available. Please create a planet first.
    </div>
  );
}
```

#### Partial Data Handling
```javascript
// Handle missing planet properties
const planetName = planet?.name || 'Unknown Planet';
const coordinates = planet?.coordinates || `${planet?.x || 0}:${planet?.y || 0}:${planet?.z || 0}`;
```

### Error Boundaries

#### Component-Level Error Handling
```javascript
class FleetManagementErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('FleetManagement error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-center text-red-400 py-8">
          Something went wrong with the Fleet Management tab.
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling

#### Retry Logic
```javascript
const fetchFleetsWithRetry = async (retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios.get('/api/fleet');
      return response.data;
    } catch (error) {
      if (i === retries - 1) throw error; // Last attempt failed
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // Exponential backoff
    }
  }
};
```

#### User-Friendly Error Messages
```javascript
const getErrorMessage = (error) => {
  if (error.response?.status === 401) {
    return 'Session expired. Please log in again.';
  }
  if (error.response?.status === 403) {
    return 'You do not have permission to perform this action.';
  }
  if (error.response?.status === 500) {
    return 'Server error. Please try again later.';
  }
  return error.response?.data?.error || 'An unexpected error occurred.';
};
```

---

## Conclusion

This specification provides a comprehensive guide to the Fleet Management tab's event mechanics, data flow, and debugging strategies. The document covers:

- Complete event flow diagrams
- Component data contracts and prop structures
- State management patterns and best practices
- Debugging checklists for common issues
- Testing strategies for different levels
- Performance optimization techniques
- Error handling and recovery strategies

Use this document as a reference for maintaining, debugging, and extending the Fleet Management functionality.
