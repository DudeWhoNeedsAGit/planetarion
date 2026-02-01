const request = require('supertest');

const enabled = process.env.PLANETARION_SUPERTEST === '1';

(enabled ? describe : describe.skip)('Supertest Harness Smoke', () => {
  test('backend /health is reachable', async () => {
    const res = await request('http://localhost:5000').get('/health');
    expect(res.status).toBe(200);
  });
});

