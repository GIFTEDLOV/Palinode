import { describe, expect, it } from 'vitest';
import { protocolPhase, txSnapshot } from './client';
import type { TrackedTransaction } from '../types';

const prior: TrackedTransaction = { id: '0xabc', label: 'semantic review', method: 'assess_revocation', args: ['case'], phase: 'SUBMITTED', protocolStatus: 'SUBMITTED', executionResult: 'NOT_VOTED', result: '—', submittedAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z' };

describe('GenLayer lifecycle adapter', () => {
  it('maps protocol phases without treating ACCEPTED as final', () => {
    expect(protocolPhase('PENDING', 'NOT_VOTED')).toBe('PENDING');
    expect(protocolPhase('PROPOSING', 'NOT_VOTED')).toBe('PROPOSING');
    expect(protocolPhase('COMMITTING', 'NOT_VOTED')).toBe('COMMITTING');
    expect(protocolPhase('REVEALING', 'NOT_VOTED')).toBe('REVEALING');
    expect(protocolPhase('ACCEPTED', 'NOT_VOTED')).toBe('ACCEPTED / PROVISIONAL');
    expect(protocolPhase('READY_TO_FINALIZE', 'NOT_VOTED')).toBe('FINALIZATION AVAILABLE');
    expect(protocolPhase('FINALIZED', 'FINISHED_WITH_RETURN')).toBe('FINALIZED SUCCESS');
    expect(protocolPhase('FINALIZED', 'FINISHED_WITH_ERROR')).toBe('FINALIZED ERROR');
  });

  it('requires final execution success for application success', () => {
    expect(txSnapshot({ statusName: 'FINALIZED', txExecutionResultName: 'FINISHED_WITH_RETURN', resultName: 'ok' }, prior).phase).toBe('FINALIZED SUCCESS');
    expect(txSnapshot({ statusName: 'FINALIZED', txExecutionResultName: 'FINISHED_WITH_ERROR' }, prior).phase).toBe('FINALIZED ERROR');
  });
});
