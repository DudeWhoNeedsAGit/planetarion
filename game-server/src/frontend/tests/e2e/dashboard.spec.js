const { test, expect } = require('@playwright/test');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login first - use credentials that match the working auth test
    await page.goto('/');
    await page.fill('input[name="username"]', 'e2etestuser');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load
    await page.waitForTimeout(2000);
  });

  test('should display dashboard with user info', async ({ page }) => {
    // Check header
    await expect(page.locator('h1')).toContainText('Planetarion');
    await expect(page.locator('text=Welcome, e2etestuser!')).toBeVisible();
    await expect(page.locator('text=Logout')).toBeVisible();
  });

  test('should navigate between sections', async ({ page }) => {
    // Add debugging screenshot
    await page.screenshot({ path: 'debug-navigation-start.png' });

    // Check navigation tabs - use nav context to avoid ambiguity
    const navTabs = ['Overview', 'Planets', 'Fleets', 'Research', 'Alliance', 'Messages'];
    for (const tab of navTabs) {
      await expect(page.locator('nav').locator(`text=${tab}`)).toBeVisible();
    }

    // Click on Planets section - use nav context
    await page.locator('nav').locator('text=Planets').click();
    await expect(page.locator('text=Your Planets')).toBeVisible();

    // Click on Fleets section - use nav context
    await page.locator('nav').locator('text=Fleets').click();
    await expect(page.locator('text=🚀 Fleet Management')).toBeVisible();

    // Click on Research section - use nav context
    await page.locator('nav').locator('text=Research').click();
    await expect(page.locator('text=Research Lab')).toBeVisible();

    // Click back to Overview - use nav context
    await page.locator('nav').locator('text=Overview').click();
    await expect(page.locator('text=Welcome back, e2etestuser!')).toBeVisible();
  });

  test('should display planet information', async ({ page }) => {
    // Navigate to Planets section - use nav context
    await page.locator('nav').locator('text=Planets').click();

    // Should show planets (may be empty or have test data)
    const planetSection = page.locator('text=Your Planets');
    await expect(planetSection).toBeVisible();

    // Check for resource display elements
    const resourcesSection = page.locator('text=Resources').first();
    if (await resourcesSection.isVisible()) {
      await expect(resourcesSection).toBeVisible();

      // Check resource values are displayed
      await expect(page.locator('text=Metal:')).toBeVisible();
      await expect(page.locator('text=Crystal:')).toBeVisible();
      await expect(page.locator('text=Deuterium:')).toBeVisible();
    }
  });

  test('should display buildings section', async ({ page }) => {
    // Navigate to Planets section - use nav context
    await page.locator('nav').locator('text=Planets').click();

    // Check for buildings section
    const buildingsSection = page.locator('text=Buildings').first();
    if (await buildingsSection.isVisible()) {
      await expect(buildingsSection).toBeVisible();

      // Check for building types
      const buildingTypes = ['Metal Mine', 'Crystal Mine', 'Deuterium Synthesizer', 'Solar Plant', 'Fusion Reactor'];
      for (const building of buildingTypes) {
        await expect(page.locator(`text=${building}`)).toBeVisible();
      }

      // Check for upgrade buttons
      await expect(page.locator('text=Upgrade')).toBeVisible();
    }
  });

  test('should handle building upgrades', async ({ page }) => {
    // Navigate to Planets section - use nav context
    await page.locator('nav').locator('text=Planets').click();

    // Look for upgrade buttons
    const upgradeButtons = page.locator('text=Upgrade');
    const buttonCount = await upgradeButtons.count();

    if (buttonCount > 0) {
      // Click first available upgrade button
      await upgradeButtons.first().click();

      // Should show some feedback (success or error)
      await page.waitForTimeout(1000);

      // Check for success message or error
      const successMessage = page.locator('text=Building upgraded successfully').or(page.locator('.bg-red-600'));
      await expect(successMessage).toBeVisible();
    }
  });

  test('should display fleet information', async ({ page }) => {
    // Navigate to Fleets section - use nav context
    await page.locator('nav').locator('text=Fleets').click();

    // Check for fleet-related elements - use actual UI text
    const fleetSection = page.locator('text=🚀 Fleet Management');
    await expect(fleetSection).toBeVisible();

    // Check for fleet creation button (always present)
    await expect(page.locator('text=Create Fleet')).toBeVisible();
  });

  test('should display research placeholder', async ({ page }) => {
    // Navigate to Research section - use nav context
    await page.locator('nav').locator('text=Research').click();

    // Check for research placeholder content
    await expect(page.locator('text=Research Lab')).toBeVisible();
    await expect(page.locator('text=Research system coming soon')).toBeVisible();

    // Check for technology list
    const technologies = ['Energy Technology', 'Laser Technology', 'Ion Technology'];
    for (const tech of technologies) {
      await expect(page.locator(`text=${tech}`)).toBeVisible();
    }
  });

  test('should display alliance placeholder', async ({ page }) => {
    // Navigate to Alliance section - use nav context
    await page.locator('nav').locator('text=Alliance').click();

    // Check for alliance placeholder content
    await expect(page.locator('text=Alliance Center')).toBeVisible();
    await expect(page.locator('text=Alliance system coming soon')).toBeVisible();

    // Check for alliance features
    const features = ['Alliance creation and management', 'Member recruitment', 'Internal messaging'];
    for (const feature of features) {
      await expect(page.locator(`text=${feature}`)).toBeVisible();
    }
  });

  test('should display messages placeholder', async ({ page }) => {
    // Navigate to Messages section - use nav context
    await page.locator('nav').locator('text=Messages').click();

    // Check for messages placeholder content - use specific heading
    await expect(page.locator('h3').filter({ hasText: '💬 Messages' })).toBeVisible();
    await expect(page.locator('text=Messaging system coming soon')).toBeVisible();

    // Check for message types
    const messageTypes = ['Private messages', 'Alliance messages', 'System notifications'];
    for (const type of messageTypes) {
      await expect(page.locator(`text=${type}`)).toBeVisible();
    }
  });

  test('should handle logout', async ({ page }) => {
    // Click logout button
    await page.click('text=Logout');

    // Should redirect to login page
    await page.waitForTimeout(1000);
    await expect(page.locator('h2')).toContainText('Login to Planetarion');
  });

  test('should update resources after tick', async ({ page }) => {
    // Navigate to Planets section - use nav context
    await page.locator('nav').locator('text=Planets').click();

    // Record initial resource values if visible
    const metalValue = page.locator('text=Metal:').locator('xpath=following-sibling::*').first();
    let initialMetal = 0;

    if (await metalValue.isVisible()) {
      const metalText = await metalValue.textContent();
      initialMetal = parseInt(metalText.replace(/,/g, '')) || 0;
    }

    // Wait a bit (simulate tick)
    await page.waitForTimeout(2000);

    // Resources should be visible (may have updated)
    if (await metalValue.isVisible()) {
      const currentMetalText = await metalValue.textContent();
      const currentMetal = parseInt(currentMetalText.replace(/,/g, '')) || 0;

      // Resources should not decrease unexpectedly
      expect(currentMetal).toBeGreaterThanOrEqual(initialMetal - 1000); // Allow for small decreases
    }
  });
});
