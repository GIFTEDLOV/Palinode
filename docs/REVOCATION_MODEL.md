# Revocation model

## Opening a case

A case is opened against an existing `EVIDENCE` node only. It records:

- case ID generated from target evidence ID and notice digest;
- target evidence ID;
- submitter;
- notice/correction HTTPS URI;
- notice SHA-256 and exact byte length;
- opening reason code: `CHANGED`, `CORRECTED`, `WITHDRAWN`, `SUPERSEDED`,
  `COMPROMISED`, or `INVALIDATED`;
- bounded compact opening note;
- opening sequence and transaction datetime; and
- separate case, result, semantic, materiality, and queue fields.

An exact `(target_evidence_id, notice_sha256)` case is rejected as a duplicate.
Distinct notices can create distinct cases for the same evidence. There is no
case deletion.

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
