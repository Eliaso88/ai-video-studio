const { chromium } = require('playwright');
(async () => {
  const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api';
  const FRONTEND = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://127.0.0.1:3000';
  const browser = await chromium.launch();
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE_CONSOLE', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE_ERROR', err.toString()));
  page.on('requestfailed', req => console.log('REQ_FAILED', req.url(), req.failure()?.errorText));
  page.on('response', async resp => {
    try {
      if (resp.request().url().includes('/api')) {
        console.log('API_RESP', resp.status(), resp.request().method(), resp.request().url());
        const t = await resp.text();
        console.log('API_BODY_START');
        console.log(t.slice(0, 2000));
        console.log('API_BODY_END');
      }
    } catch (e) { console.error('RESP_ERR', e); }
  });

  console.log('Fetching scripts list from API...');
  const scriptsRes = await page.request.get(`${API}/scripts`);
  let scripts = [];
  try { scripts = await scriptsRes.json(); } catch (e) { console.log('Failed to parse scripts JSON', e); }
  console.log('Scripts count:', (scripts && scripts.length) || 0);
  if (!scripts || scripts.length === 0) {
    console.log('No scripts available — run e2e_test.py first.');
    await browser.close();
    process.exit(0);
  }
  const scriptId = scripts[0].id;
  const url = `${FRONTEND}/render/${scriptId}`;
  console.log('Navigating to', url);
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  } catch (e) { console.log('Goto error', e.toString()); }
  await page.waitForTimeout(3000);

  try {
    const html = await page.content();
    console.log('PAGE_HTML_START');
    console.log(html.slice(0, 5000));
    console.log('PAGE_HTML_END');
  } catch (e) { console.log('Error reading page content', e); }

  try {
    await page.screenshot({ path: 'frontend/debug_render.png', fullPage: false });
    console.log('Saved screenshot: frontend/debug_render.png');
  } catch (e) { console.log('Screenshot failed', e); }

  await browser.close();
})();
