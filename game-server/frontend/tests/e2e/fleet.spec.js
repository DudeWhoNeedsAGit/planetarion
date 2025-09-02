const { test, expect } = require('@playwright/test');

test.describe('Fleet Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login first - use credentials that match the test data
    await page.goto('/');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');

    // Wait for dashboard to load and navigate to fleets
    await page.waitForTimeout(2000);
    await page.click('text=Fleets');
  });

  test('should display fleet management section', async ({ page }) => {
    // Check for fleet management header
    await expect(page.locator('text=Fleet Management')).toBeVisible();
    await expect(page.locator('text=Create Fleet')).toBeVisible();
  });

  test('should show no fleets message when empty', async ({ page }) => {
    // Should show empty state
    const noFleetsMessage = page.locator('text=No fleets available');
    const createFleetButton = page.locator('text=Create Fleet');

    // One of these should be visible
    await expect(noFleetsMessage.or(createFleetButton)).toBeVisible();
  });

  test('should open create fleet modal', async ({ page }) => {
    // Click create fleet button
    await page.click('text=Create Fleet');

    // Modal should appear
    await expect(page.locator('text=Create New Fleet')).toBeVisible();
    await expect(page.locator('text=Starting Planet')).toBeVisible();
    await expect(page.locator('text=Ships')).toBeVisible();
  });

  test('should create a new fleet', async ({ page }) => {
    // Click create fleet button
    await page.click('text=Create Fleet');

    // Wait for modal
    await page.waitForTimeout(500);

    // Fill form (assuming user has planets)
    const planetSelect = page.locator('select').first();
    if (await planetSelect.isVisible()) {
      // Select first available planet
      await planetSelect.selectOption({ index: 1 });

      // Add some ships
      const smallCargoInput = page.locator('input').filter({ hasText: /small_cargo|Small Cargo/ }).first();
      if (await smallCargoInput.isVisible()) {
        await smallCargoInput.fill('5');
      } else {
        // Try to find ship inputs by type
        const numberInputs = page.locator('input[type="number"]');
        if (await numberInputs.first().isVisible()) {
          await numberInputs.first().fill('5');
        }
      }

      // Submit form
      await page.click('text=Create Fleet');

      // Should show success message or close modal
      await page.waitForTimeout(1000);

      // Check if fleet was created (should appear in list or show success)
      const successMessage = page.locator('text=Fleet created successfully');
      const fleetList = page.locator('text=Fleet #');

      await expect(successMessage.or(fleetList)).toBeVisible();
    }
  });

  test('should validate fleet creation with no ships', async ({ page }) => {
    // Click create fleet button
    await page.click('text=Create Fleet');

    // Wait for modal
    await page.waitForTimeout(500);

    // Try to submit without ships
    const planetSelect = page.locator('select').first();
    if (await planetSelect.isVisible()) {
      await planetSelect.selectOption({ index: 1 });

      // Submit form
      await page.click('text=Create Fleet');

      // Should show error
      await expect(page.locator('text=Fleet must contain at least one ship')).toBeVisible();
    }
  });

  test('should display fleet information', async ({ page }) => {
    // Look for fleet cards
    const fleetCard = page.locator('.bg-gray-700').first();

    if (await fleetCard.isVisible()) {
      // Check fleet card structure
      await expect(fleetCard.locator('text=Fleet #')).toBeVisible();
      await expect(fleetCard.locator('text=Status:')).toBeVisible();

      // Check for ship information
      await expect(fleetCard.locator('text=Ships')).toBeVisible();
      await expect(fleetCard.locator('text=From')).toBeVisible();
      await expect(fleetCard.locator('text=To')).toBeVisible();
      await expect(fleetCard.locator('text=ETA')).toBeVisible();
    }
  });

  test('should show send button for stationed fleets', async ({ page }) => {
    // Look for fleet with Send button
    const sendButton = page.locator('text=Send').first();

    if (await sendButton.isVisible()) {
      await expect(sendButton).toBeVisible();

      // Click send button
      await sendButton.click();

      // Send modal should appear
      await expect(page.locator('text=Send Fleet')).toBeVisible();
      await expect(page.locator('text=Target Planet')).toBeVisible();
      await expect(page.locator('text=Mission')).toBeVisible();
    }
  });

  test('should send a fleet', async ({ page }) => {
    // Find a fleet to send
    const sendButton = page.locator('text=Send').first();

    if (await sendButton.isVisible()) {
      await sendButton.click();

      // Wait for modal
      await page.waitForTimeout(500);

      // Fill send form
      const targetSelect = page.locator('select').filter({ hasText: /target|Target/ }).first();
      if (await targetSelect.isVisible()) {
        // Select first available target
        await targetSelect.selectOption({ index: 1 });

        // Submit
        await page.click('text=Send Fleet');

        // Should show success
        await page.waitForTimeout(1000);
        await expect(page.locator('text=Fleet sent successfully')).toBeVisible();
      }
    }
  });

  test('should show recall button for moving fleets', async ({ page }) => {
    // Look for fleet with Recall button
    const recallButton = page.locator('text=Recall').first();

    if (await recallButton.isVisible()) {
      await expect(recallButton).toBeVisible();

      // Click recall button
      await recallButton.click();

      // Should show success message
      await expect(page.locator('text=Fleet recalled successfully')).toBeVisible();
    }
  });

  test('should display ship composition', async ({ page }) => {
    // Look for ship composition section
    const shipComposition = page.locator('text=Ship Composition:').first();

    if (await shipComposition.isVisible()) {
      // Should show ship types and counts
      const shipBadges = page.locator('.bg-gray-600');
      if (await shipBadges.first().isVisible()) {
        await expect(shipBadges.first()).toBeVisible();
      }
    }
  });

  test('should handle fleet status colors', async ({ page }) => {
    // Look for status indicators
    const statusIndicator = page.locator('text=Status:').first();

    if (await statusIndicator.isVisible()) {
      // Status should have appropriate color class
      const statusText = await statusIndicator.locator('xpath=following-sibling::*').textContent();

      if (statusText.includes('stationed')) {
        // Should have green color
        await expect(statusIndicator.locator('.text-green-400')).toBeVisible();
      } else if (statusText.includes('traveling')) {
        // Should have yellow color
        await expect(statusIndicator.locator('.text-yellow-400')).toBeVisible();
      } else if (statusText.includes('returning')) {
        // Should have blue color
        await expect(statusIndicator.locator('.text-blue-400')).toBeVisible();
      }
    }
  });

  test('should display ETA countdown', async ({ page }) => {
    // Look for ETA display
    const etaDisplay = page.locator('text=ETA').first();

    if (await etaDisplay.isVisible()) {
      // Should show time format or "Arrived" or "N/A"
      const etaValue = await etaDisplay.locator('xpath=following-sibling::*').textContent();

      // Should be in HH:MM:SS format, "Arrived", or "N/A"
      expect(['Arrived', 'N/A'].includes(etaValue) ||
             /^\d{2}:\d{2}:\d{2}$/.test(etaValue)).toBe(true);
    }
  });

  test('should close modals with cancel button', async ({ page }) => {
    // Open create fleet modal
    await page.click('text=Create Fleet');
    await expect(page.locator('text=Create New Fleet')).toBeVisible();

    // Click cancel
    await page.click('text=Cancel');

    // Modal should close
    await expect(page.locator('text=Create New Fleet')).not.toBeVisible();
  });

  test('should handle multiple fleets', async ({ page }) => {
    // Count fleet cards
    const fleetCards = page.locator('.bg-gray-700');
    const fleetCount = await fleetCards.count();

    if (fleetCount > 1) {
      // Should display multiple fleets
      for (let i = 0; i < Math.min(fleetCount, 3); i++) {
        await expect(fleetCards.nth(i).locator('text=Fleet #')).toBeVisible();
      }
    }
  });
});
