# PALINODE v2 Authorization and Public API Model

This document describes the pre-deployment authorization boundary of
`contracts/palinode_v2.py`. The archived Studionet contract at
`0x9c9d1993cd938846D1163Bba9AA81AC6d165de88` is not upgraded by this review.

## Endpoint control

Evidence registration is controlled by the current controller declared by the
active source-authority version. Non-evidence nodes are permissionless records,
but their creator is their controller.

## Dependency edges

`register_dependency(parent, child, relationship)` requires the caller to
control the child only. The child controller is the edge assertor because the
child is the party declaring what it relies on. Parent existence, canonical
identity, creation order, non-superseded status, relationship validity, and the
bounded incoming-edge and active-cause reconciliation checks remain mandatory.

Parent ownership is intentionally not required. An authority may publish
evidence and an independent consumer may cite it without the publisher signing
the consumer's graph. `edge_assertor` records who made the child-side claim.
The child controller and duplicate-identity checks prevent unauthorized graph
writes and fan-in/fan-out griefing; each child has a bounded incoming capacity,
while a public parent has no lifetime outgoing quota that another party can
consume.

## Successor lineage

PALINODE defines a successor as an official replacement in the same source
authority lineage. `link_evidence_successor` therefore requires the current
predecessor authority controller, a later evidence node, matching subject
metadata, the same stable authority ID/lineage, and independently `CLEARED`
successor evidence. Unrelated corrective evidence is not called a successor;
it is a third-party challenge or corroborating artifact.

The link stores creator, sequence, and authority-version provenance but never
changes reliance. Only a successful, cause-bound recovery result may transition
the predecessor to `SUPERSEDED`.

## Notice standing and challenge semantics

Cases whose notice authority is the target evidence's authority lineage are
`AUTHORITATIVE_REVOCATION`. A same-lineage withdrawal or correction may produce
the appropriate `MATERIAL` effect, including `INVALIDATE`, when semantic
consensus supports it.

An unrelated active authority may open a permissionless
`THIRD_PARTY_CHALLENGE`. It cannot impersonate publisher withdrawal or emit a
source-authoritative reason for that purpose. A semantically material challenge
may still produce the bounded adverse result `QUESTION` with
`MATERIAL_THIRD_PARTY_CHALLENGE`; it may not deterministically invalidate the
original source. Garbage or immaterial challenge evidence produces no adverse
state. A revoked challenger authority cannot open a case. The source owner has
no suppression or veto path over third-party review.

## Authority lifecycle and historical authentication

Normal, authenticated rotation marks the old version `SUPERSEDED` and keeps
the authority active. Evidence registered under that historical version may be
authenticated against its original binding. Explicit authority revocation is a
different state: the authority becomes `REVOKED`, historical version records
remain inspectable with their prior status, and authentication fails closed for
all versions under that authority. `SUPERSEDED` and `REVOKED` are never
collapsed into one version status.

## Public API audit

The v2 schema contains 46 public methods: 21 writes and 25 views. Every write
below has an explicit caller rule, state/capacity effect, and retry property.

### Writes

