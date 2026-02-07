const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Planet rename selection stability', () => {
  test('renames the originally selected planet even after background refresh', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const ownedPlanets = await planetsRes.json();
    expect(Array.isArray(ownedPlanets)).toBeTruthy();
    expect(ownedPlanets.length).toBeGreaterThan(1);

    const targetPlanet = ownedPlanets[1];
    const originalTargetName = targetPlanet.name;

    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-planets').click();
    await expect(page.getByTestId('section-planets')).toBeVisible({ timeout: 60000 });

    const selector = page.getByTestId('planet-selector-dropdown');
    if (await selector.count()) {
      await expect(selector).toBeVisible({ timeout: 60000 });
      await selector.selectOption(String(targetPlanet.id));
    } else {
      const buttonsWrap = page.getByTestId('planet-selector-buttons');
      await expect(buttonsWrap).toBeVisible({ timeout: 60000 });
      const targetLabel = `(${targetPlanet.x}:${targetPlanet.y}:${targetPlanet.z})`;
      await buttonsWrap.getByRole('button', { name: new RegExp(targetLabel.replace(/[()]/g, '\\$&')) }).click();
    }

    await page.getByTestId('planet-rename-open').click();
    await expect(page.getByTestId('planet-rename-modal')).toBeVisible({ timeout: 60000 });

    const renameInput = page.getByTestId('planet-rename-input');
    const nextName = `Rename Lock ${Date.now()}`;
    await renameInput.fill(nextName);

    // Polling refresh runs every 10s in Dashboard; wait past one cycle.
    await page.waitForTimeout(11000);

    await page.getByTestId('planet-rename-submit').click();
    await expect(page.getByTestId('planet-rename-modal')).not.toBeVisible({ timeout: 60000 });

    const afterRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(afterRes.ok()).toBeTruthy();
    const afterPlanets = await afterRes.json();
    const renamedTarget = afterPlanets.find((p) => p.id === targetPlanet.id);
    const firstPlanet = afterPlanets.find((p) => p.id === ownedPlanets[0].id);

    expect(renamedTarget).toBeTruthy();
    expect(renamedTarget.name).toBe(nextName);
    expect(firstPlanet).toBeTruthy();
    if (ownedPlanets[0].id !== targetPlanet.id) {
      expect(firstPlanet.name).toBe(ownedPlanets[0].name);
    }
    // Sanity: target actually changed from original.
    expect(renamedTarget.name).not.toBe(originalTargetName);
  });
});
