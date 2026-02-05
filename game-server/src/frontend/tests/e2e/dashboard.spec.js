const { test, expect } = require('@playwright/test');
const { loginViaLocalStorage } = require('./helpers/testSession');
const { goToSection } = require('./helpers/nav');

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page, request }) => {
    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
  });

  test('should display dashboard with user info', async ({ page }) => {
    // Check header
    await expect(page.locator('h1')).toContainText('Planetarion');
    await expect(page.locator('text=Welcome, e2etestuser!')).toBeVisible();
    await expect(page.getByTestId('logout-button')).toBeVisible();
  });

  test('should navigate between sections', async ({ page }) => {
    // Check navigation tabs - use nav context to avoid ambiguity
    await expect(page.getByTestId('nav-overview')).toBeVisible();
    await expect(page.getByTestId('nav-planets')).toBeVisible();
    await expect(page.getByTestId('nav-fleets')).toBeVisible();
    await expect(page.getByTestId('nav-research')).toBeVisible();
    await expect(page.getByTestId('nav-more')).toBeVisible();

    await goToSection(page, 'planets');
    await expect(page.locator('text=Your Planets')).toBeVisible();

    await goToSection(page, 'fleets');
    await expect(page.getByTestId('fleet-management')).toBeVisible();

    await goToSection(page, 'research');
    await expect(page.getByRole('heading', { name: /research lab/i })).toBeVisible();

    await goToSection(page, 'overview');
    await expect(page.locator('text=Welcome back, e2etestuser!')).toBeVisible();
  });

  test('should display planet information', async ({ page }) => {
    await goToSection(page, 'planets');
    await expect(page.locator('text=Your Planets')).toBeVisible();
  });

  test('should display buildings section', async ({ page }) => {
    await goToSection(page, 'planets');
    await expect(page.locator('text=Buildings')).toBeVisible();
  });

  test('should handle building upgrades', async ({ page }) => {
    test.skip(true, 'Upgrade flow is data-dependent; covered by backend integration tests.');
  });

  test('should display fleet information', async ({ page }) => {
    await goToSection(page, 'fleets');

    // Check for fleet-related elements - use actual UI text
    await expect(page.getByTestId('fleet-management')).toBeVisible();
    await expect(page.getByTestId('fleet-create-button')).toBeVisible();
  });

  test('should display research placeholder', async ({ page }) => {
    await goToSection(page, 'research');

    // Research MVP: ensure the dashboard renders key UI sections.
    await expect(page.getByRole('heading', { name: /research lab/i })).toBeVisible();
    await expect(page.getByTestId('research-points')).toBeVisible();
    await expect(page.getByTestId('research-queue-empty')).toBeVisible();
  });

  test('should display alliance placeholder', async ({ page }) => {
    await goToSection(page, 'alliance');

    // Check for alliance placeholder content
    await expect(page.locator('text=Alliance Center')).toBeVisible();
    await expect(page.locator('text=Alliance system coming soon')).toBeVisible();

    // Check for alliance features
    const features = ['Alliance creation and management', 'Member recruitment', 'Internal messaging'];
    for (const feature of features) {
      await expect(page.locator(`text=${feature}`)).toBeVisible();
    }
  });

  test('should display messages placeholder', async ({ page }) => {
    await goToSection(page, 'messages');

    // Check for messages placeholder content - use specific heading
    await expect(page.locator('h3').filter({ hasText: '💬 Messages' })).toBeVisible();
    await expect(page.locator('text=Messaging system coming soon')).toBeVisible();

    // Check for message types
    const messageTypes = ['Private messages', 'Alliance messages', 'System notifications'];
    for (const type of messageTypes) {
      await expect(page.locator(`text=${type}`)).toBeVisible();
    }
  });

  test('should handle logout', async ({ page }) => {
    // Click logout button
    await page.getByTestId('logout-button').click();
    await expect(page.locator('h2')).toContainText('Login to Planetarion');
  });

  test('should update resources after tick', async ({ page }) => {
    test.skip(true, 'Tick/resource deltas are backend concerns; covered by backend integration tests.');
  });
});
