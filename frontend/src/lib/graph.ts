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
