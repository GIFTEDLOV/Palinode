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

## Source-authority spoofing

Caller-selected labels and URLs are not authority proof. A source authority is
committed only after the registering address and canonical HTTPS origin are
bound by an independently retrieved, consensus-checked
`/.well-known/palinode.json` document containing the challenge nonce and fixed
verification policy. Evidence and notices must reference that verified
authority, and normalized URIs must remain under its origin. Wrong-origin URLs,
unregistered authority IDs, wrong nonces, and wrong address bindings fail.

The registry has no owner override or authority rewrite path. Authority
rotation creates a new version only after a current canonical-origin
declaration proves the new controller; the old controller cannot impersonate
the new version. Explicit revocation lowers current trust without rewriting
historical evidence.

## Replay and duplicate cases

Node IDs are generated from contract state and immutable sequence; caller IDs
are not trusted. Exact evidence identity and the complete target/authority/URI/
digest/length challenge identity are rejected. Different notices remain
independent, ordered by opening sequence, and cannot suppress one another. A
semantic attempt budget bounds conclusive adjudication, while retryable source
outages do not consume it. Completed propagation returns zero and cannot repeat
state changes.

## Permissionless adverse review

Opening a valid challenge does not require the evidence creator or subject to
approve it. Owners/admins cannot erase, suppress, cancel, rewrite, or override
cases, assessment results, reliance transitions, or consensus outcomes. The
only access controls are deterministic validity, authority binding, duplicate,
capacity, and bounded retry rules.

## Graph-cycle attempts

Every edge requires existing distinct nodes and
`seq(parent) < seq(child)`. Since sequences never change and edges are never
rewritten, a cycle cannot be introduced through supported writes.

## Graph fan-out and denial of service

Per-node incoming/outgoing limits, bounded recent history, fixed mirror counts,
bounded retry telemetry, fetch-size limits, assessment attempt limits, bounded
page views, and a 32-edge propagation limit constrain per-transaction resource
use. There are no global lifetime node/edge/case/authority caps that can brick
future independent writes. The queue is resumable, so no transaction must
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

Committed evidence outage becomes the explicit node assessment state
`SOURCE_UNAVAILABLE`, distinct from semantic `INCONCLUSIVE`. Any caller may
retry. A cross-origin retrieval mirror must pass independent consensus
retrieval and exact byte-length/SHA-256 verification before it becomes a
retrieval location; it never gains source-authority semantics. The original
identity is never changed. A failed mirror leaves the locked case untouched,
so outage cannot create either a false verdict or a permanent identity
deadlock.

## Fake replacement evidence

Replacement is a new immutable node and an explicit succession assertion. The
old evidence record is not edited to look as if the replacement existed earlier.
Lineage assertions are visible and cannot be duplicated.

## Unauthorized mutation

There is no owner or arbitrary status/verdict setter. Public methods create
records, edges, cases, successor links, semantic assessments, and bounded queue
steps only. Statuses can change only through the internal transition table and
deterministic case/lineage paths.

Registration starts `UNASSESSED`, not consensus-cleared. Assessment and
current reliance are separate state machines with explicit legal transitions;
views expose both so a UI cannot infer one from the other.

## Frontend or indexer corruption

Frontend-generated IDs are ignored for new objects. Indexer state is derived
and non-canonical; callers can read the contract directly and submit writes
without it. No indexer output is accepted as a semantic result.

## Transaction-finality confusion

An EVM receipt or accepted proposal is not necessarily final Intelligent
Contract state. Integrators must follow the GenLayer transaction lifecycle and
appeal window. Phase 1 has no consequential cross-contract message path.

## Recovery and cross-case composition

Recovery identities bind the affected node, successor evidence, and one
material adverse case. A successor must be linked and independently cleared;
the result is restricted to `REINSTATE`, `SUPERSEDE`, `NO_CHANGE`, or
inconclusive. Each material case owns a separate bounded active-cause slot.
Resolving one cause cannot erase another, and ordinary later cases cannot
downgrade a stronger reliance status. Recovery queues use their own case key,
cursor, and bounded step limit, preventing cross-case queue interference.

Submission, provisional acceptance, execution result, finalization, and
timeout are separate application states. A timeout does not authorize
automatic resubmission; the persisted transaction ID is polled again.
`ACCEPTED` alone is not final application success.

The application model must persist the submitted GenLayer transaction ID and
track submission, accepted consensus, execution success, and finalization as
separate states. A timeout resumes polling the same transaction ID rather than
automatically submitting a duplicate.

## Residual risks

This model does not make a public page immutable, make LLMs truthful, or
guarantee that a committee is honest. It bounds and exposes those risks and
requires explicit consensus on a narrow question before deterministic impact.
