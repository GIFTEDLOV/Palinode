/* global process, console, Buffer, URL, window */
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const base = process.env.PALINODE_LOCAL_URL || 'http://127.0.0.1:4173';
const repoRoot = path.resolve(process.cwd(), '..');
const caseId = '86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534';
const fixture = JSON.parse(await readFile(path.join(repoRoot, 'frontend', 'tests', 'fixtures', 'v4-rpc', 'responses.json'), 'utf8'));
const errors = [];
const walletAddress = '0x1111111111111111111111111111111111111111';
const chainId = '0xf22f';

function keyFor(payload) { return JSON.stringify({ ...payload, id: 0 }); }
function encodedText(payload) {
  const data = String(payload.params?.[0]?.data || '').replace(/^0x/, '');
  try { return Buffer.from(data, 'hex').toString('utf8'); } catch { return ''; }
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
await context.route('**/favicon.ico', (route) => route.fulfill({ status: 204, body: '' }));
await context.addInitScript(({ walletAddress, chainId }) => {
  const requests = [];
  const listeners = new Map();
  const provider = {
    request: async ({ method, params }) => {
      requests.push({ method, params });
      if (method === 'eth_chainId') return chainId;
      if (method === 'eth_accounts' || method === 'eth_requestAccounts') return [walletAddress];
      if (method === 'wallet_switchEthereumChain') return null;
      if (method === 'eth_estimateGas') return '0x5208';
      if (method === 'eth_gasPrice') return '0x1';
      if (method === 'eth_sendTransaction') return '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
      if (method === 'eth_getTransactionCount') return '0x0';
      if (method === 'eth_getBalance') return '0x0';
      if (method === 'net_version') return '61999';
      return null;
    },
    on: (event, listener) => { listeners.set(event, listener); },
    removeListener: (event) => { listeners.delete(event); },
  };
  window.ethereum = provider;
  window.__palinodeWalletRequests = requests;
}, { walletAddress, chainId });

context.on('page', (page) => {
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
});
await context.route('**/api/rpc**', async (route) => {
  const request = route.request();
  if (request.method() !== 'POST') return route.continue();
  const payload = JSON.parse(request.postData() || '{}');
  if (payload.method === 'gen_getTransactionLifecycle') {
    return route.fulfill({ status: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: payload.id, result: { storedStatus: 'PENDING' } }) });
  }
  if (payload.method === 'eth_getTransactionByHash') {
    return route.fulfill({ status: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: payload.id, result: null }) });
  }
  if (payload.method === 'eth_estimateGas' || payload.method === 'eth_gasPrice' || payload.method === 'eth_getTransactionCount') {
    return route.fulfill({ status: 200, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: payload.id, result: payload.method === 'eth_gasPrice' ? '0x1' : payload.method === 'eth_getTransactionCount' ? '0x0' : '0x5208' }) });
  }
  if (payload.method !== 'gen_call') return route.continue();
  const entry = fixture.responses[keyFor(payload)];
  if (!entry) throw new Error('Missing V4 fixture response for ' + encodedText(payload));
  return route.fulfill({ status: entry.status, headers: entry.headers, body: entry.body });
});

const page = await context.newPage();
await page.goto(new URL('/app/revocations/' + caseId, base).toString(), { waitUntil: 'domcontentloaded' });
await page.getByText('OPERATOR WALLET SMOKE', { exact: true }).waitFor({ timeout: 10_000 });
if (await page.getByRole('button', { name: 'Assess consensus' }).count()) throw new Error('Completed case still exposes Assess consensus.');
const smokeButton = page.getByRole('button', { name: 'Approve one safe no-op write' });
await smokeButton.click();
await page.getByRole('dialog').waitFor();
const dialogText = await page.getByRole('dialog').innerText();
if (!dialogText.includes('process_impact') || !dialogText.includes(caseId) || !dialogText.toLowerCase().includes('max_steps') || !dialogText.includes('SIGN EXACT NO-OP')) throw new Error('Safe confirmation descriptor is incomplete.');
const beforeCancel = await page.evaluate(() => window.__palinodeWalletRequests.filter((request) => request.method === 'eth_sendTransaction' || request.method === 'gen_sendTransaction'));
if (beforeCancel.length) throw new Error('Wallet provider was invoked before confirmation.');
await page.getByRole('button', { name: 'CANCEL' }).click();
if (await page.getByRole('dialog').count()) throw new Error('Cancel did not close the confirmation dialog.');
const afterCancel = await page.evaluate(() => window.__palinodeWalletRequests.filter((request) => request.method === 'eth_sendTransaction' || request.method === 'gen_sendTransaction'));
if (afterCancel.length) throw new Error('Cancel caused a wallet write.');
await smokeButton.click();
await page.getByRole('button', { name: 'SIGN EXACT NO-OP' }).click();
await page.waitForTimeout(1_500);
const requests = await page.evaluate(() => window.__palinodeWalletRequests);
const writeRequests = requests.filter((request) => request.method === 'eth_sendTransaction' || request.method === 'gen_sendTransaction');
if (writeRequests.length !== 1) throw new Error('Expected exactly one provider-backed write, got ' + writeRequests.length + ' requests=' + JSON.stringify(requests) + ' body=' + await page.locator('body').innerText());
const serializedWrite = JSON.stringify(writeRequests[0]);
const encodedWriteData = String(writeRequests[0].params?.[0]?.data || '').replace(/^0x/, '');
const decodedWriteData = Buffer.from(encodedWriteData, 'hex').toString('utf8');
if (!decodedWriteData.includes('process_impact') || !decodedWriteData.includes(caseId)) throw new Error('Provider write did not contain the expected process_impact case descriptor: ' + serializedWrite + ' decoded=' + decodedWriteData);
if (serializedWrite.includes('assess_revocation')) throw new Error('Provider dispatched the forbidden assess_revocation method.');
if (errors.length) throw new Error('Unexpected browser errors: ' + errors.join(' | '));
const result = { result: 'PASS', completedCase: caseId, assessButtonVisible: false, dialog: { method: 'process_impact', args: [caseId, 1], cancelProviderCalls: 0 }, providerWriteCount: writeRequests.length, providerWrite: writeRequests[0], unexpectedConsoleErrors: errors.length };
await context.close();
await browser.close();
console.log(JSON.stringify(result, null, 2));
