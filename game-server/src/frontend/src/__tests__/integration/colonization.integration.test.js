// JS Integration (Supertest) against the running Python backend.
// Run via: make supertest

const request = require('supertest');

const enabled = process.env.PLANETARION_SUPERTEST === '1';
const api = request('http://localhost:5000');

async function resetTwoPlayerScenario() {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const res = await api
    .post('/api/admin/scenarios/two-player/reset')
    .set('X-Planetarion-Dev-Token', devToken)
    .send({ password: 'testpassword123' });
  expect(res.status).toBe(200);
  return res.body;
}

async function login(username, password = 'testpassword123') {
  const res = await api.post('/api/auth/login').send({ username, password });
  expect(res.status).toBe(200);
  const token = res.body.access_token || res.body.token;
  expect(token).toBeTruthy();
  return token;
}

async function runTick() {
  const res = await api.post('/api/tick').send({});
  expect(res.status).toBe(200);
}

(enabled ? describe : describe.skip)('Colonization loop (JS)', () => {
  test('alpha colonizes an empty coordinate, then sees new planet ownership', async () => {
    const scenario = await resetTwoPlayerScenario();
    const alphaFleetId = scenario.fleets.alpha_fleet_id;
    const alphaId = scenario.users.alpha.id;

    const alphaToken = await login('alpha');
    const auth = { Authorization: `Bearer ${alphaToken}` };

    // Pick a deterministic coordinate close enough to avoid fuel validation failures.
    const [hx, hy, hz] = String(scenario.planets.alpha_home.coords).split(':').map((v) => parseInt(v, 10));
    // Keep distance low enough to fit within the seeded deuterium budget.
    const target = { x: hx + 150, y: hy + 150, z: hz + 150 };

    const send = await api
      .post('/api/fleet/send')
      .set(auth)
      .send({ fleet_id: alphaFleetId, mission: 'colonize', target_x: target.x, target_y: target.y, target_z: target.z });

    if (send.status !== 200) {
      throw new Error(`Colonize send failed: ${send.status} ${JSON.stringify(send.body)}`);
    }

    // Resolve colonization and return.
    await runTick();
    await runTick();

    const planets = await api.get('/api/planet').set(auth);
    expect(planets.status).toBe(200);
    expect(Array.isArray(planets.body)).toBe(true);

    const colonized = planets.body.find((p) => p.x === target.x && p.y === target.y && p.z === target.z);
    expect(colonized).toBeTruthy();
    expect(colonized.user_id).toBe(alphaId);
  });
});
