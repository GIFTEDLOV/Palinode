# Deployment and canary record

The canary used only stable Studionet:

```text
RPC: https://studio.genlayer.com/api
chain ID: 61999
```

Before broadcast, the operator must confirm the contract source SHA-256, clean
worktree, deployer public address, funding, fee estimate, and stable tool
versions without exposing or storing a private key. The transaction ID must be
persisted. A mined or `ACCEPTED` transaction is provisional; success requires
the actual final consensus status and a successful execution result. The
contract address, schema/readback, `contract_info` where available, and source
hash parity must then be checked.

The controlled fixture is deployed at `https://palinode-fixture.vercel.app` and
serves the exact committed bytes recorded in
`evidence/studionet/fixture.json`. The local GLSim issue is recorded as
`KNOWN_LOCAL_BLOCKER`; it did not block the hosted Studionet canary. Studionet
reported zero outer gas price and zero base fee at preflight, so the canary
used the measured gasless RPC policy rather than inventing a funding budget.

The archived Phase 2.5 deployment was finalized successfully:

```text
contract: 0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4
deployment tx: 0xdfc919f95a0276be9381a3e38d871e0b45e4ec14ed4040f13f6257d758098ddc
source sha256: eb39390b9da51e70aa54af130c1d45ab392c1b85d327975c462df5d5f10984be
```

The live deterministic lifecycle finalized through authority registration,
evidence authentication, graph registration, challenge opening, successor
authentication, and lineage linking. The real validator result for the
revocation assessment was recorded as `RETRYABLE`/`INCONCLUSIVE` with
`LLM_MALFORMED`; no impact or recovery was fabricated. Full archived
transaction IDs and readbacks are in `evidence/studionet/canary-v1/`.

Phase 2.6 deployed the corrected source once after all local gates passed. It
used `evidence/studionet/canary-v2/`, persisted a new transaction ID before
polling, and required final consensus plus successful execution. The deployment
finalized at `0xDD918F99553717f6e157A7Ca2FfE902B4E3a438B`, but the one permitted
live semantic assessment later reached `UNDETERMINED` because the provider
returned an unlisted bounded reason enum. The old address is an archived
canary and is never silently upgraded. No second deployment or semantic retry
was submitted.

No transaction is rebroadcast after a timeout, and no fake domain ownership or
weakened authority rule is permitted.

## Final canary-v3

The final candidate was deployed exactly once from the clean freeze candidate:

```text
contract: 0x9c9d1993cd938846D1163Bba9AA81AC6d165de88
deployment tx: 0xdc1e5a61f584b2907a0bdadf258ece092fcb361110395c4055b95ffd048f6bd8
source sha256: bd5e981605f2533bd5354a4e884288d585020514d4be9eaabd9cdb4ff39d4c06
status: FINALIZED / FINISHED_WITH_RETURN
```

The fresh lifecycle used only the controlled fixture. V1 authentication stayed
`CLEARED` through challenge opening, semantic review, invalidation,
propagation, and recovery. The one semantic assessment returned the strict
bounded result `CONCLUSIVE / MATERIAL / INVALIDATE / MATERIAL_WITHDRAWAL`.
Both bounded queues finalized `COMPLETE`. The semantic transaction was tracked
again by ID in a restarted process with zero resubmissions. The installed SDK
does not provide a network source-download endpoint; the source-parity
artifact therefore records the exact submitted local hash and that limitation.
