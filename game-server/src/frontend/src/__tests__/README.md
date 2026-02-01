# JavaScript Integration Tests

This directory contains **JavaScript integration tests** that test the frontend against the real backend API using Supertest. These tests provide maximum realism by testing against the actual backend implementation without mocks.

## Overview

Unlike Playwright (which tests the full browser experience), these tests focus on:
- ✅ **API Integration**: Real HTTP requests to backend endpoints
- ✅ **Authentication Flow**: JWT token handling and validation
- ✅ **Data Flow**: Request → Backend Processing → Database → Response
- ✅ **Business Logic**: Fleet operations, colonization workflows
- ✅ **Error Handling**: Real error responses and edge cases

## Test Structure

```
src/__tests__/
├── integration/           # Integration tests (Supertest)
│   ├── colonization.integration.test.js
│   └── fleet.integration.test.js
├── utils/                 # Test utilities and helpers
│   └── testUtils.js
└── README.md             # This file
```

## Prerequisites

1. **Backend Running**: The backend must be running and accessible
2. **Database**: Test database must be available
3. **Dependencies**: Install test dependencies

```bash
cd game-server/src/frontend
npm install
```

## Running Tests

### Run All Integration Tests
```bash
npm run test:integration
```

### Run Specific Test Suites
```bash
# Colonization tests only
npm run test:colonization

# Fleet tests only
npm run test:fleet
```

### Run with Coverage
```bash
npm run test:integration -- --coverage
```

### Run in Watch Mode
```bash
npm run test:integration -- --watchAll=false
```

### Run Single Test File
```bash
npx jest src/__tests__/integration/colonization.integration.test.js --watchAll=false
```

## Test Categories

### 1. Colonization Integration Tests

**File**: `colonization.integration.test.js`

Tests the complete colonization workflow:
- ✅ Fleet creation with colony ships
- ✅ Colonization mission sending
- ✅ Fleet arrival and colony creation
- ✅ Resource initialization
- ✅ Event logging
- ✅ Multiple simultaneous colonizations
- ✅ Validation and error handling

**Key Test Scenarios**:
```javascript
// Complete colonization workflow
test('should complete full colonization workflow', async () => {
  // 1. Create colonization fleet
  // 2. Send to unowned coordinates
  // 3. Wait for arrival
  // 4. Verify colony creation
  // 5. Check event logging
});

// Validation tests
test('should reject colonization without colony ship', async () => {
  // Test error handling
});
```

### 2. Fleet Operations Integration Tests

**File**: `fleet.integration.test.js`

Tests all fleet-related operations:
- ✅ Fleet CRUD operations
- ✅ Mission types (transport, deploy, attack)
- ✅ Fleet recall functionality
- ✅ Travel mechanics and timing
- ✅ Authentication and authorization
- ✅ Resource management

**Key Test Scenarios**:
```javascript
// Fleet lifecycle
test('should create and manage fleet lifecycle', async () => {
  // Create → Send → Travel → Arrive → Complete
});

// Mission validation
test('should validate mission requirements', async () => {
  // Check fuel, ships, targets, etc.
});
```

## Test Utilities

### AuthHelper Class
Handles user registration and authentication:

```javascript
const authHelper = new AuthHelper(app);

// Register and login user
const { user, token, authHeader } = await authHelper.registerAndLogin({
  username: 'testuser',
  email: 'test@example.com'
});

// Use in API calls
const response = await request(app)
  .get('/api/fleet')
  .set(authHeader);
```

### DatabaseHelper Class
Manages test data creation and cleanup:

```javascript
const dbHelper = new DatabaseHelper(app);

// Create test planet
const planet = await dbHelper.createTestPlanet(userId, {
  name: 'Test Colony',
  x: 100, y: 200, z: 300
});

// Create test fleet
const fleet = await dbHelper.createTestFleet(userId, planetId, {
  small_cargo: 10,
  colony_ship: 1
});
```

### FleetHelper Class
Specialized fleet operations:

```javascript
const fleetHelper = new FleetHelper(app, authHelper, dbHelper);

// Create colonization-ready fleet
const fleet = await fleetHelper.createColonizationFleet(user, planet);

// Send colonization mission
await fleetHelper.sendColonizationMission(fleet.id, coords, authHeader);

// Wait for arrival
const arrivedFleet = await fleetHelper.waitForFleetArrival(fleetId, authHeader);
```

## Test Data Management

### Automatic Cleanup
Tests automatically clean up created data:

```javascript
afterAll(async () => {
  await cleanupTestData(app, testUser.id, authHeader);
});
```

### Test Isolation
Each test suite runs with:
- ✅ Fresh user accounts
- ✅ Isolated planets and fleets
- ✅ Clean database state
- ✅ Independent authentication

## Configuration

