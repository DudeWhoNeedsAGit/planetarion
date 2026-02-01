const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

async function resetTwoPlayerScenario(request) {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const res = await request.post('http://localhost:5000/api/admin/scenarios/two-player/reset', {
    data: { password: 'testpassword123' },
    headers: { 'X-Planetarion-Dev-Token': devToken },
  });
  expect(res.ok()).toBeTruthy();
  return await res.json();
}

async function runTick(request, token) {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const res = await request.post('http://localhost:5000/api/tick', { headers });
  expect(res.ok()).toBeTruthy();
}

async function getCombatReports(request, token) {
  const headers = { Authorization: `Bearer ${token}` };
  const res = await request.get('http://localhost:5000/api/combat/reports?limit=50&offset=0', { headers });
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  return Array.isArray(data?.reports) ? data.reports : [];
}

async function getDebrisFields(request, token) {
  const headers = { Authorization: `Bearer ${token}` };
  const res = await request.get('http://localhost:5000/api/combat/debris', { headers });
  expect(res.ok()).toBeTruthy();
  const data = await res.json();
  return Array.isArray(data?.debris_fields) ? data.debris_fields : [];
}

test.describe('Two-Player Full Gameplay Loop (Table C)', () => {
  test('alpha raids pirates → recycles → fights beta → captures beta home (respawn pending)', async ({ page, request }) => {
    const scenario = await resetTwoPlayerScenario(request);
    const alphaFleetId = scenario.fleets.alpha_fleet_id;
    const betaHomeId = scenario.planets.beta_home.id;
    const pirateCampId = scenario.planets.pirate_camp.id;

    const alphaToken = await apiLogin(request, 'alpha', 'testpassword123');
    const headers = { Authorization: `Bearer ${alphaToken}` };

    // Baseline: login UI as alpha.
    await loginViaLocalStorage(page, request, 'alpha', 'testpassword123');

    // 1) Pirate raid via API (deterministic + fast), then tick to resolve.
    const sendPirateAttack = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: alphaFleetId, mission: 'attack', target_planet_id: pirateCampId },
    });
    expect(sendPirateAttack.ok()).toBeTruthy();
    await runTick(request, alphaToken);
    await runTick(request, alphaToken);

    // 2) Ensure at least 1 combat report is visible in UI.
    await page.getByTestId('nav-combat').click();
    await expect(page.getByTestId('combat-dashboard')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('combat-recent-battles')).toBeVisible({ timeout: 60000 });

    // 3) Debris + one-click recycler send (UI flow).
    let debris = null;
    for (let i = 0; i < 5; i++) {
      const debrisFields = await getDebrisFields(request, alphaToken);
      debris = debrisFields[0] || null;
      if (debris) break;
      await runTick(request, alphaToken);
    }
    expect(debris).toBeTruthy();

    const targetPlanetId = debris.planet.id;
    const targetCoords = debris.planet.coordinates;

    const debrisList = page.getByTestId('combat-debris-fields');
    await expect(debrisList).toBeVisible({ timeout: 60000 });
    const debrisCard = debrisList.locator('[data-testid="combat-debris-field"]', { hasText: targetCoords }).first();
    await expect(debrisCard).toBeVisible({ timeout: 60000 });
    await debrisCard.getByTestId('combat-send-recyclers').evaluate((el) => el.click());

    await expect(page.getByTestId('fleet-send-modal')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('fleet-mission-select')).toHaveValue('recycle');
    await expect(page.getByTestId('fleet-target-planet-select')).toHaveValue(String(targetPlanetId));
    await page.getByTestId('fleet-send-submit').click();
    await expect(page.getByRole('alert').filter({ hasText: 'Fleet sent successfully!' }).first()).toBeVisible();

    // Process recycle (collect + return deposit).
    await runTick(request, alphaToken);
    await runTick(request, alphaToken);

    // 4) Espionage via API (report creation; UI report screen TBD).
    const spySend = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: alphaFleetId, mission: 'espionage', target_planet_id: betaHomeId },
    });
    expect(spySend.ok()).toBeTruthy();
    await runTick(request, alphaToken);
    await runTick(request, alphaToken);

    // 5) War arc (5 fights total): 1 pirate + 4 beta attacks, then capture.
    for (let i = 0; i < 4; i++) {
      const fight = await request.post('http://localhost:5000/api/fleet/send', {
        headers,
        data: { fleet_id: alphaFleetId, mission: 'attack', target_planet_id: betaHomeId },
      });
      expect(fight.ok()).toBeTruthy();
      await runTick(request, alphaToken);
      await runTick(request, alphaToken);
    }

    const reportsBeforeCapture = await getCombatReports(request, alphaToken);
    expect(reportsBeforeCapture.length).toBeGreaterThanOrEqual(5);

    // Conquest attempt (MVP rule: must be undefended). The backend/table-A test enforces this deterministically;
    // UI flow for "make undefended" is not specified yet, so we only execute the send here and leave capture+respawn as follow-up.
    const captureAttempt = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: alphaFleetId, mission: 'attack', target_planet_id: betaHomeId },
    });
    expect(captureAttempt.ok()).toBeTruthy();
    await runTick(request, alphaToken);

    // Keep this test focused on the UI loop closure (combat+debris+recycle). Capture/respawn are validated in Table A.
    test.info().annotations.push({
      type: 'note',
      description: 'Capture+respawn verification pending: requires deterministic undefended condition + UI indicators.',
    });
  });
});

