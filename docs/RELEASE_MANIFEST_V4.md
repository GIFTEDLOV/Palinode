# PALINODE V4 Release Manifest

This manifest is the authoritative release record for the frozen PALINODE V4
frontend and protocol publication.

## Identity

- Project: PALINODE — Semantic Revocation Graph
- Release source commit: `be8a14b09f4ad1f40a9fdb0429dd16d3942795a9`
- Publication documentation commit: the final commit containing this manifest
- Publication date: `2026-09-22`
- Freeze status: `READY`

## Deployment

- Production URL: https://palinode-app.vercel.app
- Production deployment ID: `dpl_HjZaHi6m7bagByh9icJ8RAJqQrFf`
- Network: Studionet
- Chain ID: `61999`
- V4 contract: `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`
- Frozen source: `contracts/palinode_v2.py`
- Source SHA-256: `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`

## Verified assurance

- Backend: 55 direct, 5 invariant, 34 adversarial, and 2 property tests
- Mutation catalogue: 49 total, 46 killed, 3 retired obsolete mutations, 0 survived
- Frontend tests: 49 passed
- Deterministic browser E2E: 96 assertions passed, 0 unexpected console errors
- Responsive QA: desktop, tablet, and mobile passed
- Rate-limit regression: passed
- Real EIP-1193 wallet proof: passed

These results are engineering assurance, not formal verification.

## Primary real-wallet proof

- Transaction: `0x5550723fae8da058933a3b8adc7a54280170573132ad224b2e00756ff0e63451`
- Sender: `0x4f7a14c8cd83caa18Fafc35aA91a8483Cc95E3E5`
- Target: `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`
- Method: `process_impact`
- Arguments: `["86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534", 1]`
- Protocol status: `FINALIZED`
- Execution result: `FINISHED_WITH_RETURN`
- Return: `0`
- Canonical mutation: `NONE`

A separate manual duplicate safe QA transaction was also finalized state-neutrally:

- Transaction: `0x1e505972ba15d231e029469be17fde7e9e6e911b95cb28d040111e37ae3662bc`
- Classification: `MANUAL_DUPLICATE_SUBMISSION=YES`
- Automatic resubmissions: `0`

## Reviewer fixture

- Reviewer fixture: https://palinode-reviewer-fixture.vercel.app
- Authority C standing and byte-mismatch evidence are committed under
  `evidence/studionet/v4/`.
- The V1 evidence and failed pre-review wallet attempt remain historical records;
  they are not hidden or rewritten.

## Archived deployment

- Archived pre-review V1 contract:
  `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88`
- V1 is not the current production contract.

## Publication

- GitHub: https://github.com/GIFTEDLOV/Palinode
- Final publication is a normal push to `origin/main`; no force push is used.
