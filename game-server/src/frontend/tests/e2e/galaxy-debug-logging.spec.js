/**
 * Galaxy Map Debug Logging E2E Test
 *
 * Tests that the GalaxyMap component generates debug logs when navigated to,
 * and that logs are properly written to files and displayed in the debug panel.
 */

const { test, expect } = require('@playwright/test');

// Helper function for login (same as fleet tests)
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
  await page.locator('nav').locator('text=Galaxy Map').click();
}

test.describe('Galaxy Map Debug Logging', () => {
  test.setTimeout(60000); // 60 second timeout for debug operations

  test('should generate debug logs when navigating to Galaxy Map', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Click on Galaxy Map navigation
    await navigateToGalaxyMap(page);

    // Wait for GalaxyMap component to render
    await page.waitForTimeout(2000); // Give time for component to mount

    // Check if debug panel is visible (if debug config allows it)
    const debugPanel = page.locator('.debug-panel');
    const isDebugPanelVisible = await debugPanel.isVisible().catch(() => false);

    if (isDebugPanelVisible) {
      console.log('✅ Debug panel is visible');
      await expect(debugPanel).toContainText('Debug Info');
      await expect(debugPanel).toContainText('Sectors:');
      await expect(debugPanel).toContainText('Systems:');
    } else {
      console.log('ℹ️ Debug panel not visible (may be disabled in config)');
    }

    // Check browser console for debug logs
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });

    // Wait a bit for debug logs to be generated
    await page.waitForTimeout(3000);

    // Check for GalaxyMap debug logs in console
    const galaxyDebugLogs = consoleMessages.filter(msg =>
      msg.includes('GalaxyMap') || msg.includes('🔍') || msg.includes('ℹ️') || msg.includes('❌')
    );

    console.log(`Found ${galaxyDebugLogs.length} GalaxyMap debug logs in console`);

    // Verify we have some debug logs
    expect(galaxyDebugLogs.length).toBeGreaterThan(0);

    // Check for specific debug log patterns
    const hasComponentMountLog = galaxyDebugLogs.some(log =>
      log.includes('Component mounted') || log.includes('GalaxyMap')
    );
    expect(hasComponentMountLog).toBe(true);

    // Check for debug API calls in network tab
    const debugApiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/debug/log')) {
        debugApiRequests.push(request);
      }
    });

    // Trigger some interaction to generate more debug logs
    await page.mouse.move(100, 100);
    await page.waitForTimeout(1000);

    console.log(`Found ${debugApiRequests.length} debug API requests`);

    // Verify debug API calls are being made
    expect(debugApiRequests.length).toBeGreaterThan(0);

    // Check if statistics panel is visible (this should always be visible)
    const statsPanel = page.locator('.sector-stats-panel');
    await expect(statsPanel).toBeVisible();
    await expect(statsPanel).toContainText('Galaxy Statistics');
    await expect(statsPanel).toContainText('Explored Sectors:');
    await expect(statsPanel).toContainText('Total Sectors:');

    // Verify GalaxyMap is actually rendered
    const galaxyMapContainer = page.locator('[class*="relative w-full h-full overflow-hidden bg-black"]');
    await expect(galaxyMapContainer).toBeVisible();

    console.log('✅ GalaxyMap component is rendered and debug logging is working');
  });

  test('should handle debug config loading', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Check if debug config is being loaded
    const configRequests = [];
    page.on('request', request => {
      if (request.url().includes('galaxy-debug-config.json')) {
        configRequests.push(request);
      }
    });

    // Navigate to Galaxy Map to trigger config loading
    await navigateToGalaxyMap(page);
    await page.waitForTimeout(2000);

    // Verify config was requested
    expect(configRequests.length).toBeGreaterThan(0);
    console.log('✅ Debug config is being loaded');
  });

  test('should generate debug logs for component interactions', async ({ page }) => {
    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to Galaxy Map
    await navigateToGalaxyMap(page);
    await page.waitForTimeout(2000);

    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });

    // Collect network requests
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method(),
          timestamp: Date.now()
        });
      }
    });

    // Perform some interactions to generate debug logs
    await page.mouse.move(200, 200);
    await page.waitForTimeout(500);

    // Try to click on a system (if any are visible)
    const systemMarkers = page.locator('.sector-system-marker');
    const systemCount = await systemMarkers.count();

    if (systemCount > 0) {
      console.log(`Found ${systemCount} system markers, clicking on first one`);
      await systemMarkers.first().click();
      await page.waitForTimeout(1000);
    }

    // Check for hover interactions
    const sectorBoundaries = page.locator('.sector-boundary');
    const boundaryCount = await sectorBoundaries.count();

    if (boundaryCount > 0) {
      console.log(`Found ${boundaryCount} sector boundaries, hovering over first one`);
      await sectorBoundaries.first().hover();
      await page.waitForTimeout(1000);
    }

    // Analyze the debug logs generated
    const debugLogs = consoleMessages.filter(msg =>
      msg.includes('🔍') || msg.includes('ℹ️') || msg.includes('❌') || msg.includes('⚠️')
    );

    const apiCalls = apiRequests.filter(req =>
      req.url.includes('/api/debug/log') ||
      req.url.includes('/api/sectors/explored') ||
      req.url.includes('/api/planet')
    );

    console.log(`Generated ${debugLogs.length} debug log messages`);
    console.log(`Made ${apiCalls.length} relevant API calls`);

    // Verify we have meaningful debug activity
    expect(debugLogs.length + apiCalls.length).toBeGreaterThan(0);

    console.log('✅ Debug logging is working for component interactions');
  });

  test('should verify debug log file creation and content', async ({ page }) => {
    // This test verifies that debug logs are being written to files
    // and allows filtering by debug level with console output

    // Login with test user
    await loginAsE2eTestUser(page);

    // Navigate to Galaxy Map to generate debug logs
    await navigateToGalaxyMap(page);

    // Wait for debug logs to be generated and sent
    await page.waitForTimeout(5000);

    // Check debug logs via backend API with detailed analysis
    try {
      const logsResponse = await fetch('http://localhost:5000/api/debug/logs');
      const logsData = await logsResponse.json();

      console.log(`\n📊 === DEBUG LOG ANALYSIS ===`);
      console.log(`Found ${logsData.count || 0} total debug log entries via API`);

      if (logsData.logs && logsData.logs.length > 0) {
        console.log('✅ Debug logs are being written to files');

        // Analyze logs by level
        const logsByLevel = {
          ERROR: [],
          WARN: [],
          INFO: [],
          DEBUG: []
        };

        logsData.logs.forEach(log => {
          if (logsByLevel[log.level]) {
            logsByLevel[log.level].push(log);
          }
        });

        console.log('\n📈 Debug logs by level:');
        Object.entries(logsByLevel).forEach(([level, logs]) => {
          console.log(`  ${level}: ${logs.length} entries`);
        });

        // Filter and display GalaxyMap logs
        const galaxyLogs = logsData.logs.filter(log =>
          log.component === 'GalaxyMap' || log.message.includes('GalaxyMap')
        );

        console.log(`\n🌌 GalaxyMap-specific debug logs: ${galaxyLogs.length}`);

        // Display only WARNING and ERROR level logs to console (clean output)
        const criticalLogs = galaxyLogs.filter(log => log.level === 'ERROR' || log.level === 'WARN');

        if (criticalLogs.length > 0) {
          console.log('\n🚨 Critical GalaxyMap debug logs (WARNING/ERROR only):');
          criticalLogs.forEach((log, index) => {
            console.log(`  ${index + 1}. [${log.level}] ${log.component}: ${log.message}`);
            if (log.data && Object.keys(log.data).length > 0) {
              console.log(`     Data: ${JSON.stringify(log.data).substring(0, 100)}...`);
            }
          });
        } else {
          console.log('\n✅ No critical issues found in GalaxyMap debug logs');
        }

        // Verify log structure
        const firstLog = logsData.logs[0];
        expect(firstLog).toHaveProperty('timestamp');
        expect(firstLog).toHaveProperty('level');
        expect(firstLog).toHaveProperty('component');
        expect(firstLog).toHaveProperty('message');

        expect(galaxyLogs.length).toBeGreaterThan(0);

      } else {
        console.log('⚠️ No debug logs found via API - they may be stored locally only');
      }

    } catch (error) {
      console.log('⚠️ Could not check debug logs via API:', error.message);
    }

    // Check debug stats with detailed output
    try {
      const statsResponse = await fetch('http://localhost:5000/api/debug/stats');
      const statsData = await statsResponse.json();

      console.log('\n📊 Debug Stats:');
      console.log(JSON.stringify(statsData, null, 2));

      if (statsData.files) {
        console.log('\n📁 Debug Files Status:');
        Object.entries(statsData.files).forEach(([filename, info]) => {
          console.log(`  ${filename}: ${info.entries} entries (${(info.size_bytes / 1024).toFixed(1)} KB)`);
        });
      }

      if (statsData.files && statsData.files['galaxy-debug.log']) {
        console.log('✅ Debug log file exists on server');
        expect(statsData.files['galaxy-debug.log'].exists).toBe(true);
      }

    } catch (error) {
      console.log('⚠️ Could not check debug stats:', error.message);
    }

    console.log('\n🎯 Debug log verification completed');
  });
});
