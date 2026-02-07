// JS Integration (Supertest) against the running Python backend.
// Run via: make supertest

const request = require('supertest');

const enabled = process.env.PLANETARION_SUPERTEST === '1';
const api = request('http://localhost:5000');

if (enabled) {
  // In development mode, fleet travel uses real-time (default min 30s).
  // Keep these tests robust by allowing for real-time waiting.
  jest.setTimeout(120_000);
}

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

async function sleep(ms) {
  await new Promise((r) => setTimeout(r, ms));
}

async function waitForFleetLegThenTick({ auth, fleetId, minWaitSeconds = 0 }) {
  const list = await api.get('/api/fleet').set(auth);
  expect(list.status).toBe(200);
  const fleet = (Array.isArray(list.body) ? list.body : []).find((f) => String(f.id) === String(fleetId));
  expect(fleet).toBeTruthy();

  const eta = Number(fleet.eta || 0) || 0;
  const waitSeconds = Math.max(minWaitSeconds, eta) + 1;
  if (waitSeconds > 0) await sleep(waitSeconds * 1000);
  await runTick();
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

    // Leg 1: travel + resolve colonization.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });
    // Leg 2: return.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });

    const planets = await api.get('/api/planet').set(auth);
    expect(planets.status).toBe(200);
    expect(Array.isArray(planets.body)).toBe(true);

    const colonized = planets.body.find((p) => p.x === target.x && p.y === target.y && p.z === target.z);
    expect(colonized).toBeTruthy();
    expect(colonized.user_id).toBe(alphaId);
  });
});
