// playwright.config.js
module.exports = {
  testDir: './tests/e2e',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : 6,
  reporter: [['html', { open: 'never' }]],
  use: {
    actionTimeout: 0,
    baseURL: 'http://localhost:3000', // Frontend dev server
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true, // Run tests in headless mode to avoid popping up browser windows
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...require('playwright').devices['Desktop Chrome'],
      },
    },
  ],
  // Disable webServer since Makefile handles frontend startup
  // webServer: {
  //   command: 'REACT_APP_BACKEND_URL=http://localhost:5000 npm start',
  //   port: 3000,
  //   timeout: 120 * 1000,
  //   reuseExistingServer: !process.env.CI,
  // },
};
