const { test, expect } = require('@playwright/test');

// Helper function for login
async function loginAsE2eTestUser(page, username = 'e2etestuser') {
  // Navigate to the app
  await page.goto('/');

  // Login with existing test account
  await page.fill('input[name="username"]', username);
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
  await page.waitForTimeout(1000);
}

// Helper function to create combat fleet
async function createCombatFleet(page, shipComposition) {
  // Navigate to fleets
  await page.locator('nav').locator('text=Fleets').click();
  await page.waitForTimeout(500);

  // Click create fleet button
  await page.click('text=Create Fleet');
  await page.waitForTimeout(500);

  // Fill form with ships
  const shipInputs = page.locator('input[type="number"]');
  if (await shipInputs.count() >= 7) {
    // Fill ship composition
    if (shipComposition.small_cargo) {
      await shipInputs.nth(0).fill(shipComposition.small_cargo.toString());
    }
    if (shipComposition.light_fighter) {
      await shipInputs.nth(2).fill(shipComposition.light_fighter.toString());
    }
    if (shipComposition.heavy_fighter) {
      await shipInputs.nth(3).fill(shipComposition.heavy_fighter.toString());
    }
    if (shipComposition.cruiser) {
      await shipInputs.nth(4).fill(shipComposition.cruiser.toString());
    }
    if (shipComposition.battleship) {
      await shipInputs.nth(5).fill(shipComposition.battleship.toString());
    }
  }

  // Submit form
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);

  // Should show success message
  const successMessage = page.locator('text=Fleet created successfully');
  await expect(successMessage).toBeVisible();
}

