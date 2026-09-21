# PALINODE v2 Authorization Model

The archived Studionet contract is not upgraded. This document describes the
authorization boundary of `contracts/palinode_v2.py`.

## Endpoint control

Evidence registration is controlled by the current controller declared by the
active source-authority version. The caller cannot register authority-owned
evidence with arbitrary title or subject metadata. Non-evidence nodes remain
permissionless records, but their creator is their controller.

## Dependency edges

`register_dependency(parent, child, relationship)` requires the caller to
control both endpoints. This is intentionally a one-phase, same-controller
assertion rule: an unrelated caller cannot attach its evidence to another
party's claim, consume endpoint capacity, or create a future propagation path.

Each edge stores its `assertor` and exposes it through
`get_dependency_record`. Edges are immutable and active after acceptance; v2
does not expose an arbitrary edge-rewrite or edge-deactivation authority.

## Successor lineage

`link_evidence_successor` requires the current source-authority controller of
the predecessor, a later evidence node, matching subject metadata, the same
stable authority lineage, and independently `CLEARED` successor evidence.
Lineage registration stores creator, sequence, and authority-version
provenance. It never changes reliance status. Only a successful cause-bound
recovery result can transition a predecessor to `SUPERSEDED`.

## Permissionless operations

The following remain permissionless because their effect is bounded by
deterministic identity and consensus rules:

- opening a revocation case;
- assessing a case or recovery case;
- processing an already-created impact queue;
- retrying a case with already verified mirror IDs.

Permissionless review does not grant authority to rewrite evidence,
dependencies, lineage, or consensus results.

## Authority lifecycle

Authority rotation is proven by the authority origin's versioned declaration.
Normal rotation marks the old version `SUPERSEDED`, not `REVOKED`, so evidence
registered under that historical version remains re-authenticatable while the
authority itself remains active. Explicit authority revocation produces
`REVOKED` trust and blocks further authentication.

## Notice standing

Cases whose notice authority is the target evidence's stable authority lineage
are `AUTHORITATIVE_REVOCATION`. Other active authorities may submit
`THIRD_PARTY_CHALLENGE` cases, but deterministic post-validation prohibits a
third-party challenge from producing `INVALIDATE`. It may only question the
record under the typed propagation policy.
