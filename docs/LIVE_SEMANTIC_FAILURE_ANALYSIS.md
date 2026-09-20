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

## Phase 2.6 corrected-canary transaction

- Transaction: `0xc0d05d17df0d27e9ffca02d5aaa03a42ccd99d9d6abc59d876cd002054478e2c`
- Contract: `0xDD918F99553717f6e157A7Ca2FfE902B4E3a438B`
- Case: `c33a6a26f342279d29676b59c6242959cf219c1a30449508ea5f45341209b699`
- Final status: `UNDETERMINED`
- Consensus result: `MAJORITY_DISAGREE`
- Active validators: three `disagree`; two idle after quorum.

The leader equivalence output had the correct seven fields and parsed JSON, but
returned this bounded result code:

```json
{
  "result_status": "CONCLUSIVE",
  "change_authentic": true,
  "same_subject": true,
  "original_evidence_affected": true,
  "materiality": "MATERIAL",
  "root_effect": "INVALIDATE",
  "reason_code": "MATERIAL_REVOCATION"
}
```

`MATERIAL_REVOCATION` was not present in the deployed contract's fixed
`SEMANTIC_REASON_CODES` tuple. The shared validator therefore rejected the
candidate as an unsupported enum and the deterministic post-consensus check
returned `semantic result rejected`. This is classification **E/I** from the
requested taxonomy: an unsupported enum value, not a missing JSON response,
dict/double-decoding bug, source outage, or casing-only difference. The
available hosted RPC again did not expose the documented debug trace method or
raw provider payload beyond the decoded equivalence output.

The safety result was correct: no case assessment or impact mutation was
committed. The target evidence remained `authentication_status=CLEARED` and
`reliance_status=ACTIVE`; the case remained `OPEN`. The exact trace is also
stored in `evidence/studionet/canary-v2/semantic-failure.json`.

The smallest local follow-up is to add `MATERIAL_REVOCATION` as an explicit
allowed enum and list every allowed reason code in the prompt. This is not
fuzzy parsing or a relaxation of the bounded schema. It was applied locally
after the one permitted live semantic attempt; it was not deployed during this
run, so canary-v2 remains an archived failed semantic-closure attempt.

## Canary-v3 resolution

The unreleased fix was intentionally limited to the prompt/schema boundary. It
did not add synonyms or loosen validation. The prompt now says to return JSON
only, use exactly the supplied keys and enum values, avoid combined/renamed
labels and prefixes/suffixes, and verify exact enum membership before return.
`MATERIAL_REVOCATION` remains legal only as a closed `reason_code`.

Canary-v3 deployment transaction
`0xdc1e5a61f584b2907a0bdadf258ece092fcb361110395c4055b95ffd048f6bd8`
finalized with `FINISHED_WITH_RETURN`. Its single semantic transaction
`0x00d76be0d0680cb24d4726caf881c97a9d618c6efc94ad61cef0acf5888487e5`
finalized with a canonical seven-field result:

```json
{
  "result_status": "CONCLUSIVE",
  "change_authentic": true,
  "same_subject": true,
  "original_evidence_affected": true,
  "materiality": "MATERIAL",
  "root_effect": "INVALIDATE",
  "reason_code": "MATERIAL_WITHDRAWAL"
}
```

This confirms the corrected boundary on hosted Studionet. V1 authentication
remained `CLEARED` while its reliance state was invalidated and later
superseded by the matching V2 recovery. Full transaction IDs and readbacks are
under `evidence/studionet/canary-v3/`.
