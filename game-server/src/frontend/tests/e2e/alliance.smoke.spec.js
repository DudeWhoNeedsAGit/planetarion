const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Alliance UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders alliance placeholder section', async ({ page }) => {
    await page.getByTestId('nav-alliance').click();
    await expect(page.getByTestId('section-alliance')).toBeVisible();
    await expect(page.getByRole('heading', { name: /alliance center/i })).toBeVisible();
    await expect(page.getByText(/alliance system coming soon/i)).toBeVisible();
  });
});

