import { useEffect, useState } from 'react';

export type CanonicalDetailStatus = 'LOADING' | 'READY' | 'DEGRADED' | 'NOT_FOUND';

export type CanonicalDetailState<T> = {
  status: CanonicalDetailStatus;
  record?: T;
  error?: unknown;
};

export function isCanonicalAbsenceError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error || '');
  return /(malformed|invalid)\s+(case|recovery|node|authority)\s+id|(?:case|recovery case|node|authority)\s+(?:does not exist|not found|unknown)/i.test(message);
}

export function resolveCanonicalDetail<T>(input: {
  snapshotRecord?: T;
  directStatus: 'pending' | 'success' | 'missing' | 'error';
  directRecord?: T;
  error?: unknown;
}): CanonicalDetailState<T> {
  if (input.snapshotRecord) return { status: 'READY', record: input.snapshotRecord };
  if (input.directStatus === 'pending') return { status: 'LOADING' };
  if (input.directStatus === 'success' && input.directRecord) return { status: 'READY', record: input.directRecord };
  if (input.directStatus === 'missing') return { status: 'NOT_FOUND' };
  return { status: 'DEGRADED', error: input.error };
}

export function useCanonicalDetail<T>(
  id: string | undefined,
  snapshotRecord: T | undefined,
  readDirect: (id: string) => Promise<T>,
): CanonicalDetailState<T> & { retry: () => void } {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<CanonicalDetailState<T>>(() => resolveCanonicalDetail({ snapshotRecord, directStatus: snapshotRecord ? 'success' : 'pending' }));

  useEffect(() => {
    let active = true;
    if (!id) {
      return () => { active = false; };
    }
    if (snapshotRecord) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setState({ status: 'READY', record: snapshotRecord });
      return () => { active = false; };
    }
    setState({ status: 'LOADING' });
    void readDirect(id).then((record) => {
      if (active) setState(record ? { status: 'READY', record } : { status: 'NOT_FOUND' });
    }).catch((error: unknown) => {
      if (!active) return;
      setState(isCanonicalAbsenceError(error) ? { status: 'NOT_FOUND' } : { status: 'DEGRADED', error });
    });
    return () => { active = false; };
  }, [attempt, id, readDirect, snapshotRecord]);

  return { ...state, retry: () => setAttempt((value) => value + 1) };
}
