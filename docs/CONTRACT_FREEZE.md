# PALINODE contract freeze

This record freezes the Phase 2.7 contract candidate after the final local
gates and one controlled hosted canary lifecycle. The freeze applies to the
contract source at the source-freeze commit below; later evidence and
documentation commits do not change `contracts/palinode.py`.

## Frozen deployment

| Field | Value |
|---|---|
| Source-freeze commit | `4a18242600218914ef4fa5de441bebd385967a1b` |
| Repository evidence/docs freeze commit | `a310654b29dccc3c66f85bd382d28527f337d718` |
| Contract source SHA-256 | `bd5e981605f2533bd5354a4e884288d585020514d4be9eaabd9cdb4ff39d4c06` |
| Studionet address | `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88` |
| Deployment transaction | `0xdc1e5a61f584b2907a0bdadf258ece092fcb361110395c4055b95ffd048f6bd8` |
| Final deployment status | `FINALIZED` |
| Execution result | `FINISHED_WITH_RETURN` |
| Network | `studionet` |
| RPC | `https://studio.genlayer.com/api` |
| Chain ID | `61999` |
| ABI method count | `41` (`20` views, `21` writes) |

## Gate evidence

- Direct tests: `28 passed`.
- Invariant tests: `5 passed`.
- Adversarial tests: `34 passed`.
- Property tests: `2 passed`.
- Combined local protocol suite: `69 passed`.
- Mutation harness: `34/34 killed`, survivors `[]`.
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
8. The revocation transaction was tracked again after process restart by the
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

The contract is frozen for the next application/frontend phase. Any later
change to `contracts/palinode.py` requires a new security review and canary.
