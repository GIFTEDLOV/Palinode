import { describe, expect, it } from 'vitest';
import { asRecord, formatStatus, pageMeta, pageSlots, statusClass } from './utils';

describe('bounded read helpers', () => {
  it('extracts only declared page slots and stops at a non-advancing cursor', () => {
    expect(pageSlots({ count: '2', slot_0: 'a', slot_1: 'b', slot_2: 'ignored' })).toEqual(['a', 'b']);
    expect(pageMeta({ count: '2', next_cursor: '4' }, 2)).toEqual({ nextCursor: 4, exhausted: false });
    expect(pageMeta({ count: '2', next_cursor: '2' }, 2).exhausted).toBe(true);
  });

  it('rejects object-shaped readback from becoming an accidental record', () => {
    expect(asRecord(null)).toEqual({});
    expect(asRecord({ answer: 42 })).toEqual({ answer: '42' });
  });

  it('renders statuses with semantic classes', () => {
    expect(formatStatus('SOURCE_UNAVAILABLE')).toBe('Source Unavailable');
    expect(statusClass('INVALIDATED')).toContain('danger');
    expect(statusClass('CLEARED')).toContain('good');
  });
});
