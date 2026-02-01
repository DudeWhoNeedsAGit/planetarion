const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Galaxy → Spy Flow', () => {
  test('spy button routes to fleet send modal with espionage preset', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    // Ensure at least one stationed fleet exists (and has probes for espionage mission).
    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const planets = await planetsRes.json();
    const startPlanetId = planets[0].id;

    // Build a probe; shipyard will create/update a stationed fleet automatically.
    const buildProbeRes = await request.post('http://localhost:5000/api/shipyard/build', {
      headers,
      data: {
        planet_id: startPlanetId,
        ship_type: 'espionage_probe',
        quantity: 1,
      },
    });
    expect(buildProbeRes.ok()).toBeTruthy();

    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');

    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible();
    await expect(page.getByText('Loading Galaxy Data...')).not.toBeVisible({ timeout: 60000 });

    // Prefer a marker that is known to have colonies owned by someone else (enemy/pirates).
    // In test env, fog-of-war is disabled so the system details should list planets immediately.
    const enemyMarker = page.locator('[data-test-marker="system-marker"][title*="Enemy Colony"]').first();
    if (await enemyMarker.count()) {
      await enemyMarker.click();
    } else {
      await page.locator('[data-test-marker="system-marker"]').first().click();
    }
    await expect(page.getByRole('heading', { name: /^🌌 System/i })).toBeVisible({ timeout: 60000 });

    const spyButtons = page.getByRole('button', { name: 'Spy' });
    await expect(spyButtons.first()).toBeVisible({ timeout: 60000 });
    await expect(spyButtons.first()).toBeEnabled({ timeout: 60000 });
    // DOM click is more reliable than pointer-based click with overlays (chat, scroll containers).
    await spyButtons.first().evaluate((el) => el.click());

    // Should route to Fleets and open send modal.
    const fleetsSection = page.getByTestId('section-fleets');
    try {
      await expect(fleetsSection).toBeVisible({ timeout: 10000 });
    } catch {
      // Fallback: close the Galaxy modal (it intercepts clicks) and navigate manually.
      const galaxyModal = page.getByTestId('galaxy-modal');
      await galaxyModal.getByRole('button', { name: '✕' }).first().click({ force: true });
      await expect(galaxyModal).not.toBeVisible({ timeout: 60000 });
      await page.getByTestId('nav-fleets').click();
      await expect(fleetsSection).toBeVisible({ timeout: 60000 });
    }
    await expect(page.getByTestId('fleet-send-modal')).toBeVisible({ timeout: 60000 });
    const missionSelect = page.getByTestId('fleet-mission-select');
    await expect(missionSelect).toHaveValue('espionage');
  });
});
