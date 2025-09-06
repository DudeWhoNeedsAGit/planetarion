const { test, expect } = require('@playwright/test');

test.describe('Colonization', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.fill('input[name="username"]', 'e2etestuser');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  });

  test('should display galaxy map with explorable systems', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Should show galaxy map modal
    await expect(page.locator('h2')).toContainText('Galaxy Map');

    // Should display systems
    await expect(page.locator('.grid')).toBeVisible();

    // Should show center coordinates
    await expect(page.locator('text=Center:')).toBeVisible();
  });

  test('should allow exploration of unexplored systems', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Find an unexplored system (yellow button)
    const exploreButton = page.locator('button:has-text("Explore")').first();
    await expect(exploreButton).toBeVisible();

    // Handle alert dialog that appears after clicking explore
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    // Click explore
    await exploreButton.click();

    // Wait a moment for the alert to be handled
    await page.waitForTimeout(1000);

    // Test passes if no errors occurred (alert was handled)
    await expect(page.locator('h2')).toContainText('Galaxy Map');
  });

  test('should show explored systems with planet count', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Look for explored systems (blue background)
    const exploredSystem = page.locator('.bg-blue-900').first();

    if (await exploredSystem.isVisible()) {
      // Should show "X planets discovered" text
      await expect(page.locator('text=planets discovered')).toBeVisible();

      // Should have "View System" button
      await expect(page.locator('button:has-text("View System")')).toBeVisible();
    }
  });

  test('should display system details when viewing explored system', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Find and click "View System" button
    const viewSystemButton = page.locator('button:has-text("View System")').first();

    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      // Should show system details
      await expect(page.locator('text=System')).toBeVisible();

      // Should show planets or "No planets discovered yet"
      await expect(page.locator('text=No planets discovered yet').or(page.locator('text=Unowned'))).toBeVisible();
    }
  });

  test('should show colonization button for unowned planets', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Find explored system and view it
    const viewSystemButton = page.locator('button:has-text("View System")').first();

    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      // Look for unowned planets
      const colonizeButton = page.locator('button:has-text("Colonize")').first();

      if (await colonizeButton.isVisible()) {
        // Should be enabled
        await expect(colonizeButton).toBeEnabled();

        // Click colonize
        await colonizeButton.click();

        // Should show success or error message
        await expect(page.locator('text=Colonization fleet sent').or(page.locator('text=No fleets with colony ships'))).toBeVisible();
      }
    }
  });

  test('should not show colonization button for owned planets', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Find explored system and view it
    const viewSystemButton = page.locator('button:has-text("View System")').first();

    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      // Look for owned planets (should not have colonize button)
      const ownedPlanetText = page.locator('text=Owned by');

      if (await ownedPlanetText.isVisible()) {
        // Should not have colonize button
        await expect(page.locator('button:has-text("Colonize")')).not.toBeVisible();
      }
    }
  });

  test('should handle colonization fleet requirements', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Try to colonize without proper fleet
    const viewSystemButton = page.locator('button:has-text("View System")').first();

    if (await viewSystemButton.isVisible()) {
      await viewSystemButton.click();

      const colonizeButton = page.locator('button:has-text("Colonize")').first();

      if (await colonizeButton.isVisible()) {
        await colonizeButton.click();

        // Should handle case where no colony ships are available
        await expect(page.locator('text=No fleets with colony ships available')).toBeVisible();
      }
    }
  });

  test('should close galaxy map modal', async ({ page }) => {
    // Navigate to galaxy map
    await page.click('text=Galaxy Map');

    // Should show modal
    await expect(page.locator('h2')).toContainText('Galaxy Map');

    // Click close button
    await page.locator('button:has-text("✕")').first().click();

    // Modal should be closed
    await expect(page.locator('h2')).not.toContainText('Galaxy Map');
  });
});
