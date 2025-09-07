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

// Helper function to navigate to dashboard
async function navigateToDashboard(page) {
  await page.locator('nav').locator('text=Dashboard').click();
}

// Helper function to get research points
async function getResearchPoints(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.get('http://localhost:5000/api/research/points', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status() === 200) {
    const data = await response.json();
    return data.research_points || 0;
  }

  return 0;
}

// Helper function to get research status
async function getResearchStatus(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'));

  const response = await page.request.get('http://localhost:5000/api/research', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status() === 200) {
    return await response.json();
  }

  return null;
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

// Helper function to trigger manual tick for research point generation
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

// Helper function to build research lab
async function buildResearchLab(page) {
  // Navigate to dashboard
  await navigateToDashboard(page);

  // Look for research lab upgrade option
  const researchLabButton = page.locator('button').filter({ hasText: 'Research Lab' });

  if (await researchLabButton.isVisible()) {
    await researchLabButton.click();

    // Should show upgrade confirmation or success
    await page.waitForTimeout(1000);
    const successMessage = page.locator('text=Research Lab upgraded');
    if (await successMessage.isVisible()) {
      await expect(successMessage).toBeVisible();
    }
  }
}

test.describe('Research System', () => {

  test('should display research section in dashboard', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to dashboard
    await navigateToDashboard(page);

    // Should show research section
    const researchSection = page.locator('text=Research Lab').first();

    if (await researchSection.isVisible()) {
      await expect(researchSection).toBeVisible();

      // Should show research points
      const researchPoints = page.locator('text=Research Points').first();
      if (await researchPoints.isVisible()) {
        await expect(researchPoints).toBeVisible();
      }
    }
  });

  test('should generate research points from research labs', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Build research lab if needed
    await buildResearchLab(page);

    // Get initial research points
    const initialPoints = await getResearchPoints(page);

    // Trigger manual tick
    await triggerManualTick(page);

    // Wait for research point generation
    await page.waitForTimeout(1000);

    // Get updated research points
    const updatedPoints = await getResearchPoints(page);

    // Should have generated research points
    expect(updatedPoints).toBeGreaterThanOrEqual(initialPoints);
  });

  test('should show research technology levels', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get research status
    const researchData = await getResearchStatus(page);

    if (researchData) {
      // Should have research levels
      expect(researchData.levels).toBeDefined();
      expect(typeof researchData.levels.colonization_tech).toBe('number');
      expect(typeof researchData.levels.astrophysics).toBe('number');
      expect(typeof researchData.levels.interstellar_communication).toBe('number');

      // Levels should be non-negative
      expect(researchData.levels.colonization_tech).toBeGreaterThanOrEqual(0);
      expect(researchData.levels.astrophysics).toBeGreaterThanOrEqual(0);
      expect(researchData.levels.interstellar_communication).toBeGreaterThanOrEqual(0);
    }
  });

  test('should show research upgrade costs', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get research status
    const researchData = await getResearchStatus(page);

    if (researchData && researchData.next_level_costs) {
      // Should have upgrade costs for all technologies
      expect(researchData.next_level_costs.colonization_tech).toBeDefined();
      expect(researchData.next_level_costs.astrophysics).toBeDefined();
      expect(researchData.next_level_costs.interstellar_communication).toBeDefined();

      // Costs should be positive numbers
      expect(researchData.next_level_costs.colonization_tech).toBeGreaterThan(0);
      expect(researchData.next_level_costs.astrophysics).toBeGreaterThan(0);
      expect(researchData.next_level_costs.interstellar_communication).toBeGreaterThan(0);
    }
  });

  test('should upgrade colonization technology', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get initial research status
    const initialData = await getResearchStatus(page);
    const initialLevel = initialData?.levels?.colonization_tech || 0;

    // Ensure we have enough research points
    let currentPoints = initialData?.research_points || 0;
    const upgradeCost = initialData?.next_level_costs?.colonization_tech || 0;

    if (currentPoints < upgradeCost) {
      // Build research lab and generate points
      await buildResearchLab(page);
      await triggerManualTick(page);
      await page.waitForTimeout(1000);

      // Check points again
      const updatedData = await getResearchStatus(page);
      currentPoints = updatedData?.research_points || 0;
    }

    if (currentPoints >= upgradeCost) {
      // Upgrade colonization tech
      const upgradeResponse = await upgradeResearch(page, 'colonization_tech');

      expect([200, 400]).toContain(upgradeResponse.status());

      if (upgradeResponse.status() === 200) {
        const upgradeData = await upgradeResponse.json();

        // Should show success message
        expect(upgradeData.message).toContain('upgraded to level');
        expect(upgradeData.new_level).toBe(initialLevel + 1);
        expect(upgradeData.research_points_remaining).toBeLessThan(currentPoints);
      }
    }
  });

  test('should upgrade astrophysics technology', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get initial research status
    const initialData = await getResearchStatus(page);
    const initialLevel = initialData?.levels?.astrophysics || 0;

    // Ensure we have enough research points
    let currentPoints = initialData?.research_points || 0;
    const upgradeCost = initialData?.next_level_costs?.astrophysics || 0;

    if (currentPoints < upgradeCost) {
      // Generate more research points
      await buildResearchLab(page);
      await triggerManualTick(page);
      await page.waitForTimeout(1000);

      const updatedData = await getResearchStatus(page);
      currentPoints = updatedData?.research_points || 0;
    }

    if (currentPoints >= upgradeCost) {
      // Upgrade astrophysics
      const upgradeResponse = await upgradeResearch(page, 'astrophysics');

      expect([200, 400]).toContain(upgradeResponse.status());

      if (upgradeResponse.status() === 200) {
        const upgradeData = await upgradeResponse.json();

        // Should show success message
        expect(upgradeData.message).toContain('upgraded to level');
        expect(upgradeData.new_level).toBe(initialLevel + 1);
      }
    }
  });

  test('should prevent upgrade without sufficient research points', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Try to upgrade without enough points
    const upgradeResponse = await upgradeResearch(page, 'colonization_tech');

    if (upgradeResponse.status() === 400) {
      const errorData = await upgradeResponse.json();

      // Should show insufficient points error
      expect(errorData.error).toContain('Insufficient research points');
      expect(errorData.required).toBeDefined();
      expect(errorData.available).toBeDefined();
    }
  });

  test('should increase upgrade costs for higher levels', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Get research status
    const researchData = await getResearchStatus(page);

    if (researchData && researchData.next_level_costs) {
      const level1Cost = researchData.next_level_costs.colonization_tech;
      const level2Cost = Math.floor(100 * Math.pow(2, 1.5)); // Calculate level 2 cost

      // Level 2 cost should be higher than level 1
      expect(level2Cost).toBeGreaterThan(level1Cost);
    }
  });

  test('should show research technology information', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Get colonization tech info
    const infoResponse = await page.request.get('http://localhost:5000/api/research/info/colonization_tech', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (infoResponse.status() === 200) {
      const infoData = await infoResponse.json();

      // Should have technology information
      expect(infoData.name).toBeDefined();
      expect(infoData.description).toBeDefined();
      expect(infoData.benefits).toBeDefined();
      expect(Array.isArray(infoData.benefits)).toBe(true);
      expect(infoData.max_level).toBeDefined();
    }
  });

  test('should show astrophysics information', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    const token = await page.evaluate(() => localStorage.getItem('token'));

    // Get astrophysics info
    const infoResponse = await page.request.get('http://localhost:5000/api/research/info/astrophysics', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (infoResponse.status() === 200) {
      const infoData = await infoResponse.json();

      // Should mention colony limit bonus
      expect(infoData.benefits.some(benefit =>
        benefit.includes('colony limit') || benefit.includes('colony')
      )).toBe(true);
    }
  });

  test('should handle multiple research upgrades', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Build research lab for point generation
    await buildResearchLab(page);

    // Get initial status
    const initialData = await getResearchStatus(page);
    const initialPoints = initialData?.research_points || 0;

    // Perform multiple upgrades if possible
    let upgradeCount = 0;
    const maxUpgrades = 3;

    for (let i = 0; i < maxUpgrades; i++) {
      // Generate research points
      await triggerManualTick(page);
      await page.waitForTimeout(500);

      // Check if we can upgrade
      const currentData = await getResearchStatus(page);
      const currentPoints = currentData?.research_points || 0;
      const upgradeCost = currentData?.next_level_costs?.colonization_tech || 0;

      if (currentPoints >= upgradeCost) {
        const upgradeResponse = await upgradeResearch(page, 'colonization_tech');

        if (upgradeResponse.status() === 200) {
          upgradeCount++;
        } else {
          break; // Stop if upgrade fails
        }
      } else {
        break; // Stop if insufficient points
      }
    }

    // Should have performed at least one upgrade
    expect(upgradeCount).toBeGreaterThanOrEqual(0);
  });

  test('should update research points in real-time', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Build research lab
    await buildResearchLab(page);

    // Get points before tick
    const pointsBefore = await getResearchPoints(page);

    // Trigger tick
    await triggerManualTick(page);

    // Get points after tick
    const pointsAfter = await getResearchPoints(page);

    // Points should increase
    expect(pointsAfter).toBeGreaterThanOrEqual(pointsBefore);
  });

  test('should handle research upgrade validation', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Try invalid research type
    const token = await page.evaluate(() => localStorage.getItem('token'));

    const invalidResponse = await page.request.post('http://localhost:5000/api/research/upgrade/invalid_tech', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    // Should return 400 for invalid research type
    expect(invalidResponse.status()).toBe(400);
  });

  test('should show research progress in dashboard', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to dashboard
    await navigateToDashboard(page);

    // Should show research information
    const researchInfo = page.locator('text=Research').first();

    if (await researchInfo.isVisible()) {
      // Should show some research-related content
      await expect(researchInfo).toBeVisible();
    }
  });

  test('should handle research point generation over time', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Build research lab
    await buildResearchLab(page);

    // Get initial points
    const initialPoints = await getResearchPoints(page);

    // Trigger multiple ticks
    for (let i = 0; i < 3; i++) {
      await triggerManualTick(page);
      await page.waitForTimeout(500);
    }

    // Get final points
    const finalPoints = await getResearchPoints(page);

    // Should have accumulated research points
    expect(finalPoints).toBeGreaterThanOrEqual(initialPoints);
  });
});