| Method | Caller authorization | State/capacity effect | Permissionless and retry semantics |
|---|---|---|---|
| `register_source_authority` | Anyone; domain declaration is consensus-verified | Creates one authority/version record | Safe because origin/address/nonce identity is canonical; duplicate identity rejects |
| `rotate_source_authority` | Current authority controller | Supersedes one version and creates the next | Declaration is consensus-verified; monotonic version prevents replay |
| `revoke_source_authority` | Current authority controller | Marks authority trust `REVOKED` and current version revoked | Idempotent retry is rejected; historical authentication fails closed |
| `authenticate_evidence` | Anyone | Consensus-checks locked bytes and changes assessment only | Safe because URI, digest, length, subject, and historical version are locked; repeated valid calls are bounded by assessment rules |
| `register_evidence` | Current controller of the selected authority | Appends immutable evidence metadata | Capacity is byte-bounded; exact identity rejects duplicates |
| `register_claim`, `register_decision`, `register_attestation`, `register_authorization`, `register_node` | Anyone for non-evidence node types | Appends immutable node metadata | Safe permissionless creation; derived IDs and sequence make retries/duplicates distinct rather than rewrites |
| `register_dependency` | Controller of the child only | Adds one immutable edge, increments bounded incoming/outgoing counters, and reconciles active causes | Safe cross-party reliance; duplicate identity, creation order, incoming cap, and bounded late-edge reconciliation reject abuse |
| `link_evidence_successor` | Controller of the predecessor evidence | Stores one immutable successor link and provenance | Safe because it cannot change reliance; duplicate predecessor/successor links reject retries |
| `open_revocation_case` | Anyone | Creates one locked case and bounded queues/telemetry | Permissionless review is safe because identity is immutable and no node state changes on open; exact case identity rejects duplicates |
| `assess_revocation` | Anyone | Consensus-mutates case result and, only for valid material results, active causes | Source must be `CLEARED`; assessment count and result history are bounded; retryable outcomes remain retryable |
| `process_impact` | Anyone | Processes at most the caller's bounded step count for one case | Cursor-scoped, resumable, and idempotent; cannot exceed per-call bound |
| `retry_revocation_case` | Anyone using only verified mirror IDs | Changes retrieval pointers and bounded retry telemetry | No caller-supplied URL or re-authentication; only `INCONCLUSIVE` cases retry |
| `add_evidence_mirror` | Evidence authority controller | Adds one verified mirror up to mirror capacity | Consensus verifies exact digest/length; duplicate mirror identity rejects retries |
| `add_notice_mirror` | Target controller for authoritative notice, or notice-authority controller for challenge | Adds one verified notice mirror up to mirror capacity | Consensus verifies exact digest/length; duplicate identity rejects retries |
| `open_recovery_case` | Anyone | Creates one cause-bound recovery case | Safe permissionless operation; requires material case completion, exhausted propagation, linked same-lineage `CLEARED` successor, and active cause; identity rejects duplicates |
| `assess_recovery` | Anyone | Consensus-mutates one recovery result and resolves exactly one cause on success | Requires complete adverse propagation; bounded assessments and retry telemetry; no owner override |
| `process_recovery_impact` | Anyone | Processes bounded recovery propagation for one case | Cursor-scoped and idempotent; completed recovery is a no-op |

### Views

| Method family | Bounded/current or historical semantics |
|---|---|
| `get_node_record`, `get_dependency_record`, `get_evidence_successor_link` | Bounded immutable identity plus current reliance/status and link provenance |
| `get_source_authority`, `get_source_authority_version` | Current authority or one historical version; version status remains explicit |
| `get_revocation_case`, `get_recovery_case` | Bounded locked inputs, consensus result, standing, queue/retry state, and history pointers |
| `get_impact_queue_state`, `get_recovery_queue_state` | Bounded cursor/status/queue telemetry for resumable processing |
| `get_active_causes` | Constant-size highest-severity counters and active count; no unbounded list is returned |
| `get_active_causes_page` | Paginated individually keyed cause identities and severities |
| `get_evidence_mirrors`, `get_notice_mirrors` | Bounded verified mirror lists tied to locked identities |
| `get_status_history`, `get_assessment_history`, `get_case_result_history`, `get_recovery_result_history` | Recent bounded ring/history views; totals and cursors preserve historical scale |
| `get_retry_telemetry`, `get_recovery_retry_telemetry` | Recent bounded retry ring/history views with totals |
| `get_node_ids_page`, `get_edge_ids_page`, `get_case_ids_page`, `get_authority_ids_page`, `get_recovery_ids_page` | Cursor/limit-paginated identifiers with explicit maximum page size |

Permissionless operations do not grant authority to rewrite evidence,
dependencies, lineage, historical identity, or consensus results. Deterministic
standing rules constrain which semantic root effects and reason codes can
become canonical state.
