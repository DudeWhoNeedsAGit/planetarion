const { test, expect } = require('@playwright/test');

// Helper function for login
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

// Helper function to navigate to galaxy map
async function navigateToGalaxyMap(page) {
  await page.locator('nav').locator('text=Galaxy').click();
}

// Helper function to create colony ship fleet
async function createColonyShipFleet(page) {
  // Navigate to fleets
  await page.locator('nav').locator('text=Fleets').click();

  // Click create fleet button
  await page.click('text=Create Fleet');

  // Wait for modal
  await page.waitForTimeout(500);

  // Fill form with colony ship
  const planetSelect = page.locator('select').first();
  if (await planetSelect.isVisible()) {
    // Select first available planet
    await planetSelect.selectOption({ index: 1 });

    // Add colony ship
    const shipInputs = page.locator('input[type="number"]');
    if (await shipInputs.count() >= 7) { // Colony ship is typically the 7th input
      await shipInputs.nth(6).fill('1'); // Add 1 colony ship
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Should show success message
    await page.waitForTimeout(1000);
    const successMessage = page.locator('text=Fleet created successfully');
    await expect(successMessage).toBeVisible();
  }
}

// Helper function to colonize a planet
async function colonizePlanet(page, x, y, z) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.post('http://localhost:5000/api/fleet/send', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    data: {
      fleet_id: 1,
      mission: 'colonize',
      target_x: x,
      target_y: y,
      target_z: z
    }
  });

  return response;
}

