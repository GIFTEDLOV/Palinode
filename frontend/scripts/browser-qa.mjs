/* global document, window */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const localUrl = process.env.PALINODE_LOCAL_URL || 'http://127.0.0.1:4175';
const productionUrl = process.env.PALINODE_PRODUCTION_URL || 'https://palinode-app.vercel.app';
const repoRoot = path.resolve(process.cwd(), '..');
const deterministic = process.env.PALINODE_SUITE === 'deterministic';
const simulate429 = deterministic && process.env.PALINODE_SIMULATE_429 === 'once';
const rateLimitOnly = simulate429 && process.env.PALINODE_RATE_LIMIT_ONLY === 'true';
const deterministicFixture = deterministic
  ? JSON.parse(await readFile(path.join(repoRoot, 'frontend', 'tests', 'fixtures', 'v4-rpc', 'responses.json'), 'utf8'))
  : null;
const deterministicProof = deterministic
  ? {
    evidence: '/app/evidence/ad68b1c64e951fc88b3cb94cbb481978555c4fef7d82cbf68938f1e5c2b492ee',
    decision: '/app/decisions/9210f33e55b66de6c6680a1a7ea51c4fe6651233f2116299e5bbf26188692e9d',
    revocation: '/app/revocations/86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534',
    thirdParty: '/app/revocations/085a386fb3f6f7638fbfcb41b2b69dbfa0ba17e2641178c161aef14d77ceef53',
    recovery: '/app/recoveries/8541568d68dacb839e6d0434c4a15019ba7ba4424a04667b574bbbeddd7acb1e',
    authority: '/app/authorities/f5d0db56d7bf3eb85e2b5ef02f15ec06170db45d1ada322982e8d382c664f4b3',
    authorityC: '/app/authorities/2a5d4150757d86f9ea35b602de289eaebed92246d20039c113655f020acf8ffc',
  }
  : null;
const browserQaRoot = path.join(repoRoot, 'artifacts', 'browser-qa');
const finalRoot = path.join(repoRoot, 'artifacts', 'final-screenshots');
const summaryFile = process.env.PALINODE_SUMMARY_FILE || path.join(browserQaRoot, 'summary.json');
const viewports = {
  desktop_1440x900: { width: 1440, height: 900 },
  desktop_1920x1080: { width: 1920, height: 1080 },
  laptop_1280x800: { width: 1280, height: 800 },
  tablet_1024x768: { width: 1024, height: 768 },
  tablet_768x1024: { width: 768, height: 1024 },
  mobile_430x932: { width: 430, height: 932 },
  mobile_390x844: { width: 390, height: 844 },
  mobile_375x812: { width: 375, height: 812 },
};
const routes = [
  ['landing', '/'], ['overview', '/app'], ['graph', '/app/graph'], ['evidence', '/app/evidence'],
  ['decisions', '/app/decisions'], ['revocations', '/app/revocations'], ['recoveries', '/app/recoveries'],
  ['authorities', '/app/authorities'], ['activity', '/app/activity'], ['proof', '/app/proof'],
  ['integrate', '/app/integrate'], ['docs', '/docs'],
];
const finalScreenshotNames = {
  'desktop_1440x900:landing': ['01-landing-desktop.png'],
  'desktop_1440x900:overview': ['02-overview.png'],
  'desktop_1440x900:graph': ['03-global-graph.png'],
  'desktop_1440x900:revocation-detail': ['04-blast-radius.png', '06-revocation-command-center.png'],
  'desktop_1440x900:evidence-detail': ['05-evidence-detail.png'],
  'desktop_1440x900:recovery-detail': ['07-recovery-command-center.png'],
  'desktop_1440x900:authority-detail': ['08-authority-detail.png'],
  'desktop_1440x900:proof': ['09-proof-security.png'],
  'mobile_430x932:landing': ['10-mobile-landing.png'],
  'mobile_430x932:graph': ['11-mobile-graph.png'],
  'mobile_430x932:revocation-detail': ['12-mobile-revocation.png'],
};

