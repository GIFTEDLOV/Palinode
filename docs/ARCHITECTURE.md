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
   strict input bounds, node sequencing, typed edges, duplicate policy, and
   versioned source-authority lifecycle.
2. Isolated semantic adjudication: bounded HTTPS retrieval and a constrained
   LLM result inside `gl.vm.run_nondet_unsafe`; pure evidence authentication
   uses deterministic digest/length comparison without an LLM.
3. Deterministic consequences: result persistence, separate assessment and
   reliance transitions, root impact, and resumable edge-by-edge propagation.
4. Cause-aware recovery: an immutable recovery case can resolve only the
   adverse cause named in its identity, then process the same typed graph in a
   bounded resumable queue.

Source-authority registration and rotation are bounded consensus boundaries: the
registering address and normalized HTTPS origin are committed only after the
derived `/.well-known/palinode.json` challenge binds address, origin, nonce,
   and policy. Evidence and notices reference verified, active authorities;
   callers do not choose validators.

## State ownership

The GenLayer Intelligent Contract state is canonical. The GenLayer consensus
result is canonical only once accepted under the protocol's lifecycle and
finality rules. A future frontend or indexer can materialize views of node,
edge, case, and queue state, but the contract remains authoritative for writes
and reads needed for correctness.

Application transaction tracking is non-canonical and documented separately in
`docs/TRANSACTION_MODEL.md`. It preserves transaction IDs and distinguishes
submission, consensus acceptance, execution success, and finalization.

## Atomicity

Each registration, edge creation, case opening, semantic assessment, and queue
step is one deterministic contract transaction. A semantic assessment commits
state only after the nondeterministic block returns an accepted, schema-valid
result. A validator never writes contract storage, traverses the graph, or
computes downstream impact.

There are no protocol-wide lifetime caps on node, edge, authority, revocation,
or recovery registries. Their ID arrays are append-only history and are not
returned wholesale: bounded page views keep each read bounded. Execution
bounds remain local to fan-in/fan-out, queues, pages, mirrors, strings,
retrieval bodies, retry telemetry, and semantic attempts.

## Explicit non-goals

PALINODE does not fetch and archive complete documents on-chain, declare broad
real-world truth, replace legal review, settle escrow, or permit an operator to
rewrite history. It does not use EVM calls, ERC20 transfers, accepted-state
irreversible messages, or multiple Intelligent Contracts in Phase 1.

## Recovery shape

An old evidence object is never edited into a replacement. A replacement is a
new immutable evidence object. `link_evidence_successor` records explicit
lineage and may move the old object to `SUPERSEDED`; its original URI, digest,
length, sequence, creator, and history remain inspectable. A recovery case
then binds one material adverse case to that successor. Consensus decides only
whether the specific defect is resolved; deterministic code resolves that
case's cause and bounded downstream causes. Other active causes remain
effective.
