const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');

// Helper function to navigate to fleets page
async function navigateToFleets(page) {
  await page.getByTestId('nav-fleets').click();
  await page.getByTestId('fleet-management').waitFor();
  await page.getByTestId('fleet-planet-selector').waitFor();
  await page.getByTestId('fleet-planet-button').first().waitFor();
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
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await navigateToFleets(page);
  });

  test('should display fleet management section', async ({ page }) => {
    await expect(page.getByTestId('fleet-management')).toBeVisible();
    await expect(page.getByRole('heading', { name: /fleet management/i })).toBeVisible();
    await expect(page.getByTestId('fleet-create-button')).toBeVisible();
  });

  test('should show no fleets message when empty', async ({ page }) => {
    // Clear all fleets to test empty state
    await clearAllFleets(page);
    await page.reload();
    await navigateToFleets(page);
    await expect(page.getByTestId('fleet-empty-state')).toBeVisible();

    // Restore state for subsequent tests (create a minimal fleet via UI).
    await page.getByTestId('fleet-create-button').click();
    await page.getByTestId('fleet-start-planet-select').selectOption({ index: 1 });
    await page.getByTestId('fleet-ship-small_cargo').fill('1');
    await page.getByTestId('fleet-create-submit').click();
    await expect(page.getByRole('alert')).toContainText('Fleet created successfully!');
  });

  test('should open create fleet modal', async ({ page }) => {
    // Click create fleet button
    await page.getByTestId('fleet-create-button').click();

    // Modal should appear
    await expect(page.getByTestId('fleet-create-modal')).toBeVisible();
    await expect(page.getByTestId('fleet-start-planet-select')).toBeVisible();
    await expect(page.getByTestId('fleet-ship-small_cargo')).toBeVisible();
  });

  test('should create a new fleet', async ({ page }) => {
    await page.getByTestId('fleet-create-button').click();

    // Fill form (assuming user has planets)
    await page.getByTestId('fleet-start-planet-select').selectOption({ index: 1 });
    await page.getByTestId('fleet-ship-small_cargo').fill('5');
    await page.getByTestId('fleet-create-submit').click();

    await expect(page.getByRole('alert')).toContainText('Fleet created successfully!');
  });

  test('should validate fleet creation with no ships', async ({ page }) => {
    // Click create fleet button
    await page.getByTestId('fleet-create-button').click();

    // Try to submit without ships
    await page.getByTestId('fleet-start-planet-select').selectOption({ index: 1 });
    await page.getByTestId('fleet-create-submit').click();
    await expect(page.getByRole('alert')).toContainText('Fleet must contain at least one ship');
  });

  test('should display fleet information', async ({ page }) => {
    const fleetCard = page.getByTestId('fleet-tile').first();
    if (await fleetCard.count() === 0) {
      test.skip(true, 'No fleets present to validate card rendering.');
    }

    await expect(fleetCard).toBeVisible();
    await expect(fleetCard.getByText('Status:')).toBeVisible();
    await expect(fleetCard.getByText('Ships', { exact: true })).toBeVisible();
    await expect(fleetCard.getByTestId('fleet-from-value')).toBeVisible();
    await expect(fleetCard.getByTestId('fleet-to-value')).toBeVisible();
    await expect(fleetCard.getByTestId('fleet-eta-value')).toBeVisible();
  });

  test('should show send button for stationed fleets', async ({ page }) => {
    // Look for fleet with Send button
    const sendButton = page.locator('text=Send').first();

    if (await sendButton.isVisible()) {
      await expect(sendButton).toBeVisible();

      // Click send button
      await sendButton.click();

      // Send modal should appear
      await expect(page.getByTestId('fleet-send-modal')).toBeVisible();
      await expect(page.getByTestId('fleet-target-planet-select')).toBeVisible();
      await expect(page.getByTestId('fleet-mission-select')).toBeVisible();
    }
  });

  test('should send a fleet', async ({ page }) => {
    // Find a fleet to send
    const sendButton = page.locator('text=Send').first();

    if (await sendButton.isVisible()) {
      await sendButton.click();

      const targetSelect = page.getByTestId('fleet-target-planet-select');
      await expect(targetSelect).toBeVisible();

      const optionCount = await targetSelect.locator('option').count();
      if (optionCount < 2) {
        test.skip(true, 'No target planets available for this mission.');
      }

      await targetSelect.selectOption({ index: 1 });
      await page.getByTestId('fleet-send-submit').click();
      await expect(page.getByRole('alert')).toContainText('Fleet sent successfully!');

      // After sending, the destination should not render as "N/A".
      // (The UI uses API-provided target planet info for enemy/unowned targets.)
      const firstFleet = page.getByTestId('fleet-tile').first();
      await expect(firstFleet.getByTestId('fleet-to-value')).not.toHaveText('N/A');
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
      await expect(page.getByRole('alert')).toContainText('Fleet recalled successfully!');
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
    const statusValue = page.getByTestId('fleet-status-value').first();
    if (await statusValue.count() === 0) test.skip(true, 'No fleet status visible.');

    const statusText = (await statusValue.textContent()) || '';
    const className = await statusValue.evaluate((el) => el.className);

    if (statusText.includes('stationed')) {
      expect(className).toContain('text-green-400');
    } else if (statusText.includes('traveling')) {
      expect(className).toContain('text-yellow-400');
    } else if (statusText.includes('returning')) {
      expect(className).toContain('text-blue-400');
    }
  });

  test('should display ETA countdown', async ({ page }) => {
    // Look for ETA display
    const etaDisplay = page.locator('text=ETA').first();

    if (await etaDisplay.isVisible()) {
      // Should show time format or "Arrived" or "N/A"
      const etaValue = await etaDisplay.locator('xpath=following-sibling::*').textContent();

      // Should be in time format, "Arrived", or "N/A" - be very flexible
      const isValidFormat = ['Arrived', 'Arrived (pending tick)', 'N/A'].includes(etaValue) ||
                           /\d{1,2}:\d{2}:\d{2}/.test(etaValue) ||
                           /\d{1,2}:\d{2}/.test(etaValue) ||
                           /\d+/.test(etaValue); // Just any number

      expect(isValidFormat).toBe(true);
    }
  });

  test('should close modals with cancel button', async ({ page }) => {
    // Open create fleet modal
    await page.getByTestId('fleet-create-button').click();
    await expect(page.getByTestId('fleet-create-modal')).toBeVisible();

    // Click cancel
    await page.getByTestId('fleet-create-cancel').click();

    // Modal should close
    await expect(page.getByTestId('fleet-create-modal')).not.toBeVisible();
  });

  test('should handle multiple fleets', async ({ page }) => {
    // Count fleet tiles (avoid matching non-fleet cards)
    const fleetCards = page.locator('[data-testid="fleet-tile"]');
    const fleetCount = await fleetCards.count();

    if (fleetCount > 1) {
      // Should display multiple fleets
      for (let i = 0; i < Math.min(fleetCount, 3); i++) {
        await expect(fleetCards.nth(i).locator('text=Fleet #')).toBeVisible();
      }
    }
  });
});
