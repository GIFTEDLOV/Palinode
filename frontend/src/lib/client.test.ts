import { describe, expect, it } from 'vitest';
import { protocolPhase, trackingDelayedSnapshot, txSnapshot } from './client';
import type { TrackedTransaction } from '../types';
import type { GenLayerTransaction } from 'genlayer-js/types';

const prior: TrackedTransaction = { id: '0xabc', label: 'semantic review', method: 'assess_revocation', args: ['case'], phase: 'SUBMITTED', protocolStatus: 'SUBMITTED', executionResult: 'NOT_VOTED', result: '—', submittedAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z' };

describe('GenLayer lifecycle adapter', () => {
  it('maps protocol phases without treating ACCEPTED as final', () => {
    expect(protocolPhase('PENDING', 'NOT_VOTED')).toBe('PENDING');
    expect(protocolPhase('PROPOSING', 'NOT_VOTED')).toBe('PROPOSING');
    expect(protocolPhase('COMMITTING', 'NOT_VOTED')).toBe('COMMITTING');
    expect(protocolPhase('REVEALING', 'NOT_VOTED')).toBe('REVEALING');
    expect(protocolPhase('ACCEPTED', 'NOT_VOTED')).toBe('ACCEPTED / PROVISIONAL');
    expect(protocolPhase('APPEAL_COMMITTING', 'NOT_VOTED', 'Finalize')).toBe('FINALIZATION AVAILABLE');
    expect(protocolPhase('FINALIZED', 'FINISHED_WITH_RETURN')).toBe('FINALIZED SUCCESS');
    expect(protocolPhase('FINALIZED', 'FINISHED_WITH_ERROR')).toBe('FINALIZED ERROR');
  });

  it('requires final execution success for application success', () => {
    const success = { statusName: 'FINALIZED', txExecutionResultName: 'FINISHED_WITH_RETURN', resultName: 'ok' } as unknown as GenLayerTransaction;
    const failure = { statusName: 'FINALIZED', txExecutionResultName: 'FINISHED_WITH_ERROR' } as unknown as GenLayerTransaction;
    expect(txSnapshot(success, prior).phase).toBe('FINALIZED SUCCESS');
    expect(txSnapshot(failure, prior).phase).toBe('FINALIZED ERROR');
  });

  it('marks an unavailable status read as tracking delayed without exposing the transport error', () => {
    const delayed = trackingDelayedSnapshot({ ...prior, error: 'An unknown RPC error occurred. Version: viem@2.56.8' });
    expect(delayed.phase).toBe('TRACKING DELAYED');
    expect(delayed.error).toBeUndefined();
    expect(delayed.id).toBe(prior.id);
  });
});
