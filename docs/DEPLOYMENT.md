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

The one permitted deployment was finalized successfully:

```text
contract: 0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4
deployment tx: 0xdfc919f95a0276be9381a3e38d871e0b45e4ec14ed4040f13f6257d758098ddc
source sha256: eb39390b9da51e70aa54af130c1d45ab392c1b85d327975c462df5d5f10984be
```

The live deterministic lifecycle finalized through authority registration,
evidence authentication, graph registration, challenge opening, successor
authentication, and lineage linking. The real validator result for the
revocation assessment was recorded as `RETRYABLE`/`INCONCLUSIVE` with
`LLM_MALFORMED`; no impact or recovery was fabricated. A permissionless retry
transaction was finalized and the recovery case remains correctly deferred
until a material active cause exists. Full transaction IDs and readbacks are
in `evidence/studionet/transactions.json` and `lifecycle.json`.

No transaction is rebroadcast after a timeout, and no fake domain ownership or
weakened authority rule is permitted.
