# Deployment gate

No deployment has been broadcast for Phase 2.

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

The canary is currently blocked before broadcast by two concrete conditions:
the local GLSim deployment path hits an installed Windows runner/temp-file
failure, and there is no controlled HTTPS authority fixture serving the exact
PALINODE well-known document. The authority check will not be weakened or
replaced with a fake public-domain ownership claim. When the fixture exists,
only its live authority portion should be added to the smoke lifecycle before
semantic spending.

