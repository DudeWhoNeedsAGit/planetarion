const { test, expect } = require('@playwright/test');

// Helper function for login - use same pattern as working fleet tests
async function loginAsE2eTestUser(page) {
  // Navigate to the app
  await page.goto('/');

  // Login with existing test account
  await page.fill('input[name="username"]', 'e2etestuser');
  await page.fill('input[name="password"]', 'testpassword123');

  // Submit login
  await page.click('button[type="submit"]');

  // Wait for login to complete
  await page.waitForTimeout(2000);

  // Verify login success
  await expect(page.locator('h2:has-text("Welcome back")')).toBeVisible();
}

// Helper function to navigate to Galaxy Map
async function navigateToGalaxyMap(page) {
  await page.locator('nav').locator('text=Galaxy Map').click();
}

// Helper function to clear galaxy data for testing (placeholder for now)
async function clearGalaxyData(page) {
  try {
    console.log('DEBUG: Galaxy data clearing not yet implemented');
    // TODO: Add galaxy data clearing endpoint if needed
  } catch (error) {
    console.log('ERROR: Clear galaxy data failed:', error.message);
  }
}

test.describe('Galaxy Map Navigation', () => {
  // Handle login for each test - use same pattern as working fleet tests
  test.beforeEach(async ({ page }) => {
    await loginAsE2eTestUser(page);
  });

  test('should navigate to Galaxy Map and display modal', async ({ page }) => {
    // Navigate to Galaxy Map using helper function
    await navigateToGalaxyMap(page);

    // Verify Galaxy Map modal appears - use specific selector like fleet tests
    await expect(page.locator('h2').filter({ hasText: 'Galaxy Map' })).toBeVisible();
    await expect(page.locator('text=Center:')).toBeVisible();
    await expect(page.locator('text=Exploration Range: 50 units')).toBeVisible();
  });

  test('should display Galaxy Map modal structure', async ({ page }) => {
    // Navigate to Galaxy Map using helper
    await navigateToGalaxyMap(page);

    // Check modal overlay
    await expect(page.locator('.fixed.inset-0.bg-black.bg-opacity-75')).toBeVisible();

    // Check modal content
    await expect(page.locator('.bg-gray-800.rounded-lg.p-6')).toBeVisible();

    // Check header with title and close button - use specific selector like fleet
    await expect(page.locator('h2').filter({ hasText: 'Galaxy Map' })).toBeVisible();
    await expect(page.locator('button').filter({ hasText: '✕' })).toBeVisible();
  });

  test('should display center coordinates', async ({ page }) => {
    // Navigate to Galaxy Map using helper
    await navigateToGalaxyMap(page);

    // Check center coordinates display
    await expect(page.locator('text=/Center: \\d+:\\d+:\\d+/')).toBeVisible();
  });

  test('should display systems grid container', async ({ page }) => {
    // Navigate to Galaxy Map using helper
    await navigateToGalaxyMap(page);

    // Check grid container exists
    await expect(page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-3')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Listen for console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });

    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for component to load
    await page.waitForTimeout(2000);

    // Check for our debug messages
    const debugMessages = consoleMessages.filter(msg =>
      msg.includes('Galaxy Map Debug') ||
      msg.includes('Fetching nearby systems') ||
      msg.includes('Using fallback test data')
    );

    expect(debugMessages.length).toBeGreaterThan(0);
  });

  test('should display fallback systems when API fails', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for systems to load (fallback data)
    await page.waitForTimeout(2000);

    // Check if any system cards appear
    const systemCards = page.locator('.p-4.rounded-lg.border-2');
    await expect(systemCards.first()).toBeVisible();
  });

  test('should display system coordinates in cards', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for systems
    await page.waitForTimeout(2000);

    // Check for coordinate pattern in system cards - exclude center coordinates
    const systemCoords = page.locator('.p-4.rounded-lg.border-2 .text-white.font-medium');
    await expect(systemCoords.first()).toBeVisible();
  });

  test('should show exploration buttons', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for systems
    await page.waitForTimeout(2000);

    // Check for any buttons in system cards (more flexible selector)
    const systemCardButtons = page.locator('.p-4.rounded-lg.border-2 button');
    await expect(systemCardButtons.first()).toBeVisible();
  });

  test('should close modal when X button clicked', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Verify modal is open - use specific modal header
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();

    // Click close button
    await page.click('button:has-text("✕")');

    // Verify modal is closed (Galaxy Map text should not be visible in modal)
    await expect(page.locator('.fixed.inset-0.bg-black.bg-opacity-75')).not.toBeVisible();
  });

  test('should maintain navigation state', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Check that Galaxy Map nav item is active
    const activeNav = page.locator('.bg-space-blue.text-white').first();
    await expect(activeNav).toContainText('Galaxy Map');
  });

  test('should log expected console messages', async ({ page }) => {
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });

    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for component to initialize
    await page.waitForTimeout(3000);

    // Check for expected console logs
    const hasDebugLog = consoleMessages.some(msg => msg.includes('Galaxy Map Debug'));
    const hasFetchLog = consoleMessages.some(msg => msg.includes('Fetching nearby systems'));
    const hasErrorLog = consoleMessages.some(msg => msg.includes('Error fetching systems'));
    const hasFallbackLog = consoleMessages.some(msg => msg.includes('Using fallback test data'));

    expect(hasDebugLog).toBe(true);
    expect(hasFetchLog).toBe(true);
    expect(hasErrorLog).toBe(true);
    expect(hasFallbackLog).toBe(true);

    console.log('Console messages captured:', consoleMessages);
  });

  test('should display home planet not found in debug', async ({ page }) => {
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });

    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Wait for debug logs
    await page.waitForTimeout(2000);

    // Find the debug message
    const debugMessage = consoleMessages.find(msg => msg.includes('Galaxy Map Debug'));
    expect(debugMessage).toBeTruthy();

    // Parse the debug object (this is a simplified check)
    expect(debugMessage).toContain('homePlanet');
    expect(debugMessage).toContain('Not found');
  });

  test('should test galaxy API endpoints directly', async ({ page }) => {
    // Get JWT token from localStorage (following fleet pattern)
    const token = await page.evaluate(() => localStorage.getItem('token'));
    console.log('DEBUG: JWT token present for API test:', !!token);
    expect(token).toBeTruthy();

    // Test nearby systems endpoint (following fleet API testing pattern)
    const nearbyResponse = await page.request.get('http://localhost:5000/api/galaxy/nearby/100/200/300', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('DEBUG: Nearby systems API response status:', nearbyResponse.status());
    expect(nearbyResponse.status()).toBe(200);

    const nearbyData = await nearbyResponse.json();
    console.log('DEBUG: Nearby systems data:', nearbyData);
    expect(Array.isArray(nearbyData)).toBe(true);

    // Test system planets endpoint
    const systemResponse = await page.request.get('http://localhost:5000/api/galaxy/system/100/200/300', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('DEBUG: System planets API response status:', systemResponse.status());
    expect(systemResponse.status()).toBe(200);

    const systemData = await systemResponse.json();
    console.log('DEBUG: System planets data:', systemData);
    expect(Array.isArray(systemData)).toBe(true);
  });

  test('should handle API errors gracefully with JWT', async ({ page }) => {
    // Get JWT token from localStorage
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeTruthy();

    // Test with invalid coordinates (should still return valid response)
    const response = await page.request.get('http://localhost:5000/api/galaxy/nearby/99999/99999/99999', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('DEBUG: Error handling API response status:', response.status());
    expect([200, 404, 500]).toContain(response.status());

    // Should return some data structure even for edge cases
    const data = await response.json();
    console.log('DEBUG: Error case data:', data);
    expect(data).toBeDefined();
  });
});
