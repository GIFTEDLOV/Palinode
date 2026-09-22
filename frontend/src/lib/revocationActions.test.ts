import { describe, expect, it } from 'vitest';
import { revocationActionState } from './revocationActions';

describe('revocation action state machine', () => {
  it('allows assessment only for an open, cleared target', () => {
    expect(revocationActionState({ case_status: 'OPEN', target_authentication_status: 'CLEARED' })).toMatchObject({ canAssess: true, canRetry: false, canProcessImpact: false, isComplete: false });
  });

  it('blocks assessment for an open, non-cleared target', () => {
    expect(revocationActionState({ case_status: 'OPEN', target_authentication_status: 'PENDING' }).canAssess).toBe(false);
  });

  it('exposes only impact processing while propagating', () => {
    expect(revocationActionState({ case_status: 'PROPAGATING', target_authentication_status: 'CLEARED' })).toEqual({ canAssess: false, canRetry: false, canProcessImpact: true, isComplete: false });
  });

  it('exposes no normal protocol action after completion', () => {
    expect(revocationActionState({ case_status: 'COMPLETE', target_authentication_status: 'CLEARED' })).toEqual({ canAssess: false, canRetry: false, canProcessImpact: false, isComplete: true });
  });

  it('allows a retry only for an inconclusive case', () => {
    expect(revocationActionState({ case_status: 'INCONCLUSIVE', target_authentication_status: 'CLEARED' })).toMatchObject({ canAssess: true, canRetry: true, canProcessImpact: false });
  });
});
