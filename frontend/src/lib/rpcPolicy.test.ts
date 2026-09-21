import { describe, expect, it } from 'vitest';
import { MAX_RPC_BODY_BYTES, validateRpcPayload } from './rpcPolicy';

describe('public RPC relay policy', () => {
  it('allows bounded canonical reads and transaction status reads', () => {
    expect(validateRpcPayload(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'gen_call', params: [] }))).toMatchObject({ ok: true, request: { method: 'gen_call' } });
    expect(validateRpcPayload(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'gen_getTransactionStatus', params: [{ txId: '0x1' }] }))).toMatchObject({ ok: true, request: { method: 'gen_getTransactionStatus' } });
  });

  it('blocks arbitrary write relay methods, malformed JSON, batches, and oversized bodies', () => {
    expect(validateRpcPayload(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'eth_sendRawTransaction', params: [] }))).toMatchObject({ ok: false });
    expect(validateRpcPayload('{bad json')).toMatchObject({ ok: false });
    expect(validateRpcPayload(JSON.stringify([{ jsonrpc: '2.0', id: 1, method: 'gen_call', params: [] }]))).toMatchObject({ ok: false });
    expect(validateRpcPayload('x'.repeat(MAX_RPC_BODY_BYTES + 1))).toMatchObject({ ok: false, status: 413 });
  });
});
