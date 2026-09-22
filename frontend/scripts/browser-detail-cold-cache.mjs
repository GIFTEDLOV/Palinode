/* global process, Buffer, URL, console */
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const base = process.env.PALINODE_LOCAL_URL || 'http://127.0.0.1:4175';
const repoRoot = path.resolve(process.cwd(), '..');
const targetCase = '86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534';
const fixture = JSON.parse(await readFile(path.join(repoRoot, 'frontend', 'tests', 'fixtures', 'v4-rpc', 'responses.json'), 'utf8'));
const outputFile = path.join(repoRoot, 'artifacts', 'browser-qa', 'detail-cold-cache.json');
const pageMethods = ['get_node_ids_page', 'get_edge_ids_page', 'get_authority_ids_page', 'get_case_ids_page', 'get_recovery_ids_page'];
function keyFor(payload) { return JSON.stringify({ ...payload, id: 0 }); }
function encodedText(payload) {
  const data = String(payload.params?.[0]?.data || '').replace(/^0x/, '');
  try { return Buffer.from(data, 'hex').toString('utf8'); } catch { return ''; }
}
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const errors = [];
let global429 = 0;
context.on('page', (page) => {
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error' && !/429|rate limit|throttl/i.test(message.text())) errors.push(message.text()); });
});
await context.route('**/api/rpc**', async (route) => {
  const request = route.request();
  if (request.method() !== 'POST') return route.continue();
  const payload = JSON.parse(request.postData() || '{}');
  if (payload.method !== 'gen_call') return route.continue();
  const encoded = encodedText(payload);
  if (pageMethods.some((method) => encoded.includes(method))) {
    global429 += 1;
    return route.fulfill({ status: 429, headers: { 'content-type': 'application/json', 'retry-after': '2' }, body: JSON.stringify({ jsonrpc: '2.0', id: payload.id, error: { code: -32005, message: 'deterministic cold-cache throttle' } }) });
  }
  const entry = fixture.responses[keyFor(payload)];
  if (!entry) throw new Error('Missing V4 fixture response for ' + encoded);
  return route.fulfill({ status: entry.status, headers: entry.headers, body: entry.body });
});
const page = await context.newPage();
await page.goto(new URL('/app/revocations/' + targetCase, base).toString(), { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#root');
await page.getByText('OPERATOR WALLET SMOKE', { exact: true }).waitFor({ timeout: 10_000 });
const body = await page.locator('body').innerText();
if (body.includes('Review case not found')) throw new Error('Cold-cache detail incorrectly rendered Not Found.');
if (!body.includes('Completed-case state-neutral write')) throw new Error('Completed-case wallet panel did not render.');
if (!body.includes(targetCase)) throw new Error('Target case ID was not rendered.');
if (errors.length) throw new Error('Unexpected browser errors: ' + errors.join(' | '));
const result = { result: 'PASS', targetCase, global429, directRecordRendered: true, notFoundRendered: false, walletPanelVisible: true, consoleErrors: errors.length };
await mkdir(path.dirname(outputFile), { recursive: true });
await writeFile(outputFile, JSON.stringify(result, null, 2));
await context.close();
await browser.close();
console.log(JSON.stringify(result, null, 2));
