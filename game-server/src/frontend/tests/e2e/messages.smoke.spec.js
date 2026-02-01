const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

test.describe('Messages UI Smoke', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('renders messages placeholder section', async ({ page }) => {
    await page.getByTestId('nav-messages').click();
    await expect(page.getByTestId('section-messages')).toBeVisible();
    await expect(page.getByRole('heading', { name: /messages/i })).toBeVisible();
    await expect(page.getByText(/messaging system coming soon/i)).toBeVisible();
  });
});

