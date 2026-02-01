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
  await page.getByTestId('dashboard').waitFor({ timeout: 60000 });
}

module.exports = {
  apiLogin,
  loginViaLocalStorage,
};
