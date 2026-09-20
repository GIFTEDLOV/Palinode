# Graph model

## Nodes

Supported node types are exactly:

`EVIDENCE`, `CLAIM`, `DECISION`, `ATTESTATION`, and `AUTHORIZATION`.

Each node receives a contract-generated 64-character lowercase SHA-256 ID and
an immutable creation sequence from one monotonic sequence. The caller never
supplies a node ID. Evidence additionally stores HTTPS source URI, content
SHA-256, exact declared byte length, subject identifier, title, creator, and
transaction datetime.

## Edges

Supported dependency relationships are exactly:

`SUPPORTS`, `REQUIRES`, `DERIVED_FROM`, `QUALIFIES`, `AUTHORIZES`,
`CORROBORATES`, and `CONTRADICTS`.

An edge stores its own ID, parent, child, relationship, creation sequence, and
active flag. It is accepted only if both nodes exist, the nodes differ, the
relationship is supported, the identity tuple is not duplicated, and:

```text
node_sequence(parent) < node_sequence(child)
```

This is the exact DAG invariant. Since node sequences never change and all
supported writes enforce the inequality, every directed path strictly
increases in sequence. A directed cycle would require a strict increase around
the cycle and is therefore impossible without an unbounded graph traversal.

Per-node incoming and outgoing edge limits are 64. Global Phase 1 limits are
4096 nodes and 16,384 edges.

## Propagation policy

A material semantic result creates one deterministic root effect. It does not
automatically invalidate every descendant.

| Relationship | Root `INVALIDATE` | Root `QUESTION` | Rationale |
|---|---|---|---|
| `REQUIRES` | `QUARANTINED` | `UNDER_REVIEW` | Direct reliance on a required basis is blocked or reviewed |
| `DERIVED_FROM` | `UNDER_REVIEW` | `UNDER_REVIEW` | Derivation needs review, not automatic invalidation |
| `SUPPORTS` | `QUESTIONED` | `QUESTIONED` | Loss of support questions the child |
| `QUALIFIES` | `QUESTIONED` | `QUESTIONED` | A qualification change questions reliance |
| `AUTHORIZES` | `QUARANTINED` | `UNDER_REVIEW` | Direct authorization reliance is blocked or reviewed |
| `CORROBORATES` | no change | no change | One corroborator failing does not prove the conclusion fails |
| `CONTRADICTS` | no change | no change | Removing a contradiction does not harm the child |

The table is applied to the edge currently being processed. A child is marked
once per case, and its outgoing edges are then queued. Existing stronger status
from another case is never downgraded by a weaker effect.

## Bounded work queue

Each material case owns a queue of edge IDs and a monotonic cursor. Assessment
seeds the queue with the target evidence's outgoing edges. `process_impact`:

1. validates the case and `1 <= max_steps <= 32`;
2. processes at most `max_steps` queued edges from that case;
3. applies the relationship table and enqueues newly reached child edges;
4. advances the case cursor and processed-step counter; and
5. marks the case `COMPLETE` when the cursor reaches queue length.

Queue membership is scoped by `case_id`. Queue entries are idempotently
deduplicated. Calling the method after completion returns zero and cannot
mutate state. A transaction never performs recursive DFS/BFS or scans the
entire graph.
