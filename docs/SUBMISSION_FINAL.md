# PALINODE — Final Submission Package

## Project name

PALINODE

## One-line description

PALINODE maps semantic evidence changes to bounded, typed recovery actions across dependent decisions.

## Approximately 300-character description

PALINODE is a semantic revocation graph for evidence-dependent decisions. It binds evidence to source authorities, lets GenLayer reach consensus on whether a change is materially relevant, then deterministically propagates typed effects through claims, decisions, attestations, and authorizations while preserving history and enabling explicit recovery.

## Approximately 700-character description

PALINODE addresses stale-evidence risk: a decision can be defensible when made but require reconsideration when its evidence is corrected, withdrawn, revoked, superseded, compromised, or materially unreliable. Immutable evidence identities, authority/version binding, and typed dependency edges define the graph. GenLayer handles the narrow semantic question—whether authenticated evidence materially undermines the registered dependency—while deterministic contract code enforces identity, authorization, typed propagation, active causes, bounded queues, and recovery. Historical authentication remains separate from current reliance, so the system can question, quarantine, supersede, or authorize invalidation without rewriting history.

## Full project description

PALINODE is a semantic revocation graph for evidence-backed decisions. Its core
graph is:

`Evidence -> Claim -> Decision -> Attestation -> Authorization / downstream dependency`

When evidence changes, PALINODE verifies the exact registered bytes and then
uses GenLayer semantic consensus only for the bounded materiality question.
Deterministic contract logic records the result, applies a typed root effect,
propagates bounded active causes, and supports explicit successor recovery.

The model separates historical validity from current reliance. An evidence item
can remain authenticated and historically inspectable while its reliance becomes
`QUESTIONED`, `QUARANTINED`, `INVALIDATED`, or `SUPERSEDED`.

## Why GenLayer?

Deterministic code can compare immutable identifiers, digests, byte lengths,
authority bindings, and graph structure. It cannot, by itself, retrieve and
contextualize mutable public evidence and decide whether a correction materially
undermines a registered dependency. GenLayer provides an adversarially shared
semantic-consensus boundary for that narrow question. It does not decide
arbitrary truth and PALINODE does not treat it as an oracle: the contract alone
controls the accepted structured result and every state mutation.

## Technical architecture

- Frozen Intelligent Contract: `contracts/palinode_v2.py`
- V4 contract: `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`
- Network: Studionet, chain `61999`
- Production app: https://palinode-app.vercel.app
- Source SHA-256: `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`
- Public repository: https://github.com/GIFTEDLOV/Palinode

Release identity is split deliberately: contract source freeze
`14bb4574a8d248c978b55ff1fb70f32c0293f313`; initial V4 release source
`be8a14b09f4ad1f40a9fdb0429dd16d3942795a9`; and the current repository /
frontend release source HEAD, `b59f85d346f7234b50ec15a3f4b97a87fc667cd8`; the
final metadata commit and GitHub release are recorded separately. The contract itself has
not changed.

The frontend reads bounded canonical views, distinguishes authentication from
reliance, renders canonical impact separately from graph reachability, persists
transaction IDs, and uses the connected EIP-1193 wallet provider for writes.

## Core features

- Immutable evidence identities
- Source authority and historical-version binding
- Typed dependency graph with child-side edge assertion
- Source-authoritative revocation and independent third-party challenge
- GenLayer semantic adverse review
- Bounded relationship-specific propagation
- Individually keyed active causes
- Successor lineage and explicit recovery
- Historical validity/current reliance separation
- Deterministic same-URL evidence drift detection
- Finalized transaction tracking without automatic resubmission

## Security and reliability

V4 prevents successor hijacking, unauthorized dependency poisoning, non-cleared
semantic review, digest/byte-length mismatch before semantic execution, late-edge
bypass, cause-counter corruption, premature recovery, prompt injection, and
unbounded reads. Third-party challengers can question reliance but cannot
impersonate source-authoritative invalidation. Historical authority versions are
authenticated according to their recorded binding; benign supersession remains
distinct from revocation. Mirrors, prompts, queues, and public views are bounded.

## Live reviewer walkthrough

Suggested 2–4 minute flow:

1. Open the landing page and Overview.
2. Open Evidence V1 and show `CLEARED` authentication versus current reliance.
3. Open the typed graph and canonical blast-radius view.
4. Open the source-authoritative material revocation and show typed propagation.
5. Open the third-party challenge and show `MATERIAL` / `QUESTION` and its
   challenge-specific reason rather than source-authoritative invalidation.
6. Open successor and recovery records; show V1 remains historical while its
   reliance is superseded.
7. Open Proof & Security and show the byte-mismatch proof and release gates.
8. Show the frozen deployment metadata and real wallet proof.

## Live links and release identity

- GitHub: https://github.com/GIFTEDLOV/Palinode
- Production: https://palinode-app.vercel.app
- Network: Studionet / `61999`
- Intelligent Contract: `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`
- Frozen source: `contracts/palinode_v2.py`
- Source SHA-256: `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`

## Testing and assurance

Backend V4 assurance recorded for release:

- 28 direct tests
- 5 invariant tests
- 34 adversarial tests
- 2 property tests
- 27 reviewer-remediation V2 tests
- 96 contract tests total
- 49 mutation cases: 46 killed, 3 retired obsolete mutations, 0 survived

Frontend release gates:

- 49 tests passed
- Deterministic browser E2E: 96 responsive assertions passed
- Desktop, tablet, and mobile: passed
- Rate-limit regression: passed
- Unexpected deterministic E2E console errors: 0
- Real EIP-1193 wallet proof: passed

These are engineering test results, not formal verification.

## Real wallet proof

Primary operator-controlled proof:

- TX: `0x5550723fae8da058933a3b8adc7a54280170573132ad224b2e00756ff0e63451`
- Sender: `0x4f7a14c8cd83caa18Fafc35aA91a8483Cc95E3E5`
- Target: `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`
- Method: `process_impact`
- Args: `["86bb1eaddcd802361a5105a8e492cc67f2d3fc647e2a20111bd1158ea4e07534", 1]`
- Result: `FINALIZED` / `FINISHED_WITH_RETURN` / `0`
- Canonical mutation: `NONE`

A second manually approved duplicate safe transaction also finalized with
return `0` and no canonical mutation. It is preserved transparently in the
release evidence and was not an automatic resubmission.

## Known history

The V1 deployment at `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88` is the
**ARCHIVED PRE-REVIEW DEPLOYMENT**. The current release is V4 at the contract
address listed above; V1 is not the production source or runtime target.

## Steward remediation

The Revocations page now provides a validated `open_revocation_case` flow that
submits the frozen V4 seven-argument write for CLEARED evidence. Repository
tests assert the exact method and argument order.
