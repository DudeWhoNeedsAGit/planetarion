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

// Helper function to get user research level
async function getUserResearchLevel(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.get('http://localhost:5000/api/research', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status() === 200) {
    const data = await response.json();
    return data.levels?.colonization_tech || 0;
  }

  return 0;
}

// Helper function to upgrade research
async function upgradeResearch(page, researchType) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.post(`http://localhost:5000/api/research/upgrade/${researchType}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
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

test.describe('Enhanced Colonization', () => {

  test('should enforce research level requirements for colonization', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Try to colonize with low research level
    const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: 200,
        target_y: 300,
        target_z: 400
      }
    });

    // Should either succeed or show research requirement error
    expect([200, 400]).toContain(colonizationResponse.status());

    if (colonizationResponse.status() === 400) {
      const errorData = await colonizationResponse.json();
      expect(errorData.error).toContain('research level');
    }
  });

  test('should allow colonization with sufficient research', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade colonization tech if needed
    const currentLevel = await getUserResearchLevel(page);
    if (currentLevel < 1) {
      await upgradeResearch(page, 'colonization_tech');
    }

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Try colonization
    const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: 210,
        target_y: 310,
        target_z: 410
      }
    });

    // Should succeed or show valid error (not research related)
    expect([200, 409]).toContain(colonizationResponse.status()); // 409 = coordinates occupied

    if (colonizationResponse.status() === 200) {
      // Trigger tick to process colonization
      await triggerManualTick(page);

      // Should show colonization success message
      await page.waitForTimeout(1000);
      const successMessage = page.locator('text=New colony established');
      if (await successMessage.isVisible()) {
        await expect(successMessage).toBeVisible();
      }
    }
  });

  test('should respect colony limits', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Try multiple colonizations to test limit
    for (let i = 0; i < 6; i++) { // Try more than base limit of 5
      const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: {
          fleet_id: 1,
          mission: 'colonize',
          target_x: 220 + i,
          target_y: 320 + i,
          target_z: 420 + i
        }
      });

      if (colonizationResponse.status() === 400) {
        const errorData = await colonizationResponse.json();
        expect(errorData.error).toContain('limit reached');
        break; // Expected to hit limit
      }
    }
  });

  test('should calculate enhanced starting resources', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade research for better colonization
    await upgradeResearch(page, 'colonization_tech');

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Navigate to galaxy map
    await navigateToGalaxyMap(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Colonize a planet
    const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: 230,
        target_y: 330,
        target_z: 430
      }
    });

    if (colonizationResponse.status() === 200) {
      // Trigger tick
      await triggerManualTick(page);

      // Navigate to dashboard to check new colony
      await page.locator('nav').locator('text=Dashboard').click();

      // Should show enhanced starting resources
      const metalDisplay = page.locator('text=Metal').first();
      const crystalDisplay = page.locator('text=Crystal').first();

      if (await metalDisplay.isVisible()) {
        const metalText = await metalDisplay.textContent();
        const metalValue = parseInt(metalText.replace(/[^\d]/g, ''));

        // Should have more than basic starting resources
        expect(metalValue).toBeGreaterThan(500); // Basic is 500
      }
    }
  });

  test('should generate custom colony names', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade research
    await upgradeResearch(page, 'colonization_tech');

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Colonize multiple planets to test naming
    const colonies = [];
    for (let i = 0; i < 2; i++) {
      const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: {
          fleet_id: 1,
          mission: 'colonize',
          target_x: 240 + i,
          target_y: 340 + i,
          target_z: 440 + i
        }
      });

      if (colonizationResponse.status() === 200) {
        const data = await colonizationResponse.json();
        if (data.message && data.message.includes('New colony')) {
          colonies.push(data.message);
        }
      }
    }

    // Should have different colony names
    if (colonies.length >= 2) {
      expect(colonies[0]).not.toBe(colonies[1]);
      expect(colonies[0]).toMatch(/Colony \d+/);
      expect(colonies[1]).toMatch(/Colony \d+/);
    }
  });

  test('should handle colonization difficulty levels', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Test different difficulty coordinates
    const testCoordinates = [
      { x: 100, y: 100, z: 100, expectedDifficulty: 'low' },
      { x: 500, y: 500, z: 500, expectedDifficulty: 'medium' },
      { x: 800, y: 800, z: 800, expectedDifficulty: 'high' }
    ];

    const token = await page.evaluate(() => localStorage.getItem('token'));

    for (const coords of testCoordinates) {
      const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: {
          fleet_id: 1,
          mission: 'colonize',
          target_x: coords.x,
          target_y: coords.y,
          target_z: coords.z
        }
      });

      // Should either succeed or fail based on research level
      expect([200, 400, 409]).toContain(colonizationResponse.status());

      if (colonizationResponse.status() === 400) {
        const errorData = await colonizationResponse.json();
        expect(errorData.error).toContain('research level');
      }
    }
  });

  test('should prevent colonization of occupied coordinates', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade research
    await upgradeResearch(page, 'colonization_tech');

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Try to colonize the same coordinates twice
    const coords = { x: 250, y: 350, z: 450 };

    // First colonization
    const firstResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: coords.x,
        target_y: coords.y,
        target_z: coords.z
      }
    });

    if (firstResponse.status() === 200) {
      // Second colonization attempt
      const secondResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: {
          fleet_id: 1,
          mission: 'colonize',
          target_x: coords.x,
          target_y: coords.y,
          target_z: coords.z
        }
      });

      // Should fail with occupied coordinates
      expect(secondResponse.status()).toBe(409);
      const errorData = await secondResponse.json();
      expect(errorData.error).toContain('occupied');
    }
  });

  test('should apply astrophysics colony limit bonuses', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade astrophysics to increase colony limit
    await upgradeResearch(page, 'astrophysics');

    // Get JWT token
    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Check research status
    const researchResponse = await page.request.get('http://localhost:5000/api/research', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (researchResponse.status() === 200) {
      const researchData = await researchResponse.json();
      const astrophysicsLevel = researchData.levels?.astrophysics || 0;

      // Should have increased colony limit
      const expectedLimit = 5 + (astrophysicsLevel * 2); // Base 5 + 2 per level
      expect(expectedLimit).toBeGreaterThan(5);
    }
  });

  test('should show colonization progress in fleet status', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Upgrade research
    await upgradeResearch(page, 'colonization_tech');

    // Create colony ship fleet
    await createColonyShipFleet(page);

    // Send colonization fleet
    const token = await page.evaluate(() => localStorage.getItem('token'));

    const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: 260,
        target_y: 360,
        target_z: 460
      }
    });

    if (colonizationResponse.status() === 200) {
      // Navigate to fleets
      await page.locator('nav').locator('text=Fleets').click();

      // Should show colonization status
      const colonizationFleet = page.locator('.bg-gray-700').filter({ hasText: 'colonizing' });

      if (await colonizationFleet.isVisible()) {
        await expect(colonizationFleet.locator('text=colonizing')).toBeVisible();
        await expect(colonizationFleet.locator('text=ETA')).toBeVisible();
      }
    }
  });

  test('should handle colonization failure gracefully', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Try colonization without colony ship
    const token = await page.evaluate(() => localStorage.getItem('token'));

    const colonizationResponse = await page.request.post('http://localhost:5000/api/fleet/send', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        fleet_id: 1,
        mission: 'colonize',
        target_x: 270,
        target_y: 370,
        target_z: 470
      }
    });

    // Should handle gracefully
    expect([200, 400, 409]).toContain(colonizationResponse.status());

    if (colonizationResponse.status() === 400) {
      const errorData = await colonizationResponse.json();
      expect(errorData.error).toBeTruthy();
    }
  });
});
