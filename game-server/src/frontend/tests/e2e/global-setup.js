const { request } = require('@playwright/test');

async function globalSetup() {
  const ctx = await request.newContext();
  try {
    const minimal = process.env.PW_MINIMAL === '1' ? 'true' : 'false';
    const response = await ctx.post(`http://localhost:5000/populate?deterministic=true&minimal=${minimal}`);
    if (!response.ok()) {
      throw new Error(`Populate failed: ${response.status()} ${await response.text()}`);
    }
  } finally {
    await ctx.dispose();
  }
}

module.exports = globalSetup;
