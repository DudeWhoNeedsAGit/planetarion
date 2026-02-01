const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Combat UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders combat center and tabs', async ({ page }) => {
    await page.getByTestId('nav-combat').click();
    await expect(page.getByTestId('combat-dashboard')).toBeVisible();
    await expect(page.getByRole('heading', { name: /combat center/i })).toBeVisible();
    await expect(page.getByTestId('combat-tab-overview')).toBeVisible();
    await expect(page.getByTestId('combat-tab-battles')).toBeVisible();
    await expect(page.getByTestId('combat-tab-statistics')).toBeVisible();
    await expect(page.getByTestId('combat-recent-battles')).toBeVisible();
    await expect(page.getByTestId('combat-debris-fields')).toBeVisible();

    // If there are any recent battles, clicking one should open the detail modal.
    const firstRecent = page.getByTestId('combat-recent-battle').first();
    if (await firstRecent.count()) {
      await firstRecent.click();
      await expect(page.getByRole('heading', { name: /detailed battle report/i })).toBeVisible();
      await page.getByRole('button', { name: '×' }).click();
    }

    // If there are any debris fields, clicking "Send recyclers" should navigate to fleets.
    const sendRecyclers = page.getByTestId('combat-send-recyclers').first();
    if (await sendRecyclers.count()) {
      await sendRecyclers.click();
      await expect(page.getByTestId('fleet-management')).toBeVisible();
    }
  });
});
