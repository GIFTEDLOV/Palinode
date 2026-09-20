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
> registered evidence in the context in which downstream nodes rely on it?

The prompt supplies registered metadata, bounded retrieved data, and the
current retrieved digest as untrusted data. It explicitly instructs the model
not to follow commands embedded in source pages.

## Strict result

The LLM candidate is accepted only with exactly these fields:

| Field | Allowed values |
|---|---|
| `change_authentic` | boolean |
| `same_subject` | boolean |
| `original_evidence_affected` | boolean |
| `materiality` | `MATERIAL`, `IMMATERIAL`, `INCONCLUSIVE` |
| `root_effect` | `INVALIDATE`, `QUESTION`, `NO_CHANGE`, `INCONCLUSIVE` |
| `reason_code` | fixed semantic or infrastructure code set |

The contract adds `result_status`: `CONCLUSIVE` or `RETRYABLE`. No raw LLM
prose is stored. `MATERIAL` requires all three boolean predicates to be true,
a `MATERIAL_*` reason, and an `INVALIDATE` or `QUESTION` root effect.
`IMMATERIAL` requires `NO_CHANGE`. Semantic ambiguity is an explicit
`INCONCLUSIVE` result.

## Failure behavior

HTTPS failure, non-2xx response, oversized or invalid UTF-8 body, notice digest
or length mismatch, malformed JSON, or LLM failure becomes a retryable
`INCONCLUSIVE` case result. Validator disagreement rejects the nondeterministic
block and does not commit a semantic mutation. No failure path becomes
`MATERIAL` or `IMMATERIAL`.

## Liveness and mirror recovery

`SOURCE_UNAVAILABLE` is a node assessment state distinct from semantic
`INCONCLUSIVE`. A caller may retry an `INCONCLUSIVE` case through
`retry_revocation_case(case_id, evidence_mirror_uri, notice_mirror_uri)`.
The original evidence and notice URI, authority, digest, and byte length are
locked in the case. v1 permits mirror locations only under the same verified
authority origin, and consensus independently retrieves both mirrors and
checks exact bytes, SHA-256, and length before storing them as retrieval
locations. A failed or mismatching mirror reverts without changing identity.
Retryable infrastructure failures do not consume the eight conclusive/semantic
assessment attempts, preventing source outage from becoming a permanent
deadlock. Each retry transaction remains bounded and may be repeated by any
caller.

`assess_revocation` accepts only `case_id`; it reads the locked case identity
and current verified retrieval locations. A caller cannot substitute a new
target evidence or notice during reassessment.

## Authority and reviewer safety

Notice URLs must reference a verified source authority. The source authority
registry uses a consensus-checked canonical
`https://origin/.well-known/palinode.json` document binding the registering
address, origin, policy, and nonce. Callers do not select validators or
semantic decision-makers. GenLayer's assigned leader and validator committee
remain authoritative for the semantic result; application owners have no
suppression or override path.
