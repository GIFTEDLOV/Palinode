# Consensus model

## Boundary

`assess_revocation` captures all required immutable inputs before entering the
nondeterministic block. The block performs only bounded `gl.nondet.web.get`
retrieval, bounded UTF-8 decoding, digest checks for the submitted notice, and
`gl.nondet.exec_prompt` with `response_format="json"`.

No storage writes, graph traversal, cross-contract calls, or message emission
occur inside the boundary.

## Leader responsibility

The leader retrieves both sources independently, constructs the fixed prompt,
and returns one strict bounded result. It cannot return arbitrary statuses,
prose, graph effects, or storage changes. Pre-validation rejects extra keys,
missing keys, invalid enums, inconsistent booleans, and inconsistent materiality
or root-effect combinations.

## Validator responsibility

The validator first verifies that the leader result is a `gl.vm.Return` with a
valid bounded result. It then independently repeats the same source retrieval
and semantic evaluation and requires exact agreement on every result field.
It does not write its own result into storage. A disagreement is `False`,
allowing the GenLayer consensus lifecycle to reject or rotate the proposal.

This is a custom leader/validator architecture rather than a convenience
wrapper because PALINODE needs exact field constraints, independent retrieval,
explicit infrastructure outcomes, and no equivalence over free-form prose.

## Result and post-consensus mutation

The agreed result contains:

```text
result_status: CONCLUSIVE | RETRYABLE
change_authentic: bool
same_subject: bool
original_evidence_affected: bool
materiality: MATERIAL | IMMATERIAL | INCONCLUSIVE
root_effect: INVALIDATE | QUESTION | NO_CHANGE | INCONCLUSIVE
reason_code: fixed enum
```

Only after `run_nondet_unsafe` returns does deterministic code write the case
result, assessment sequence/time, root status, and queue state. `process_impact`
is entirely deterministic and can be called later in bounded steps.

## Prompt injection and outage behavior

Evidence and correction pages are wrapped as untrusted data and are explicitly
not instructions. User-controlled metadata is inserted only into marked data
sections of a fixed authority-bearing task; it cannot extend the allowed result
schema. A source outage, timeout, HTTP error, invalid encoding, digest mismatch,
malformed result, or LLM error becomes explicit retryable inconclusive state or
consensus disagreement. It never silently becomes a semantic verdict.

## Finality

Accepted is not the same as protocol finality. Consumers must track the
Intelligent Contract transaction through its finalization lifecycle before
using the result as final application state.
