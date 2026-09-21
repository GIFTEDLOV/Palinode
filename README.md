# PALINODE

PALINODE is a semantic revocation graph for evidence-dependent decisions: when
foundational evidence changes, GenLayer determines whether the change is
material and PALINODE deterministically traces and updates the downstream
reliance graph without rewriting history.

**Live app:** https://palinode-app.vercel.app<br>
**Studionet contract (frozen V4):** `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`<br>
**Network:** Studionet / chain `61999`<br>
**Frozen source SHA-256:** `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`<br>
**Freeze commit:** `14bb4574a8d248c978b55ff1fb70f32c0293f313`<br>
**Source:** `contracts/palinode_v2.py`

PALINODE is intentionally not a generic AI classifier, ordinary provenance
registry, simple fact-checker, dispute escrow, or backend database with a
decentralization label. The Intelligent Contract is canonical.

An ordinary smart contract can enforce the typed graph and hashes, but cannot
itself retrieve and contextualize mutable, unstructured evidence. An ordinary
backend can perform that semantic work, but its answer is controlled by one
operator and is not an adversarially shared GenLayer consensus outcome.

## The problem

A decision can be defensible when it is made and still require reconsideration
when the evidence beneath it is corrected, withdrawn, superseded, compromised,
or shown to be materially unreliable. Ordinary records preserve what was
registered, but do not determine which downstream decisions are affected.

## Why GenLayer

The contract can enforce identities, permissions, graph structure, state
transitions, and bounded propagation. It cannot by itself retrieve and
contextualize mutable public evidence. A conventional backend can perform that
semantic work, but its result is controlled by one operator. GenLayer provides
the consensus boundary for the bounded semantic question; deterministic
contract logic remains authoritative for every state mutation and graph effect.

## How PALINODE works

The lifecycle is: authenticate an immutable evidence identity, register typed
dependencies, open a permissionless challenge when evidence changes, adjudicate
materiality through GenLayer, propagate only the relationship-specific impact,
and use explicit successor evidence and recovery to resolve a particular active
cause without erasing history.

## Release status

This release contains one canonical Intelligent Contract at
[contracts/palinode_v2.py](contracts/palinode_v2.py). The former V1 deployment at
`0x9c9d1993cd938846D1163Bba9AA81AC6d165de88` is archived historical evidence;
it is not upgraded in place. The derived application lives
under [frontend](frontend); it does not replace canonical contract state. There
is no indexer database, ERC20 integration, or cross-contract messaging in this
phase. The source is published at https://github.com/GIFTEDLOV/Palinode. The
local security closure, cause-aware recovery lifecycle, bounded
pagination, adversarial tests, mutation harness, integration harness, and a
controlled Studionet proof are implemented. V4 is the frozen release after
reviewer closure: 46 public methods (21 writes, 25 views), cross-party
dependency authorization, typed third-party challenge standing, active-cause
propagation, and deterministic byte-identity checks. Live reviewer evidence
includes Authority C's `MATERIAL` / `QUESTION` challenge and a same-URL
`SOURCE_DIGEST_MISMATCH` proof before semantic adjudication. See
[docs/CONTRACT_FREEZE.md](docs/CONTRACT_FREEZE.md) and
[docs/FRONTEND_V4_MIGRATION.md](docs/FRONTEND_V4_MIGRATION.md).

The target is stable Studionet:

- GenLayer RPC: `https://studio.genlayer.com/api`
- Chain ID: `61999`
- network alias: `studionet`

`studio-dev`, chain ID `61997`, and Bradbury remain intentionally out of scope
for this phase.

## What GenLayer decides

The leader and validators independently retrieve bounded HTTPS evidence and
correction pages inside a nondeterministic execution boundary. They produce and
check only a strict structured result:

```json
{
  "result_status": "CONCLUSIVE",
  "change_authentic": true,
  "same_subject": true,
  "original_evidence_affected": true,
  "materiality": "MATERIAL",
  "root_effect": "INVALIDATE",
  "reason_code": "MATERIAL_CORRECTION"
}
```

The validator independently repeats the bounded retrieval and semantic task,
then requires exact agreement on all bounded fields. Malformed output is
rejected at the nondeterministic boundary; retrieval failure, digest mismatch,
encoding failure, and LLM failure become an explicit retryable path or a
consensus disagreement. None becomes a successful material or immaterial
verdict.

