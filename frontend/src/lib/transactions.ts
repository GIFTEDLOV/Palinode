import type { TrackedTransaction } from '../types';

export const TERMINAL_PHASES = ['FINALIZED SUCCESS', 'FINALIZED ERROR', 'UNDETERMINED'] as const;

export function isTerminalTransaction(transaction: TrackedTransaction) {
  return (TERMINAL_PHASES as readonly string[]).includes(transaction.phase);
}

export function mergeTrackedTransaction(current: TrackedTransaction[], next: TrackedTransaction[]) {
  const updates = new Map(next.map((transaction) => [transaction.id, transaction]));
  return [...current.map((transaction) => updates.get(transaction.id) || transaction), ...next.filter((transaction) => !current.some((item) => item.id === transaction.id))]
    .slice(0, 20);
}

export function resumableTransactions(current: TrackedTransaction[]) {
  return current.filter((transaction) => !isTerminalTransaction(transaction));
}

export function persistenceRecord(transaction: TrackedTransaction) {
  return { id: transaction.id, submittedAt: transaction.submittedAt, method: transaction.method };
}
