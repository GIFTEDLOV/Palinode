import type { RawRecord } from '../types';

export function asRecord(value: unknown): RawRecord {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, String(item ?? '')]));
}

export function pageSlots(value: unknown): string[] {
  const record = asRecord(value);
  const count = Math.max(0, Number(record.count ?? 0));
  return Array.from({ length: count }, (_, index) => record[`slot_${index}`]).filter(Boolean);
}

export function pageMeta(value: unknown, cursor: number) {
  const record = asRecord(value);
  const nextCursor = Number(record.next_cursor ?? cursor);
  const count = Number(record.count ?? 0);
  return { nextCursor, exhausted: count === 0 || nextCursor <= cursor };
}

export function truncate(value: string, left = 8, right = 6) {
  if (!value) return '—';
  if (value.length <= left + right + 1) return value;
  return `${value.slice(0, left)}…${value.slice(-right)}`;
}

export function titleCase(value: string) {
  return value.toLowerCase().replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatDate(value?: string) {
  if (!value) return '—';
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export function formatStatus(value?: string) {
  return titleCase(value || 'UNKNOWN');
}

export function statusClass(value?: string) {
  const normalized = (value || '').toLowerCase();
  if (normalized.includes('invalid') || normalized.includes('error') || normalized.includes('reject')) return 'status status-danger';
  if (normalized.includes('question') || normalized.includes('review') || normalized.includes('quarant') || normalized.includes('pending') || normalized.includes('inconclusive')) return 'status status-warn';
  if (normalized.includes('clear') || normalized.includes('active') || normalized.includes('success') || normalized.includes('final')) return 'status status-good';
  if (normalized.includes('super') || normalized.includes('recover')) return 'status status-violet';
  return 'status status-neutral';
}

export function pick<T>(record: RawRecord, key: string, fallback = '—'): T | string {
  return record[key] || fallback;
}
