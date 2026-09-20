# Threat model

## Prompt injection

Evidence and notice bodies may contain instructions such as “ignore prior
rules.” They are inserted into marked data sections and the prompt states that
they are untrusted data. The output parser accepts only fixed keys and enums;
embedded text cannot create a status or mutate storage.

## Malicious or stale evidence

A caller may register a malicious document or a mutable URL. Registration
records provenance metadata and a digest but does not assert broad truth.
Current evidence drift is visible to semantic adjudication. Notice retrieval
must match its registered digest and length. Source outage or stale content does
not silently create a result.

## Replay and duplicate cases

Node IDs are generated from contract state and immutable sequence; caller IDs
are not trusted. Exact evidence identity and exact target/notice-digest case
identity are rejected. A case has a retry cap. Completed propagation returns
zero and cannot repeat state changes.

## Graph-cycle attempts

Every edge requires existing distinct nodes and
`seq(parent) < seq(child)`. Since sequences never change and edges are never
rewritten, a cycle cannot be introduced through supported writes.

## Graph fan-out and denial of service

Per-node incoming/outgoing limits, global node/edge limits, per-node transition
limits, fetch-size limits, assessment retry limits, and a 32-edge propagation
limit constrain resource use. The queue is resumable, so no transaction must
traverse a full graph.

## Unbounded propagation

No recursive graph walk exists. Each queue transaction consumes a caller-bounded
number of edges below the hard maximum and advances a monotonic cursor.

## Malformed semantic output

JSON is required and parsed strictly. Extra or missing keys, invalid booleans,
unsupported enum values, inconsistent materiality/root combinations, and
unsupported reason codes return `LLM_MALFORMED` retryable inconclusive state.

## Validator disagreement

The validator independently retrieves and evaluates the same bounded inputs.
Any disagreement returns `False` and prevents post-consensus mutation. The
contract does not accept the leader merely because it is the leader.

## External source outage

Non-2xx responses, timeouts, missing mocks, oversized bodies, invalid UTF-8,
and submitted-notice digest/length mismatches are explicit infrastructure
reasons. They cannot become `MATERIAL` or `IMMATERIAL`.

## Fake replacement evidence

Replacement is a new immutable node and an explicit succession assertion. The
old evidence record is not edited to look as if the replacement existed earlier.
Lineage assertions are visible and cannot be duplicated.

## Unauthorized mutation

There is no owner or arbitrary status/verdict setter. Public methods create
records, edges, cases, successor links, semantic assessments, and bounded queue
steps only. Statuses can change only through the internal transition table and
deterministic case/lineage paths.

## Frontend or indexer corruption

Frontend-generated IDs are ignored for new objects. Indexer state is derived
and non-canonical; callers can read the contract directly and submit writes
without it. No indexer output is accepted as a semantic result.

## Transaction-finality confusion

An EVM receipt or accepted proposal is not necessarily final Intelligent
Contract state. Integrators must follow the GenLayer transaction lifecycle and
appeal window. Phase 1 has no consequential cross-contract message path.

## Residual risks

This model does not make a public page immutable, make LLMs truthful, or
guarantee that a committee is honest. It bounds and exposes those risks and
requires explicit consensus on a narrow question before deterministic impact.
