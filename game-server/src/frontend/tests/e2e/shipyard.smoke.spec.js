const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Shipyard UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders shipyard section', async ({ page }) => {
    await page.getByTestId('nav-shipyard').click();
    await expect(page.getByTestId('section-shipyard')).toBeVisible();
    await expect(page.getByRole('heading', { name: /shipyard/i })).toBeVisible();
    await expect(page.getByText(/build ships/i)).toBeVisible();
  });
});

