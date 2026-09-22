import { describe, expect, it } from 'vitest';
import { CHAIN_ID, CONTRACT_ADDRESS } from '../config';
import { assertSafeProcessImpactDescriptor, createPendingWriteDescriptor } from './writeDescriptor';

const caseId = '86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534';

describe('confirmed wallet write descriptors', () => {
  it('binds the exact safe V4 action', () => {
    const descriptor = createPendingWriteDescriptor({ label: 'Process completed case', method: 'process_impact', args: [caseId, 1] });
    expect(descriptor).toMatchObject({ contract: CONTRACT_ADDRESS, method: 'process_impact', args: [caseId, 1], value: 0n, chainId: CHAIN_ID });
    expect(() => assertSafeProcessImpactDescriptor(descriptor, caseId)).not.toThrow();
  });

  it('rejects method substitution before provider dispatch', () => {
    const descriptor = createPendingWriteDescriptor({ label: 'Assess review', method: 'assess_revocation', args: [caseId] });
    expect(() => assertSafeProcessImpactDescriptor(descriptor, caseId)).toThrow(/process_impact/);
  });
});
