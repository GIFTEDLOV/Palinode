# PALINODE

PALINODE is a Semantic Revocation Graph for evidence-dependent decisions.
It records explicit, typed dependencies between evidence, claims, decisions,
attestations, and authorizations. When foundational evidence is later
corrected, withdrawn, superseded, compromised, or shown to be materially
unreliable, GenLayer adjudicates whether that change materially undermines the
registered evidence in its dependency context. Deterministic contract logic
then applies typed, bounded impact through the graph.

PALINODE is intentionally not a generic AI classifier, ordinary provenance
registry, simple fact-checker, dispute escrow, or backend database with a
decentralization label. The Intelligent Contract is canonical.

An ordinary smart contract can enforce the typed graph and hashes, but cannot
itself retrieve and contextualize mutable, unstructured evidence. An ordinary
backend can perform that semantic work, but its answer is controlled by one
operator and is not an adversarially shared GenLayer consensus outcome.

## Phase 2 status

This phase contains one canonical Intelligent Contract at
[contracts/palinode.py](contracts/palinode.py). There is no frontend, indexer,
deployment, ERC20 integration, cross-contract messaging, or GitHub repository
in this phase. The local security closure and integration harnesses are
implemented; live authority validation and a Studionet canary remain gated on
external fixtures and network tooling.

The target is stable Studionet:

- GenLayer RPC: `https://studio.genlayer.com/api`
- Chain ID: `61999`
- network alias: `studionet`

`studio-dev`, chain ID `61997`, Bradbury, and deployment are intentionally out
of scope for this phase.

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
then requires exact agreement on all bounded fields. Malformed output,
retrieval failure, digest mismatch, encoding failure, and LLM failure become an
explicit `RETRYABLE`/`INCONCLUSIVE` result or a consensus disagreement; none
becomes a successful material or immaterial verdict.

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
immutable creation sequence, current reliance status, separate assessment
status, authority binding, and historical validity metadata.

Registration is not assessment. Every newly registered node starts
`assessment_status=UNASSESSED` and `status=ACTIVE`; those are intentionally
independent dimensions. Assessment states are `UNASSESSED`, `PENDING`,
`CLEARED`, `REJECTED`, `INCONCLUSIVE`, and `SOURCE_UNAVAILABLE`. Contract
views expose both fields directly, so a UI never has to infer consensus
clearance from current reliance.

## Lifecycle

1. An authority registers a canonical HTTPS origin and proves control by a
   consensus-checked `/.well-known/palinode.json` document binding the origin,
   caller address, policy, and nonce. Authorities have a stable ID and
   versioned `ACTIVE`/`REVOKED` lifecycle; rotation creates a new version and
   never rewrites historical evidence.
2. A caller registers evidence or a non-evidence node. Evidence must reference
   a verified authority whose origin contains the normalized source URI.
   Registration is permissionless and generates the canonical ID on-chain.
3. A caller registers a typed dependency from an earlier node to a later node.
4. Any caller opens a revocation case against evidence with a verified notice
   authority, locked URI, digest, byte length, and reason code. Owners cannot
   suppress or erase cases.
5. `assess_revocation(case_id)` assesses only the immutable case identity;
   callers cannot substitute another evidence or notice URL.
6. If retrieval is unavailable, the node becomes `SOURCE_UNAVAILABLE`, not
   semantically cleared or rejected. Any caller may use
   `retry_revocation_case(case_id, evidence_mirror_id, notice_mirror_id)`;
   permissionless mirrors may come from independent HTTPS origins, but are
   accepted only after consensus-checked digest and byte-length equality. A
   mirror is retrieval-only and cannot change canonical identity or clear an
   object.
7. Deterministic code records the consensus result and applies the root effect.
8. `process_impact(case_id, max_steps)` resumes bounded edge propagation until
   the case is complete.
9. Replacement evidence is a new immutable object. `link_evidence_successor`
   records lineage without rewriting the old object.

## Trust boundaries

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

## Development commands

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
`docs/DEPLOYMENT.md`.

## Known limitations

- The protocol still supports one canonical contract only and does not expose
  an indexer or UI.
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
- Local GLSim integration currently has a Windows runner/temp-file failure in
  the installed toolchain; the test records the exact skip instead of treating
  direct-mode success as network proof.
- The current propagation policy is conservative but intentionally not a
  complete domain theory for every decision system.
- Recovery records successor lineage, but a full successor re-adjudication
  workflow and reinstatement governance are future work.
- The direct harness uses the stable `v0.2.16` GenVM artifact. The repository
  does not claim that direct-mode compatibility alone proves Studionet
  production behavior, and no Studionet transaction has been broadcast.
- No legal, regulatory, or factual truth guarantee is implied by a semantic
  verdict; PALINODE records a bounded adjudication of registered dependency
  impact.

See the [documentation index](docs/ARCHITECTURE.md) for the complete protocol
model.
