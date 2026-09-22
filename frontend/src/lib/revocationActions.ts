import type { RevocationCase } from '../types';

export type RevocationActionState = {
  canAssess: boolean;
  canRetry: boolean;
  canProcessImpact: boolean;
  isComplete: boolean;
};

export function revocationActionState(item: Pick<RevocationCase, 'case_status' | 'target_authentication_status'>): RevocationActionState {
  const isComplete = item.case_status === 'COMPLETE';
  const canAssess = !isComplete
    && (item.case_status === 'OPEN' || item.case_status === 'INCONCLUSIVE')
    && item.target_authentication_status === 'CLEARED';
  return {
    canAssess,
    canRetry: item.case_status === 'INCONCLUSIVE' && !isComplete,
    canProcessImpact: item.case_status === 'PROPAGATING',
    isComplete,
  };
}
