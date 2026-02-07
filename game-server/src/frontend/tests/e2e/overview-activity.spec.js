const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage, resetScenarioPack } = require('./helpers/testSession');

async function runTick(request, token) {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const res = await request.post('http://localhost:5000/api/tick', { headers });
  expect(res.ok()).toBeTruthy();
}

async function restoreSnapshot(request) {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const res = await request.post('http://localhost:5000/api/admin/db/restore', {
    headers: { 'X-Planetarion-Dev-Token': devToken },
  });
  expect(res.ok()).toBeTruthy();
}

test.describe('Overview activity feed', () => {
  test.afterEach(async ({ request }) => {
    // This spec intentionally mutates global state by switching scenarios.
    // Restore the DB snapshot so other specs can still assume the default dataset.
    await restoreSnapshot(request);
  });

  test('shows combat + capture related events from tick logs', async ({ page, request }) => {
    const scenario = await resetScenarioPack(request, 'two-player');
    const alphaFleetId = scenario.fleets.alpha_fleet_id;
    const pirateCampId = scenario.planets.pirate_camp.id;

    const alphaToken = await apiLogin(request, 'alpha', 'testpassword123');
    const headers = { Authorization: `Bearer ${alphaToken}` };

    const sendPirateAttack = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: alphaFleetId, mission: 'attack', target_planet_id: pirateCampId },
    });
    expect(sendPirateAttack.ok()).toBeTruthy();

    await runTick(request, alphaToken);
    await runTick(request, alphaToken);

    await loginViaLocalStorage(page, request, 'alpha', 'testpassword123');
    await page.getByTestId('nav-overview').click();

    const list = page.getByTestId('overview-activity-list');
    await expect(list).toBeVisible({ timeout: 60000 });
    await expect(list.getByTestId('overview-activity-item').first()).toBeVisible();

    // Ensure at least one combat-related entry is present.
    await expect(list).toContainText(/Combat between/i);
  });
});
