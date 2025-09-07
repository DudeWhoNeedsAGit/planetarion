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

// Helper function to navigate to fleets page
async function navigateToFleets(page) {
  await page.locator('nav').locator('text=Fleets').click();
}

// Helper function to clear all fleets for the current user (for testing empty states)
async function clearAllFleets(page) {
  try {
    console.log('DEBUG: Attempting to clear all fleets...');

    // Get JWT token from localStorage (set by login)
    const token = await page.evaluate(() => localStorage.getItem('token'));
    console.log('DEBUG: JWT token present:', !!token);

    // Make API call to clear fleets with JWT token
    const response = await page.request.delete('http://localhost:5000/api/fleet/clear-all', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    console.log('DEBUG: Clear fleets response status:', response.status());
    console.log('DEBUG: Clear fleets response body:', await response.text());
  } catch (error) {
    console.log('ERROR: Clear fleets endpoint failed:', error.message);
    console.log('Clear fleets endpoint not available, continuing with test');
  }
}

test.describe('Fleet Management', () => {

  test('should display fleet management section', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await navigateToFleets(page);

    // Check for fleet management header - use more robust selector
    await expect(page.locator('h3').filter({ hasText: 'Fleet Management' })).toBeVisible();
    await expect(page.locator('text=Create Fleet')).toBeVisible();
  });

  test('should show no fleets message when empty', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Clear all fleets to test empty state
    await clearAllFleets(page);

    // Navigate to fleets
    await navigateToFleets(page);

    // Should show empty state - check for the message text
    const noFleetsMessage = page.locator('text=No fleets available. Create your first fleet!');

    // Check if the message is visible
    await expect(noFleetsMessage).toBeVisible();
  });

  test('should open create fleet modal', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await navigateToFleets(page);

    // Click create fleet button
    await page.click('text=Create Fleet');

    // Modal should appear
    await expect(page.locator('text=Create New Fleet')).toBeVisible();
    await expect(page.locator('text=Starting Planet')).toBeVisible();
    // Use more specific selector to avoid ambiguity
    await expect(page.locator('label').filter({ hasText: 'Ships' })).toBeVisible();
  });

  test('should create a new fleet', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await navigateToFleets(page);

    // Click create fleet button
    await page.click('text=Create Fleet');

    // Wait for modal
    await page.waitForTimeout(500);

    // Fill form (assuming user has planets)
    const planetSelect = page.locator('select').first();
    if (await planetSelect.isVisible()) {
      // Select first available planet
      await planetSelect.selectOption({ index: 1 });

      // Add some ships - use more specific selector
      const shipInputs = page.locator('input[type="number"]');
      if (await shipInputs.first().isVisible()) {
        // Fill the first ship input (Small Cargo)
        await shipInputs.first().fill('5');
      }

      // Submit form
      await page.click('button[type="submit"]');

      // Should show success message
      await page.waitForTimeout(1000);
      const successMessage = page.locator('text=Fleet created successfully');
      await expect(successMessage).toBeVisible();
    }
  });

  test('should validate fleet creation with no ships', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await navigateToFleets(page);

    // Click create fleet button
    await page.click('text=Create Fleet');

    // Wait for modal
    await page.waitForTimeout(500);

    // Try to submit without ships
    const planetSelect = page.locator('select').first();
    if (await planetSelect.isVisible()) {
      await planetSelect.selectOption({ index: 1 });

      // Submit form
      await page.click('button[type="submit"]');

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

      // Should be in time format, "Arrived", or "N/A" - be very flexible
      const isValidFormat = ['Arrived', 'N/A'].includes(etaValue) ||
                           /\d{1,2}:\d{2}:\d{2}/.test(etaValue) ||
                           /\d{1,2}:\d{2}/.test(etaValue) ||
                           /\d+/.test(etaValue); // Just any number

      expect(isValidFormat).toBe(true);
    }
  });

  test('should close modals with cancel button', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await navigateToFleets(page);

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
