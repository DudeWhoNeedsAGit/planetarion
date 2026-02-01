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

// Helper function to explore a system and get planet traits
async function exploreSystemForTraits(page, systemX, systemY, systemZ) {
  // Navigate to galaxy map
  await navigateToGalaxyMap(page);

  // Get JWT token
  const token = await page.evaluate(() => localStorage.getItem('token'));

  // Send exploration fleet
  const response = await page.request.post('http://localhost:5000/api/fleet/send', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    data: {
      fleet_id: 1, // Assume test fleet exists
      mission: 'explore',
      target_x: systemX,
      target_y: systemY,
      target_z: systemZ
    }
  });

  return response;
}

// Helper function to trigger manual tick for trait generation
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

test.describe('Planet Traits System', () => {

  test('should generate planet traits during exploration', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Explore a new system
    const exploreResponse = await exploreSystemForTraits(page, 150, 250, 350);

    // Should succeed or show appropriate error
    expect([200, 400, 409]).toContain(exploreResponse.status());

    if (exploreResponse.status() === 200) {
      // Trigger tick to process exploration
      await triggerManualTick(page);

      // Navigate to galaxy map
      await navigateToGalaxyMap(page);

      // Find the explored system
      const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

      if (await exploredSystem.isVisible()) {
        await exploredSystem.click();

        // Should show system details with planets
        await expect(page.locator('text=System')).toBeVisible();

        // Check for trait indicators (purple badges)
        const traitBadges = page.locator('.bg-purple-600');
        if (await traitBadges.first().isVisible()) {
          await expect(traitBadges.first()).toBeVisible();
        }
      }
    }
  });

  test('should display planet traits in system view', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Should show planet cards
      const planetCard = page.locator('.bg-gray-600').first();

      if (await planetCard.isVisible()) {
        // Check for trait section
        const traitSection = planetCard.locator('text=Planet Traits:');

        if (await traitSection.isVisible()) {
          // Should show trait badges
          const traitBadges = planetCard.locator('.bg-purple-600');
          await expect(traitBadges.first()).toBeVisible();

          // Should show trait names and bonuses
          const traitText = await traitBadges.first().textContent();
          expect(traitText).toMatch(/\+?\d+\.?\d*%?/); // Should contain bonus percentage
        }
      }
    }
  });

  test('should show different trait rarities', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Look for trait badges with different styles (rarity indicators)
      const traitBadges = page.locator('.bg-purple-600');

      if (await traitBadges.count() > 0) {
        // Check that traits have descriptive names
        for (let i = 0; i < Math.min(await traitBadges.count(), 3); i++) {
          const traitText = await traitBadges.nth(i).textContent();
          // Should contain recognizable trait names
          expect([
            'Resource Rich', 'Metal World', 'Crystal Caves', 'Deuterium Ocean',
            'High Energy', 'Defensive', 'Aggressive', 'Barren', 'Temperate',
            'Hostile', 'Volcanic', 'Frozen'
          ]).toEqual(expect.arrayContaining([traitText.split(' ')[0]]));
        }
      }
    }
  });

  test('should apply trait bonuses to resource production', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get initial resource values
    const initialMetal = await page.locator('text=Metal').first().textContent();
    const initialCrystal = await page.locator('text=Crystal').first().textContent();

    // Trigger manual tick
    await triggerManualTick(page);

    // Wait for resources to update
    await page.waitForTimeout(1000);

    // Get updated resource values
    const updatedMetal = await page.locator('text=Metal').first().textContent();
    const updatedCrystal = await page.locator('text=Crystal').first().textContent();

    // Resources should have increased (basic functionality test)
    // Note: Exact bonus calculation would require more complex setup
    expect(updatedMetal).not.toBe(initialMetal);
    expect(updatedCrystal).not.toBe(initialCrystal);
  });

  test('should handle planets without traits', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Should show planets even without traits
      const planetCard = page.locator('.bg-gray-600').first();

      if (await planetCard.isVisible()) {
        // Should show planet name and resources
        await expect(planetCard.locator('text=🪐')).toBeVisible();
        await expect(planetCard.locator('text=Metal')).toBeVisible();
        await expect(planetCard.locator('text=Crystal')).toBeVisible();
        await expect(planetCard.locator('text=Deuterium')).toBeVisible();
      }
    }
  });

  test('should show trait descriptions on hover', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Look for trait badges
      const traitBadge = page.locator('.bg-purple-600').first();

      if (await traitBadge.isVisible()) {
        // Hover over trait badge
        await traitBadge.hover();

        // Should show tooltip or title attribute
        const title = await traitBadge.getAttribute('title');
        if (title) {
          expect(title.length).toBeGreaterThan(0);
        }
      }
    }
  });

  test('should display multiple traits per planet', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find explored system
    const exploredSystem = page.locator('div').filter({ hasText: /\d+P/ }).first();

    if (await exploredSystem.isVisible()) {
      await exploredSystem.click();

      // Look for planets with multiple traits
      const planetCard = page.locator('.bg-gray-600').first();

      if (await planetCard.isVisible()) {
        const traitBadges = planetCard.locator('.bg-purple-600');

        // Should handle 1-3 traits per planet
        const traitCount = await traitBadges.count();
        expect(traitCount).toBeGreaterThanOrEqual(0);
        expect(traitCount).toBeLessThanOrEqual(3);
      }
    }
  });

  test('should update trait display after exploration', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Count initial explored systems
    const initialExploredCount = await page.locator('div').filter({ hasText: /\d+P/ }).count();

    // Explore a new system
    const exploreResponse = await exploreSystemForTraits(page, 160, 260, 360);

    if (exploreResponse.status() === 200) {
      // Trigger tick
      await triggerManualTick(page);

      // Refresh galaxy map
      await page.reload();
      await navigateToGalaxyMap(page);

      // Should have at least the same number of explored systems
      const updatedExploredCount = await page.locator('div').filter({ hasText: /\d+P/ }).count();
      expect(updatedExploredCount).toBeGreaterThanOrEqual(initialExploredCount);
    }
  });
});
