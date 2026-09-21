import type { EdgeRecord, NodeRecord } from '../types';

export function normalizeGraph(nodes: NodeRecord[], edges: EdgeRecord[]) {
  const nodeIds = new Set(nodes.map((node) => node.node_id));
  const validEdges = edges.filter((edge) => nodeIds.has(edge.parent_node_id) && nodeIds.has(edge.child_node_id) && edge.parent_node_id !== edge.child_node_id);
  return { nodes, edges: validEdges };
}

export function downstreamOf(root: string, nodes: NodeRecord[], edges: EdgeRecord[]) {
  const nodeById = new Map(nodes.map((node) => [node.node_id, node]));
  const results: { node: NodeRecord; distance: number; edge: EdgeRecord }[] = [];
  const queue = [{ id: root, distance: 0 }];
  const seen = new Set([root]);
  while (queue.length) {
    const current = queue.shift();
    if (!current) break;
    for (const edge of edges.filter((candidate) => candidate.parent_node_id === current.id)) {
      const node = nodeById.get(edge.child_node_id);
      if (!node || seen.has(node.node_id)) continue;
      seen.add(node.node_id);
      const distance = current.distance + 1;
      results.push({ node, distance, edge });
      queue.push({ id: node.node_id, distance });
    }
  }
  return results;
}

export type CanonicalImpact = {
  node: NodeRecord;
  distance: number;
  edge: EdgeRecord;
  caseId: string;
  causeId: string;
  effect: string;
};

/**
 * Canonical impact is deliberately narrower than graph reachability.  A node
 * is affected only when the contract's individually keyed cause mapping names
 * this case; a reachable CORROBORATES/CONTRADICTS node remains related only.
 */
export function canonicalImpactFromCauses(root: string, caseId: string, nodes: NodeRecord[], edges: EdgeRecord[], causeSlots: Record<string, string[]>) {
  const reachable = downstreamOf(root, nodes, edges);
  return reachable.flatMap(({ node, distance, edge }) => {
    const matching = (causeSlots[node.node_id] || []).filter((slot) => slot.startsWith(`${caseId}|`));
    return matching.map((slot) => {
      const [, effect = 'UNKNOWN'] = slot.split('|');
      return { node, distance, edge, caseId, causeId: caseId, effect } satisfies CanonicalImpact;
    });
  });
}
