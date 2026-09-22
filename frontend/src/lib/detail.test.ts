import { describe, expect, it } from 'vitest';
import { isCanonicalAbsenceError, resolveCanonicalDetail } from './detail';

describe('canonical detail loading model', () => {
  it('does not infer absence while the global registry is empty or refreshing', () => {
    expect(resolveCanonicalDetail({ directStatus: 'pending' }).status).toBe('LOADING');
  });

  it('uses a direct canonical record when the snapshot has no matching item', () => {
    const record = { id: 'case-86' };
    expect(resolveCanonicalDetail({ directStatus: 'success', directRecord: record })).toEqual({ status: 'READY', record });
  });

  it('keeps a cached detail record visible when a refresh is throttled', () => {
    const record = { id: 'cached-case' };
    expect(resolveCanonicalDetail({ snapshotRecord: record, directStatus: 'error', error: new Error('429') })).toEqual({ status: 'READY', record });
  });

  it('returns professional degraded state when no detail cache exists', () => {
    expect(resolveCanonicalDetail({ directStatus: 'error', error: new Error('temporary upstream unavailable') }).status).toBe('DEGRADED');
  });

  it('renders not found only after a successful canonical absence result', () => {
    expect(resolveCanonicalDetail({ directStatus: 'missing' }).status).toBe('NOT_FOUND');
  });

  it.each(['revocation case', 'recovery case', 'evidence record', 'authority record', 'decision record'])('applies the same state machine to %s', () => {
    expect(resolveCanonicalDetail({ directStatus: 'pending' }).status).toBe('LOADING');
    expect(resolveCanonicalDetail({ directStatus: 'missing' }).status).toBe('NOT_FOUND');
  });

  it('classifies only explicit V4 canonical absence errors as not found', () => {
    expect(isCanonicalAbsenceError(new Error('execution reverted: case does not exist'))).toBe(true);
    expect(isCanonicalAbsenceError(new Error('execution reverted: malformed case ID'))).toBe(true);
    expect(isCanonicalAbsenceError(new Error('HTTP 429: too many requests'))).toBe(false);
    expect(isCanonicalAbsenceError(new Error('network timeout'))).toBe(false);
  });
});
