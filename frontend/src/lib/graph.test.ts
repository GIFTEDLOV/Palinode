import { describe, expect, it } from 'vitest';
import { downstreamOf, normalizeGraph } from './graph';
import type { EdgeRecord, NodeRecord } from '../types';

const node = (id: string): NodeRecord => ({ node_id: id, node_type: 'CLAIM', title: id, subject_id: '', creation_sequence: id, reliance_status: 'ACTIVE', authentication_status: 'UNASSESSED', assessment_status: 'UNASSESSED', status: 'ACTIVE', source_uri: '' });
const edge = (parent: string, child: string): EdgeRecord => ({ edge_id: `${parent}-${child}`, parent_node_id: parent, child_node_id: child, relationship: 'REQUIRES', creation_sequence: child, active: 'true' });

describe('canonical graph read model', () => {
  it('drops orphaned edges rather than inventing nodes', () => {
    const result = normalizeGraph([node('a'), node('b')], [edge('a', 'b'), edge('b', 'missing')]);
    expect(result.edges).toHaveLength(1);
  });

  it('computes a bounded, cycle-safe downstream view', () => {
    const nodes = ['a', 'b', 'c'].map(node);
    const result = downstreamOf('a', nodes, [edge('a', 'b'), edge('b', 'c'), edge('c', 'a')]);
    expect(result.map((item) => item.node.node_id)).toEqual(['b', 'c']);
    expect(result.map((item) => item.distance)).toEqual([1, 2]);
  });
});
