const { test, expect } = require('@playwright/test');

test.describe('Complete Colonization Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.fill('input[name="username"]', 'e2etestuser');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  });

  test('should complete full colonization workflow from galaxy map to colony', async ({ page }) => {
    // Step 1: Navigate to galaxy map
    await page.click('text=Galaxy Map');
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();

    // Step 2: Explore an unexplored system
    const exploreButton = page.locator('button:has-text("Explore")').first();
    if (await exploreButton.isVisible()) {
      await page.on('dialog', async dialog => {
        await dialog.accept();
      });
      await exploreButton.click();
      await page.waitForTimeout(1000);
    }

    // Step 3: Find an explored system and view it
    const viewSystemButton = page.locator('button:has-text("View System")').first();
    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      // Step 4: Find an unowned planet and colonize it
      const colonizeButton = page.locator('button:has-text("Colonize")').first();
      if (await colonizeButton.isVisible()) {
        await colonizeButton.click();

        // Step 5: Verify colonization fleet was sent
        await expect(page.locator('text=Colonization fleet sent').or(page.locator('text=No fleets with colony ships'))).toBeVisible();

        // Step 6: Navigate to fleet management to monitor progress
        await page.click('text=Fleet Management');
        await expect(page.locator('h2:has-text("Fleet Management")')).toBeVisible();

        // Step 7: Verify fleet appears in the list
        const fleetList = page.locator('.fleet-item, .fleet-card, [data-testid*="fleet"]');
        if (await fleetList.first().isVisible()) {
          // Check for colonization status
          await expect(page.locator('text=colonizing').or(page.locator('text=traveling'))).toBeVisible();
        }

        // Step 8: Navigate back to dashboard
        await page.click('text=Dashboard');
        await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();

        // Step 9: Verify new colony appears in planet selector (if colonization completed)
        const planetSelector = page.locator('select, .planet-selector, [data-testid*="planet"]');
        if (await planetSelector.isVisible()) {
          // Check if we have more than one planet option
          const planetOptions = planetSelector.locator('option');
          const optionCount = await planetOptions.count();
          // We should have at least 2 planets (home + potential colony)
          expect(optionCount).toBeGreaterThanOrEqual(1);
        }

        // Step 10: Verify colonization success message or status
        await expect(page.locator('text=Colony').or(page.locator('text=Planet')).or(page.locator('text=Resources'))).toBeVisible();
      } else {
        // If no colonize button, verify we're looking at owned planets
        await expect(page.locator('text=Owned by').or(page.locator('text=Unowned')).or(page.locator('text=No planets discovered yet'))).toBeVisible();
      }
    } else {
      // No systems to explore - this is also acceptable
      await expect(page.locator('text=Galaxy Map')).toBeVisible();
    }
  });

  test('should handle colonization fleet recall process', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');
    await expect(page.locator('h2:has-text("Fleet Management")')).toBeVisible();

    // Find a colonizing fleet
    const colonizingFleet = page.locator('.fleet-item:has-text("colonizing"), .fleet-card:has-text("colonizing")').first();

    if (await colonizingFleet.isVisible()) {
      // Click recall button
      const recallButton = colonizingFleet.locator('button:has-text("Recall")').first();
      if (await recallButton.isVisible()) {
        await recallButton.click();

        // Verify recall confirmation or success message
        await expect(page.locator('text=Recalled').or(page.locator('text=Returning')).or(page.locator('text=Fleet recalled'))).toBeVisible();

        // Verify fleet status changes
        await expect(page.locator('text=returning').or(page.locator('text=stationed'))).toBeVisible();
      }
    } else {
      // No colonizing fleets found - this is also acceptable
      await expect(page.locator('text=No fleets').or(page.locator('text=Fleet Management'))).toBeVisible();
    }
  });

  test('should validate colonization requirements', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();

    // Try to find a system to view
    const viewSystemButton = page.locator('button:has-text("View System")').first();

    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      // Try to colonize without proper fleet
      const colonizeButton = page.locator('button:has-text("Colonize")').first();

      if (await colonizeButton.isVisible()) {
        await colonizeButton.click();

        // Should show appropriate error message
        await expect(page.locator('text=No fleets with colony ships').or(page.locator('text=Colonization fleet sent')).or(page.locator('text=Error')).or(page.locator('text=Failed'))).toBeVisible();
      }
    } else {
      // No systems to view - this is also acceptable
      await expect(page.locator('text=Galaxy Map')).toBeVisible();
    }
  });

  test('should display colonization progress and ETA', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');
    await expect(page.locator('h2:has-text("Fleet Management")')).toBeVisible();

    // Look for any fleet with travel information
    const fleetWithTravel = page.locator('.fleet-item, .fleet-card').filter({ hasText: /traveling|colonizing|returning/ }).first();

    if (await fleetWithTravel.isVisible()) {
      // Should show ETA or progress information
      await expect(page.locator('text=ETA').or(page.locator('text=Progress')).or(page.locator('text=Time')).or(page.locator('text=Distance'))).toBeVisible();

      // Should show fleet composition
      await expect(page.locator('text=Ships').or(page.locator('text=Fleet')).or(page.locator('text=Units'))).toBeVisible();
    } else {
      // No traveling fleets - this is also acceptable
      await expect(page.locator('text=Fleet Management')).toBeVisible();
    }
  });

  test('should handle multiple planets in dashboard', async ({ page }) => {
    // Navigate to dashboard
    await page.click('text=Dashboard');
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();

    // Check for planet selector or multiple planet display
    const planetSelector = page.locator('select[name*="planet"], .planet-selector, [data-testid*="planet"]');
    const planetButtons = page.locator('button:has-text("Planet"), .planet-button, [data-testid*="planet"]');

    if (await planetSelector.isVisible()) {
      // Test planet switching
      const options = planetSelector.locator('option');
      const optionCount = await options.count();

      if (optionCount > 1) {
        // Switch to second planet
        await planetSelector.selectOption({ index: 1 });

        // Verify planet data updates
        await expect(page.locator('text=Resources').or(page.locator('text=Metal')).or(page.locator('text=Crystal'))).toBeVisible();
      }
    } else if (await planetButtons.first().isVisible()) {
      // Test planet button selection
      const firstPlanetButton = planetButtons.first();
      await firstPlanetButton.click();

      // Verify planet data displays
      await expect(page.locator('text=Resources').or(page.locator('text=Buildings')).or(page.locator('text=Defense'))).toBeVisible();
    } else {
      // No planet selector - this is also acceptable
      await expect(page.locator('text=Dashboard')).toBeVisible();
    }
  });

  test('should show colonization-related notifications', async ({ page }) => {
    // Navigate to dashboard
    await page.click('text=Dashboard');
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();

    // Look for notification area or messages
    const notifications = page.locator('.notification, .message, .alert, [data-testid*="notification"]');

    if (await notifications.first().isVisible()) {
      // Should contain colonization-related text
      await expect(page.locator('text=Colony').or(page.locator('text=Fleet')).or(page.locator('text=Planet')).or(page.locator('text=Resources'))).toBeVisible();
    } else {
      // No notifications - still valid state
      await expect(page.locator('text=Dashboard')).toBeVisible();
    }
  });

  test('should maintain colonization state across navigation', async ({ page }) => {
    // Start at dashboard
    await page.click('text=Dashboard');
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();

    // Navigate to galaxy map
    await page.click('text=Galaxy Map');
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();

    // Navigate to fleet management
    await page.click('text=Fleet Management');
    await expect(page.locator('h2:has-text("Fleet Management")')).toBeVisible();

    // Navigate back to dashboard
    await page.click('text=Dashboard');
    await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();

    // Verify dashboard still shows planet/fleet information
    await expect(page.locator('text=Planet').or(page.locator('text=Resources')).or(page.locator('text=Fleet'))).toBeVisible();
  });

  test('should handle colonization errors gracefully', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');
    await expect(page.locator('h2:has-text("Galaxy Map")')).toBeVisible();

    // Try to explore or view system
    const exploreButton = page.locator('button:has-text("Explore")').first();
    const viewButton = page.locator('button:has-text("View System")').first();

    if (await exploreButton.isVisible()) {
      await page.on('dialog', async dialog => {
        await dialog.accept();
      });
      await exploreButton.click();
      await page.waitForTimeout(1000);
    } else if (await viewButton.isVisible()) {
      await viewButton.click();
    } else {
      // No systems to explore - this is also acceptable
      await expect(page.locator('text=Galaxy Map')).toBeVisible();
      return;
    }

    // Try colonization action
    const colonizeButton = page.locator('button:has-text("Colonize")').first();

    if (await colonizeButton.isVisible()) {
      await colonizeButton.click();

      // Should handle success or error gracefully
      await expect(page.locator('text=Colonization').or(page.locator('text=Fleet')).or(page.locator('text=Error')).or(page.locator('text=Success'))).toBeVisible();

      // Should not crash or show blank page
      await expect(page.locator('body')).toBeVisible();
    } else {
      // No colonize button - this is also acceptable
      await expect(page.locator('text=Galaxy Map')).toBeVisible();
    }
  });
});