## What deterministic code decides

After an agreed result, the contract alone:

- creates immutable node, edge, and case records;
- enforces SHA-256 identities, HTTPS-only sources, strict field bounds, and
  duplicate policy;
- proves acyclicity by requiring every edge to point from a lower node sequence
  to a higher node sequence;
- applies the explicit node status transition table;
- applies only the relationship-specific propagation policy; and
- processes impact through a resumable per-case edge queue with a maximum of
  32 edges per call.

The contract never stores fetched document bodies. It stores source URI,
content digest, exact byte length, subject, title, creator, transaction time,
immutable creation sequence, current reliance status, separate authentication
status, authority binding, and historical validity metadata.

Registration is not authentication. Every newly registered node starts
`authentication_status=UNASSESSED` and `reliance_status=ACTIVE`; those are
intentionally independent dimensions. Authentication states are `UNASSESSED`, `PENDING`,
`CLEARED`, `REJECTED`, `INCONCLUSIVE`, and `SOURCE_UNAVAILABLE`. Contract
views expose `authentication_status`, the compatibility alias
`assessment_status`, and `reliance_status` directly. Revocation review is
case-scoped and never rewrites authentication.

## Authentication vs reliance

Evidence authentication and current reliance are separate dimensions. `CLEARED`
authentication means the authority-bound source was retrieved and matched its
committed URI, digest, and byte length. It does not mean the evidence can never
be challenged. A later material revocation can leave authentication `CLEARED`
while current reliance becomes `INVALIDATED`, `QUESTIONED`, or `SUPERSEDED`.

## Dependency graph

The graph contains `EVIDENCE`, `CLAIM`, `DECISION`, `ATTESTATION`, and
`AUTHORIZATION` nodes. Edges are typed as `SUPPORTS`, `REQUIRES`,
`DERIVED_FROM`, `QUALIFIES`, `AUTHORIZES`, `CORROBORATES`, or `CONTRADICTS`.
Creation ordering proves acyclicity without an unbounded traversal.

## Revocation and blast radius

A revocation case locks the target evidence, notice authority, notice URI,
digest, and byte length. GenLayer returns only bounded structured fields. The
contract then applies a typed root effect and a resumable bounded queue. A
`SUPPORTS` edge can question a claim while a `REQUIRES` edge can quarantine a
decision; an adverse source does not automatically invalidate every descendant.

## Successor evidence and recovery

Replacement evidence is a new immutable record. A successor relationship and a
cause-aware recovery case can resolve only the adverse cause it proves
corrected. The original evidence, revocation case, and status history remain
inspectable. This is succession, not rewriting.

## Live Studionet proof

The recorded live proof is:

1. Evidence V1 authenticated as `CLEARED`.
2. Revocation finalized as `CONCLUSIVE` / `MATERIAL` / `INVALIDATE` with
   `MATERIAL_WITHDRAWAL`.
3. Typed propagation changed the Claim to `QUESTIONED` and the Decision to
   `QUARANTINED`.
4. Evidence V2 authenticated independently as `CLEARED`.
5. Recovery finalized as `CONCLUSIVE` / `SUPERSEDE` /
   `RECOVERY_RESOLVED_SUPERSEDE`.
6. V1 authentication remained `CLEARED` while its current reliance became
   `SUPERSEDED`.
7. An unrelated Authority C challenge was classified as
   `MATERIAL_THIRD_PARTY_CHALLENGE` with `QUESTION`; it could not produce
   source-authoritative `INVALIDATE` semantics.
8. A registered BODY A served as BODY B at the same URI and the contract
   committed `SOURCE_DIGEST_MISMATCH` without an adverse cause or semantic
   mutation.

This demonstrates that historical authentication can remain true while current
reliance evolves.

## Lifecycle

1. An authority registers a canonical HTTPS origin and proves control by a
   consensus-checked `/.well-known/palinode.json` document binding the origin,
   caller address, policy, and nonce. Authorities have a stable ID and
   versioned `ACTIVE`/`REVOKED` lifecycle; rotation creates a new version and
   never rewrites historical evidence.
2. The active source-authority controller registers evidence; generic
   non-evidence node registration remains permissionless. Evidence must
   reference a verified authority whose origin contains the normalized source
   URI. The canonical ID is generated on-chain.
