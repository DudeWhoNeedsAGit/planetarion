const { test, expect } = require('@playwright/test');
const { apiLogin, loginViaLocalStorage } = require('./helpers/testSession');

async function runTick(page) {
  const runTickBtn = page.getByTestId('run-tick-button');
  if (await runTickBtn.isVisible()) {
    await runTickBtn.click();
    return;
  }
  await page.request.post('http://localhost:5000/api/tick');
}

test.describe('Research MVP', () => {
  test('start research → wait → tick completes → level increases', async ({ page, request }) => {
    const token = await apiLogin(request, 'e2etestuser', 'testpassword123');
    const headers = { Authorization: `Bearer ${token}` };

    // Seed RP to avoid waiting many ticks to afford the first upgrade.
    const seedRes = await request.post('http://localhost:5000/api/admin/research/seed-points', {
      headers,
      data: { username: 'e2etestuser', research_points: 10000 },
    });
    expect(seedRes.ok()).toBeTruthy();

    // Ensure at least one planet has a research lab so RP accrues (and to match MVP premise).
    const planetsRes = await request.get('http://localhost:5000/api/planet', { headers });
    expect(planetsRes.ok()).toBeTruthy();
    const planets = await planetsRes.json();
    const planetId = planets[0].id;

    // Upgrade research lab to level 1 (if not already).
    await request.put('http://localhost:5000/api/planet/buildings', {
      headers,
      data: { planet_id: planetId, buildings: { research_lab: 1 } },
    });

    await loginViaLocalStorage(page, request, 'e2etestuser', 'testpassword123');
    await page.getByTestId('nav-research').click();
    await expect(page.getByTestId('section-research')).toBeVisible({ timeout: 60000 });

    // Reset any existing research state so this test is deterministic against a restored DB snapshot.
    await request.post('http://localhost:5000/api/research/cancel', { headers });

    const beforeRes = await request.get('http://localhost:5000/api/research', { headers });
    expect(beforeRes.ok()).toBeTruthy();
    const before = await beforeRes.json();
    const beforeLevel = Number(before.levels?.astrophysics || 0);
    const durationSeconds = Number(before.next_level_durations_seconds?.astrophysics || 2);

    // Start the research via API for reliability; verify UI reflects the queue.
    const startRes = await request.post('http://localhost:5000/api/research/start', { headers, data: { key: 'astrophysics' } });
    expect(startRes.ok()).toBeTruthy();

    await page.reload();
    await page.getByTestId('nav-research').click();
    await expect(page.getByTestId('research-queue-active')).toBeVisible({ timeout: 60000 });

    // Wait for completion time, then tick to process completion.
    await page.waitForTimeout(durationSeconds * 1000 + 700);
    // Use backend tick for determinism (the Run Tick button is covered elsewhere).
    await request.post('http://localhost:5000/api/tick');

    // Poll backend until completion applied, then assert UI level updates.
    await expect
      .poll(
        async () => {
          const res = await request.get('http://localhost:5000/api/research', { headers });
          const body = await res.json();
          return Number(body.levels?.astrophysics || 0);
        },
        { timeout: 60000 }
      )
      .toBe(beforeLevel + 1);

    await page.reload();
    await page.getByTestId('nav-research').click();
    await expect(page.getByTestId('research-level-astrophysics')).toContainText(`L${beforeLevel + 1}`);

    // Also ensure activity feed contains the research completion after navigating to Overview.
    await page.getByTestId('nav-overview').click();
    const list = page.getByTestId('overview-activity-list');
    await expect(list).toBeVisible({ timeout: 60000 });
    await expect(list).toContainText(/Research completed/i);
  });
});
