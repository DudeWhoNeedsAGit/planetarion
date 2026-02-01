const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Galaxy Map UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('opens and closes the galaxy map modal', async ({ page }) => {
    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible();
    await expect(page.getByTestId('galaxy-modal-content')).toBeVisible();
    await expect(page.getByRole('heading', { name: /galaxy map/i })).toBeVisible();

    await page.getByTestId('galaxy-close').click();
    await expect(page.getByTestId('galaxy-modal')).not.toBeVisible();
  });

  test('renders at least one system marker', async ({ page }) => {
    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible();

    // Wait for the GalaxyMap to finish its initial fetch.
    await expect(page.getByText('Loading Galaxy Data...')).not.toBeVisible({ timeout: 60000 });

    // GalaxyMap tags markers for test diagnostics.
    const systemMarkers = page.locator('[data-test-marker="system-marker"]');
    await expect(systemMarkers.first()).toBeVisible({ timeout: 60000 });
  });

  test('clicking a system marker opens system details', async ({ page }) => {
    await page.getByTestId('nav-galaxy').click();
    await expect(page.getByTestId('galaxy-modal')).toBeVisible();

    await expect(page.getByText('Loading Galaxy Data...')).not.toBeVisible({ timeout: 60000 });

    const systemMarkers = page.locator('[data-test-marker="system-marker"]');
    await expect(systemMarkers.first()).toBeVisible({ timeout: 60000 });

    await systemMarkers.first().click();
    await expect(page.getByRole('heading', { name: /^🌌 System/i })).toBeVisible({ timeout: 60000 });
  });
});
