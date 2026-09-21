# Revocation model

## Opening a case

A case is opened against an existing `EVIDENCE` node only. It records:

- case ID generated from the complete locked challenge identity;
- target evidence ID;
- submitter;
- verified notice authority ID;
- normalized notice/correction HTTPS URI;
- notice SHA-256 and exact byte length;
- opening reason code: `CHANGED`, `CORRECTED`, `WITHDRAWN`, `SUPERSEDED`,
  `COMPROMISED`, or `INVALIDATED`;
- bounded compact opening note;
- opening sequence and transaction datetime; and
- separate case, result, semantic, materiality, retrieval, retry, assessment,
  and queue fields.

The immutable challenge identity is:

```text
(target_evidence_id, notice_authority_id, normalized_notice_uri,
 notice_sha256, notice_byte_length)
```

An exact duplicate identity is rejected. Different notices remain separate
cases for the same evidence and are independently assessable. Opening order is
the monotonic `opened_sequence`; a later case never suppresses or supersedes
an earlier adverse notice. There is no case deletion or owner cancellation.
Opening is permissionless subject only to deterministic validity, authority,
duplicate, and capacity rules.

## Semantic question

The adjudicator is not asked whether the evidence is broadly true. It is asked:

> Does the submitted correction/revocation materially undermine the specific
> registered evidence?

The model receives no unbounded graph traversal or downstream decision text.
The prompt supplies registered metadata and bounded retrieved data as
untrusted data. Deterministic relationship-specific propagation supplies the
downstream graph context after the bounded evidence-level result. Before this
prompt is constructed, the fetched target evidence and notice must match their
locked SHA-256 and exact byte lengths.

## Strict result

The LLM candidate is accepted only with exactly these fields:

| Field | Allowed values |
|---|---|
| `result_status` | `CONCLUSIVE`, `RETRYABLE` |
| `change_authentic` | boolean |
| `same_subject` | boolean |
| `original_evidence_affected` | boolean |
| `materiality` | `MATERIAL`, `IMMATERIAL`, `INCONCLUSIVE` |
| `root_effect` | `INVALIDATE`, `QUESTION`, `NO_CHANGE`, `INCONCLUSIVE` |
| `reason_code` | fixed semantic or infrastructure code set |

No raw LLM prose is stored. `MATERIAL` requires all three boolean predicates to be true,
a `MATERIAL_*` reason, and an `INVALIDATE` or `QUESTION` root effect.
`IMMATERIAL` requires `NO_CHANGE`. Semantic ambiguity is an explicit
`INCONCLUSIVE` result.

The material reason enum is closed, not fuzzy. It includes the explicit
`MATERIAL_REVOCATION` token observed in the controlled canary in addition to
the correction, withdrawal, supersession, compromise, and invalidation
variants. An unknown token remains validator-rejected.

## Failure behavior

HTTPS failure, non-2xx response, oversized or invalid UTF-8 body, notice digest
or length mismatch, or LLM call failure becomes a retryable `INCONCLUSIVE`
case result. A malformed or schema-invalid leader result is not converted into
an accepted `LLM_MALFORMED` verdict: the shared validator rejects it, allowing
leader rotation or a failed transaction. Validator disagreement likewise
rejects the nondeterministic block and does not commit a semantic mutation. No
failure path becomes `MATERIAL` or `IMMATERIAL`.

## Liveness and mirror recovery

Authentication `SOURCE_UNAVAILABLE` is a node authentication state distinct
from a revocation case's retryable `INCONCLUSIVE`. A caller may retry an open
or inconclusive case through
`retry_revocation_case(case_id, evidence_mirror_id, notice_mirror_id)`.
The original evidence and notice URI, authority, digest, and byte length are
locked in the case. Permissionless mirror candidates may be cross-origin, but
consensus independently retrieves both mirrors and checks exact bytes,
SHA-256, and length before storing a retrieval location. A failed or
mismatching mirror reverts without changing identity or granting authority.
Retryable infrastructure failures do not consume the eight conclusive/semantic
assessment attempts, preventing source outage from becoming a permanent
deadlock. Retry telemetry uses a monotonic counter and a fixed eight-entry ring,
so repeated failure cannot grow storage without bound. Each retry transaction
remains bounded and may be repeated by any caller.

`assess_revocation` accepts only `case_id`; it reads the locked case identity
and current verified retrieval locations. A caller cannot substitute a new
target evidence or notice during reassessment.

## Authority and reviewer safety

Notice URLs must reference a verified, currently active source authority. An
authoritative notice must use the same authority lineage as the target
evidence; an unrelated verified authority is explicitly a third-party
challenge and may yield `MATERIAL`/`QUESTION` with
`MATERIAL_THIRD_PARTY_CHALLENGE`, but cannot impersonate withdrawal or yield
`MATERIAL`/`INVALIDATE`. The source authority
registry uses a consensus-checked canonical
`https://origin/.well-known/palinode.json` document binding the registering
address, origin, policy, and nonce. A case locks the notice authority version
and all content identity fields; reassessment accepts only `case_id`. Callers do not select validators or
  semantic decision-makers. GenLayer's assigned leader and validator committee
  remain authoritative for the semantic result; application owners have no
  suppression or override path. The target's `authentication_status` is not
  changed by opening, retrying, assessing, propagating, or recovering a
  revocation case; only explicit `authenticate_evidence` operations can change
  that dimension.

## Recovery cases

`open_recovery_case(affected_node_id, successor_evidence_id, adverse_case_id,
opening_note)` is permissionless but deterministic. It requires the successor
to be an evidence node with the same subject, independently `CLEARED`, and
explicitly linked from the affected evidence. The adverse case must be the
same target, conclusive `MATERIAL`, and still own an active cause. The recovery
identity is the immutable tuple `(affected_node_id, successor_evidence_id,
adverse_case_id)`; exact duplicates are rejected.

`assess_recovery(recovery_id)` asks whether the authenticated successor
resolves the specific prior defect. The bounded result is:

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

The only effects are `REINSTATE`, `SUPERSEDE`, `NO_CHANGE`, and
`INCONCLUSIVE`. Source/notice outage, digest mismatch, malformed output, and
LLM failure are `RETRYABLE` and enter an explicit retryable state. They never
resolve a cause. `process_recovery_impact(recovery_id, max_steps)` is a
deterministic bounded queue operation and can be resumed or repeated safely.
Historical adverse cases remain intact. Recovery A cannot remove active cause
B; the node becomes clear for current reliance only after all active causes
that affect it have been separately resolved.
