# Impact propagation

## Root effect

Only a conclusive `MATERIAL` result starts destructive or questioning impact.
The root evidence is moved to `INVALIDATED` for `root_effect=INVALIDATE` or
`QUESTIONED` for `root_effect=QUESTION`. An immaterial result has `NO_CHANGE`;
an inconclusive or retryable result does not mutate node reliance state.

## Typed consequences

The exact edge table is defined in [GRAPH_MODEL.md](GRAPH_MODEL.md): required
and authorization reliance is quarantined or reviewed, derivation is reviewed,
support and qualification are questioned, and corroboration or contradiction
does not produce an automatic destructive effect.

This is intentionally not reachability-based invalidation. The graph records
that an impact path exists; the relationship type determines the conservative
status effect at each edge.

## Queue algorithm

The case stores `case_queue[case_id]`, `case_cursor[case_id]`, processed count,
per-case seen-node keys, and per-case queued-edge keys. The queue contains edge
IDs, not recursive call frames. A child is enqueued only after its first typed
impact and only its outgoing edges are added.

`MAX_IMPACT_STEPS_PER_CALL` is 32. A caller may use several transactions to
resume a large graph. Per-node fan-out and graph capacity also bound the total
queue. A completed case returns zero on repeated processing and cannot be
processed forever. Queue keys include the case ID, so one case cannot consume
or mutate another case's queue.

The current reliance composition is a monotonic severity lattice for ordinary
revocation causes: `QUESTIONED < UNDER_REVIEW < QUARANTINED < INVALIDATED`.
`ACTIVE`, `REINSTATED`, and `INCONCLUSIVE` are the zero-severity baseline;
`SUPERSEDED` is lineage-specific. A weaker later case is a no-op. Only an
explicit successor/recovery path can resolve a stronger cause; an immaterial
case never restores reliance.

## Idempotence and stronger prior state

Queue entries are deduplicated. A node already at an equal or stronger current
status is not downgraded by a weaker impact. The status transition table still
governs every actual transition and appends history. Replaying a completed
step cannot erase or rewrite any prior state.
