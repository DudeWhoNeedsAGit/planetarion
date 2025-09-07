const { test, expect } = require('@playwright/test');

test.describe('Authentication', () => {
  test('should allow user registration and login', async ({ page }) => {
    // Generate unique username to avoid conflicts
    const uniqueUsername = `testuser_${Date.now()}`;
    const testPassword = 'testpassword123';
    const testEmail = `${uniqueUsername}@example.com`;

    console.log(`🧪 Testing registration for user: ${uniqueUsername}`);

    // Navigate to register page
    await page.goto('/#register');
    console.log('📍 Navigated to register page');

    // Wait for page to load completely
    await page.waitForLoadState('networkidle');
    console.log('📍 Page loaded');

    // Should be on register page
    await expect(page.locator('h2')).toContainText('Join Planetarion');
    console.log('✅ On register page');

    // Fill registration form
    await page.fill('input[name="username"]', uniqueUsername);
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    console.log('✅ Form filled');

    // Submit registration
    await page.click('button[type="submit"]');
    console.log('📤 Registration submitted');

    // Wait for registration to complete - check for either success or error
    await page.waitForTimeout(3000);

    // Check if registration succeeded by looking for dashboard elements
    const dashboardVisible = await page.locator('h2:has-text("Welcome back")').isVisible().catch(() => false);

    if (dashboardVisible) {
      console.log('✅ Registration successful - redirected to dashboard');
    } else {
      // Check for error messages
      const errorVisible = await page.locator('.bg-red-600').isVisible().catch(() => false);
      if (errorVisible) {
        const errorText = await page.locator('.bg-red-600').textContent();
        console.log(`❌ Registration failed with error: ${errorText}`);
        throw new Error(`Registration failed: ${errorText}`);
      } else {
        console.log('❌ Registration did not complete - no dashboard or error visible');
        // Take a screenshot for debugging
        await page.screenshot({ path: 'registration-debug.png' });
        throw new Error('Registration did not complete successfully');
      }
    }

    // Verify we're logged in by checking for user info
    await expect(page.locator('text=Dashboard')).toBeVisible();
    console.log('✅ Dashboard elements visible');

    // Now test login with the newly created account
    console.log('🔄 Testing login with newly created account');

    // First logout by clearing localStorage and reloading
    await page.evaluate(() => {
      localStorage.clear();
    });
    await page.reload();
    console.log('📍 Logged out and reloaded');

    // Should be back on login page
    await expect(page.locator('h2')).toContainText('Login to Planetarion');
    console.log('✅ Back on login page');

    // Login with the newly registered account
    await page.fill('input[name="username"]', uniqueUsername);
    await page.fill('input[name="password"]', testPassword);
    console.log('✅ Login form filled');

    // Submit login
    await page.click('button[type="submit"]');
    console.log('📤 Login submitted');

    // Wait for login to complete
    await page.waitForTimeout(3000);

    // Check if login succeeded
    const loginSuccess = await page.locator('h2:has-text("Welcome back")').isVisible().catch(() => false);

    if (loginSuccess) {
      console.log('✅ Login successful');
    } else {
      const loginError = await page.locator('.bg-red-600').textContent().catch(() => '');
      console.log(`❌ Login failed: ${loginError}`);
      throw new Error(`Login failed: ${loginError}`);
    }

    // Verify successful login
    await expect(page.locator('h2:has-text("Welcome back")')).toBeVisible();
    await expect(page.locator('text=Dashboard')).toBeVisible();
    console.log('✅ Login test completed successfully');
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
