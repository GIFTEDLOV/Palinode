# Recovery model

Recovery is the controlled counterpart to semantic revocation. It never edits
the original evidence, adverse case, or historical status. A replacement is a
new evidence node with its own immutable source identity and independent
authentication.

## Preconditions and identity

`open_recovery_case(affected_node_id, successor_evidence_id, adverse_case_id,
opening_note)` is permissionless. Deterministic guards require:

- the affected node and successor exist;
- the successor is an evidence node with the same subject;
- the successor assessment is `CLEARED`;
- `link_evidence_successor` explicitly binds old evidence to successor;
- the adverse case targets the affected evidence and is conclusive `MATERIAL`;
- the adverse case still owns an active cause; and
- the identity `(affected_node_id, successor_evidence_id, adverse_case_id)` has
  not already been used.

The recovery record stores the submitter, opening sequence/time, locked node
IDs, adverse case ID, bounded result, assessment count, retry telemetry, and a
separate bounded impact queue. No owner or administrator can call a direct
reinstate setter.

## Semantic question and result

`assess_recovery(recovery_id)` asks:

> Does the authenticated successor evidence resolve the specific material
> defect that caused the locked adverse reliance state, sufficiently to restore
> current reliance or explicitly supersede the affected evidence?

The leader and validator retrieve only the locked successor and locked adverse
notice. Their exact bounded result is:

```json
{
  "result_status": "CONCLUSIVE",
  "same_subject": true,
  "successor_relevant": true,
  "prior_defect_resolved": true,
  "recovery_effect": "REINSTATE",
  "reason_code": "RECOVERY_RESOLVED_REINSTATE"
}
```

`recovery_effect` is one of `REINSTATE`, `SUPERSEDE`, `NO_CHANGE`, or
`INCONCLUSIVE`. Retrieval failure, digest/length mismatch, malformed response,
or LLM failure is `RETRYABLE` with a fixed reason code. It is stored as
`INCONCLUSIVE` recovery state, does not resolve a cause, and does not consume
the conclusive recovery-attempt budget. Retry telemetry is a fixed eight-entry
ring plus a monotonic counter.

## Active causes

Every material revocation case that affects a node creates a distinct
`node_id|case_id` cause with its typed severity. A node stores at most 64 named
active cause slots; this bounds per-node execution while preserving historical
case records. The slot limit is not allowed to suppress a later finding: when
the slots are full, additional causes are retained in a monotonic overflow
summary containing a count, strongest severity, latest strongest case ID, and
rolling commitment. The overflow summary is a conservative safety lock; named
slot recovery cannot clear it, so the node cannot become safer than the
recorded causes justify. This is exposed by `get_active_causes` and keeps
recovery accounting fail-closed at the boundary.

The current reliance state is the maximum active ordinary severity:

```text
QUESTIONED < UNDER_REVIEW < QUARANTINED < INVALIDATED
```

Resolving recovery A clears only A. If B remains, the node stays at B's
severity. Only after the final active adverse cause is resolved may the target
become `REINSTATED`, or `SUPERSEDED` when the accepted recovery effect is
`SUPERSEDE`. Historical revocation and recovery records remain inspectable.

## Bounded propagation

`process_recovery_impact(recovery_id, max_steps)` uses a dedicated queue and
cursor, with `max_steps` limited to 32. It removes only the locked adverse
case's cause from affected descendants. It never consumes another case's
queue, recursively traverses the graph, or reprocesses a completed recovery.
Repeated calls are idempotent and return zero after completion.

## Failure and trust boundaries

The successor's `CLEARED` state means exact availability and identity at its
authority-bound canonical source; it is not a broad truth guarantee. A mirror
cannot make it cleared. GenLayer consensus decides the bounded semantic result;
deterministic contract logic alone applies cause resolution and propagation.
An indexer, frontend, evidence owner, or recovery submitter cannot override a
result or remove an adverse historical record.
