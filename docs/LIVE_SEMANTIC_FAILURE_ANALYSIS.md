# Live semantic failure analysis

## Archived transaction

- Transaction: `0xed7831679d5b96a1c93dded5dc128e6446aa0f3ce06d10860bef0460de2b5441`
- Contract: archived canary `0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4`
- Final transaction status: `FINALIZED`
- Consensus result: `MAJORITY_AGREE`
- Agreeing validator execution result: `SUCCESS`
- Equivalence output: the leader receipt and both agreeing validator records
  contained the same seven-field *canonical fallback* object.

## Runtime evidence

The Studionet transaction receipt exposed the following decoded equivalence
payload for the semantic block:

```json
{
  "change_authentic": false,
  "materiality": "INCONCLUSIVE",
  "original_evidence_affected": false,
  "reason_code": "LLM_MALFORMED",
  "result_status": "RETRYABLE",
  "root_effect": "INCONCLUSIVE",
  "same_subject": false
}
```

That object was produced by the contract's fallback path, not by the model as a
canonical semantic answer. The available receipt does not include the raw
provider response; it includes only the value returned from the nondeterministic
block. For completeness, the observed returned object was:

```json
{
  "change_authentic": false,
  "materiality": "INCONCLUSIVE",
  "original_evidence_affected": false,
  "reason_code": "SEMANTIC_INCONCLUSIVE",
  "result_status": "CONCLUSIVE",
  "root_effect": "INCONCLUSIVE",
  "same_subject": false
}
```

The same shape was present in the agreeing validator records. The available
Studionet RPC did not implement the documented `gen_dbg_traceTransaction`
method; therefore no raw LLM return value or VM stdout/stderr trace beyond the
validator `genvm_result` was available. The validator results did not report a
nondeterministic disagreement or execution error. The only non-empty stderr
was the known pickling-storage warning.

## Root cause

Classification: **I — a concrete strict-parser failure is proven, but the
current Studionet endpoint does not expose the raw provider payload needed to
distinguish B, D, E, or H further**.

The contract's `_normalise_llm_result` converted every provider response that
failed its strict six-field validation into the synthetic
`RETRYABLE / LLM_MALFORMED` result before the validator equivalence decision.
The canonical state then recorded `INCONCLUSIVE` and correctly performed no
impact propagation, but the live semantic decision was lost. The receipt proves
the fallback was consensus-agreed; it cannot prove which raw provider field or
enum caused the six-field validation to fail because that payload was not
returned by the available debug endpoint.

This was not a source outage, validator disagreement, or graph mutation bug.
The provider-selected leader model was
reported as `policy:prd-sonnet` with an Anthropic Sonnet 4.6 fallback; the
contract must not rely on either model emitting a particular undocumented
subset of the requested fields.

## Affected code

- `contracts/palinode.py::_normalise_llm_result`
- malformed/unsupported model output was converted into an accepted retryable
  candidate before the validator equivalence check.

## Why direct tests missed it

The direct fixtures supplied hand-written six-field JSON responses and asserted
that malformed output became an accepted retryable case. They therefore did
not test rejection of an invalid leader candidate and did not represent the
provider/runtime behavior that produced the live fallback.

## Corrective design

The corrected contract will:

1. make the seven-field schema explicit in the prompt and one shared strict
   validator;
2. accept a decoded dict or a JSON string only when it has exactly that schema;
3. return an invalid candidate unchanged to the nondeterministic boundary when
   the model response is malformed, so validators reject it rather than turning
   it into a semantic verdict;
4. reserve deterministic retryable results for explicit infrastructure
   failures such as source unavailability or an LLM call exception; and
5. apply no graph or storage mutation until a validated result passes the
   validator equivalence rule.

The exact live seven-field response is a regression fixture in the direct and
adversarial test suites.
