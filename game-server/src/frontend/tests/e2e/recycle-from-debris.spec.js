const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

async function restoreSnapshot(request) {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const res = await request.post('http://localhost:5000/api/admin/db/restore', {
    headers: { 'X-Planetarion-Dev-Token': devToken },
  });
  expect(res.ok()).toBeTruthy();
}

test.describe('Recycle From Combat Debris', () => {
  test.setTimeout(120000);

  test('build recyclers → click Send recyclers in Combat → collect + return + deposit', async ({ page, request }) => {
    // Keep this spec deterministic even when running in the full suite.
    await restoreSnapshot(request);

    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    // Pick a start planet owned by the player.
    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const userPlanets = await planetsRes.json();
    const startPlanet = userPlanets[0];
    const startPlanetId = startPlanet.id;

    // Ensure a stationed fleet with recyclers exists (shipyard creates/updates one).
    const buildRecyclerRes = await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: { planet_id: startPlanetId, ship_type: 'recycler', quantity: 10 },
    });
    expect(buildRecyclerRes.ok()).toBeTruthy();

    // Snapshot origin resources after building recyclers (shipyard spends resources).
    const afterBuildPlanetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(afterBuildPlanetsRes.ok()).toBeTruthy();
    const afterBuildPlanets = await afterBuildPlanetsRes.json();
    const baselineStartPlanet = afterBuildPlanets.find((p) => p.id === startPlanetId);
    const beforeMetal = Number(baselineStartPlanet?.resources?.metal ?? baselineStartPlanet?.metal ?? 0);
    const beforeCrystal = Number(baselineStartPlanet?.resources?.crystal ?? baselineStartPlanet?.crystal ?? 0);
    const beforeDeut = Number(baselineStartPlanet?.resources?.deuterium ?? baselineStartPlanet?.deuterium ?? 0);

    // Find pirates user + a pirate planet to attack (pirates are spawned near player in populate).
    const usersRes = await request.get('http://localhost:5000/users');
    expect(usersRes.ok()).toBeTruthy();
    const users = await usersRes.json();
    const piratesUser = users.find((u) => u.username === 'pirates');
    expect(piratesUser).toBeTruthy();

    const allPlanetsRes = await request.get('http://localhost:5000/api/planets');
    expect(allPlanetsRes.ok()).toBeTruthy();
    const allPlanets = await allPlanetsRes.json();
    const piratePlanet = allPlanets.find((p) => p.user_id === piratesUser.id);
    expect(piratePlanet).toBeTruthy();

    // Create an attacker fleet using planet-available ships.
    // (This uses /api/fleet which draws from Planet ship counts; recycler ships are tracked on fleets.)
    const createAttackFleetRes = await request.post('http://localhost:5000/api/fleet', {
      headers,
      data: {
        start_planet_id: startPlanetId,
        ships: {
          light_fighter: 5,
          heavy_fighter: 2,
        },
      },
    });
    expect(createAttackFleetRes.ok()).toBeTruthy();
    const createdFleet = (await createAttackFleetRes.json())?.fleet;
    const attackFleetId = createdFleet?.id;
    expect(attackFleetId).toBeTruthy();

    // Send the fleet on an attack mission to create debris.
    const sendAttackRes = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: {
        fleet_id: attackFleetId,
        mission: 'attack',
        target_planet_id: piratePlanet.id,
      },
    });
    expect(sendAttackRes.ok()).toBeTruthy();

    // Run ticks until at least one debris field exists; keep a deterministic target.
    let debrisTarget = null;
    for (let i = 0; i < 5; i++) {
      await request.post('http://localhost:5000/api/tick');
      const debrisRes = await request.get('http://localhost:5000/api/combat/debris', { headers });
      expect(debrisRes.ok()).toBeTruthy();
      const debrisFields = (await debrisRes.json())?.debris_fields || [];

      // The Combat UI only renders the first 5 items. Pick index 0 so UI + API stay aligned.
      debrisTarget = debrisFields[0] || null;
      if (debrisTarget) break;
    }
    expect(debrisTarget).toBeTruthy();

    const targetPlanetId = debrisTarget.planet.id;
    const targetCoords = debrisTarget.planet.coordinates;
    const debrisResources = debrisTarget.resources || {};
    const totalDebris =
      Number(debrisResources.metal || 0) +
      Number(debrisResources.crystal || 0) +
      Number(debrisResources.deuterium || 0);
    // We built 10 recyclers → capacity 10,000 total (1000 each).
    const expectedTotalCollected = Math.min(totalDebris, 10000);

    // UI: login and click "Send recyclers" from the Combat debris list.
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-combat').click();
    await expect(page.getByTestId('combat-dashboard')).toBeVisible({ timeout: 60000 });

    const debrisList = page.getByTestId('combat-debris-fields');
    await expect(debrisList).toBeVisible({ timeout: 60000 });

    const debrisCard = debrisList.locator('[data-testid="combat-debris-field"]', { hasText: targetCoords }).first();
    await expect(debrisCard).toBeVisible({ timeout: 60000 });
    await debrisCard.getByTestId('combat-send-recyclers').evaluate((el) => el.click());

    // Combat now asks for an explicit source planet + recycling focus before navigating to Fleets.
    const recycleCfg = page.getByTestId('combat-recycle-config-modal');
    await expect(recycleCfg).toBeVisible({ timeout: 60000 });
    await recycleCfg.getByTestId('combat-recycle-continue').click();

    // Should navigate to Fleets and open send modal preset to recycle.
    await expect(page.getByTestId('fleet-send-modal')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('fleet-mission-select')).toHaveValue('recycle');

    // Target should be selected (by planet id).
    const targetSelect = page.getByTestId('fleet-target-planet-select');
    await expect(targetSelect).toBeVisible();
    await expect(targetSelect).toHaveValue(String(targetPlanetId));

    // Send recyclers.
    await page.getByTestId('fleet-send-submit').click();
    await expect(page.getByRole('alert').filter({ hasText: 'Fleet sent successfully!' }).first())
      .toBeVisible();

    // Backend processing: tick 1 collects debris into cargo and sets the fleet to returning,
    // tick 2 delivers cargo to origin planet (return arrival is 0s in testing but requires another tick cycle).
    await request.post('http://localhost:5000/api/tick');
    await request.post('http://localhost:5000/api/tick');

    // Verify origin planet resources increased by at least what recyclers can collect.
    const afterPlanetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(afterPlanetsRes.ok()).toBeTruthy();
    const afterPlanets = await afterPlanetsRes.json();
    const afterStartPlanet = afterPlanets.find((p) => p.id === startPlanetId);
    expect(afterStartPlanet).toBeTruthy();
    const afterMetal = Number(afterStartPlanet?.resources?.metal ?? afterStartPlanet?.metal ?? 0);
    const afterCrystal = Number(afterStartPlanet?.resources?.crystal ?? afterStartPlanet?.crystal ?? 0);
    const afterDeut = Number(afterStartPlanet?.resources?.deuterium ?? afterStartPlanet?.deuterium ?? 0);

    const gainedTotal = (afterMetal - beforeMetal) + (afterCrystal - beforeCrystal) + (afterDeut - beforeDeut);
    expect(gainedTotal).toBeGreaterThanOrEqual(expectedTotalCollected);
  });
});
