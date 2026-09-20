# Trust model

## Canonical components

| Component | Trust role | Canonical? |
|---|---|---|
| GenLayer chain consensus and finality | Orders Intelligent Contract transactions and resolves accepted consensus outcomes | Yes for protocol lifecycle |
| `contracts/palinode.py` state | Stores node, edge, case, status, lineage, and queue state | Yes for PALINODE application state |
| Accepted semantic result | Bounded leader result accepted by validator equivalence logic | Yes after protocol acceptance/finality |
| Validator committee | Independently checks the leader's bounded proposal | Consensus participant, not an app authority |
| Web evidence and correction URLs | Untrusted input to the semantic boundary | No |
| LLM outputs | Untrusted candidate input constrained by schema and validator comparison | No by themselves |
| Frontend | User interface and transaction builder | No |
| Indexer/database | Derived query acceleration and presentation | No |
| Case submitter | Proposes a case and metadata | No |
| Source authority challenge document | Proves control of a canonical HTTPS origin for one immutable authority record | No; independently retrieved consensus input |

## Registration and access

Registration is permissionless. Anyone may register an immutable node, typed
edge, successor assertion, or revocation notice. This is an explicit protocol
choice: the contract records claims and adjudicated impact without giving an
owner the ability to rewrite evidence, erase nodes, override consensus, or
change the transition policy at runtime.

Adverse review is also permissionless. A case submitter does not need to be
the evidence creator, and the evidence creator cannot suppress, erase, cancel,
or rewrite a valid case. Exact duplicates are rejected while distinct notices
remain separate canonical cases.

Authority-backed evidence and notices require a verified authority ID. The
authority is bound to the registering address and normalized HTTPS origin by a
consensus-checked `/.well-known/palinode.json` challenge. A caller cannot label
an arbitrary origin as authoritative, select the validators, or choose the
semantic decision-makers for its own case. Authority IDs have versioned
controllers and explicit `ACTIVE`/`REVOKED` lifecycle.

There is no owner, administrator, pause authority, arbitrary status setter, or
verdict override in Phase 1. Capacity constants and enums are code-level
protocol configuration and can change only through a future code-governance
decision, not through a public method.

## What the model does not trust

The contract does not trust a caller-generated ID, mutable URL, current page
contents, raw LLM prose, frontend cache, indexer output, or a single leader.
It verifies digests and lengths where the submitted notice is retrieved and
fails closed on retrieval or parsing problems.

## Historical validity versus current reliance

`HISTORICAL_ACCEPTED` is immutable registration history metadata. It does not
mean that the evidence is permanently true. Current reliance is represented by
the separate node status state machine and status history. Thus an object can
remain historically accepted while currently `QUESTIONED`, `QUARANTINED`,
`SUPERSEDED`, or `INVALIDATED`.

Registration and assessment are separate: a new node is `UNASSESSED`, not
consensus-cleared. `get_node_record` exposes `assessment_status` and `status`
simultaneously. `SOURCE_UNAVAILABLE` is an explicit liveness state, not a
semantic rejection or clearance. Any caller may retry through digest-verified
cross-origin retrieval mirrors without changing the locked evidence identity.
Mirrors are not authority records and cannot clear an object by themselves.

## Finality boundary

An EVM submission receipt is not by itself PALINODE finality. Consumers must
wait for the GenLayer Intelligent Contract transaction to reach its applicable
final status before treating a semantic result or propagation mutation as
final. `ACCEPTED` is tracked separately from execution success and finalization.
The application layer must persist the transaction ID and resume polling it
after timeouts rather than resubmitting automatically. This repository has not
deployed or called Studionet in Phase 2: the canary is gated until local
integration and a controlled live authority fixture are available.