async function waitForApp(page) {
  await page.waitForSelector('#root');
  await page.waitForTimeout(120);
  const syncing = page.locator('.breadcrumb em');
  if (await syncing.count()) await syncing.first().waitFor({ state: 'detached', timeout: 7_000 }).catch(() => undefined);
  await page.waitForTimeout(120);
}
async function route(page, base, pathname) {
  const response = await page.goto(new URL(pathname, base).toString(), { waitUntil: 'domcontentloaded' });
  await waitForApp(page);
  if (pathname.includes('/evidence/') || pathname.includes('/decisions/') || pathname.includes('/revocations/') || pathname.includes('/recoveries/') || pathname.includes('/authorities/')) {
    await page.waitForFunction(() => ![...document.querySelectorAll('.detail-supplement')].some((element) => (element.textContent || '').includes('Loading')), { timeout: 7_000 }).catch(() => undefined);
  }
  if (!response || response.status() !== 200) throw new Error(`${base}${pathname}: HTTP ${response?.status()}`);
}
async function collectIds(page, base) {
  const ids = {};
  for (const [type, pathname, selector] of [
    ['evidence', '/app/evidence', 'a.registry-card'],
    ['decision', '/app/decisions', 'a.registry-card'],
    ['revocation', '/app/revocations', 'a.case-card'],
    ['recovery', '/app/recoveries', 'a.case-card'],
    ['authority', '/app/authorities', 'a.registry-card'],
  ]) {
    await route(page, base, pathname);
    const count = await page.locator(selector).count();
    ids[type] = count ? await page.locator(selector).first().getAttribute('href') : null;
  }
  return ids;
}
function recordError(errors, value) { if (value) errors.push(String(value)); }
async function assertNoOverflow(page, label) {
  const result = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }));
  if (result.scrollWidth > result.innerWidth + 1) {
    const offenders = await page.evaluate(() => [...document.querySelectorAll('body *')].map((element) => { const rect = element.getBoundingClientRect(); return { tag: element.tagName, className: element.className, right: Math.round(rect.right), width: Math.round(rect.width), text: (element.textContent || '').trim().slice(0, 90) }; }).filter((item) => item.right > window.innerWidth + 1 && item.width > 0).slice(-8));
    throw new Error(`${label}: horizontal overflow ${result.scrollWidth} > ${result.innerWidth}; offenders=${JSON.stringify(offenders)}`);
  }
}
async function screenshot(page, target, viewport, name, outputRoot) {
  await mkdir(path.join(outputRoot, target), { recursive: true });
  await page.screenshot({ path: path.join(outputRoot, target, `${viewport}_${name}.png`), fullPage: true });
}

await mkdir(browserQaRoot, { recursive: true });
await mkdir(finalRoot, { recursive: true });
const browser = await chromium.launch({ headless: true });
const summary = { targets: {}, assertions: [], screenshots: [] };
const readCache = new Map();
const targets = deterministic
  ? [['deterministic', localUrl]]
  : process.env.PALINODE_TARGET === 'wallet-only'
  ? []
  : process.env.PALINODE_TARGET === 'production'
  ? [['production', productionUrl]]
  : process.env.PALINODE_TARGET === 'local'
    ? [['local', localUrl]]
    : [['local', localUrl], ['production', productionUrl]];

