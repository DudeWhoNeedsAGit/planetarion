/**
 * Enhanced Fleet UI Tests
 *
 * Tests the enhanced fleet management UI including:
 * - Coordinate auto-fill when planet is selected
 * - Planet selection clearing when coordinates are entered
 * - Colony ship validation and feedback
 * - Travel progress visualization
 * - Fleet overview display
 */

const { test, expect } = require('@playwright/test');

test.describe('Enhanced Fleet Management UI', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3000');

    // Wait for the app to load
    await page.waitForSelector('#root');

    // Login first (assuming login form exists)
    await page.fill('input[placeholder*="username" i]', 'testuser');
    await page.fill('input[placeholder*="password" i]', 'password');
    await page.click('button:has-text("Login")');

    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 });
  });

  test('coordinate auto-fill when planet selected', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page to load
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Click create fleet button
    await page.click('button:has-text("Create Fleet")');

    // Wait for fleet creation form
    await page.waitForSelector('[data-testid="fleet-creation-form"]');

    // Select start planet
    await page.selectOption('[data-testid="start-planet-select"]', '1'); // Assuming planet ID 1

    // Select target planet for colonization
    await page.selectOption('[data-testid="target-planet-select"]', '2'); // Assuming planet ID 2

    // Verify coordinates are auto-filled
    const targetX = await page.inputValue('[data-testid="target-x-input"]');
    const targetY = await page.inputValue('[data-testid="target-y-input"]');
    const targetZ = await page.inputValue('[data-testid="target-z-input"]');

    expect(targetX).not.toBe('');
    expect(targetY).not.toBe('');
    expect(targetZ).not.toBe('');

    // Verify coordinates match selected planet
    expect(targetX).toBe('100'); // Assuming test planet coordinates
    expect(targetY).toBe('200');
    expect(targetZ).toBe('300');
  });

  test('planet selection clears when coordinates entered', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Click create fleet button
    await page.click('button:has-text("Create Fleet")');

    // Wait for fleet creation form
    await page.waitForSelector('[data-testid="fleet-creation-form"]');

    // First select a target planet
    await page.selectOption('[data-testid="target-planet-select"]', '2');

    // Verify planet is selected
    const selectedPlanet = await page.inputValue('[data-testid="target-planet-select"]');
    expect(selectedPlanet).toBe('2');

    // Now manually enter coordinates
    await page.fill('[data-testid="target-x-input"]', '500');
    await page.fill('[data-testid="target-y-input"]', '600');
    await page.fill('[data-testid="target-z-input"]', '700');

    // Verify planet selection is cleared
    const clearedPlanet = await page.inputValue('[data-testid="target-planet-select"]');
    expect(clearedPlanet).toBe(''); // Should be empty
  });

  test('colony ship validation prevents invalid missions', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Click create fleet button
    await page.click('button:has-text("Create Fleet")');

    // Wait for fleet creation form
    await page.waitForSelector('[data-testid="fleet-creation-form"]');

    // Create fleet without colony ships
    await page.selectOption('[data-testid="start-planet-select"]', '1');
    await page.fill('[data-testid="small-cargo-input"]', '10');
    await page.fill('[data-testid="light-fighter-input"]', '5');
    // Leave colony ship at 0

    // Try to select colonization mission
    await page.selectOption('[data-testid="mission-select"]', 'colonize');

    // Enter target coordinates
    await page.fill('[data-testid="target-x-input"]', '100');
    await page.fill('[data-testid="target-y-input"]', '200');
    await page.fill('[data-testid="target-z-input"]', '300');

    // Try to send fleet
    await page.click('button:has-text("Send Fleet")');

    // Verify error message appears
    await page.waitForSelector('[data-testid="error-message"]');
    const errorText = await page.textContent('[data-testid="error-message"]');
    expect(errorText.toLowerCase()).toContain('colony ship');
  });

  test('colony ship validation allows valid colonization', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Click create fleet button
    await page.click('button:has-text("Create Fleet")');

    // Wait for fleet creation form
    await page.waitForSelector('[data-testid="fleet-creation-form"]');

    // Create fleet with colony ships
    await page.selectOption('[data-testid="start-planet-select"]', '1');
    await page.fill('[data-testid="small-cargo-input"]', '10');
    await page.fill('[data-testid="colony-ship-input"]', '1'); // Include colony ship

    // Select colonization mission
    await page.selectOption('[data-testid="mission-select"]', 'colonize');

    // Enter target coordinates
    await page.fill('[data-testid="target-x-input"]', '100');
    await page.fill('[data-testid="target-y-input"]', '200');
    await page.fill('[data-testid="target-z-input"]', '300');

    // Send fleet
    await page.click('button:has-text("Send Fleet")');

    // Verify success message or fleet appears in list
    await page.waitForSelector('[data-testid="success-message"]', { timeout: 5000 });
    const successText = await page.textContent('[data-testid="success-message"]');
    expect(successText.toLowerCase()).toContain('success');
  });

  test('travel progress visualization for active fleets', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for traveling fleets
    const travelingFleets = await page.$$('[data-testid="traveling-fleet"]');

    if (travelingFleets.length > 0) {
      // Test the first traveling fleet
      const fleetElement = travelingFleets[0];

      // Verify travel information is displayed
      const progressBar = await fleetElement.$('[data-testid="progress-bar"]');
      expect(progressBar).not.toBeNull();

      // Verify progress percentage is shown
      const progressText = await fleetElement.$('[data-testid="progress-text"]');
      expect(progressText).not.toBeNull();

      const progressValue = await progressText.textContent();
      expect(progressValue).toMatch(/\d+(\.\d+)?%/); // Should contain percentage

      // Verify current position is shown
      const currentPosition = await fleetElement.$('[data-testid="current-position"]');
      expect(currentPosition).not.toBeNull();

      const positionText = await currentPosition.textContent();
      expect(positionText).toMatch(/\d+:\d+:\d+/); // Should contain coordinates
    }
  });

  test('fleet overview displays comprehensive information', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for fleet list items
    const fleetItems = await page.$$('[data-testid="fleet-item"]');

    if (fleetItems.length > 0) {
      // Test the first fleet
      const fleetItem = fleetItems[0];

      // Verify basic fleet information
      const fleetId = await fleetItem.$('[data-testid="fleet-id"]');
      expect(fleetId).not.toBeNull();

      const mission = await fleetItem.$('[data-testid="fleet-mission"]');
      expect(mission).not.toBeNull();

      const status = await fleetItem.$('[data-testid="fleet-status"]');
      expect(status).not.toBeNull();

      // Verify ship composition is displayed
      const shipComposition = await fleetItem.$('[data-testid="ship-composition"]');
      expect(shipComposition).not.toBeNull();

      // Verify planet information
      const startPlanet = await fleetItem.$('[data-testid="start-planet"]');
      expect(startPlanet).not.toBeNull();

      // For traveling fleets, check target planet info
      const targetPlanet = await fleetItem.$('[data-testid="target-planet"]');
      if (targetPlanet) {
        const targetText = await targetPlanet.textContent();
        expect(targetText.length).toBeGreaterThan(0);
      }
    }
  });

  test('coordinate-based mission display', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for coordinate-based missions (colonization, exploration)
    const coordinateMissions = await page.$$('[data-testid="coordinate-mission"]');

    if (coordinateMissions.length > 0) {
      // Test the first coordinate-based mission
      const missionElement = coordinateMissions[0];

      // Verify target coordinates are displayed
      const targetCoords = await missionElement.$('[data-testid="target-coordinates"]');
      expect(targetCoords).not.toBeNull();

      const coordsText = await targetCoords.textContent();
      expect(coordsText).toMatch(/\d+:\d+:\d+/); // Should contain coordinates

      // Verify no target planet is shown (coordinate-based)
      const targetPlanet = await missionElement.$('[data-testid="target-planet"]');
      if (targetPlanet) {
        const planetText = await targetPlanet.textContent();
        expect(planetText.toLowerCase()).toContain('coordinate') ||
               expect(planetText.toLowerCase()).toContain('empty space');
      }
    }
  });

  test('fleet speed calculation display', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for traveling fleets
    const travelingFleets = await page.$$('[data-testid="traveling-fleet"]');

    if (travelingFleets.length > 0) {
      // Test the first traveling fleet
      const fleetElement = travelingFleets[0];

      // Verify fleet speed is displayed
      const fleetSpeed = await fleetElement.$('[data-testid="fleet-speed"]');
      if (fleetSpeed) {
        const speedText = await fleetSpeed.textContent();
        expect(speedText).toMatch(/\d+(\.\d+)?/); // Should contain numeric speed
      }

      // Verify distance is displayed
      const distance = await fleetElement.$('[data-testid="travel-distance"]');
      if (distance) {
        const distanceText = await distance.textContent();
        expect(distanceText).toMatch(/\d+(\.\d+)?/); // Should contain numeric distance
      }
    }
  });

  test('eta formatting and countdown', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for traveling fleets
    const travelingFleets = await page.$$('[data-testid="traveling-fleet"]');

    if (travelingFleets.length > 0) {
      // Test the first traveling fleet
      const fleetElement = travelingFleets[0];

      // Verify ETA is displayed
      const eta = await fleetElement.$('[data-testid="fleet-eta"]');
      expect(eta).not.toBeNull();

      const etaText = await eta.textContent();

      // ETA should be either formatted time or "Arrived"
      expect(
        etaText === 'Arrived' ||
        etaText.match(/\d{1,2}:\d{2}(:\d{2})?/) || // HH:MM or HH:MM:SS format
        etaText.match(/\d{1,2}:\d{2}/) // MM:SS format
      ).toBeTruthy();
    }
  });

  test('error handling for invalid fleet operations', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Try to send fleet without required fields
    await page.click('button:has-text("Send Fleet")');

    // Verify error message appears
    await page.waitForSelector('[data-testid="error-message"]');
    const errorText = await page.textContent('[data-testid="error-message"]');
    expect(errorText.length).toBeGreaterThan(0);
    expect(errorText.toLowerCase()).toContain('required') ||
           expect(errorText.toLowerCase()).toContain('missing') ||
           expect(errorText.toLowerCase()).toContain('invalid');
  });

  test('fleet recall functionality', async ({ page }) => {
    // Navigate to fleet management
    await page.click('text=Fleet Management');

    // Wait for fleet management page
    await page.waitForSelector('[data-testid="fleet-management"]');

    // Look for traveling fleets with recall button
    const recallButtons = await page.$$('button:has-text("Recall")');

    if (recallButtons.length > 0) {
      // Click the first recall button
      await recallButtons[0].click();

      // Verify confirmation or success message
      await page.waitForSelector('[data-testid="success-message"]', { timeout: 5000 });
      const successText = await page.textContent('[data-testid="success-message"]');
      expect(successText.toLowerCase()).toContain('recall');
    }
  });
});