3. The controller of the child asserts a typed dependency from an earlier
   parent node to a later child node. The parent must exist and satisfy graph
   preconditions, but its publisher does not have to approve another party's
   reliance. The edge assertor is stored on-chain.
4. Any caller opens a revocation case against evidence with a verified notice
   authority, locked URI, digest, byte length, and reason code. Owners cannot
   suppress or erase cases.
5. `assess_revocation(case_id)` assesses only the immutable case identity;
   callers cannot substitute another evidence or notice URL.
6. If evidence authentication retrieval is unavailable, the node becomes
   `SOURCE_UNAVAILABLE`, not cleared or rejected. If revocation retrieval is
   unavailable, the case becomes retryable/inconclusive while authentication
   remains unchanged. Any caller may use
   `retry_revocation_case(case_id, evidence_mirror_id, notice_mirror_id)`;
   permissionless mirrors may come from independent HTTPS origins, but are
   accepted only after consensus-checked digest and byte-length equality. A
   mirror is retrieval-only and cannot change canonical identity or clear an
   object.
7. Deterministic code records the consensus result and applies the root effect.
8. `process_impact(case_id, max_steps)` resumes bounded edge propagation until
   the case is complete.
9. Replacement evidence is a new immutable object. The predecessor authority
   controls `link_evidence_successor`; it records lineage without changing
   reliance or rewriting the old object.
10. A permissionless recovery case binds one material adverse case to one
    already linked and independently `CLEARED` successor. GenLayer adjudicates
    whether that successor resolves the specific defect; deterministic bounded
    recovery propagation removes only that case's active cause. Another active
    adverse cause keeps the node adversely affected.

There are no protocol-wide lifetime caps on nodes, edges, authorities,
revocation cases, or recovery cases. Per-node fan-in/fan-out, bounded queues,
fixed-size history/telemetry rings, mirror limits, string/body limits, and
per-call step limits remain. Lifetime IDs are exposed only through bounded page
views, never through an unbounded full-list getter.

## Security model

Canonical state is the GenLayer Intelligent Contract state and the consensus
result accepted for the semantic block. Validator selection is protocol-owned;
callers cannot select reviewers or semantic decision-makers for their own
cases. Authority challenge results, evidence/notice identities, assessment
transitions, reliance transitions, and impact queues are canonical only after
the applicable GenLayer transaction is final. Web pages, LLM responses,
caller input, wallets, frontends, indexers, and databases are non-canonical
inputs or views. An indexer may present state but can never authorize a
mutation or replace a contract read.

## Application transaction state

The future UI must track the GenLayer transaction ID returned by submission and
persist it across restarts. `ACCEPTED` means that a proposed outcome reached
consensus; it is not proof that execution succeeded or that the transaction is
final. The client state model therefore keeps separate fields for submission,
consensus acceptance, execution success, and finalization, and resumes polling
the same transaction ID after timeout instead of automatically resubmitting.

## Architecture

The React/TypeScript/Vite application in `frontend/` reads bounded canonical
pages from the frozen Studionet contract and presents the dependency graph,
blast radius, evidence authentication versus reliance, revocation and
recovery command centers, authority records, activity, proof, and integration
guidance. Browser writes use the frozen ABI and persist GenLayer transaction
IDs locally; the client requires final protocol state plus
`FINISHED_WITH_RETURN` before displaying a successful write.

Run it locally:

```powershell
cd frontend
npm install
npm run typecheck
npm test
npm run lint
npm run build
npm run dev
npm run browser-qa
```

Wallet connection is optional for read-only exploration; write actions require
a compatible wallet on Studionet. The controlled static fixture at
`https://palinode-fixture.vercel.app` remains separate from the application.
The production frontend is deployed at
`https://palinode-app.vercel.app`. Browser reads use a narrow same-origin
`/api/rpc` relay because the public Studionet RPC does not expose browser CORS;
the relay forwards only to `https://studio.genlayer.com/api` and never becomes
canonical state.

The application routes are organized around the protocol lifecycle: overview,
global graph, evidence and decision records, revocation and recovery command
centers, authorities, activity, Proof & Security, integration guidance, and
protocol docs. The graph, blast-radius views, authentication/reliance split,
immutable notice identity, active causes, and successor recovery read the
bounded contract model rather than a frontend database.

