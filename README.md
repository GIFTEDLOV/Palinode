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

## Phase 1 status

Phase 1 contains one canonical Intelligent Contract at
[contracts/palinode.py](contracts/palinode.py). There is no frontend, indexer,
deployment, ERC20 integration, cross-contract messaging, or GitHub repository
in this phase.

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
immutable creation sequence, current status, and historical validity metadata.

## Lifecycle

1. A caller registers evidence or a non-evidence node. Registration is
   permissionless and generates the canonical ID on-chain; callers cannot
   supply or reuse a node ID.
2. A caller registers a typed dependency from an earlier node to a later node.
3. A caller opens a revocation case against an evidence node with a correction
   notice URI, digest, byte length, and reason code.
4. `assess_revocation(case_id)` reaches the semantic consensus boundary.
5. Deterministic code records the result and applies the root effect.
6. `process_impact(case_id, max_steps)` resumes bounded edge propagation until
   the case is complete.
7. Replacement evidence is a new immutable object. `link_evidence_successor`
   records lineage without rewriting the old object.

## Trust boundaries

Canonical state is the GenLayer Intelligent Contract state and the consensus
result accepted for the semantic block. Validator independence and GenLayer
finality are part of the trust model. Web pages, LLM responses, caller input,
wallets, frontends, indexers, and databases are non-canonical inputs or views.
An indexer may present state but can never authorize a mutation or replace a
contract read.

## Development commands

From PowerShell in the repository root:

```powershell
.venv\Scripts\python.exe -m pytest tests/direct tests/invariants -q
$env:GENVM_VERSION = "v0.2.16"
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
.venv\Scripts\genvm-lint.exe check contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe typecheck contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe schema contracts/palinode.py --output artifacts/palinode_abi.json
```

The same sequence is available as `scripts/phase1_checks.ps1`. Direct tests
use `genlayer-test` mocks for web and LLM calls; they do not contact Studionet.
Integration testing against Studionet is a later, explicitly authorized step.

## Known limitations

- Phase 1 supports one contract only and does not expose an indexer or UI.
- Semantic adjudication relies on independently retrieved public HTTPS pages;
  page availability, page mutation, model disagreement, and source ambiguity
  remain explicit failure or inconclusive paths.
- The current propagation policy is conservative but intentionally not a
  complete domain theory for every decision system.
- Recovery records successor lineage, but a full successor re-adjudication
  workflow and reinstatement governance are future work.
- The direct harness uses the stable `v0.2.16` GenVM artifact. The repository
  does not claim that direct-mode compatibility alone proves Studionet
  production behavior.
- No legal, regulatory, or factual truth guarantee is implied by a semantic
  verdict; PALINODE records a bounded adjudication of registered dependency
  impact.

See the [documentation index](docs/ARCHITECTURE.md) for the complete protocol
model.
