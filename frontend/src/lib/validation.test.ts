import { describe, expect, it } from 'vitest';
import { firstError, hexDigest, httpsUrl, positiveInteger, supportedRelationship } from './validation';

describe('explicit write validation', () => {
  it('rejects malformed identity, URL, enum, and bounded integer inputs', () => {
    expect(hexDigest('abc')).toBeTruthy();
    expect(httpsUrl('http://example.test', 'Origin')).toContain('HTTPS');
    expect(supportedRelationship('MADE_UP')).toBeTruthy();
    expect(positiveInteger('0', 'max_steps', 32)).toBeTruthy();
    expect(positiveInteger('33', 'max_steps', 32)).toContain('32');
  });

  it('returns the first specific error and clears for valid values', () => {
    expect(firstError(null, 'second error')).toBe('second error');
    expect(firstError(null, undefined)).toBeNull();
    expect(hexDigest('a'.repeat(64))).toBeNull();
    expect(httpsUrl('https://example.test', 'Origin')).toBeNull();
  });
});