The release browser pass uses Playwright against the local production build and
the production alias across desktop, tablet, and mobile viewports. The V4 pass
also covers provider wiring, lifecycle display, canonical impact, pagination,
and explicit form validation. A real wallet write remains a controlled operator
smoke against a completed case; no protocol changes are made by the frontend.

## Testing

The recorded freeze gates are 55 direct tests, 5 invariant tests, 34
adversarial tests, 2 property tests, and 46/49 security mutations killed,
with 3 obsolete overflow-summary mutations retired and 0 survivors.
These are engineering test results, not formal verification.

## Run locally

From PowerShell in the repository root:

```powershell
.venv\Scripts\python.exe -m pytest tests/direct tests/invariants -q
$env:GENVM_VERSION = "v0.2.16"
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
.venv\Scripts\genvm-lint.exe check contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe typecheck contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe schema contracts/palinode.py --output artifacts/palinode_schema.json --json
.venv\Scripts\python.exe -m pytest tests/adversarial tests/property -q
.venv\Scripts\python.exe -m pytest tests/integration -q -rs
.venv\Scripts\python.exe scripts/mutation_checks.py
```

The same sequence is available as `scripts/phase1_checks.ps1`. Direct tests
use `genlayer-test` mocks for web and LLM calls; they do not contact Studionet.
The integration suite exercises the supported local GLSim JSON-RPC surface and
reports runner-specific skips separately; local GLSim is not evidence of
Studionet deployment compatibility. See `docs/INTEGRATION_TESTING.md` and
`docs/DEPLOYMENT.md`. The resumable hosted canary harness is
`scripts/studionet_canary.py`; it persists transaction IDs and never
automatically resubmits them.

## Known limitations

- The protocol still supports one canonical contract only. The frontend is a
  derived client and does not replace a purpose-built indexer for large-scale
  history search.
- Semantic adjudication relies on independently retrieved public HTTPS pages;
  page availability, page mutation, model disagreement, and source ambiguity
  remain explicit failure or inconclusive paths.
- Authority verification is limited to the fixed
  `WELL_KNOWN_ADDRESS_NONCE_V1` policy. A controlled public HTTPS fixture is
  still required to exercise live domain proof; the code does not weaken this
  requirement for testing.
- Authority versions support permissionless domain-declaration rotation and
  explicit controller revocation. Revocation lowers trust for new writes but
  does not rewrite historical evidence or silently invalidate it.
- Recovery is consensus-backed and cause-aware. `REINSTATED` is never an owner
  setter: each active adverse cause must be resolved by its own accepted
  recovery result. `SUPERSEDED` remains distinct from reinstatement.
- Local GLSim integration has an observed Windows runner/temp-file failure in
  the installed toolchain; one isolated clean reproduction is required before
  recording it as a known local blocker, and hosted Studionet remains the
  authoritative integration target.
- The current propagation policy is conservative but intentionally not a
  complete domain theory for every decision system.
- Authority versions have no permanent eight-version lifetime cap. They are
  paginated for bounded reads; benign rotation marks the old version
  `SUPERSEDED`, while explicit revocation remains distinct and historical
  evidence keeps its recorded version.
- Live recovery and semantic behavior still depend on public HTTPS availability
  and real validator agreement; local mocks cannot prove hosted behavior.
- The direct harness uses the stable `v0.2.16` GenVM artifact. The repository
  does not claim that direct-mode compatibility alone proves Studionet
  production behavior. The archived canary-v1 and canary-v2 evidence retain
  their actual hosted outcomes; canary-v3 is the candidate frozen address.
  The installed SDK does not expose a network source-download endpoint, so
  source parity is recorded against the exact submitted source hash and this
  limitation is explicit in the freeze record.
- No legal, regulatory, or factual truth guarantee is implied by a semantic
  verdict; PALINODE records a bounded adjudication of registered dependency
  impact.
- The frontend cannot provide a real signature or account-funding test without
  an operator wallet extension. It handles disconnected, wrong-network,
  account-change, and disconnect states, but the release QA does not claim a
  live wallet signature was made.

See the [documentation index](docs/ARCHITECTURE.md) for the complete protocol
model.
