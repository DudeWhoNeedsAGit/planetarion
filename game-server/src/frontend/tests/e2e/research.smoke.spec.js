const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Research UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders research placeholder section', async ({ page }) => {
    await page.getByTestId('nav-research').click();
    await expect(page.getByTestId('section-research')).toBeVisible();
    await expect(page.getByRole('heading', { name: /research lab/i })).toBeVisible();
    await expect(page.getByText(/research system coming soon/i)).toBeVisible();
  });
});