### Environment Variables
```bash
# Backend URL (if different from localhost:5000)
REACT_APP_API_URL=http://localhost:5000

# Test database
TEST_DATABASE_URL=sqlite:///test.db

# JWT settings
JWT_SECRET_KEY=test_secret_key
```

### Jest Configuration
Tests use default Jest configuration with:
- ✅ ES6 modules support
- ✅ Async/await support
- ✅ 30-second timeout for integration tests
- ✅ Automatic test discovery

## Best Practices

### Test Organization
```javascript
describe('Feature Name', () => {
  describe('Sub-feature', () => {
    beforeAll(async () => {
      // Setup test data
    });

    afterAll(async () => {
      // Cleanup
    });

    test('should do something', async () => {
      // Test implementation
    });
  });
});
```

### Error Handling
```javascript
// Test error responses
test('should handle API errors gracefully', async () => {
  const response = await request(app)
    .post('/api/fleet/send')
    .send({ invalid: 'data' });

  expect(response.status).toBe(400);
  expect(response.body.error).toBeDefined();
});
```

### Authentication Testing
```javascript
// Test protected endpoints
test('should require authentication', async () => {
  const response = await request(app)
    .get('/api/fleet'); // No auth header

  expect(response.status).toBe(401);
});
```

## Debugging Tests

### Console Logging
Tests include debug logging for troubleshooting:

```javascript
console.log('DEBUG: Fleet created:', fleet);
console.log('DEBUG: API response:', response.body);
```

### Test Isolation
Each test runs independently with:
- ✅ Unique user accounts
- ✅ Fresh database state
- ✅ Isolated API calls

### Performance Monitoring
Tests include timing for performance validation:

```javascript
const startTime = Date.now();
// ... test operations ...
const duration = Date.now() - startTime;
expect(duration).toBeLessThan(5000); // 5 second limit
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run JavaScript Integration Tests
  run: |
    cd game-server/src/frontend
    npm run test:integration -- --coverage
    npm run test:ci
```

### Docker Integration
```yaml
- name: Run Integration Tests
  run: |
    docker-compose up -d backend db
    cd game-server/src/frontend
    npm run test:integration
```

## Troubleshooting

### Common Issues

#### Backend Not Running
```
Error: connect ECONNREFUSED 127.0.0.1:5000
```
**Solution**: Start the backend server first
```bash
cd game-server
make backend
```

#### Database Connection Issues
```
Error: SQLITE_CANTOPEN: unable to open database file
```
**Solution**: Ensure test database exists
```bash
cd game-server
make db-init
```

#### Authentication Failures
```
Error: 401 Unauthorized
```
**Solution**: Check JWT token validity
```javascript
console.log('Token:', token);
console.log('Auth header:', authHeader);
```

#### Timeout Issues
```
Error: Timeout of 30000ms exceeded
```
**Solution**: Increase timeout for complex operations
```javascript
test('long running test', async () => {
  // ... test code ...
}, 60000); // 60 second timeout
```

## Performance Benchmarks

### Test Execution Times
- **Simple API calls**: 100-500ms
- **Fleet operations**: 500-2000ms
- **Colonization workflow**: 3000-8000ms
- **Multiple fleets**: 5000-15000ms

### Resource Usage
- **Memory**: 50-100MB per test suite
- **CPU**: Minimal (single-threaded)
- **Network**: Local API calls only
- **Database**: Lightweight SQLite operations

## Comparison with Playwright

| Aspect | Supertest Integration | Playwright E2E |
|--------|----------------------|----------------|
| **Speed** | ⚡ Fast (seconds) | 🐌 Slow (minutes) |
| **Scope** | API + Business Logic | Full UI + API |
| **Setup** | Simple (no browser) | Complex (browser setup) |
| **Reliability** | 🔒 High (no UI flakiness) | 🎲 Medium (UI timing issues) |
| **Debugging** | 🐛 Easy (console logs) | 🔍 Complex (browser dev tools) |
| **Realism** | 🎯 High (real backend) | 🎯 High (real user experience) |
| **CI Performance** | 🚀 Excellent | ⚠️ Resource intensive |
| **Best For** | API testing, business logic | User workflows, UI testing |

## Contributing

### Adding New Tests
1. Create test file in `src/__tests__/integration/`
2. Use existing utilities from `testUtils.js`
3. Follow naming convention: `*.integration.test.js`
4. Add appropriate cleanup in `afterAll`
5. Update this README if needed

### Test Naming Convention
```javascript
// Good: Descriptive and specific
test('should create colonization fleet with proper composition', async () => { ... });

// Bad: Vague and generic
test('should work', async () => { ... });
```

### Code Coverage
Aim for high coverage of:
- ✅ API endpoints
- ✅ Business logic
- ✅ Error conditions
- ✅ Edge cases
- ✅ Authentication flows

This testing setup provides **fast, reliable, and realistic integration tests** that validate the complete JavaScript ↔ Backend interaction without the overhead of full browser automation.
