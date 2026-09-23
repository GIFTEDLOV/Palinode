# PALINODE V4 Release Manifest

This document explains the release identities and points to the canonical
machine-readable index at
`evidence/studionet/v4/release-manifest.json`. The JSON index references the
existing proof records under `evidence/studionet/v4/`; it does not duplicate
their transaction payloads.

## Current release status

V4 is deployed on Studionet, and the production frontend is live at
https://palinode-app.vercel.app. The contract is frozen at
`0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`; this hardening pass does not
change or redeploy it.

The three repository identities are distinct:

- Contract source freeze: `14bb4574a8d248c978b55ff1fb70f32c0293f313`.
- Initial V4 release source: `be8a14b09f4ad1f40a9fdb0429dd16d3942795a9`.
- Current repository / frontend release HEAD: the final HEAD of this pass,
  recorded in the JSON index and the GitHub release.

## Frozen contract

| Field | Value |
|---|---|
| Source path | `contracts/palinode_v2.py` |
| Source SHA-256 | `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601` |
| Network | Studionet |
| Chain ID | `61999` |
| RPC | `https://studio.genlayer.com/api` |
| Address | `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b` |
| Schema | 46 methods: 21 writes, 25 views |

## Verified assurance

- Contract collection: 28 direct, 5 invariant, 34 adversarial, 2 property,
  and 27 reviewer-remediation V2 tests; 96 total.
- Mutation catalogue: 49 total, 46 killed, 3 retired, 0 survived.
- Integration: 6 passed and 1 known Windows GLSim skip.
- Frontend: 57 tests passed, typecheck/lint/build passed.
- Browser: 96 deterministic route assertions, 0 unexpected console errors,
  desktop/tablet/mobile passed, and rate-limit regression passed.
- CI write paths use fixtures and mocks only.

## Live proof and fee policy

The primary wallet proof transaction is
`0x5550723fae8da058933a3b8adc7a54280170573132ad224b2e00756ff0e63451`.
It finalized `process_impact` with `FINISHED_WITH_RETURN`, return `0`, and no
canonical mutation. The canonical V4 proof state remains the authenticated V1
and V2 evidence lineage, material withdrawal and typed propagation, successor
recovery, third-party `QUESTION` standing, and same-URL digest mismatch before
semantic adjudication.

Application value for PALINODE writes is `0`. Stable `genlayer-js` `1.1.8`
already estimates gas and reads `eth_gasPrice` through `writeContract`; the
recorded Studionet behavior is gas price `0`. The frontend still persists one
transaction ID, treats `ACCEPTED` as provisional, and requires finalized
`FINISHED_WITH_RETURN` for durable write success.

Archived V1/V2/V3 canaries and deployment records are historical only. They are
not active runtime defaults, and no license is added by this release pass.
