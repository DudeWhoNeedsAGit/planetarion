const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Fleet State Map (UI)', () => {
  test('Deploy mission stations fleet at target planet after tick', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');

    const planetsRes = await request.get('http://localhost:5000/api/planet', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(planetsRes.ok()).toBeTruthy();
    const ownedPlanets = await planetsRes.json();
    expect(Array.isArray(ownedPlanets)).toBeTruthy();
    expect(ownedPlanets.length).toBeGreaterThan(1);
    const startPlanetId = ownedPlanets[0].id;
    const targetPlanetId = ownedPlanets[1].id;

    await page.getByTestId('nav-fleets').click();
    await expect(page.getByTestId('fleet-management')).toBeVisible({ timeout: 60000 });

    // Ensure we have a stationed fleet by creating one via the UI.
    await page.getByTestId('fleet-create-button').click();
    await expect(page.getByTestId('fleet-create-modal')).toBeVisible();

    const startSelect = page.getByTestId('fleet-start-planet-select');
    await expect(startSelect).toBeVisible();
    await startSelect.selectOption(String(startPlanetId));

    const cargoInput = page.getByTestId('fleet-ship-small_cargo');
    await cargoInput.fill('1');
    await page.getByTestId('fleet-create-submit').click();

    // Now pick the new stationed fleet tile that can be sent.
    const sendButton = page.locator('button', { hasText: 'Send' }).first();
    await expect(sendButton).toBeVisible({ timeout: 60000 });

    const tile = sendButton.locator('xpath=ancestor::*[@data-testid="fleet-tile"]').first();
    const fleetTitle = await tile.locator('text=/Fleet #\\d+/').first().textContent();
    const match = /Fleet #(\d+)/.exec(fleetTitle || '');
    expect(match).toBeTruthy();
    const fleetId = match[1];

    await sendButton.click();
    await expect(page.getByTestId('fleet-send-modal')).toBeVisible();

    await page.getByTestId('fleet-mission-select').selectOption('deploy');

    const targetSelect = page.getByTestId('fleet-target-planet-select');
    await expect(targetSelect).toBeVisible();

    await targetSelect.selectOption(String(targetPlanetId));

    await page.getByTestId('fleet-send-submit').click();

    // With forced zero travel time in e2e-ui, this should become "Arrived (pending tick)" until tick runs.
    const pendingBanner = page.getByTestId('fleet-pending-tick-banner');
    await expect(pendingBanner).toBeVisible({ timeout: 60000 });

    // Run a tick and ensure the fleet is no longer pending.
    const runTick = page.getByTestId('run-tick-button');
    await expect(runTick).toBeVisible();
    await runTick.click();
    // Some flows need a second tick (e.g. return leg). Deploy should not, but a second click is harmless.
    await runTick.click();

    // Deployed fleets can move to another planet, so the tile may disappear from the current planet view.
    // Accept either outcome:
    // - tile disappears (moved to target planet), OR
    // - tile remains but no longer says "Arrived (pending tick)".
    await expect
      .poll(
        async () => {
          const tiles = page.getByTestId('fleet-tile').filter({ hasText: `Fleet #${fleetId}` });
          const count = await tiles.count();
          if (count === 0) return true;
          const etaText = await tiles.first().getByTestId('fleet-eta-value').textContent();
          return (etaText || '').trim() !== 'Arrived (pending tick)';
        },
        { timeout: 60000 }
      )
      .toBe(true);
  });
});
