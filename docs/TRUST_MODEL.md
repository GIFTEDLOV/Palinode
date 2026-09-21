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

Generic non-evidence node registration and case submission are permissionless,
but authority-bearing writes are not. Evidence registration requires the
active source-authority controller; dependency registration requires control of
the child endpoint while validating the parent deterministically; and successor
lineage requires the predecessor authority controller plus a cleared
same-lineage successor. This lets independent consumers cite public evidence
without letting arbitrary callers write another party's child graph or consume
bounded capacity.
The contract still records immutable claims and adjudicated impact without
giving an owner the ability to rewrite evidence, erase nodes, override
consensus, or change the transition policy at runtime.

Adverse review is also permissionless. A case submitter does not need to be
the evidence creator, and the evidence creator cannot suppress, erase, cancel,
or rewrite a valid case. Exact duplicates are rejected while distinct notices
remain separate canonical cases.

Authority-backed evidence and notices require a verified authority ID. An
authoritative notice is restricted to the target evidence's authority lineage;
an unrelated verified authority is recorded as a third-party challenge and may
produce only a consensus-supported `MATERIAL`/`QUESTION` challenge, never an
authoritative invalidation. The authority is bound to the
registering address and normalized HTTPS origin by a
consensus-checked `/.well-known/palinode.json` challenge. A caller cannot label
an arbitrary origin as authoritative, select the validators, or choose the
semantic decision-makers for its own case. Authority IDs have versioned
controllers and explicit `ACTIVE`/`REVOKED` lifecycle.

There is no owner, administrator, pause authority, arbitrary status setter, or
verdict override. There are no global lifetime registry caps that an actor can
fill to brick unrelated future registrations. Per-operation bounds are fixed
protocol rules, and ID enumeration is paginated.

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

Registration and authentication are separate: a new node is `UNASSESSED`, not
consensus-cleared. `get_node_record` exposes `authentication_status` (with the
legacy `assessment_status` alias) and `reliance_status` simultaneously.
`SOURCE_UNAVAILABLE` is an explicit authentication liveness state, not a
semantic rejection or clearance. Revocation review is case-scoped and cannot
rewrite authentication. Any caller may retry through digest-verified
cross-origin retrieval mirrors without changing the locked evidence identity.
Semantic adjudication is evidence-level only; relationship-specific downstream
effects are deterministic and do not get invented by the model.
Mirrors are not authority records and cannot clear an object by themselves.

Recovery is not a trust shortcut. A caller may open a recovery case only after
the successor is linked and independently `CLEARED`, but only the bounded
consensus result can resolve the named adverse cause. No owner-only reinstate
method exists; active causes from other cases are not removed.

## Finality boundary

An EVM submission receipt is not by itself PALINODE finality. Consumers must
wait for the GenLayer Intelligent Contract transaction to reach its applicable
final status before treating a semantic result or propagation mutation as
final. `ACCEPTED` is tracked separately from execution success and finalization.
The application layer must persist the transaction ID and resume polling it
after timeouts rather than resubmitting automatically. The archived Phase 2.5
canary is recorded under `evidence/studionet/canary-v1/`; it is not the final
deployment and is not upgraded in place. The corrected Phase 2.6 canary-v2
deployment finalized, but its single semantic attempt was safely
`UNDETERMINED` because of an unlisted provider reason enum; it is not frozen as
the final protocol deployment.

The final canary-v3 deployment is the frozen candidate, not an in-place
upgrade of either archived address. Its single live semantic assessment
finalized as a canonical `CONCLUSIVE`/`MATERIAL`/`INVALIDATE` result, and the
controlled recovery finalized after the matching cause was resolved. The V3
deployment, lifecycle, and restart-tracking evidence are under
`evidence/studionet/canary-v3/`; the freeze record is
`docs/CONTRACT_FREEZE.md`.
