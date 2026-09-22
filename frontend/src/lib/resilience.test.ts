import { describe, expect, it, vi } from 'vitest';
import { isUpstreamThrottle, readBackoffMs, retryRead } from './resilience';

describe('upstream read resilience', () => {
  it('recognizes throttling without encoding a provider quota', () => {
    expect(isUpstreamThrottle(new Error('HTTP 429 from upstream'))).toBe(true);
    expect(isUpstreamThrottle(new Error('Rate limit exceeded'))).toBe(true);
    expect(isUpstreamThrottle(new Error('contract decode failed'))).toBe(false);
  });

  it('uses bounded backoff and succeeds after a transient throttle', async () => {
    vi.useFakeTimers();
    const operation = vi.fn().mockRejectedValueOnce(new Error('HTTP 429')).mockResolvedValueOnce('LIVE');
    const promise = retryRead(operation);
    await vi.advanceTimersByTimeAsync(readBackoffMs(0));
    await expect(promise).resolves.toBe('LIVE');
    expect(operation).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });
});
