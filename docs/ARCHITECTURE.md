# PALINODE architecture

## Purpose

PALINODE records whether a later change to registered foundational evidence
materially undermines a particular downstream dependency. The semantic
question is contextual and evidence-dependent; the consequences are typed,
deterministic, and bounded.

## One canonical contract

Phase 1 intentionally keeps registration, lineage, revocation state, semantic
result, node status, propagation queue, and recovery-compatible succession in
`contracts/palinode.py`. This prevents an indexer or second contract from
becoming an accidental source of truth while the invariants are being proven.

The contract has three layers:

1. Deterministic registration and validation: canonical IDs, immutable metadata,
   strict input bounds, node sequencing, typed edges, and duplicate policy.
2. Isolated semantic adjudication: bounded HTTPS retrieval and a constrained
   LLM result inside `gl.vm.run_nondet_unsafe`.
3. Deterministic consequences: result persistence, status transitions, root
   impact, and resumable edge-by-edge propagation.

## State ownership

The GenLayer Intelligent Contract state is canonical. The GenLayer consensus
result is canonical only once accepted under the protocol's lifecycle and
finality rules. A future frontend or indexer can materialize views of node,
edge, case, and queue state, but the contract remains authoritative for writes
and reads needed for correctness.

## Atomicity

Each registration, edge creation, case opening, semantic assessment, and queue
step is one deterministic contract transaction. A semantic assessment commits
state only after the nondeterministic block returns an accepted, schema-valid
result. A validator never writes contract storage, traverses the graph, or
computes downstream impact.

## Explicit non-goals

PALINODE does not fetch and archive complete documents on-chain, declare broad
real-world truth, replace legal review, settle escrow, or permit an operator to
rewrite history. It does not use EVM calls, ERC20 transfers, accepted-state
irreversible messages, or multiple Intelligent Contracts in Phase 1.

## Future recovery shape

An old evidence object is never edited into a replacement. A replacement is a
new immutable evidence object. `link_evidence_successor` records explicit
lineage and may move the old object to `SUPERSEDED`; its original URI, digest,
length, sequence, creator, and history remain inspectable.
