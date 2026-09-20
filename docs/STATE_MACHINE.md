# State machines

## Node status

The current status is separate from immutable identity and historical
validity. No public method accepts an arbitrary target status. Internal status
changes use the explicit relation below; a no-op transition is also rejected by
the transition helper.

| Current | Legal next statuses |
|---|---|
| `ACTIVE` | `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED` |
| `QUESTIONED` | `ACTIVE`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `INCONCLUSIVE` |
| `UNDER_REVIEW` | `ACTIVE`, `QUESTIONED`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `INCONCLUSIVE` |
| `QUARANTINED` | `UNDER_REVIEW`, `SUPERSEDED`, `INVALIDATED`, `REINSTATED`, `INCONCLUSIVE` |
| `SUPERSEDED` | `REINSTATED`, `INVALIDATED` |
| `INVALIDATED` | `REINSTATED` |
| `REINSTATED` | `ACTIVE`, `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `INCONCLUSIVE` |
| `INCONCLUSIVE` | `ACTIVE`, `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `REINSTATED` |

Every transition appends a compact status-history record containing transition
sequence, node ID, old status, new status, reason code, and case ID. Each node
is limited to 16 transitions in Phase 1.

## Revocation case status

Case status is not overloaded with semantic fields:

- `OPEN`: case exists and has not produced an assessment.
- `INCONCLUSIVE`: semantic ambiguity or an explicit retryable infrastructure
  result; no destructive root or descendant effect is applied.
- `PROPAGATING`: a material result created a root effect and has queued edges.
- `COMPLETE`: no queued work remains, or a conclusive immaterial result had no
  impact to process.

The case separately stores `result_status` (`PENDING`, `CONCLUSIVE`, or
`RETRYABLE`), `semantic_verdict`/`materiality` (`PENDING`, `MATERIAL`,
`IMMATERIAL`, `INCONCLUSIVE`), and `root_effect` (`PENDING`, `INVALIDATE`,
`QUESTION`, `NO_CHANGE`, `INCONCLUSIVE`).

## Assessment transitions

`OPEN` and `INCONCLUSIVE` cases may be assessed, subject to eight assessment
attempts. A `MATERIAL` result must have root effect `INVALIDATE` or `QUESTION`;
an `IMMATERIAL` result must have `NO_CHANGE`; an `INCONCLUSIVE` or `RETRYABLE`
result cannot mutate node reliance state. A case that is `COMPLETE` or
`PROPAGATING` cannot be reassessed.

## Recovery transition

`link_evidence_successor(old, new)` stores explicit predecessor/successor
lineage. If the old evidence is not already `INVALIDATED` or `SUPERSEDED`, the
allowed `SUPERSEDED` transition is used. The old object is never rewritten.
