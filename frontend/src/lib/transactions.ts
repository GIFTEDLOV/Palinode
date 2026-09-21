import type { TrackedTransaction } from '../types';

export const TERMINAL_PHASES = ['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED', 'CANCELED'] as const;
export const MAX_RECENT_COMPLETED = 20;

export function isTerminalTransaction(transaction: TrackedTransaction) {
  return (TERMINAL_PHASES as readonly string[]).includes(transaction.phase);
}

export function mergeTrackedTransaction(current: TrackedTransaction[], next: TrackedTransaction[]) {
  const updates = new Map(next.map((transaction) => [transaction.id, transaction]));
  const merged = [...current.map((transaction) => updates.get(transaction.id) || transaction), ...next.filter((transaction) => !current.some((item) => item.id === transaction.id))];
  const unresolved = merged.filter((transaction) => !isTerminalTransaction(transaction));
  const completed = merged.filter(isTerminalTransaction).slice(0, MAX_RECENT_COMPLETED);
  return [...unresolved, ...completed];
}

export function resumableTransactions(current: TrackedTransaction[]) {
  return current.filter((transaction) => !isTerminalTransaction(transaction));
}

export function persistenceRecord(transaction: TrackedTransaction) {
  return { id: transaction.id, submittedAt: transaction.submittedAt, method: transaction.method };
}

export function encodeTransactions(transactions: TrackedTransaction[]) {
  return JSON.stringify(transactions);
}

export function decodeTransactions(value: string | null): TrackedTransaction[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value) as unknown;
    return Array.isArray(parsed) ? parsed as TrackedTransaction[] : [];
  } catch {
    return [];
  }
}