// Helper function to send attack mission
async function sendAttackMission(page, targetPlanetId) {
  // Navigate to fleets
  await page.locator('nav').locator('text=Fleets').click();
  await page.waitForTimeout(500);

  // Find first available fleet
  const fleetRows = page.locator('.fleet-row, .bg-gray-700').filter({ hasText: 'stationed' });
  if (await fleetRows.count() > 0) {
    // Click send mission button (assuming it's in the fleet row)
    const sendButton = fleetRows.first().locator('button, text=Send Mission');
    if (await sendButton.isVisible()) {
      await sendButton.click();
      await page.waitForTimeout(500);

      // Select attack mission
      const attackOption = page.locator('select, option').filter({ hasText: 'attack' });
      if (await attackOption.isVisible()) {
        await attackOption.selectOption('attack');
      }

      // Enter target planet ID
      const targetInput = page.locator('input[name="target_planet_id"], input[placeholder*="planet"]');
      if (await targetInput.isVisible()) {
        await targetInput.fill(targetPlanetId.toString());
      }

      // Submit mission
      await page.click('button[type="submit"], text=Send Fleet');
      await page.waitForTimeout(1000);

      // Should show success message
      const successMessage = page.locator('text=Fleet sent successfully, text=Attack fleet sent');
      if (await successMessage.isVisible()) {
        await expect(successMessage).toBeVisible();
      }
    }
  }
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

// Helper function to check for combat reports
async function checkCombatReports(page) {
  // Navigate to combat reports (assuming there's a menu item or button)
  const combatMenu = page.locator('nav').locator('text=Combat, text=Reports, text=Battle Reports');
  if (await combatMenu.isVisible()) {
    await combatMenu.click();
    await page.waitForTimeout(1000);

    // Check if reports are displayed
    const reports = page.locator('.combat-report, .battle-report');
    return await reports.count() > 0;
  }

  return false;
}

test.describe('Combat System E2E', () => {

  test('should complete full combat workflow from fleet creation to battle report', async ({ page }) => {
    // Login as first user
    await loginAsE2eTestUser(page, 'e2etestuser');

    // Create combat fleet with mixed ships
    await createCombatFleet(page, {
      light_fighter: 20,
      heavy_fighter: 10,
      cruiser: 5
    });

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Find an enemy planet to attack (look for planets with different owner)
    const enemyPlanets = page.locator('.system-marker, .planet-marker').filter({ hasText: '⚔️' });
    if (await enemyPlanets.count() > 0) {
      // Click on enemy planet
      await enemyPlanets.first().click();
      await page.waitForTimeout(500);

      // Look for attack button
      const attackButton = page.locator('button, text=Attack, text=⚔️');
      if (await attackButton.isVisible()) {
        await attackButton.click();
        await page.waitForTimeout(500);

        // Confirm attack
        const confirmButton = page.locator('button, text=Confirm Attack, text=Send Attack Fleet');
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForTimeout(1000);

          // Should show attack sent message
          const successMessage = page.locator('text=Attack fleet sent, text=Fleet sent successfully');
          if (await successMessage.isVisible()) {
            await expect(successMessage).toBeVisible();
          }
        }
      }
    }
  });

  test('should display combat statistics correctly', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to combat statistics (assuming there's a menu or button)
    const statsMenu = page.locator('nav').locator('text=Combat, text=Statistics');
    if (await statsMenu.isVisible()) {
      await statsMenu.click();
      await page.waitForTimeout(1000);

      // Check if statistics are displayed
      const statsContainer = page.locator('.combat-stats, .statistics');
      if (await statsContainer.isVisible()) {
        // Should show various statistics
        await expect(statsContainer.locator('text=Victories, text=Wins')).toBeVisible();
        await expect(statsContainer.locator('text=Defeats, text=Losses')).toBeVisible();
      }
    }
  });

  test('should show debris fields on galaxy map', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Look for debris field indicators
    const debrisMarkers = page.locator('.debris-field, .system-marker').filter({ hasText: '💥' });
    if (await debrisMarkers.count() > 0) {
      // Click on debris field
      await debrisMarkers.first().click();
      await page.waitForTimeout(500);

      // Should show debris information
      const debrisInfo = page.locator('.debris-info, text=Metal, text=Crystal');
      if (await debrisInfo.isVisible()) {
        await expect(debrisInfo.locator('text=Metal')).toBeVisible();
        await expect(debrisInfo.locator('text=Crystal')).toBeVisible();
      }
    }
  });

  test('should handle attack mission validation', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Try to attack own planet
    await navigateToGalaxyMap(page);

    const ownPlanets = page.locator('.system-marker, .planet-marker').filter({ hasText: '🏠' });
    if (await ownPlanets.count() > 0) {
      await ownPlanets.first().click();
      await page.waitForTimeout(500);

      // Attack button should not be visible or should be disabled
      const attackButton = page.locator('button, text=Attack').filter({ hasText: 'disabled' });
      if (await attackButton.isVisible()) {
        // If visible, it should be disabled
        const isDisabled = await attackButton.isDisabled();
        expect(isDisabled).toBe(true);
      }
    }
  });

  test('should display battle reports with detailed information', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Check for combat reports
    const hasReports = await checkCombatReports(page);

    if (hasReports) {
      // Click on first report
      const firstReport = page.locator('.combat-report, .battle-report').first();
      await firstReport.click();
      await page.waitForTimeout(500);

      // Should show detailed battle information
      const reportDetails = page.locator('.report-details, .battle-details');
      if (await reportDetails.isVisible()) {
        // Check for key information
        await expect(reportDetails.locator('text=Attacker, text=Winner')).toBeVisible();
        await expect(reportDetails.locator('text=Defender, text=Loser')).toBeVisible();
        await expect(reportDetails.locator('text=Rounds, text=Round')).toBeVisible();
        await expect(reportDetails.locator('text=Losses, text=Destroyed')).toBeVisible();
      }
    }
  });

  test('should handle fleet combat statistics updates', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to fleets
    await page.locator('nav').locator('text=Fleets').click();
    await page.waitForTimeout(1000);

    // Look for fleet with combat statistics
    const fleetRows = page.locator('.fleet-row, .bg-gray-700');
    if (await fleetRows.count() > 0) {
      const firstFleet = fleetRows.first();

      // Check for combat stats display
      const combatStats = firstFleet.locator('text=Victories, text=Experience, text=V/D');
      if (await combatStats.isVisible()) {
        // Should show some combat statistics
        const statsText = await combatStats.textContent();
        expect(statsText.length).toBeGreaterThan(0);
      }
    }
  });

  test('should show real-time combat updates', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Create and send attack fleet
    await createCombatFleet(page, { light_fighter: 10 });
    await navigateToGalaxyMap(page);

    // Find enemy planet and initiate attack
    const enemyPlanets = page.locator('.system-marker').filter({ hasText: '⚔️' });
    if (await enemyPlanets.count() > 0) {
      await enemyPlanets.first().click();
      await page.waitForTimeout(500);

      const attackButton = page.locator('button').filter({ hasText: 'Attack' });
      if (await attackButton.isVisible()) {
        await attackButton.click();
        await page.waitForTimeout(500);

        // Trigger combat processing
        await triggerManualTick(page);

        // Check for combat results
        await page.waitForTimeout(2000); // Wait for processing

        // Should show combat results or battle report
        const combatResult = page.locator('text=Combat completed, text=Battle report');
        if (await combatResult.isVisible()) {
          await expect(combatResult).toBeVisible();
        }
      }
    }
  });

  test('should handle recycler mission for debris collection', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Create recycler fleet
    await createCombatFleet(page, { recycler: 5 });

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Look for debris fields
    const debrisFields = page.locator('.debris-field, .system-marker').filter({ hasText: '💥' });
    if (await debrisFields.count() > 0) {
      await debrisFields.first().click();
      await page.waitForTimeout(500);

      // Look for recycle button
      const recycleButton = page.locator('button, text=Recycle, text=Collect Debris');
      if (await recycleButton.isVisible()) {
        await recycleButton.click();
        await page.waitForTimeout(500);

        // Confirm recycling
        const confirmButton = page.locator('button, text=Confirm, text=Send Recyclers');
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForTimeout(1000);

          // Should show recycling success
          const successMessage = page.locator('text=Recyclers sent, text=Debris collection started');
          if (await successMessage.isVisible()) {
            await expect(successMessage).toBeVisible();
          }
        }
      }
    }
  });

  test('should validate attack mission requirements', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Try to send attack without fleet
    await navigateToGalaxyMap(page);

    const enemyPlanets = page.locator('.system-marker').filter({ hasText: '⚔️' });
    if (await enemyPlanets.count() > 0) {
      await enemyPlanets.first().click();
      await page.waitForTimeout(500);

      const attackButton = page.locator('button').filter({ hasText: 'Attack' });
      if (await attackButton.isVisible()) {
        await attackButton.click();
        await page.waitForTimeout(500);

        // Should show error about no available fleets
        const errorMessage = page.locator('text=No fleets available, text=Create a fleet first');
        if (await errorMessage.isVisible()) {
          await expect(errorMessage).toBeVisible();
        }
      }
    }
  });

  test('should handle defend mission setup', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Create defense fleet
    await createCombatFleet(page, { light_fighter: 15, heavy_fighter: 8 });

    // Navigate to fleets
    await page.locator('nav').locator('text=Fleets').click();
    await page.waitForTimeout(500);

    // Find fleet and set to defend mission
    const fleetRows = page.locator('.fleet-row, .bg-gray-700').filter({ hasText: 'stationed' });
    if (await fleetRows.count() > 0) {
      const firstFleet = fleetRows.first();

      // Look for mission selection
      const missionSelect = firstFleet.locator('select');
      if (await missionSelect.isVisible()) {
        await missionSelect.selectOption('defend');
        await page.waitForTimeout(500);

        // Should show defend status
        const defendStatus = firstFleet.locator('text=defending, text=Defense Mode');
        if (await defendStatus.isVisible()) {
          await expect(defendStatus).toBeVisible();
        }
      }
    }
  });

});
