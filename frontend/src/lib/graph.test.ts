import { describe, expect, it } from 'vitest';
import { canonicalImpactFromCauses, downstreamOf, normalizeGraph } from './graph';
import type { EdgeRecord, NodeRecord } from '../types';

const node = (id: string): NodeRecord => ({ node_id: id, node_type: 'CLAIM', title: id, subject_id: '', creation_sequence: id, reliance_status: 'ACTIVE', authentication_status: 'UNASSESSED', assessment_status: 'UNASSESSED', status: 'ACTIVE', source_uri: '' });
const edge = (parent: string, child: string, relationship: EdgeRecord['relationship'] = 'REQUIRES'): EdgeRecord => ({ edge_id: `${parent}-${child}`, parent_node_id: parent, child_node_id: child, relationship, creation_sequence: child, active: 'true' });

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

  it('does not call generic reachability canonical impact', () => {
    const nodes = ['root', 'corroborating', 'contradicting'].map(node);
    const edges = [edge('root', 'corroborating', 'CORROBORATES'), edge('root', 'contradicting', 'CONTRADICTS')];
    expect(canonicalImpactFromCauses('root', 'case-a', nodes, edges, {})).toEqual([]);
  });

  it('renders only descendants with an individually keyed active cause', () => {
    const nodes = ['root', 'claim', 'decision'].map(node);
    const edges = [edge('root', 'claim'), edge('claim', 'decision')];
    const impact = canonicalImpactFromCauses('root', 'case-a', nodes, edges, { claim: ['case-a|QUESTIONED'] });
    expect(impact).toHaveLength(1);
    expect(impact[0]).toMatchObject({ node: nodes[1], caseId: 'case-a', effect: 'QUESTIONED' });
  });
});
