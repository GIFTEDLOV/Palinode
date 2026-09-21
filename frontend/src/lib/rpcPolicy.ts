export const MAX_RPC_BODY_BYTES = 64 * 1024;
export const ALLOWED_RPC_METHODS = new Set([
  'eth_chainId',
  'net_version',
  'eth_blockNumber',
  'eth_getTransactionCount',
  'eth_estimateGas',
  'gen_call',
  'gen_getTransaction',
  'gen_getTransactionStatus',
  'gen_getTransactionLifecycle',
  'gen_getTransactionReceipt',
  'gen_getContractSchema',
]);

export type RpcRequest = { jsonrpc: '2.0'; id: string | number | null; method: string; params?: unknown[] };
export type RpcValidation = { ok: true; request: RpcRequest } | { ok: false; status: number; message: string };

export function validateRpcPayload(body: string): RpcValidation {
  const bytes = new TextEncoder().encode(body).byteLength;
  if (bytes > MAX_RPC_BODY_BYTES) return { ok: false, status: 413, message: 'RPC request body exceeds the PALINODE limit.' };
  let value: unknown;
  try { value = JSON.parse(body); } catch { return { ok: false, status: 400, message: 'Malformed JSON-RPC body.' }; }
  if (!value || typeof value !== 'object' || Array.isArray(value)) return { ok: false, status: 400, message: 'JSON-RPC batches are not supported.' };
  const record = value as Record<string, unknown>;
  if (record.jsonrpc !== '2.0' || typeof record.method !== 'string' || !ALLOWED_RPC_METHODS.has(record.method)) return { ok: false, status: 403, message: 'JSON-RPC method is not allowed.' };
  if (record.params !== undefined && !Array.isArray(record.params)) return { ok: false, status: 400, message: 'JSON-RPC params must be an array.' };
  const id = record.id === null || typeof record.id === 'string' || typeof record.id === 'number' ? record.id : null;
  return { ok: true, request: { jsonrpc: '2.0', id, method: record.method, params: record.params as unknown[] | undefined } };
}
