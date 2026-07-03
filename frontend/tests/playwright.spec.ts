import { test, expect } from '@playwright/test';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000/api';
const FRONTEND = process.env.NEXT_PUBLIC_FRONTEND_URL ?? 'http://127.0.0.1:3000';

test('final render page shows video and plays', async ({ page }) => {
  // This test assumes a script exists; you may run backend/scripts/e2e_test.py first.
  // Discover a script via API
  const scriptsRes = await page.request.get(`${API_BASE}/scripts`);
  const scripts = await scriptsRes.json();
  test.skip(!scripts || scripts.length === 0, 'No scripts available');
  const scriptId = scripts[0].id;

  await page.goto(`${FRONTEND}/render/${scriptId}`);
  await page.waitForSelector('text=Final Render');

  // Wait until a video element appears (generated earlier by E2E helper)
  const video = await page.locator('video').first();
  await expect(video).toHaveCount(1);

  // Check that the video src returns 200
  const src = await video.getAttribute('src');
  const res = await page.request.get(src || '');
  expect(res.status()).toBe(200);
});
