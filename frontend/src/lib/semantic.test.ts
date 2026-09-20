import { describe, expect, it } from 'vitest';
import { isSemanticResult, safeSemanticResult } from './semantic';

const valid = { result_status: 'CONCLUSIVE', change_authentic: true, same_subject: true, original_evidence_affected: true, materiality: 'MATERIAL', root_effect: 'INVALIDATE', reason_code: 'MATERIAL_WITHDRAWAL' };

describe('strict semantic result boundary', () => {
  it('accepts the exact canonical material result', () => {
    expect(isSemanticResult(valid)).toBe(true);
    expect(safeSemanticResult(valid)?.materiality).toBe('MATERIAL');
  });

  it.each(['MATERIAL_REVOCATION', 'MATERIAL_CHANGE', 'material', ' MATERIAL ', 'unknown'])('rejects invented or non-canonical materiality %s', (materiality) => {
    expect(isSemanticResult({ ...valid, materiality })).toBe(false);
  });

  it.each([null, true, 1])('rejects non-object semantic results: %s', (value) => {
    expect(isSemanticResult(value)).toBe(false);
  });

  it('rejects wrong field types and missing fields', () => {
    expect(isSemanticResult({ ...valid, change_authentic: 'true' })).toBe(false);
    expect(isSemanticResult({ ...valid, reason_code: '' })).toBe(false);
    expect(isSemanticResult({ ...valid, root_effect: 'INVALIDATE_NOW' })).toBe(false);
    expect(isSemanticResult({ ...valid, debug: 'ignored' })).toBe(false);
  });
});
