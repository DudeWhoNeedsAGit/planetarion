async function apiLogin(request, username = 'e2etestuser', password = 'testpassword123') {
  const response = await request.post('http://localhost:5000/api/auth/login', {
    data: { username, password },
  });
  if (!response.ok()) {
    throw new Error(`Login failed: ${response.status()} ${await response.text()}`);
  }
  const data = await response.json();
  return data.token || data.access_token;
}

async function loginViaLocalStorage(page, request, username, password) {
  const token = await apiLogin(request, username, password);
  await page.goto('/');
  await page.evaluate((t) => localStorage.setItem('token', t), token);
  await page.reload();
  try {
    await page.getByTestId('dashboard').waitFor({ timeout: 15000 });
    return;
  } catch (e) {
    // Some flows may land on the login screen despite a valid token (transient backend/SSE errors).
    // Fall back to a UI login so suites remain reliable.
  }

  const usernameInput = page.locator('input[name="username"]').first();
  const passwordInput = page.locator('input[name="password"]').first();
  const loginBtn = page.getByRole('button', { name: /login/i }).first();
  if (await usernameInput.isVisible().catch(() => false)) {
    await usernameInput.fill(username);
    await passwordInput.fill(password);
    await loginBtn.click();
  }

  await page.getByTestId('dashboard').waitFor({ timeout: 60000 });
}

async function resetScenarioPack(request, scenario = 'two-player', options = {}) {
  const devToken = process.env.PLANETARION_DEV_ADMIN_TOKEN || 'planetarion-dev';
  const payload = {
    scenario,
    password: options.password || 'testpassword123',
    write_snapshot: Boolean(options.writeSnapshot),
  };
  const response = await request.post(`http://localhost:5000/api/admin/scenarios/${encodeURIComponent(scenario)}/reset`, {
    data: payload,
    headers: { 'X-Planetarion-Dev-Token': devToken },
  });
  if (!response.ok()) {
    throw new Error(`Scenario reset failed (${scenario}): ${response.status()} ${await response.text()}`);
  }
  const data = await response.json();
  if (data?.contract_version !== 'scenario-pack.v1') {
    throw new Error(`Unexpected scenario contract for ${scenario}`);
  }
  return data;
}

module.exports = {
  apiLogin,
  loginViaLocalStorage,
  resetScenarioPack,
};
