/* global console, process, URL */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const repoRoot = path.resolve(process.cwd(), '..');
const outputDir = path.join(repoRoot, 'frontend', 'tests', 'fixtures', 'v4-rpc');
const outputFile = path.join(outputDir, 'responses.json');
const productionUrl = process.env.PALINODE_PRODUCTION_URL || 'https://palinode-app.vercel.app';
const contractAddress = '0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b';

function keyFor(payload) {
  return JSON.stringify({ ...payload, id: 0 });
}

const state = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'final-state.json'), 'utf8'));
const authority = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'authority.json'), 'utf8'));
const thirdParty = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'third-party-challenge.json'), 'utf8'));
const authorityC = JSON.parse(await readFile(path.join(repoRoot, 'evidence', 'studionet', 'v4', 'authority-c.json'), 'utf8'));
const routes = process.env.PALINODE_CAPTURE_DYNAMIC_ONLY === 'true'
  ? [`/app/evidence/${state.v1_id}`, `/app/revocations/${state.revocation_case_id}`, `/app/revocations/${thirdParty.case_id}`, `/app/recoveries/${state.recovery_id}`, `/app/authorities/${authority.authority_id}`, `/app/authorities/${authorityC.authority_c_id}`]
  : [
  '/', '/app', '/app/graph', `/app/evidence/${state.v1_id}`, '/app/revocations',
  `/app/revocations/${state.revocation_case_id}`, '/app/recoveries', `/app/recoveries/${state.recovery_id}`,
  '/app/authorities', `/app/authorities/${authority.authority_id}`, '/app/activity', '/app/proof', '/app/integrate', '/docs',
  ];
let prior = {};
try { prior = JSON.parse(await readFile(outputFile, 'utf8')); } catch { /* first capture */ }
const responses = { ...(prior.responses || {}) };
const requests = {};
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
await context.route('**/api/rpc**', async (route) => {
  const request = route.request();
  if (request.method() !== 'POST') return route.continue();
  const payload = JSON.parse(request.postData() || '{}');
  if (payload.method !== 'gen_call') return route.continue();
  const key = keyFor(payload);
  requests[key] = { ...payload, id: 0 };
  if (responses[key]) return route.fulfill({ status: responses[key].status, headers: responses[key].headers, body: responses[key].body });
  const upstream = await route.fetch();
  const body = await upstream.text();
  const headers = Object.fromEntries(['content-type'].map((name) => [name, upstream.headers()[name] || 'application/json']));
  if (upstream.status() === 429) throw new Error('Live capture stopped: upstream returned HTTP 429.');
  responses[key] = { status: upstream.status(), headers, body };
  await mkdir(outputDir, { recursive: true });
  await writeFile(outputFile, JSON.stringify({ schema: 1, contract: contractAddress, source: productionUrl, recordedAt: new Date().toISOString(), responses }, null, 2));
  return route.fulfill({ status: upstream.status(), headers, body });
});
const page = await context.newPage();
for (const pathname of routes) {
  console.log(`capture ${pathname}`);
  await page.goto(new URL(pathname, productionUrl).toString(), { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#root');
  await page.waitForTimeout(5_000);
}
await context.unrouteAll({ behavior: 'ignoreErrors' });
await context.close();
await browser.close();
await mkdir(outputDir, { recursive: true });
await writeFile(outputFile, JSON.stringify({ schema: 1, contract: contractAddress, source: productionUrl, recordedAt: new Date().toISOString(), responses }, null, 2));
console.log(JSON.stringify({ result: 'PASS', contract: contractAddress, routes: routes.length, requests: Object.keys(requests).length, responses: Object.keys(responses).length, outputFile }, null, 2));
