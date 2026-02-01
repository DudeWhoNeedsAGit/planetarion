const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Fleet UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders fleet management screen', async ({ page }) => {
    await page.getByTestId('nav-fleets').click();
    await expect(page.getByTestId('fleet-management')).toBeVisible();
    await expect(page.getByTestId('fleet-create-button')).toBeVisible();
    await expect(page.getByTestId('fleet-timeline')).toBeVisible();
  });

  test('renders create fleet modal', async ({ page }) => {
    await page.getByTestId('nav-fleets').click();
    await page.getByTestId('fleet-create-button').click();

    await expect(page.getByTestId('fleet-create-modal')).toBeVisible();
    await expect(page.getByTestId('fleet-start-planet-select')).toBeVisible();
    await expect(page.getByTestId('fleet-create-submit')).toBeVisible();
    await expect(page.getByTestId('fleet-create-cancel')).toBeVisible();
  });
});
