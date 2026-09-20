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
| `INVALIDATED` | `REINSTATED`, `SUPERSEDED` |
| `REINSTATED` | `ACTIVE`, `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `INCONCLUSIVE` |
| `INCONCLUSIVE` | `ACTIVE`, `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `REINSTATED` |

Every transition increments a monotonic total counter and writes a compact
status-history record containing transition sequence, node ID, old status, new
status, reason code, and case ID into a fixed 16-slot recent-history ring.
`get_status_history` exposes the total count and recent bounded slots. A node
does not lose its lifetime ability to transition merely because history is
full.

## Assessment status

Assessment status is a separate explicit state machine. It answers whether a
registered object has received a bounded consensus assessment; it is not a
shortcut for current downstream reliance.

| Current | Legal next statuses |
|---|---|
| `UNASSESSED` | `PENDING` |
| `PENDING` | `CLEARED`, `REJECTED`, `INCONCLUSIVE`, `SOURCE_UNAVAILABLE` |
| `CLEARED` | `PENDING`, `REJECTED`, `INCONCLUSIVE`, `SOURCE_UNAVAILABLE` |
| `REJECTED` | `PENDING`, `CLEARED`, `INCONCLUSIVE`, `SOURCE_UNAVAILABLE` |
| `INCONCLUSIVE` | `PENDING`, `CLEARED`, `REJECTED`, `SOURCE_UNAVAILABLE` |
| `SOURCE_UNAVAILABLE` | `PENDING`, `CLEARED`, `REJECTED`, `INCONCLUSIVE` |

Registration creates `UNASSESSED`/`ACTIVE`. Opening an adverse case creates
`PENDING` without changing reliance. A conclusive immaterial result creates
`CLEARED`; a material result creates `REJECTED`; semantic ambiguity creates
`INCONCLUSIVE`; retrieval infrastructure failure creates
`SOURCE_UNAVAILABLE`. Assessment transitions use the same fixed 16-slot
recent-history ring and a monotonic total count. Repeated retryable source
failures update bounded case telemetry rather than appending unbounded
assessment history. The node view exposes both current dimensions and the
assessment case ID.

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

`OPEN` and `INCONCLUSIVE` cases may be assessed, subject to eight conclusive or
semantic assessment attempts. Retryable infrastructure failures do not consume
that semantic attempt budget, so an unavailable source cannot deadlock a case.
`retry_revocation_case` is permissionless and may verify content-preserving
mirrors before another assessment. Each retry transaction remains bounded;
repeating it does not rewrite identity. A `MATERIAL` result must have
root effect `INVALIDATE` or `QUESTION`; an `IMMATERIAL` result must have
`NO_CHANGE`; an `INCONCLUSIVE` or `RETRYABLE` result cannot mutate node
reliance state. A case that is `COMPLETE` or `PROPAGATING` cannot be
reassessed. Exact duplicate challenge identities are rejected, while distinct
notice identities remain independent and ordered by opening sequence.

## Recovery transition

`link_evidence_successor(old, new)` stores explicit predecessor/successor
lineage. If the old evidence is not already `INVALIDATED` or `SUPERSEDED`, the
allowed `SUPERSEDED` transition is used. The old object is never rewritten.

A recovery case has its own explicit state machine:

| Current | Legal next statuses |
|---|---|
| `OPEN` | `INCONCLUSIVE`, `PROPAGATING`, `COMPLETE` |
| `INCONCLUSIVE` | `INCONCLUSIVE`, `PROPAGATING`, `COMPLETE` |
| `PROPAGATING` | `COMPLETE` |
| `COMPLETE` | none |

Only a conclusive strict recovery result can create `PROPAGATING` or
`COMPLETE` recovery state. `RETRYABLE` source/LLM failures enter
`INCONCLUSIVE`, increment a bounded retry counter/ring, and do not consume the
conclusive recovery-assessment budget. `REINSTATE` and `SUPERSEDE` resolve
only the adverse cause locked into that recovery case. A node remains affected
while any other active cause remains. There is no direct owner or administrator
reinstatement transition.
