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

## Registration and access

Registration is permissionless. Anyone may register an immutable node, typed
edge, successor assertion, or revocation notice. This is an explicit protocol
choice: the contract records claims and adjudicated impact without giving an
owner the ability to rewrite evidence, erase nodes, override consensus, or
change the transition policy at runtime.

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

## Finality boundary

An EVM submission receipt is not by itself PALINODE finality. Consumers must
wait for the GenLayer Intelligent Contract transaction to reach its applicable
final status before treating a semantic result or propagation mutation as
final. This repository does not deploy or call Studionet in Phase 1.
