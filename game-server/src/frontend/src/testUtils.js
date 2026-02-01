// Legacy helper module (moved out of __tests__ so Jest doesn't treat it as a test file).
// Some older WIP integration tests import this file.

const request = require('supertest');

// Test data factories
export const createTestUser = (overrides = {}) => ({
  username: `testuser_${Date.now()}`,
  email: `test${Date.now()}@example.com`,
  password: 'testpassword123',
  ...overrides
});

export const createTestPlanet = (userId, overrides = {}) => ({
  name: `Test Planet ${Date.now()}`,
  x: Math.floor(Math.random() * 1000),
  y: Math.floor(Math.random() * 1000),
  z: Math.floor(Math.random() * 1000),
  user_id: userId,
  metal: 1000,
  crystal: 500,
  deuterium: 0,
  ...overrides
});

export const createTestFleet = (userId, planetId, overrides = {}) => ({
  user_id: userId,
  start_planet_id: planetId,
  target_planet_id: planetId,
  mission: 'stationed',
  status: 'stationed',
  departure_time: new Date().toISOString(),
  arrival_time: new Date().toISOString(),
  small_cargo: 10,
  large_cargo: 5,
  light_fighter: 20,
  heavy_fighter: 10,
  cruiser: 5,
  battleship: 2,
  colony_ship: 1,
  recycler: 0,
  ...overrides
});

// Authentication helpers
export class AuthHelper {
  constructor(app) {
    this.app = app;
    this.tokens = new Map();
  }

  async registerAndLogin(userData = {}) {
    const user = createTestUser(userData);

    // Register user
    const registerResponse = await request(this.app)
      .post('/api/auth/register')
      .send(user);

    if (registerResponse.status !== 201) {
      throw new Error(`Registration failed: ${registerResponse.status} - ${JSON.stringify(registerResponse.body)}`);
    }

    // Login to get token
    const loginResponse = await request(this.app)
      .post('/api/auth/login')
      .send({
        username: user.username,
        password: user.password
      });

    if (loginResponse.status !== 200) {
      throw new Error(`Login failed: ${loginResponse.status} - ${JSON.stringify(loginResponse.body)}`);
    }

    const token = loginResponse.body.access_token || loginResponse.body.token;
    this.tokens.set(user.username, token);

    return {
      user,
      token,
      authHeader: { Authorization: `Bearer ${token}` }
    };
  }

  getAuthHeader(username) {
    const token = this.tokens.get(username);
    if (!token) {
      throw new Error(`No token found for user: ${username}`);
    }
    return { Authorization: `Bearer ${token}` };
  }
}

