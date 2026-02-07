const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

async function restoreSnapshot(request) {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const res = await request.post('http://localhost:5000/api/admin/db/restore', {
    headers: { 'X-Planetarion-Dev-Token': devToken },
  });
  expect(res.ok()).toBeTruthy();
}

test.describe('Combat Outcome CTA', () => {
  test.setTimeout(120000);

  test('battle report CTA opens fleets with recycle preset', async ({ page, request }) => {
    await restoreSnapshot(request);

    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const userPlanets = await planetsRes.json();
    const startPlanetId = userPlanets?.[0]?.id;
    expect(startPlanetId).toBeTruthy();

    // Ensure attacker ships + recyclers exist for follow-up.
    await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: { planet_id: startPlanetId, ship_type: 'light_fighter', quantity: 5 },
    });
    await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: { planet_id: startPlanetId, ship_type: 'recycler', quantity: 4 },
    });

    const usersRes = await request.get('http://localhost:5000/users');
    expect(usersRes.ok()).toBeTruthy();
    const users = await usersRes.json();
    const pirates = users.find((u) => u.username === 'pirates');
    expect(pirates).toBeTruthy();

    const allPlanetsRes = await request.get('http://localhost:5000/api/planets');
    expect(allPlanetsRes.ok()).toBeTruthy();
    const allPlanets = await allPlanetsRes.json();
    const piratePlanet = allPlanets.find((p) => p.user_id === pirates.id);
    expect(piratePlanet).toBeTruthy();

    const createFleetRes = await request.post('http://localhost:5000/api/fleet', {
      headers,
      data: { start_planet_id: startPlanetId, ships: { light_fighter: 3 } },
    });
    expect(createFleetRes.ok()).toBeTruthy();
    const attackFleetId = (await createFleetRes.json())?.fleet?.id;
    expect(attackFleetId).toBeTruthy();

    const sendRes = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: attackFleetId, mission: 'attack', target_planet_id: piratePlanet.id },
    });
    expect(sendRes.ok()).toBeTruthy();

    // Resolve combat and wait for at least one report (supports non-zero travel-time envs).
    let reports = [];
    for (let i = 0; i < 60; i++) {
      await request.post('http://localhost:5000/api/tick');
      const reportsRes = await request.get('http://localhost:5000/api/combat/reports?limit=20&offset=0', { headers });
      expect(reportsRes.ok()).toBeTruthy();
      reports = (await reportsRes.json())?.reports || [];
      if (reports.length > 0) break;
      await page.waitForTimeout(1000);
    }
    expect(reports.length).toBeGreaterThan(0);

    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-combat').click();
    await expect(page.getByTestId('combat-dashboard')).toBeVisible({ timeout: 60000 });

    await page.getByTestId('combat-tab-battles').click();
    const card = page.locator('.battle-report-card').first();
    await expect(card).toBeVisible({ timeout: 60000 });
    await card.click();

    await expect(page.getByTestId('combat-outcome-cta-card')).toBeVisible({ timeout: 60000 });
    await page.getByTestId('combat-cta-send-recyclers').click();

    await expect(page.getByTestId('fleet-management')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('fleet-send-modal')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('fleet-mission-select')).toHaveValue('recycle');
  });
});
