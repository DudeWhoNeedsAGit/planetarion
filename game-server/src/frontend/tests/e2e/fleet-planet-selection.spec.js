const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Fleet Management planet selection', () => {
  test('keeps selected planet across tick/event refreshes', async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');

    await page.getByTestId('nav-fleets').click();
    await expect(page.getByTestId('fleet-management')).toBeVisible({ timeout: 60000 });

    const planetButtons = page.getByTestId('fleet-planet-button');
    await expect(planetButtons.first()).toBeVisible();
    await expect(planetButtons.nth(1)).toBeVisible();

    const chosen = planetButtons.nth(1);
    const chosenLabel = (await chosen.textContent())?.trim() || null;

    await chosen.click();
    await expect(chosen).toHaveClass(/pa-btn-primary/);

    // Trigger the same refresh path the dashboard uses after processing a tick.
    const runTick = page.getByTestId('run-tick-button');
    await expect(runTick).toBeVisible();
    await runTick.click();

    if (chosenLabel) {
      const chosenAfter = page.getByTestId('fleet-planet-button').filter({ hasText: chosenLabel }).first();
      await expect(chosenAfter).toHaveClass(/pa-btn-primary/, { timeout: 60000 });
    }

    // Also ensure periodic polling doesn't reset the selection.
    await page.waitForTimeout(6000);
    if (chosenLabel) {
      const chosenAfterPoll = page.getByTestId('fleet-planet-button').filter({ hasText: chosenLabel }).first();
      await expect(chosenAfterPoll).toHaveClass(/pa-btn-primary/);
    }
  });
});
