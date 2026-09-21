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

An edge stores its own ID, parent, child, relationship, creation sequence,
assertor, and active flag. It is accepted only if both nodes exist, the nodes differ, the
relationship is supported, the identity tuple is not duplicated, and:

```text
node_sequence(parent) < node_sequence(child)
```

The caller must control both endpoint nodes; an arbitrary third party cannot
assert a dependency or consume either endpoint's capacity. This is the exact
DAG invariant. Since node sequences never change and all
supported writes enforce the inequality, every directed path strictly
increases in sequence. A directed cycle would require a strict increase around
the cycle and is therefore impossible without an unbounded graph traversal.

Per-node incoming and outgoing edge limits are 64. There are no protocol-wide
lifetime node or edge caps. Append-only ID registries are exposed through
bounded pages (`get_*_ids_page(cursor, limit)`, maximum page size 64), so a
view never has to return the complete lifetime graph.

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

There is no implicit relationship fallback: a relationship outside the seven
listed values is rejected before queue processing. `CORROBORATES` and
`CONTRADICTS` intentionally have no automatic child effect for either root
effect; their existence remains inspectable for a later, separately reasoned
review.

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

If an edge is added after a material case has already affected its parent, the
contract copies every currently active case-specific cause across the new
relationship and reopens that case's bounded queue when descendants also need
reconciliation. It does not invoke semantic consensus again. If the bounded
cause scan cannot be completed safely, the edge is rejected rather than
silently creating an untracked dependency.

Recovery uses a separate queue and cursor. It removes only the named adverse
case's active cause from each affected node. Other active causes remain in the
individually recoverable cause registry; only the final resolved cause can permit
`REINSTATED` or `SUPERSEDED` according to the accepted recovery effect.
