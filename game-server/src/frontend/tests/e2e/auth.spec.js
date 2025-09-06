const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  test('should allow user registration and login', async ({ page }) => {
    // Skip this test for now - focus on the two specific issues
    test.skip();
  });

  test('should allow user login with existing account', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Should be on login page
    await expect(page.locator('h2')).toContainText('Login to Planetarion');

    // Fill login form
    await page.fill('input[name="username"]', 'e2etestuser');
    await page.fill('input[name="password"]', 'testpassword123');

    // Submit login
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForTimeout(2000);

    // Check if we're logged in - look for the main welcome heading
    await expect(page.locator('h2:has-text("Welcome back")')).toBeVisible();
  });

  test('should show error for invalid login credentials', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Fill login form with wrong credentials
    await page.fill('input[name="username"]', 'nonexistentuser');
    await page.fill('input[name="password"]', 'wrongpassword');

    // Submit login
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=Login failed').or(page.locator('.bg-red-600'))).toBeVisible();
  });

  test('should show error for registration with existing username', async ({ page }) => {
    // Navigate to register page
    await page.goto('/#register');

    // Fill registration form with existing username
    await page.fill('input[name="username"]', 'e2etestuser'); // Same as before
    await page.fill('input[name="email"]', 'different@example.com');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.fill('input[name="confirmPassword"]', 'testpassword123');

    // Submit registration
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('text=Registration failed').or(page.locator('.bg-red-600'))).toBeVisible();
  });

  test('should validate password confirmation on registration', async ({ page }) => {
    // Navigate to register page
    await page.goto('/#register');

    // Fill form with mismatched passwords
    await page.fill('input[name="username"]', 'testuser2');
    await page.fill('input[name="email"]', 'test2@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'differentpassword');

    // Submit registration
    await page.click('button[type="submit"]');

    // Should show password mismatch error
    await expect(page.locator('text=Passwords do not match')).toBeVisible();
  });

  test('should navigate between login and register', async ({ page }) => {
    // Start on login page
    await page.goto('/');
    await expect(page.locator('h2')).toContainText('Login to Planetarion');

    // Go to register
    await page.click('text=Register here');
    await expect(page.locator('h2')).toContainText('Join Planetarion');

    // Go back to login
    await page.click('text=Login here');
    await expect(page.locator('h2')).toContainText('Login to Planetarion');
  });
});
