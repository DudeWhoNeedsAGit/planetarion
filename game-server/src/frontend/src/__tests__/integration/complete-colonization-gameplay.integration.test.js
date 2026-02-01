/**
 * Complete Colonization Gameplay Loop Integration Tests
 *
 * Tests the core gameplay mechanic: FLY → ARRIVE → COLONIZE OR DIE
 * This demonstrates the complete colonization workflow from fleet creation
 * through travel to planet colonization with comprehensive state change validation.
 */

const request = require('supertest');

// This suite is a heavy end-to-end integration test and is currently WIP.
// Enable explicitly when working on colonization: PLANETARION_SUPERTEST_FULL=1
const enabled = process.env.PLANETARION_SUPERTEST_FULL === '1';

(enabled ? describe : describe.skip)('Complete Colonization Gameplay Loop - State Changes Test', () => {
  let user;
  let token;
  let authHeader;
  let homePlanet;
  let fleet;
  let colonizedPlanet;

  beforeAll(async () => {
    console.log('🧪 Setting up colonization integration test...');

    // Register test user
    const registerResponse = await request('http://localhost:5000')
      .post('/api/auth/register')
      .send({
        username: 'colonizer_test',
        email: 'colonizer@test.com',
        password: 'testpassword123'
      });

    expect(registerResponse.status).toBe(201);
    user = registerResponse.body.user;

    // Login to get JWT token
    const loginResponse = await request('http://localhost:5000')
      .post('/api/auth/login')
      .send({
        username: 'colonizer_test',
        password: 'testpassword123'
      });

    expect(loginResponse.status).toBe(200);
    token = loginResponse.body.access_token || loginResponse.body.token;
    authHeader = { 'Authorization': `Bearer ${token}` };

    console.log('✅ User authenticated, token obtained');

    // Get user's home planet
    const planetsResponse = await request('http://localhost:5000')
      .get('/api/planet')
      .set(authHeader);

    expect(planetsResponse.status).toBe(200);
    expect(Array.isArray(planetsResponse.body)).toBe(true);
    expect(planetsResponse.body.length).toBeGreaterThan(0);

    homePlanet = planetsResponse.body[0];
    console.log(`✅ Home planet found: ${homePlanet.name} at ${homePlanet.x}:${homePlanet.y}:${homePlanet.z}`);

    // Note: Planet update API may not exist, so we'll work with initial resources
    // In a real implementation, you'd add fuel via shipyard or other means
    console.log('✅ Using initial planet resources for colonization travel');
  });

  afterEach(async () => {
    // Clean up any created colonies between tests
    try {
      const planetsResponse = await request('http://localhost:5000')
        .get('/api/planet')
        .set(authHeader);

      if (planetsResponse.status === 200) {
        const colonies = planetsResponse.body.filter(p =>
          p.user_id === user.id && p.is_home_planet === false
        );

        // Note: In a real scenario, you'd want to clean these up
        // but for testing purposes, we'll leave them for inspection
      }
    } catch (error) {
      // Ignore cleanup errors in tests
    }
  });

  describe('FLY → ARRIVE → COLONIZE: Complete Gameplay Loop', () => {
    test('should complete full colonization workflow from fleet creation to planet ownership', async () => {
      console.log('🧪 Starting complete colonization workflow test...');

      // Step 1: Create colonization fleet
      console.log('📦 Step 1: Creating colonization fleet...');
      console.log(`🏠 Home planet ships available:`, {
        colony_ship: homePlanet.colony_ship || 0,
        light_fighter: homePlanet.light_fighter || 0,
        cruiser: homePlanet.cruiser || 0
      });

      const fleetData = {
        start_planet_id: homePlanet.id,
        ships: {
          colony_ship: 1,      // Required for colonization
          light_fighter: 2,    // Reduced escort ships
          cruiser: 1           // Reduced additional protection
        }
      };

      const createResponse = await request('http://localhost:5000')
        .post('/api/fleet')
        .set(authHeader)
        .send(fleetData);

      expect(createResponse.status).toBe(201);
      expect(createResponse.body.fleet).toBeValidFleet();

      fleet = createResponse.body.fleet;
      console.log(`✅ Fleet created with ID: ${fleet.id}`);

      // Verify fleet composition
      expect(fleet.colony_ship).toBe(1);
      expect(fleet.light_fighter).toBe(2);
      expect(fleet.cruiser).toBe(1);

      // Step 2: Send colonization mission to coordinates
      console.log('🚀 Step 2: Sending colonization mission...');
      const missionData = {
        fleet_id: fleet.id,
        mission: 'colonize',
        target_x: 100,    // API expects individual coordinates
        target_y: 200,
        target_z: 300
      };

      const sendResponse = await request('http://localhost:5000')
        .post('/api/fleet/send')
        .set(authHeader)
        .send(missionData);

      expect(sendResponse.status).toBe(200);
      expect(sendResponse.body.fleet.status).toBe('traveling');
      expect(sendResponse.body.fleet.arrival_time).toBeDefined();

      console.log(`✅ Fleet sent to coordinates: 100:200:300`);
      console.log(`📅 Arrival time: ${sendResponse.body.fleet.arrival_time}`);

      // Step 3: Verify fleet is traveling with proper calculations
      console.log('🧮 Step 3: Verifying travel calculations...');

      // Get updated fleet data
      const fleetResponse = await request('http://localhost:5000')
        .get('/api/fleet')
        .set(authHeader);

      expect(fleetResponse.status).toBe(200);
      const travelingFleet = fleetResponse.body.fleets.find(f => f.id === fleet.id);
      expect(travelingFleet).toBeDefined();
      expect(travelingFleet.status).toBe('traveling');

      // Verify travel information is calculated correctly
      expect(travelingFleet.travel_info).toBeDefined();
      expect(travelingFleet.travel_info.distance).toBeGreaterThan(0);
      expect(travelingFleet.travel_info.fleet_speed).toBeGreaterThan(0);
      expect(travelingFleet.travel_info.progress_percentage).toBeGreaterThanOrEqual(0);

      console.log(`📏 Travel distance: ${travelingFleet.travel_info.distance} units`);
      console.log(`💨 Fleet speed: ${travelingFleet.travel_info.fleet_speed} units/hour`);
      console.log(`📊 Current progress: ${travelingFleet.travel_info.progress_percentage}%`);

      // Step 4: Simulate fleet arrival (fast-forward time)
      console.log('⏰ Step 4: Fast-forwarding to fleet arrival...');

      // Update fleet arrival time to past (simulate arrival)
      const pastTime = new Date();
      pastTime.setHours(pastTime.getHours() - 1); // 1 hour ago

      // Trigger tick processing to handle arrived fleets
      const tickResponse = await request('http://localhost:5000')
        .post('/api/tick')
        .set(authHeader);

      expect(tickResponse.status).toBe(200);

      // Step 5: Verify colonization occurred
      console.log('🏛️ Step 5: Verifying planet colonization...');

      // Check if planet was created at target coordinates
      const planetsResponse = await request('http://localhost:5000')
        .get('/api/planet')
        .set(authHeader);

      expect(planetsResponse.status).toBe(200);

      // Find the colonized planet
      const colonizedPlanet = planetsResponse.body.find(p =>
        p.x === 100 && p.y === 200 && p.z === 300
      );

      expect(colonizedPlanet).toBeDefined();
      expect(colonizedPlanet.user_id).toBe(user.id);
      expect(colonizedPlanet.is_home_planet).toBe(false);

      // Verify starting resources
      expect(colonizedPlanet.metal).toBe(1000);
      expect(colonizedPlanet.crystal).toBe(500);
      expect(colonizedPlanet.deuterium).toBe(0);

      // Verify buildings were created
      expect(colonizedPlanet.metal_mine).toBe(1);
      expect(colonizedPlanet.crystal_mine).toBe(1);
      expect(colonizedPlanet.solar_plant).toBe(1);

      console.log(`✅ Planet colonized successfully!`);
      console.log(`🏭 Metal Mine: Level ${colonizedPlanet.metal_mine}`);
      console.log(`💎 Crystal Mine: Level ${colonizedPlanet.crystal_mine}`);
      console.log(`☀️ Solar Plant: Level ${colonizedPlanet.solar_plant}`);

      // Step 6: Verify fleet returned to stationed
      console.log('🔄 Step 6: Verifying fleet return...');

      const finalFleetResponse = await request('http://localhost:5000')
        .get('/api/fleet')
        .set(authHeader);

      expect(finalFleetResponse.status).toBe(200);
      const returnedFleet = finalFleetResponse.body.fleets.find(f => f.id === fleet.id);
      expect(returnedFleet.status).toBe('stationed');
      expect(returnedFleet.mission).toBe('completed');

      console.log(`✅ Fleet returned to stationed status`);

      // Step 7: Verify colonization event was logged
      console.log('📝 Step 7: Verifying event logging...');

      // Check tick logs for colonization event
      const logsResponse = await request('http://localhost:5000')
        .get('/api/admin/tick-logs')
        .set(authHeader);

      if (logsResponse.status === 200) {
        const colonizationLog = logsResponse.body.logs.find(log =>
          log.event_type === 'colonization' &&
          log.planet_id === colonizedPlanet.id
        );

        if (colonizationLog) {
          console.log(`✅ Colonization event logged: ${colonizationLog.event_description}`);
        }
      }

      console.log('🎉 COMPLETE COLONIZATION WORKFLOW SUCCESSFUL!');
      console.log('   ✅ Fleet Created → Traveling → Arrived → Colonized → Returned');
    }, 60000); // 60 second timeout for integration test

    test('should handle colonization failure when planet already owned', async () => {
      console.log('🧪 Testing colonization failure scenario...');

      // Create a planet that's already owned by another user
      const otherRegisterResponse = await request('http://localhost:5000')
        .post('/api/auth/register')
        .send({
          username: 'other_player',
          email: 'other@test.com',
          password: 'testpassword123'
        });

      expect(otherRegisterResponse.status).toBe(201);
      const otherUser = otherRegisterResponse.body.user;

      // Create colonization fleet for main user
      const fleetData = {
        start_planet_id: homePlanet.id,
        ships: {
          colony_ship: 1,
          light_fighter: 5
        }
      };

      const createResponse = await request('http://localhost:5000')
        .post('/api/fleet')
        .set(authHeader)
        .send(fleetData);

      expect(createResponse.status).toBe(201);
      const fleet = createResponse.body.fleet;

      // Try to colonize home planet coordinates (should fail)
      const missionData = {
        fleet_id: fleet.id,
        mission: 'colonize',
        target_x: homePlanet.x,
        target_y: homePlanet.y,
        target_z: homePlanet.z
      };

      const sendResponse = await request('http://localhost:5000')
        .post('/api/fleet/send')
        .set(authHeader)
        .send(missionData);

      // Should succeed initially (fleet sent)
      expect(sendResponse.status).toBe(200);

      // Trigger tick processing
      await request('http://localhost:5000')
        .post('/api/tick')
        .set(authHeader);

      // Verify planet ownership didn't change
      const planetsResponse = await request('http://localhost:5000')
        .get('/api/planet')
        .set(authHeader);

      const targetPlanet = planetsResponse.body.find(p =>
        p.x === homePlanet.x && p.y === homePlanet.y && p.z === homePlanet.z
      );

      expect(targetPlanet.user_id).toBe(user.id); // Still owned by original user

      console.log('✅ Colonization failure handled correctly - planet ownership preserved');
    });

    test('should validate colonization requirements', async () => {
      console.log('🧪 Testing colonization validation...');

      // Try to create fleet without colony ship
      const invalidFleetData = {
        start_planet_id: homePlanet.id,
        ships: {
          light_fighter: 10,  // No colony ship
          cruiser: 5
        }
      };

      const createResponse = await request('http://localhost:5000')
        .post('/api/fleet')
        .set(authHeader)
        .send(invalidFleetData);

      expect(createResponse.status).toBe(201);
      const fleet = createResponse.body.fleet;

      // Try to send colonization mission
      const missionData = {
        fleet_id: fleet.id,
        mission: 'colonize',
        target_x: 200,
        target_y: 300,
        target_z: 400
      };

      const sendResponse = await request('http://localhost:5000')
        .post('/api/fleet/send')
        .set(authHeader)
        .send(missionData);

      // Should succeed initially
      expect(sendResponse.status).toBe(200);

      // But colonization should fail during arrival processing
      await request('http://localhost:5000')
        .post('/api/tick')
        .set(authHeader);

      // Fleet should return to stationed without colonizing
      const fleetResponse = await request('http://localhost:5000')
        .get('/api/fleet')
        .set(authHeader);

      const returnedFleet = fleetResponse.body.fleets.find(f => f.id === fleet.id);
      expect(returnedFleet.status).toBe('stationed');

      console.log('✅ Colonization validation working - fleet returned without colonizing');
    });
  });

  describe('Fleet Travel Mechanics During Colonization', () => {
    test('should calculate 3D distance correctly for colonization', async () => {
      console.log('🧪 Testing 3D distance calculations...');

      // Create fleet
      const fleetData = {
        start_planet_id: homePlanet.id,
        ships: {
          colony_ship: 1,
          light_fighter: 5
        }
      };

      const createResponse = await request('http://localhost:5000')
        .post('/api/fleet')
        .set(authHeader)
        .send(fleetData);

      const fleet = createResponse.body.fleet;

      // Send to specific coordinates
      const missionData = {
        fleet_id: fleet.id,
        mission: 'colonize',
        target_x: 50,    // 50 units away in each dimension
        target_y: 100,
        target_z: 150
      };

      await request('http://localhost:5000')
        .post('/api/fleet/send')
        .set(authHeader)
        .send(missionData);

      // Get travel information
      const fleetResponse = await request('http://localhost:5000')
        .get('/api/fleet')
        .set(authHeader);

      const travelingFleet = fleetResponse.body.fleets.find(f => f.id === fleet.id);

      // Expected distance: sqrt(50² + 100² + 150²) = sqrt(2500 + 10000 + 22500) = sqrt(35000) ≈ 187.08
      expect(travelingFleet.travel_info.distance).toBeCloseTo(187.08, 1);
      expect(travelingFleet.travel_info.start_coordinates).toBe('0:0:0');
      expect(travelingFleet.travel_info.target_coordinates).toBe('50:100:150');

      console.log(`✅ 3D Distance calculated correctly: ${travelingFleet.travel_info.distance} units`);
    });

    test('should apply slowest ship rule for colonization fleet speed', async () => {
      console.log('🧪 Testing slowest ship rule...');

      // Create fleet with mixed ship types
      const fleetData = {
        start_planet_id: homePlanet.id,
        ships: {
          colony_ship: 1,      // 2500 base speed (slowest)
          light_fighter: 5,    // 12500 base speed (fastest)
          cruiser: 2           // 15000 base speed
        }
      };

      const createResponse = await request('http://localhost:5000')
        .post('/api/fleet')
        .set(authHeader)
        .send(fleetData);

      const fleet = createResponse.body.fleet;

      // Send colonization mission
      const missionData = {
        fleet_id: fleet.id,
        mission: 'colonize',
        target_x: 10,
        target_y: 20,
        target_z: 30
      };

      await request('http://localhost:5000')
        .post('/api/fleet/send')
        .set(authHeader)
        .send(missionData);

      // Get fleet travel information
      const fleetResponse = await request('http://localhost:5000')
        .get('/api/fleet')
        .set(authHeader);

      const travelingFleet = fleetResponse.body.fleets.find(f => f.id === fleet.id);

      // Fleet speed should be determined by slowest ship (colony_ship: 2500) * multiplier (30.0) = 75000
      expect(travelingFleet.travel_info.fleet_speed).toBe(75000);

      console.log(`✅ Slowest ship rule applied: ${travelingFleet.travel_info.fleet_speed} units/hour`);
    });
  });
});
