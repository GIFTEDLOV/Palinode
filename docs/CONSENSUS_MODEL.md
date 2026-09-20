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

`register_source_authority` uses the same protocol-owned leader/validator
boundary for a smaller deterministic challenge result. Both sides retrieve the
derived `/.well-known/palinode.json` URL and require exact binding of the
registering address, normalized origin, nonce, policy, and Palinode version.
Authority rotation uses the same check against the canonical origin to create a
new version; the old controller is not sufficient to impersonate it. The
caller cannot choose the leader, validators, or any reviewer set.

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

Recovery uses the same leader/validator boundary with a smaller strict result:

```text
result_status: CONCLUSIVE | RETRYABLE
same_subject: bool
successor_relevant: bool
prior_defect_resolved: bool
recovery_effect: REINSTATE | SUPERSEDE | NO_CHANGE | INCONCLUSIVE
reason_code: fixed recovery enum
```

The recovery block retrieves only the locked successor and the locked adverse
notice. It does not read or mutate storage, choose validators, traverse the
graph, or calculate downstream effects. Deterministic code validates the
result, resolves only the named active cause, and later processes a bounded
recovery queue. A second active cause remains effective.

## Prompt injection and outage behavior

Evidence and correction pages are wrapped as untrusted data and are explicitly
not instructions. User-controlled metadata is inserted only into marked data
sections of a fixed authority-bearing task; it cannot extend the allowed result
schema. A source outage, timeout, HTTP error, invalid encoding, digest mismatch,
malformed result, or LLM error becomes explicit retryable inconclusive state or
consensus disagreement. It never silently becomes a semantic verdict.

Evidence retrieval failure commits assessment `SOURCE_UNAVAILABLE`, not
`CLEARED`, `REJECTED`, or semantic `INCONCLUSIVE`. The permissionless retry
path can first consensus-verify cross-origin mirror bytes against the locked
digest and length; only then can reassessment use the mirror location. A mirror
has no authority semantics.

## Finality

Accepted is not the same as protocol finality. Consumers must track the
Intelligent Contract transaction through its finalization lifecycle before
using the result as final application state.
