const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Tick Processing', () => {
  test('Run tick processes arrived fleets and updates UI', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    // Resolve user id (needed to pick a non-owned target planet for espionage).
    const usersRes = await request.get('http://localhost:5000/users');
    expect(usersRes.ok()).toBeTruthy();
    const users = await usersRes.json();
    const self = users.find((u) => u.username === 'e2etestuser');
    expect(self).toBeTruthy();

    // Choose a start planet owned by the user.
    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const ownedPlanets = await planetsRes.json();
    const startPlanetId = ownedPlanets[0].id;

    // Ensure a stationed fleet has espionage probes (shipyard will create/update a stationed fleet).
    const buildProbeRes = await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: { planet_id: startPlanetId, ship_type: 'espionage_probe', quantity: 1 },
    });
    expect(buildProbeRes.ok()).toBeTruthy();

    // Create a dedicated fleet that contains the probe (shipyard builds go to the inventory fleet).
    const createProbeFleetRes = await request.post('http://localhost:5000/api/fleet', {
      headers,
      data: {
        start_planet_id: startPlanetId,
        ships: { espionage_probe: 1 },
      },
    });
    expect(createProbeFleetRes.ok()).toBeTruthy();
    const probeFleetId = (await createProbeFleetRes.json())?.fleet?.id;
    expect(probeFleetId).toBeTruthy();

    // Find an enemy planet to spy on.
    const allPlanetsRes = await request.get('http://localhost:5000/api/planets');
    expect(allPlanetsRes.ok()).toBeTruthy();
    const allPlanets = await allPlanetsRes.json();
    const enemyPlanet = allPlanets.find((p) => p.user_id != null && p.user_id !== self.id);
    expect(enemyPlanet).toBeTruthy();

    // Send espionage; in test env travel time can be 0, so the UI will show "Arrived (pending tick)" until tick runs.
    const sendRes = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: probeFleetId, mission: 'espionage', target_planet_id: enemyPlanet.id },
    });
    expect(sendRes.ok()).toBeTruthy();

    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-fleets').click();
    await expect(page.getByTestId('fleet-management')).toBeVisible({ timeout: 60000 });

    const pendingBanner = page.getByTestId('fleet-pending-tick-banner');
    await expect(pendingBanner).toBeVisible({ timeout: 60000 });

    const tile = page.getByTestId('fleet-tile').filter({ hasText: `Fleet #${probeFleetId}` }).first();
    await expect(tile).toBeVisible({ timeout: 60000 });
    await expect(tile.getByTestId('fleet-eta-value')).toHaveText('Arrived (pending tick)', { timeout: 60000 });

    // Trigger server processing by calling the tick endpoint, then notify the UI to refresh.
    await request.post('http://localhost:5000/api/tick');
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('planetarion:tick')));
    await expect(tile.getByTestId('fleet-status-value')).not.toHaveText('traveling', { timeout: 60000 });

    // With forced zero travel time, the mission often requires a second tick to process the return leg.
    await request.post('http://localhost:5000/api/tick');
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('planetarion:tick')));
    await expect(tile.getByTestId('fleet-status-value')).toHaveText('stationed', { timeout: 60000 });
    await expect(tile.getByTestId('fleet-eta-value')).not.toHaveText('Arrived (pending tick)', { timeout: 60000 });
  });
});
