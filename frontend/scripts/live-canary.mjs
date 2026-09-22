/* global console, process, URL, document */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const productionUrl = process.env.PALINODE_PRODUCTION_URL || 'https://palinode-app.vercel.app';
const repoRoot = path.resolve(process.cwd(), '..');
const contract = '0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b';
const state = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'final-state.json'), 'utf8'));
const authority = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'authority.json'), 'utf8'));
const authorityC = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'authority-c.json'), 'utf8'));
const challenge = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'third-party-challenge.json'), 'utf8'));
const routes = [
  { name: 'landing', path: '/', expected: ['LIVE STUDIONET'] },
  { name: 'overview', path: '/app', expected: ['0x05243cB6'] },
  { name: 'graph', path: '/app/graph', expected: ['Dependency graph'] },
  { name: 'evidence-v1', path: `/app/evidence/${state.v1_id}`, expected: ['Fictional audit V1', 'CLEARED', 'SUPERSEDED'] },
  { name: 'source-revocation', path: `/app/revocations/${state.revocation_case_id}`, expected: ['MATERIAL_REVOCATION', 'INVALIDATE'] },
  { name: 'third-party-challenge', path: `/app/revocations/${challenge.case_id}`, expected: ['MATERIAL_THIRD_PARTY_CHALLENGE', 'QUESTION', 'INVALIDATE not allowed'] },
  { name: 'recovery', path: `/app/recoveries/${state.recovery_id}`, expected: ['RECOVERY_RESOLVED_SUPERSEDE', 'SUPERSEDE'] },
  { name: 'authority-c', path: `/app/authorities/${authorityC.authority_c_id}`, expected: ['palinode-reviewer-fixture.vercel.app', authorityC.authority_c_id.slice(0, 12)] },
  { name: 'proof', path: '/app/proof', expected: ['SOURCE_DIGEST_MISMATCH', 'MATERIAL_THIRD_PARTY_CHALLENGE', contract.slice(0, 12)] },
];
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
let rpc429 = 0;
const consoleErrors = [];
context.on('response', (response) => { if (response.status() === 429 && response.url().includes('/api/rpc')) rpc429 += 1; });
const page = await context.newPage();
page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
page.on('pageerror', (error) => consoleErrors.push(error.message));

async function waitForRoute(pathname, first) {
  let response;
  const link = !first ? page.locator(`a[href="${pathname}"]`).first() : null;
  if (link && await link.count()) {
    await link.click();
    await page.waitForURL(`**${pathname}`);
  } else {
    response = await page.goto(new URL(pathname, productionUrl).toString(), { waitUntil: 'domcontentloaded' });
  }
  await page.waitForSelector('#root');
  await page.waitForTimeout(2_000);
  await page.waitForFunction(() => !(document.body.innerText || '').includes('REFRESHING'), { timeout: 15_000 }).catch(() => undefined);
  if (response && response.status() !== 200) throw new Error(`${pathname}: HTTP ${response.status()}`);
  if (rpc429) throw new Error('Live canary stopped after upstream HTTP 429.');
}

const checked = [];
for (const [index, item] of routes.entries()) {
  console.log(`canary ${item.name}`);
  await waitForRoute(item.path, index === 0);
  const body = (await page.locator('body').innerText()).toLowerCase();
  for (const marker of item.expected) if (!body.includes(marker.toLowerCase())) throw new Error(`${item.name}: missing live marker ${marker}`);
  checked.push(item.path);
}
if (consoleErrors.length) throw new Error(`Live canary console errors: ${consoleErrors.join(' | ')}`);
const result = { result: 'PASS', productionUrl, contract, routes: checked, rpc429, consoleErrors: consoleErrors.length, authorityA: authority.authority_id, authorityC: authorityC.authority_c_id };
const output = path.join(repoRoot, 'artifacts', 'browser-qa', 'live-canary.json');
await mkdir(path.dirname(output), { recursive: true });
await writeFile(output, JSON.stringify(result, null, 2));
await context.close();
await browser.close();
console.log(JSON.stringify(result, null, 2));