for (const [target, base] of targets) {
  const context = await browser.newContext({ viewport: viewports.desktop_1440x900 });
  const page = await context.newPage();
  const errors = [];
  let injected429 = false;
  let firstReadAt = 0;
  let retryReadAt = 0;
  let throttledKey = '';
  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const text = message.text();
    if (simulate429 && /429|upstream rate limit \(deterministic test\)/i.test(text)) return;
    recordError(errors, text);
  });
  page.on('pageerror', (error) => recordError(errors, error.message));
  if (deterministic) {
    await context.unrouteAll({ behavior: 'ignoreErrors' });
    await context.route('https://fonts.googleapis.com/**', (route) => route.fulfill({ status: 200, headers: { 'content-type': 'text/css' }, body: '' }));
    await context.route('https://fonts.gstatic.com/**', (route) => route.fulfill({ status: 204, body: '' }));
    await context.route('**/api/rpc**', async (route) => {
      const request = route.request();
      if (request.method() !== 'POST') return route.continue();
      const payload = JSON.parse(request.postData() || '{}');
      if (payload.method !== 'gen_call') return route.continue();
      const key = JSON.stringify({ ...payload, id: 0 });
      const entry = deterministicFixture.responses[key];
      if (!entry) throw new Error(`Missing deterministic V4 fixture response for ${payload.params?.[0]?.data || payload.method}`);
      if (!firstReadAt) firstReadAt = Date.now();
      if (simulate429 && !injected429) {
        injected429 = true;
        throttledKey = key;
        return route.fulfill({ status: 429, headers: { 'content-type': 'application/json', 'retry-after': '2' }, body: JSON.stringify({ jsonrpc: '2.0', error: { code: -32005, message: 'upstream rate limit (deterministic test)' }, id: payload.id }) });
      }
      if (injected429 && key === throttledKey && !retryReadAt) retryReadAt = Date.now();
      return route.fulfill({ status: entry.status, headers: entry.headers, body: entry.body });
    });
  } else {
    await context.route('**/api/rpc**', async (route) => {
      const request = route.request();
      if (request.method() !== 'POST') return route.continue();
      let payload;
      try { payload = JSON.parse(request.postData() || '{}'); } catch { return route.continue(); }
      if (payload.method !== 'gen_call') return route.continue();
      const key = JSON.stringify({ ...payload, id: 0 });
      const cached = readCache.get(key);
      if (cached) return route.fulfill(cached);
      const response = await route.fetch();
      const body = await response.body();
      const result = { status: response.status(), headers: response.headers(), body };
      if (response.ok()) readCache.set(key, result);
      return route.fulfill(result);
    });
  }
  const ids = rateLimitOnly ? {} : await collectIds(page, base);
  if (deterministic && !rateLimitOnly) Object.assign(ids, deterministicProof);
  if (!ids.evidence && ids.revocation) {
    await route(page, base, ids.revocation);
    const evidenceLink = page.locator('a[href^="/app/evidence/"]').first();
    if (await evidenceLink.count()) ids.evidence = await evidenceLink.getAttribute('href');
  }
  const dynamicRoutes = [
    ...(rateLimitOnly ? [['overview', '/app']] : routes),
    ...(ids.evidence ? [['evidence-detail', ids.evidence]] : []),
    ...(ids.decision ? [['decision-detail', ids.decision]] : []),
    ...(ids.revocation ? [['revocation-detail', ids.revocation]] : []),
    ...(ids.recovery ? [['recovery-detail', ids.recovery]] : []),
    ...(ids.authority ? [['authority-detail', ids.authority]] : []),
    ...(deterministicProof && !rateLimitOnly ? [['third-party-detail', deterministicProof.thirdParty], ['authority-c-detail', deterministicProof.authorityC]] : []),
  ];
  const routeResults = [];
  const responsiveRoutes = new Set(['landing', 'overview', 'graph', 'evidence', 'evidence-detail', 'decision-detail', 'revocation-detail', 'recovery-detail', 'authority-detail', 'proof', 'docs']);
  for (const [name, pathname] of dynamicRoutes) {
    const sizes = responsiveRoutes.has(name) ? Object.entries(viewports) : [['desktop_1440x900', viewports.desktop_1440x900]];
    for (const [viewport, size] of sizes) {
      console.log(`${target} ${viewport} ${name}`);
      await page.setViewportSize(size);
      await route(page, base, pathname);
      await assertNoOverflow(page, `${target}/${viewport}/${name}`);
      routeResults.push(`${viewport}/${name}`);
      if (target === 'production') {
        for (const fileName of finalScreenshotNames[`${viewport}:${name}`] || []) {
          await page.screenshot({ path: path.join(finalRoot, fileName), fullPage: true });
          summary.screenshots.push(path.join('artifacts', 'final-screenshots', fileName));
        }
      }
      if (target === 'production' && ['desktop_1440x900', 'mobile_430x932'].includes(viewport)) {
        await screenshot(page, target, viewport, name, browserQaRoot);
      }
    }
  }
  await page.setViewportSize(viewports.desktop_1440x900);
  await route(page, base, '/app/graph');
  const zoom = page.locator('.graph-controls button').first();
  if (await zoom.count()) { await zoom.click(); await page.getByText('115%').waitFor(); await page.locator('.graph-controls button').nth(2).click(); await page.getByText('100%').waitFor(); }
  await page.mouse.move(700, 450); await page.mouse.down(); await page.mouse.move(760, 480); await page.mouse.up();
  await route(page, base, ids.evidence || '/app/evidence');
  if (ids.evidence) {
    const body = await page.locator('body').innerText();
    if (!body.includes('AUTHENTICATION') || !body.includes('RELIANCE')) throw new Error(`${target}: evidence authentication/reliance distinction missing`);
  }
  if (deterministic && simulate429 && (!injected429 || !retryReadAt || retryReadAt - firstReadAt < 1_000)) throw new Error(`${target}: throttle regression did not show bounded backoff/recovery`);
  if (errors.length) throw new Error(`${target}: browser console errors: ${errors.join(' | ')}`);
  summary.targets[target] = { ids, routeCount: routeResults.length, consoleErrors: errors.length, injected429, retryDelayMs: retryReadAt && firstReadAt ? retryReadAt - firstReadAt : 0 };
  await page.waitForTimeout(500);
  await context.unrouteAll({ behavior: 'ignoreErrors' });
  await context.close();
}

