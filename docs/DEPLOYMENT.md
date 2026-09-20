# Deployment gate

No PALINODE contract deployment has been broadcast for Phase 2.5.

A future canary must use only stable Studionet:

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
serves the exact committed bytes recorded in `evidence/studionet/fixture.json`.
The local GLSim issue is recorded as `KNOWN_LOCAL_BLOCKER`; it does not block
hosted Studionet by itself. The current preflight is stopped before broadcast
because the resolved public deployer address has zero GEN balance. The faucet
or another documented funding action must fund that same address first. No
contract transaction is rebroadcast after a timeout, and no fake domain
ownership or weakened authority rule is permitted.
