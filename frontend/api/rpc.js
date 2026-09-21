const UPSTREAM = 'https://studio.genlayer.com/api';
const MAX_RPC_BODY_BYTES = 64 * 1024;
const ALLOWED_RPC_METHODS = new Set([
  'eth_chainId', 'net_version', 'eth_blockNumber', 'eth_getTransactionCount',
  'eth_estimateGas', 'gen_call', 'gen_getTransaction', 'gen_getTransactionStatus',
  'gen_getTransactionLifecycle', 'gen_getTransactionReceipt', 'gen_getContractSchema',
]);
const ALLOWED_ORIGINS = new Set([
  'https://palinode-app.vercel.app',
  'http://127.0.0.1:4173',
  'http://localhost:4173',
]);

function responseHeaders(request) {
  const origin = request.headers.origin;
  const headers = { 'cache-control': 'no-store', vary: 'Origin' };
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    headers['access-control-allow-origin'] = origin;
    headers['access-control-allow-methods'] = 'POST, OPTIONS';
    headers['access-control-allow-headers'] = 'content-type';
  }
  return headers;
}

function send(response, status, body, headers) {
  response.statusCode = status;
  Object.entries(headers).forEach(([key, value]) => response.setHeader(key, value));
  response.setHeader('content-type', 'application/json; charset=utf-8');
  response.end(JSON.stringify(body));
}

async function readBody(request) {
  const chunks = [];
  let length = 0;
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    length += buffer.length;
    if (length > MAX_RPC_BODY_BYTES) throw new Error('RPC request body exceeds the PALINODE limit.');
    chunks.push(buffer);
  }
  return Buffer.concat(chunks).toString('utf8');
}

function validate(body) {
  if (Buffer.byteLength(body, 'utf8') > MAX_RPC_BODY_BYTES) return { ok: false, status: 413, message: 'RPC request body exceeds the PALINODE limit.' };
  let value;
  try { value = JSON.parse(body); } catch { return { ok: false, status: 400, message: 'Malformed JSON-RPC body.' }; }
  if (!value || typeof value !== 'object' || Array.isArray(value)) return { ok: false, status: 400, message: 'JSON-RPC batches are not supported.' };
  if (value.jsonrpc !== '2.0' || typeof value.method !== 'string' || !ALLOWED_RPC_METHODS.has(value.method)) return { ok: false, status: 403, message: 'JSON-RPC method is not allowed.' };
  if (value.params !== undefined && !Array.isArray(value.params)) return { ok: false, status: 400, message: 'JSON-RPC params must be an array.' };
  return { ok: true, value };
}

export default async function handler(request, response) {
  const headers = responseHeaders(request);
  if (request.method === 'OPTIONS') { response.statusCode = 204; Object.entries(headers).forEach(([key, value]) => response.setHeader(key, value)); return response.end(); }
  if (request.method !== 'POST') return send(response, 405, { error: 'POST only' }, headers);
  let body;
  try { body = await readBody(request); } catch (error) { return send(response, 413, { error: error instanceof Error ? error.message : 'Request body rejected.' }, headers); }
  const validation = validate(body);
  if (!validation.ok) return send(response, validation.status, { error: validation.message }, headers);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15_000);
  try {
    const upstream = await fetch(UPSTREAM, { method: 'POST', headers: { 'content-type': 'application/json' }, body, signal: controller.signal });
    const upstreamBody = await upstream.text();
    response.statusCode = upstream.status;
    Object.entries(headers).forEach(([key, value]) => response.setHeader(key, value));
    response.setHeader('content-type', upstream.headers.get('content-type') || 'application/json');
    return response.end(upstreamBody);
  } catch (error) {
    return send(response, 502, { error: error instanceof Error && error.name === 'AbortError' ? 'Studionet RPC timed out.' : 'Studionet RPC is unavailable.' }, headers);
  } finally { clearTimeout(timeout); }
}
