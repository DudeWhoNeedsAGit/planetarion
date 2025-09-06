// Simple test to verify planets page loads correctly
// Run with: node test_planets_page.js

const puppeteer = require('playwright');

async function testPlanetsPage() {
  console.log('🧪 Testing Planets Page Loading...');

  const browser = await puppeteer.chromium.launch();
  const page = await browser.newPage();

  try {
    // Navigate to the app
    console.log('📱 Opening Planetarion...');
    await page.goto('http://localhost:3000');

    // Wait for the app to load
    await page.waitForSelector('#root', { timeout: 10000 });
    console.log('✅ App loaded successfully');

    // Check if login form is present
    const loginForm = await page.$('input[type="text"], input[type="email"]');
    if (loginForm) {
      console.log('🔐 Login form detected - need to authenticate first');

      // Try to login with test credentials
      const usernameInput = await page.$('input[type="text"]');
      const passwordInput = await page.$('input[type="password"]');
      const loginButton = await page.$('button[type="submit"], button:has-text("Login")');

      if (usernameInput && passwordInput && loginButton) {
        console.log('📝 Attempting login with test credentials...');
        await usernameInput.fill('testuser');
        await passwordInput.fill('testpass');
        await loginButton.click();

        // Wait for navigation or error
        await page.waitForTimeout(2000);
      }
    }

    // Check if we're on the dashboard
    const dashboardElement = await page.$('text="🌌 Planetarion"');
    if (dashboardElement) {
      console.log('✅ Successfully logged in to dashboard');

      // Try to navigate to planets section
      console.log('🪐 Testing Planets navigation...');
      const planetsTab = await page.$('text="Planets"');
      if (planetsTab) {
        await planetsTab.click();
        await page.waitForTimeout(1000);

        // Check if planets content loaded
        const planetsContent = await page.$('text="Your Planets"');
        if (planetsContent) {
          console.log('✅ Planets page loaded successfully!');

          // Check for planet data
          const planetButtons = await page.$$('button:has-text("(")');
          console.log(`📊 Found ${planetButtons.length} planets`);

          if (planetButtons.length > 0) {
            console.log('✅ Planet data is loading correctly');
          } else {
            console.log('⚠️ No planets found - this might be expected for a new user');
          }

          // Check for resources section
          const resourcesSection = await page.$('text="Resources"');
          if (resourcesSection) {
            console.log('✅ Resources section is visible');
          } else {
            console.log('❌ Resources section not found');
          }

          // Check for buildings section
          const buildingsSection = await page.$('text="Buildings"');
          if (buildingsSection) {
            console.log('✅ Buildings section is visible');
          } else {
            console.log('❌ Buildings section not found');
          }

        } else {
          console.log('❌ Planets page did not load - "Your Planets" heading not found');
        }

      } else {
        console.log('❌ Planets tab not found in navigation');
      }

    } else {
      console.log('❌ Not on dashboard - login may have failed');
      const currentUrl = page.url();
      console.log('📍 Current URL:', currentUrl);
    }

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

// Run the test
testPlanetsPage().then(() => {
  console.log('\n🏁 Planets page test completed');
}).catch(console.error);
