# PALINODE contract freeze

This record freezes PALINODE V4 after the final local gates and controlled
Studionet reviewer evidence. The archived V1 deployment remains historical;
the application and deployment source are `contracts/palinode_v2.py`.

## Frozen deployment

| Field | Value |
|---|---|
| Source-freeze commit | `14bb4574a8d248c978b55ff1fb70f32c0293f313` |
| Frontend migration commit | `local V4 migration commit (this release)` |
| Contract source SHA-256 | `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601` |
| Source path | `contracts/palinode_v2.py` |
| Studionet address | `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b` |
| Deployment transaction | `0x77dff7d687eea1168be519b0ddced4e6d6b3854a17be743190654fb7f5d3281f` |
| Final deployment status | `FINALIZED` |
| Execution result | `FINISHED_WITH_RETURN` |
| Network | `studionet` |
| RPC | `https://studio.genlayer.com/api` |
| Chain ID | `61999` |
| ABI method count | `46` (`25` views, `21` writes) |

## Gate evidence

- Direct tests: `55 passed`.
- Invariant tests: `5 passed`.
- Adversarial tests: `34 passed`.
- Property tests: `2 passed`.
- Combined local protocol suite: `69 passed`.
- Mutation harness: `49 total`, `46 killed`, `3 retired`, `0 survived`.
- Retired mutations: obsolete overflow-summary mutations after V4 moved to
  individually keyed active causes plus severity counters.
- GenVM lint: pass.
- GenVM typecheck: pass, zero errors and warnings.
- Schema generation: pass; ABI and schema generated for the frozen source.
- Hosted integration suite: `6 passed`, `1 skipped` for the known Windows GLSim
  compressed-stream runtime blocker. The skip is not treated as Studionet
  equivalence.

## Live proof

Canary-v3 used the controlled HTTPS fixture and finalized the following
bounded lifecycle:

1. Authority registration and live `.well-known` proof passed.
2. Evidence V1 authentication passed with `CLEARED`.
3. Claim, Decision, `SUPPORTS`, and `REQUIRES` graph writes finalized.
4. The single revocation assessment finalized as
   `CONCLUSIVE / MATERIAL / INVALIDATE / MATERIAL_WITHDRAWAL`.
5. Bounded propagation completed; V1 authentication remained `CLEARED` while
   reliance moved to `INVALIDATED`, and downstream states were updated by the
   typed policy.
6. Evidence V2 independently authenticated as `CLEARED`; V1→V2 succession
   was recorded without rewriting either evidence object.
7. The matching recovery case finalized as `SUPERSEDE`; bounded recovery
   propagation completed and V1 reliance became `SUPERSEDED`.
8. An unrelated Authority C challenge produced bounded `QUESTION` semantics
   with `MATERIAL_THIRD_PARTY_CHALLENGE`; it could not produce authoritative
   `INVALIDATE`.
9. A same-URL BODY A/B mutation committed `SOURCE_DIGEST_MISMATCH` before
   semantic adjudication, with no adverse state mutation.
10. The revocation transaction was tracked again after process restart by the
   same transaction ID with zero resubmissions.

The full transaction IDs and canonical readbacks are in
`evidence/studionet/canary-v3/`. Canary-v1 and canary-v2 remain archived at
`0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4` and
`0xDD918F99553717f6e157A7Ca2FfE902B4E3a438B`; they are not upgraded in place.

## Known limitations

- The installed SDK does not expose a network source-download endpoint, so
  source parity is recorded against the exact source bytes submitted by the
  deployment harness and the limitation is explicit in
  `evidence/studionet/canary-v3/source-parity.json`.
- Semantic outcomes depend on public HTTPS availability and validator/model
  agreement; failure remains retryable or inconclusive rather than becoming a
  verdict.
- The controlled fixture is fictional test infrastructure, not a production
  authority or frontend.
- The frontend, indexer, cross-contract messaging, and token integrations are
  intentionally out of scope for this freeze.

The contract is frozen for the V4 application release. Any later contract
change requires a new security review and deployment review. The archived V1
address is not a runtime fallback.
