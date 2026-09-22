export const READ_BACKOFF_MS = [1_500, 4_000] as const;

export function isUpstreamThrottle(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error ?? '');
  return /(?:\b429\b|rate[ -]?limit|too many requests|throttl|backpressure)/i.test(message);
}

export function readBackoffMs(attempt: number): number {
  return READ_BACKOFF_MS[Math.min(Math.max(attempt, 0), READ_BACKOFF_MS.length - 1)];
}

export async function retryRead<T>(operation: () => Promise<T>, onBackoff?: (delayMs: number) => void): Promise<T> {
  let attempt = 0;
  while (true) {
    try {
      return await operation();
    } catch (error) {
      if (!isUpstreamThrottle(error) || attempt >= READ_BACKOFF_MS.length) throw error;
      const delayMs = readBackoffMs(attempt);
      onBackoff?.(delayMs);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      attempt += 1;
    }
  }
}
