import { describe, expect, it } from 'vitest';
import { mergeTrackedTransaction, persistenceRecord, resumableTransactions } from './transactions';
import type { TrackedTransaction } from '../types';

const tx = (id: `0x${string}`, phase: TrackedTransaction['phase']): TrackedTransaction => ({ id, label: 'test', method: 'register_node', args: [], phase, protocolStatus: phase, executionResult: 'NOT_VOTED', result: '—', submittedAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z' });

describe('finality-safe transaction model', () => {
  it('resumes only non-terminal transactions and never creates a replacement ID', () => {
    const active = tx('0xactive', 'PENDING');
    const done = tx('0xdone', 'FINALIZED SUCCESS');
    expect(resumableTransactions([active, done])).toEqual([active]);
    expect(persistenceRecord(active)).toEqual({ id: '0xactive', submittedAt: active.submittedAt, method: active.method });
  });

  it('merges polling updates by ID and bounds local history', () => {
    const current = [tx('0xactive', 'PENDING')];
    const updated = tx('0xactive', 'FINALIZED SUCCESS');
    const merged = mergeTrackedTransaction(current, [updated]);
    expect(merged).toHaveLength(1);
    expect(merged[0].phase).toBe('FINALIZED SUCCESS');
  });
});
