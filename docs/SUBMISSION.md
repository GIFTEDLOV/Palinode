# PALINODE submission package

## PROJECT NAME

PALINODE

## TAGLINE

Semantic revocation infrastructure for evidence-dependent decisions.

## SHORT DESCRIPTION

PALINODE uses GenLayer to judge whether changed evidence materially undermines a decision, then deterministically traces bounded impact through its dependency graph.

## MEDIUM DESCRIPTION

Decisions inherit weaknesses from the evidence beneath them. PALINODE records immutable evidence, typed dependencies, authority-bound source identities, and current reliance separately from historical authentication. When evidence is corrected, withdrawn, or compromised, GenLayer produces a bounded semantic verdict and the Intelligent Contract propagates only the relationship-specific consequence. Successor evidence and cause-aware recovery resolve the right defect without rewriting history.

## FULL DESCRIPTION

PALINODE is a Semantic Revocation Graph for evidence-dependent decisions. It addresses a gap between provenance and operational trust: a record may have been valid when created, but later evidence can be corrected, withdrawn, superseded, compromised, or shown to be materially unreliable. PALINODE preserves the original evidence and its authentication history, while exposing the current reliance state of every downstream claim and decision.

The canonical GenLayer Intelligent Contract registers authority-bound evidence, claims, decisions, attestations, authorizations, and typed dependency edges. A permissionless revocation case commits an immutable notice identity. GenLayer validators answer one bounded question: does that change materially undermine the registered evidence in the context where downstream nodes rely on it? Deterministic contract logic then applies the typed root effect and resumes bounded propagation through the graph. A `SUPPORTS` edge can question a claim while a `REQUIRES` edge can quarantine a decision; one failed source does not automatically invalidate every descendant.

Recovery is explicit. Corrected evidence is registered as a new immutable record, linked as a successor, independently authenticated, and evaluated against the specific adverse cause. Recovery never erases the old evidence, revocation case, or status history. This makes PALINODE a protocol for revisability and accountable succession, not a generic AI classifier or ordinary provenance database.

## PROBLEM

Evidence-dependent decisions need a durable answer to “what must be reconsidered now?” when foundational evidence changes. Existing systems tend to preserve a static record, rely on a centralized reviewer, or apply an overly broad invalidation rule.

## SOLUTION

Immutable identity, authority binding, typed DAG dependencies, strict semantic results, cause-aware impact propagation, and explicit successor recovery in one canonical Intelligent Contract.

## WHY GENLAYER

Smart-contract code can enforce deterministic state but cannot contextualize mutable public documents. A backend can do that work but its judgment is controlled by one operator. GenLayer supplies the consensus boundary for the semantic question while deterministic code controls all canonical mutations.

## WHAT MAKES IT NOVEL

PALINODE combines semantic materiality determination with typed, bounded, cause-aware propagation. It keeps source authentication, current reliance, review status, and historical validity as distinct dimensions.

## HOW IT WORKS

1. Bind evidence and notices to a registered HTTPS source authority.
2. Commit immutable content digest, byte length, subject, and URI identity.
3. Register typed dependency edges with creation ordering.
4. Open a permissionless revocation case.
5. Let GenLayer produce a strict bounded result.
6. Process typed impact through a resumable bounded queue.
7. Register and authenticate successor evidence.
8. Resolve only the matching adverse cause through consensus-backed recovery.

## LIVE APP

https://palinode-app.vercel.app

## GITHUB

https://github.com/GIFTEDLOV/Palinode

## STUDIONET CONTRACT (FROZEN V4)

`0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`

Source: `contracts/palinode_v2.py`<br>
SHA-256: `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`<br>
Release source commit: `14bb4574a8d248c978b55ff1fb70f32c0293f313`<br>
Archived V1: `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88`

## NETWORK

Studionet, chain ID `61999`.

## CORE FEATURES

- Authority-bound source authentication.
- Immutable evidence and notice identities.
- Typed acyclic dependency graph.
- Permissionless revocation and bounded semantic adjudication.
- Relationship-specific blast-radius propagation.
- Active-cause composition and bounded recovery.
- Successor evidence without historical rewriting.
- Finality-aware transaction handling.
- Derived frontend views with no canonical database.

## TECHNICAL ARCHITECTURE

The canonical contract is `contracts/palinode_v2.py`. The React/TypeScript/Vite
frontend reads bounded pages from the frozen Studionet address. A narrow
same-origin `/api/rpc` relay prevents browser CORS failures while forwarding to
the documented Studionet RPC; it is not canonical state. GenLayer semantic
operations are bounded structured results, never raw prose or direct graph
mutation.

## SECURITY / TESTING

Recorded freeze gates: 55 direct tests, 5 invariant tests, 34 adversarial
tests, 2 property tests, and 46/49 security mutations killed; 3 obsolete
overflow-summary mutations were retired and 0 survived. See
[SECURITY_AUDIT.md](SECURITY_AUDIT.md), [THREAT_MODEL.md](THREAT_MODEL.md),
[TRUST_MODEL.md](TRUST_MODEL.md), and [CONTRACT_FREEZE.md](CONTRACT_FREEZE.md).
These results do not constitute formal verification or a claim of perfect
security.

## LIVE PROOF

The controlled Studionet proof authenticated Evidence V1 as `CLEARED`, produced
`CONCLUSIVE` / `MATERIAL` / `INVALIDATE` with `MATERIAL_WITHDRAWAL`, propagated
Claim `QUESTIONED` and Decision `QUARANTINED`, independently authenticated
Evidence V2, and finalized recovery as `CONCLUSIVE` / `SUPERSEDE` /
`RECOVERY_RESOLVED_SUPERSEDE`. V1 authentication stayed `CLEARED` while its
current reliance became `SUPERSEDED`. Reviewer closure additionally proved
that Authority C can create a bounded third-party `QUESTION` challenge but
cannot impersonate authoritative withdrawal, and that a same-URL byte change
is rejected as `SOURCE_DIGEST_MISMATCH` before semantic adjudication.

## KNOWN LIMITATIONS

Semantic results depend on public HTTPS availability and validator agreement.
The frontend is a derived client, not a full historical indexer. Real wallet
signature and funding tests require an operator wallet extension. The frozen
contract remains a single canonical contract; no ERC20 or cross-contract
integration is included.
