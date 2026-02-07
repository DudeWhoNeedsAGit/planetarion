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
  // Wait for the current leg to complete (real-time), then tick to process it.
  // If backend is configured for instant travel, this is effectively a no-op.
  const list = await api.get('/api/fleet').set(auth);
  expect(list.status).toBe(200);
  const fleet = (Array.isArray(list.body) ? list.body : []).find((f) => String(f.id) === String(fleetId));
  expect(fleet).toBeTruthy();

  const eta = Number(fleet.eta || 0) || 0;
  const waitSeconds = Math.max(minWaitSeconds, eta) + 1;
  if (waitSeconds > 0) await sleep(waitSeconds * 1000);
  await runTick();
}

(enabled ? describe : describe.skip)('Fleet loop (Table A/C smoke via JS)', () => {
  test('alpha attacks pirates, then sees combat report + can spy beta', async () => {
    const scenario = await resetTwoPlayerScenario();
    const alphaFleetId = scenario.fleets.alpha_fleet_id;
    const pirateCampId = scenario.planets.pirate_camp.id;
    const betaHomeId = scenario.planets.beta_home.id;

    const alphaToken = await login('alpha');
    const auth = { Authorization: `Bearer ${alphaToken}` };

    // Attack pirates.
    const sendAttack = await api
      .post('/api/fleet/send')
      .set(auth)
      .send({ fleet_id: alphaFleetId, mission: 'attack', target_planet_id: pirateCampId });
    expect(sendAttack.status).toBe(200);

    // Leg 1: travel + resolve combat.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });
    // Leg 2: return to start planet.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });

    const reports = await api.get('/api/combat/reports?limit=10&offset=0').set(auth);
    expect(reports.status).toBe(200);
    expect(Array.isArray(reports.body.reports)).toBe(true);
    expect(reports.body.reports.length).toBeGreaterThan(0);

    // Spy beta.
    const sendSpy = await api
      .post('/api/fleet/send')
      .set(auth)
      .send({ fleet_id: alphaFleetId, mission: 'espionage', target_planet_id: betaHomeId });
    expect(sendSpy.status).toBe(200);

    // Leg 1: travel + resolve espionage.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });
    // Leg 2: return.
    await waitForFleetLegThenTick({ auth, fleetId: alphaFleetId });

    const spyReports = await api.get('/api/espionage/reports?limit=10&offset=0').set(auth);
    expect(spyReports.status).toBe(200);
    expect(Array.isArray(spyReports.body.reports)).toBe(true);
    expect(spyReports.body.reports.length).toBeGreaterThan(0);
  });
});