const walletContext = await browser.newContext({ viewport: viewports.mobile_430x932 });
await walletContext.route('**/api/rpc**', (route) => route.abort());
await walletContext.addInitScript(() => {
  let chain = '0x1';
  let accounts = [];
  const listeners = new Map();
  const emit = (event, value) => (listeners.get(event) || []).forEach((listener) => listener(value));
  window.ethereum = {
    request: async ({ method }) => {
      if (method === 'eth_chainId') return chain;
      if (method === 'wallet_switchEthereumChain' || method === 'wallet_addEthereumChain') { chain = '0xf22f'; emit('chainChanged', chain); return null; }
      if (method === 'eth_requestAccounts') { accounts = ['0x1111111111111111111111111111111111111111']; emit('accountsChanged', accounts); return accounts; }
      return null;
    },
    on: (event, listener) => listeners.set(event, [...(listeners.get(event) || []), listener]),
    removeListener: (event, listener) => listeners.set(event, (listeners.get(event) || []).filter((item) => item !== listener)),
  };
  window.__palinodeWalletTest = { emit, setAccount: (value) => { accounts = [value]; emit('accountsChanged', accounts); }, setChain: (value) => { chain = value; emit('chainChanged', chain); } };
});
const walletPage = await walletContext.newPage();
await route(walletPage, localUrl, '/app');
await walletPage.locator('.wallet-button').click();
await walletPage.waitForTimeout(100);
const walletConnected = await walletPage.locator('.wallet-button').textContent();
await walletPage.evaluate(() => window.__palinodeWalletTest.setChain('0x1'));
const wrongNetwork = await walletPage.locator('.network-chip').innerText();
await route(walletPage, localUrl, '/app/evidence');
await walletPage.getByRole('button', { name: 'Register evidence', exact: true }).first().click();
const evidenceFields = walletPage.locator('.form-card .field input');
await evidenceFields.nth(0).fill('https://palinode-fixture.vercel.app/evidence/reviewer-wallet-smoke.json');
await evidenceFields.nth(1).fill('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
await evidenceFields.nth(2).fill('1');
await evidenceFields.nth(3).fill('wallet-smoke');
await evidenceFields.nth(4).fill('Wallet smoke');
await evidenceFields.nth(5).fill('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
await walletPage.getByRole('button', { name: 'Register evidence', exact: true }).last().click();
const wrongNetworkWrite = await walletPage.locator('.field-error').innerText();
await walletPage.evaluate(() => window.__palinodeWalletTest.setAccount('0x2222222222222222222222222222222222222222'));
await walletPage.waitForTimeout(120);
const switchedAccount = await walletPage.locator('.wallet-button').textContent();
await walletPage.evaluate(() => window.__palinodeWalletTest.setChain('0xf22f'));
await walletPage.waitForTimeout(120);
const correctNetwork = await walletPage.locator('.network-chip').innerText();
await walletPage.locator('.wallet-button').click();
const walletDisconnected = await walletPage.locator('.wallet-button').textContent();
summary.wallet = { walletConnected, wrongNetwork, wrongNetworkWrite, switchedAccount, correctNetwork, walletDisconnected };
await walletContext.unrouteAll({ behavior: 'ignoreErrors' });
await walletContext.close();

await writeFile(summaryFile, JSON.stringify(summary, null, 2));
await browser.close();
console.log(JSON.stringify(summary, null, 2));