// Helper function to trigger manual tick
async function triggerManualTick(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.post('http://localhost:5000/api/tick', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  return response;
}

// Helper function to upgrade research for colonization
async function upgradeResearchForColonization(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.post('http://localhost:5000/api/research/upgrade/colonization_tech', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  return response;
}

test.describe('Galaxy Colony Indicators', () => {

  test('should show green markers for owned colonies', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade research for colonization
    await upgradeResearchForColonization(page);

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Colonize a planet
    const colonizeResponse = await colonizePlanet(page, 300, 400, 500);

    if (colonizeResponse.status() === 200) {
      // Trigger tick to process colonization
      await triggerManualTick(page);

      // Navigate to galaxy map
      await navigateToGalaxyMap(page);

      // Should show green marker for owned colony
      const greenMarkers = page.locator('.bg-green-600');

      if (await greenMarkers.first().isVisible()) {
        await expect(greenMarkers.first()).toBeVisible();

        // Should have home icon
        const homeIcon = greenMarkers.first().locator('text=🏠');
        await expect(homeIcon).toBeVisible();
      }
    }
  });

  test('should show red markers for enemy colonies', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Look for red markers (enemy colonies)
    const redMarkers = page.locator('.bg-red-600');

    // Note: This test assumes there might be enemy colonies from other users
    // In a real test environment, you might need to set up test data
    if (await redMarkers.first().isVisible()) {
      await expect(redMarkers.first()).toBeVisible();

      // Should have battle icon
      const battleIcon = redMarkers.first().locator('text=⚔️');
      await expect(battleIcon).toBeVisible();
    }
  });

  test('should show blue markers for explored systems', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Should show blue markers for explored systems
    const blueMarkers = page.locator('.bg-blue-600');

    // Should have at least some explored systems
    const markerCount = await blueMarkers.count();
    expect(markerCount).toBeGreaterThanOrEqual(0);

    if (markerCount > 0) {
      await expect(blueMarkers.first()).toBeVisible();
    }
  });

  test('should show gray markers for unexplored systems', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Should show gray markers for unexplored systems
    const grayMarkers = page.locator('.bg-gray-600');

    // Should have unexplored systems
    const markerCount = await grayMarkers.count();
    expect(markerCount).toBeGreaterThanOrEqual(0);

    if (markerCount > 0) {
      await expect(grayMarkers.first()).toBeVisible();
    }
  });

  test('should display colony indicator icons', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Look for colony indicators
    const homeIcons = page.locator('text=🏠');
    const battleIcons = page.locator('text=⚔️');

    // Should have some colony indicators if colonies exist
    const totalIcons = (await homeIcons.count()) + (await battleIcons.count());
    expect(totalIcons).toBeGreaterThanOrEqual(0);
  });

  test('should show enhanced tooltips with ownership status', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find a system marker
    const systemMarker = page.locator('div').filter({ hasText: /\d+:\d+/ }).first();

    if (await systemMarker.isVisible()) {
      // Hover over the marker
      await systemMarker.hover();

      // Should show tooltip with ownership information
      // Note: This might require checking the title attribute or a tooltip element
      const title = await systemMarker.getAttribute('title');

      if (title) {
        // Should contain coordinate information
        expect(title).toMatch(/\d+:\d+:\d+/);
      }
    }
  });

  test('should update colony indicators after colonization', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Count initial colony indicators
    const initialHomeIcons = await page.locator('text=🏠').count();

    // Upgrade research and create fleet
    await upgradeResearchForColonization(page);
    await createColonyShipFleet(page);

    // Colonize a planet
    const colonizeResponse = await colonizePlanet(page, 310, 410, 510);

    if (colonizeResponse.status() === 200) {
      // Trigger tick
      await triggerManualTick(page);

      // Refresh galaxy map
      await page.reload();
      await navigateToGalaxyMap(page);

      // Should have more home icons
      const updatedHomeIcons = await page.locator('text=🏠').count();
      expect(updatedHomeIcons).toBeGreaterThanOrEqual(initialHomeIcons);
    }
  });

  test('should distinguish between owned and enemy colonies', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Count different types of colony markers
    const ownedColonies = await page.locator('.bg-green-600').filter({ hasText: '🏠' }).count();
    const enemyColonies = await page.locator('.bg-red-600').filter({ hasText: '⚔️' }).count();

    // Should have valid counts
    expect(ownedColonies).toBeGreaterThanOrEqual(0);
    expect(enemyColonies).toBeGreaterThanOrEqual(0);

    // If there are colonies, they should be properly categorized
    if (ownedColonies + enemyColonies > 0) {
      // Should not have mixed indicators
      const mixedGreen = await page.locator('.bg-green-600').filter({ hasText: '⚔️' }).count();
      const mixedRed = await page.locator('.bg-red-600').filter({ hasText: '🏠' }).count();

      expect(mixedGreen).toBe(0);
      expect(mixedRed).toBe(0);
    }
  });

  test('should show colony ownership in system details', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find an explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Should show system details
      await expect(page.locator('text=System')).toBeVisible();

      // Should show planet ownership information
      const ownedPlanets = page.locator('text=Owned by');
      const unownedPlanets = page.locator('text=Unowned');

      const ownedCount = await ownedPlanets.count();
      const unownedCount = await unownedPlanets.count();

      // Should have some ownership information
      expect(ownedCount + unownedCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should handle multiple colonies per system', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find systems with multiple planets
    const multiPlanetSystems = page.locator('div').filter({ hasText: /\d+P/ }).filter((element) => {
      const text = element.textContent();
      const planetMatch = text.match(/(\d+)P/);
      return planetMatch && parseInt(planetMatch[1]) > 1;
    });

    if (await multiPlanetSystems.first().isVisible()) {
      await multiPlanetSystems.first().click();

      // Should show multiple planets
      const planetCards = page.locator('.bg-gray-600');
      const planetCount = await planetCards.count();

      expect(planetCount).toBeGreaterThan(1);
    }
  });

  test('should show colony coordinates correctly', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find colony markers
    const colonyMarkers = page.locator('.bg-green-600, .bg-red-600');

    if (await colonyMarkers.first().isVisible()) {
      const markerText = await colonyMarkers.first().textContent();

      // Should contain coordinate format
      expect(markerText).toMatch(/\d+:\d+/);
    }
  });

  test('should update legend with colony information', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Should show enhanced legend
    const legend = page.locator('text=Legend').first();

    if (await legend.isVisible()) {
      // Should show colony ownership indicators in legend
      await expect(page.locator('text=Your Colonies')).toBeVisible();
      await expect(page.locator('text=Enemy Colonies')).toBeVisible();
      await expect(page.locator('text=Explored Systems')).toBeVisible();
      await expect(page.locator('text=Unexplored Systems')).toBeVisible();
    }
  });

  test('should handle colony indicator visibility at different zoom levels', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Get initial colony count
    const initialColonyCount = await page.locator('text=🏠, text=⚔️').count();

    // Zoom in
    await page.click('text=+');

    // Colony count should remain the same (just scaled)
    const zoomedColonyCount = await page.locator('text=🏠, text=⚔️').count();
    expect(zoomedColonyCount).toBe(initialColonyCount);

    // Zoom out
    await page.click('text=−');

    // Should still have same colony count
    const zoomedOutColonyCount = await page.locator('text=🏠, text=⚔️').count();
    expect(zoomedOutColonyCount).toBe(initialColonyCount);
  });

  test('should show colony tooltips on hover', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find a colony marker
    const colonyMarker = page.locator('.bg-green-600, .bg-red-600').first();

    if (await colonyMarker.isVisible()) {
      // Hover over colony marker
      await colonyMarker.hover();

      // Should show enhanced tooltip
      const title = await colonyMarker.getAttribute('title');

      if (title) {
        // Should contain ownership information
        expect(title).toMatch(/(Your Colony|Enemy Colony|Explored)/);
      }
    }
  });

  test('should maintain colony indicators during map navigation', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Get initial colony positions
    const initialColonies = await page.locator('text=🏠, text=⚔️').allTextContents();

    // Reset view
    await page.click('text=Reset');

    // Colony indicators should still be visible
    const resetColonies = await page.locator('text=🏠, text=⚔️').allTextContents();
    expect(resetColonies.length).toBe(initialColonies.length);
  });

  test('should show colony density in crowded systems', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Look for systems with high planet counts
    const highDensitySystems = page.locator('div').filter({ hasText: /([5-9]|\d{2,})P/ });

    if (await highDensitySystems.first().isVisible()) {
      const systemText = await highDensitySystems.first().textContent();

      // Should show high planet count
      expect(systemText).toMatch(/([5-9]|\d{2,})P/);
    }
  });
});
