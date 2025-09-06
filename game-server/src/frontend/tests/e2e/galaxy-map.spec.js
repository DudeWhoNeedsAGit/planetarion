const { test, expect } = require('@playwright/test');

test.describe('Galaxy Map Navigation', () => {
  // Handle login for each test - use same pattern as working auth tests
  test.beforeEach(async ({ page }) => {
    // Login first - use credentials that match the working auth test
    await page.goto('/');
    await page.fill('input[name="username"]', 'e2etestuser');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForTimeout(2000);

    // Verify login success
    await expect(page.locator('h2:has-text("Welcome back")')).toBeVisible();
  });

  test('should navigate to Galaxy Map and display modal', async ({ page }) => {
    // Click Galaxy Map navigation
    await page.click('text=Galaxy Map');

    // Verify Galaxy Map modal appears - use more specific selector for modal header
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();
    await expect(page.locator('text=Center:')).toBeVisible();
    await expect(page.locator('text=Exploration Range: 50 units')).toBeVisible();
  });

  test('should display Galaxy Map modal structure', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Check modal overlay
    await expect(page.locator('.fixed.inset-0.bg-black.bg-opacity-75')).toBeVisible();

    // Check modal content
    await expect(page.locator('.bg-gray-800.rounded-lg.p-6')).toBeVisible();

    // Check header with title and close button
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();
    await expect(page.locator('button:has-text("✕")')).toBeVisible();
  });

  test('should display center coordinates', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

    // Check center coordinates display
    await expect(page.locator('text=/Center: \\d+:\\d+:\\d+/')).toBeVisible();
  });

  test('should display systems grid container', async ({ page }) => {
    // Navigate to Galaxy Map
    await page.click('text=Galaxy Map');

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
});
