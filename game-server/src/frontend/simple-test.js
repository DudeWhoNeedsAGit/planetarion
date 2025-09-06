const { test, expect } = require('@playwright/test');

test('frontend loads', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page.locator('text=Planetarion')).toBeVisible();
  console.log('✅ Test passed - Frontend is working!');
});
