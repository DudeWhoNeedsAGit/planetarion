const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

function dist2d(a, b) {
  const dx = (a.x || 0) - (b.x || 0);
  const dy = (a.y || 0) - (b.y || 0);
  return Math.sqrt(dx * dx + dy * dy);
}

test.describe('Galaxy Map Fleet Overlay', () => {
  test('renders a moving fleet indicator after sending a fleet', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    // Pick a start planet owned by the player.
    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const userPlanets = await planetsRes.json();
    const startPlanet = userPlanets[0];
    expect(startPlanet).toBeTruthy();

    // Ensure we have ships to create a fleet.
    const buildShipsRes = await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: { planet_id: startPlanet.id, ship_type: 'light_fighter', quantity: 5 },
    });
    expect(buildShipsRes.ok()).toBeTruthy();

    // Find a pirate system on the player's Z slice via the galaxy API (respects current scenario/snapshot).
    const nearbyRes = await request.get(
      `http://localhost:5000/api/galaxy/nearby/${startPlanet.x}/${startPlanet.y}/${startPlanet.z}?range=2000&z_band=0&limit=500`,
      { headers },
    );
    expect(nearbyRes.ok()).toBeTruthy();
    const nearby = await nearbyRes.json();
    const systems = Array.isArray(nearby?.systems) ? nearby.systems : [];
    const pirateSystem = systems
      .filter((s) => s.relation === 'pirates' || s.flags?.has_pirates)
      .sort((a, b) => dist2d(a, startPlanet) - dist2d(b, startPlanet))[0];
    expect(pirateSystem).toBeTruthy();

    const systemPlanetsRes = await request.get(
      `http://localhost:5000/api/galaxy/system/${pirateSystem.x}/${pirateSystem.y}/${pirateSystem.z}`,
      { headers },
    );
    expect(systemPlanetsRes.ok()).toBeTruthy();
    const systemPlanets = await systemPlanetsRes.json();
    const piratePlanet = Array.isArray(systemPlanets)
      ? systemPlanets.find((p) => p.owner_name === 'pirates' || p.owner === 'pirates' || p.relation === 'pirates' || p.flags?.has_pirates)
      : null;
    // Fallback: pick any enemy-owned planet in that system.
    const targetPlanet = piratePlanet || (Array.isArray(systemPlanets) ? systemPlanets.find((p) => p.user_id != null && p.user_id !== startPlanet.user_id) : null);
    expect(targetPlanet).toBeTruthy();

    // Create and send a fleet.
    const createFleetRes = await request.post('http://localhost:5000/api/fleet', {
      headers,
      data: {
        start_planet_id: startPlanet.id,
        ships: { light_fighter: 1 },
      },
    });
    expect(createFleetRes.ok()).toBeTruthy();
    const fleetId = (await createFleetRes.json())?.fleet?.id;
    expect(fleetId).toBeTruthy();

    const sendRes = await request.post('http://localhost:5000/api/fleet/send', {
      headers,
      data: { fleet_id: fleetId, mission: 'attack', target_planet_id: targetPlanet.id },
    });
    expect(sendRes.ok()).toBeTruthy();

    // UI: open Galaxy Map and verify a fleet dot is rendered.
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible();

    await expect(page.getByText('Loading Galaxy Data...')).not.toBeVisible({ timeout: 60000 });

    // Fleet overlay dots are tagged per fleet id.
    await expect(page.getByTestId(`galaxy-fleet-dot-${fleetId}`)).toBeVisible({ timeout: 60000 });
  });
});
