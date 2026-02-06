const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Galaxy Map', () => {
  test('Shows grid and nearby systems (z=0 should not fall back)', async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');

    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('galaxy-viewport')).toBeVisible({ timeout: 60000 });

    const markers = page.locator('[data-test-marker="system-marker"]');
    await expect(markers.first()).toBeVisible({ timeout: 60000 });
  });
});

