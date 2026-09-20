# Evidence model

## Immutable identity

`register_evidence` stores:

- contract-generated evidence/node ID;
- creator address;
- monotonic creation sequence;
- transaction datetime from `gl.message_raw["datetime"]`;
- normalized HTTPS source URI;
- verified `authority_id` bound to the source origin;
- lowercase 64-character content SHA-256;
- non-zero exact byte length;
- bounded subject identifier;
- bounded human-readable title; and
- current reliance status, initialized to `ACTIVE`;
- separate assessment status, initialized to `UNASSESSED`.

Full source bodies are not stored on-chain.

The recorded source URI is the canonical source identity. A separate retrieval
mirror may be cross-origin, but it is accepted only after a bounded consensus
web check proves exact digest and byte-length equality. Mirrors never change
the canonical URI, authority, authority version, subject, digest, or assessment
state, and a mirror alone can never produce `CLEARED`.

## Identity and duplicate policy

The evidence identity tuple is:

```text
(authority_id, normalized_source_uri, content_sha256, byte_length, subject_id)
```

An exact duplicate tuple is rejected. The title is recorded metadata but is not
used to make an otherwise identical evidence object distinct. Different
content digests or sources create distinct immutable objects.

## Bounds

| Field | Phase 1 bound |
|---|---:|
| Source URI | 10–2048 characters, `https://` only |
| SHA-256 | exactly 64 lowercase hexadecimal characters |
| Declared byte length | 1–16,777,216 bytes |
| Subject identifier | 1–128 characters from a restricted identifier alphabet |
| Title | 1–160 characters, no control/newline characters |
| Semantic fetch body | at most 65,536 bytes per page |

The fetch bound protects the semantic prompt. A declared source may be larger
than the semantic fetch bound, but assessment then returns a retryable explicit
`SOURCE_TOO_LARGE` result rather than truncating silently.

## Historical validity and current reliance

`HISTORICAL_ACCEPTED` records that the object passed deterministic registration
guards when created. It is not a claim that the source is permanently true.
`node_status` and append-only status history represent present reliance.

## Assessment versus reliance

Registration is not a consensus assessment. `get_node_record` exposes both
dimensions directly:

| Dimension | Values | Meaning |
|---|---|---|
| `assessment_status` | `UNASSESSED`, `PENDING`, `CLEARED`, `REJECTED`, `INCONCLUSIVE`, `SOURCE_UNAVAILABLE` | Latest explicit semantic review state |
| `status` | `ACTIVE`, `QUESTIONED`, `UNDER_REVIEW`, `QUARANTINED`, `SUPERSEDED`, `INVALIDATED`, `REINSTATED`, `INCONCLUSIVE` | Current downstream reliance state |

New nodes are `UNASSESSED` and `ACTIVE`. Opening an adverse case moves the
assessment dimension to `PENDING`; it does not itself change reliance. A
conclusive immaterial review produces `CLEARED`. A material review produces
`REJECTED` and then applies its typed reliance root effect. Infrastructure
failure produces `SOURCE_UNAVAILABLE`, never a semantic success.

## Source-authority binding

Evidence cannot attach a caller-selected authority label to an arbitrary URL.
`register_source_authority` binds the registering address to a normalized
HTTPS origin and the fixed `WELL_KNOWN_ADDRESS_NONCE_V1` policy. Consensus
retrieves the derived `/.well-known/palinode.json` document and requires the
exact Palinode version, authority address, canonical origin, nonce, and policy.
Evidence registration then requires a verified authority ID and a source URI
whose normalized origin is exactly that authority origin. Authority IDs have
versioned controller/origin records with explicit `ACTIVE` or `REVOKED` state.

Rotation is a new version proved by the canonical origin's declaration; it does
not require trusting a compromised old controller and does not rewrite old
evidence. Revocation lowers trust for new evidence and assessments while
historical records remain inspectable. There is no owner override, erase, or
arbitrary authority reassignment.

## Safe recovery lineage

Replacement evidence is registered as a new immutable node and authenticated
independently. `link_evidence_successor(old, new)` preserves both identities.
The recovery case stores the successor ID and the exact material adverse case
ID; it cannot be retargeted during reassessment. Recovery is permissionless to
submit but not permissionless to force: only a strict consensus result can
resolve that named active cause.

## Mutable URLs

The URL is a locator, not immutable storage. The registered digest remains the
historical identity. During assessment, the current evidence body is retrieved
only inside the nondeterministic boundary; the notice body must match its
registered digest and exact byte length. Current evidence digest drift is
provided as context for adjudication rather than silently rewritten into state.

If the committed URL is unavailable, the assessment state becomes
`SOURCE_UNAVAILABLE` and any caller may invoke the retry path. A mirror is
usable only when its retrieved bytes match the locked SHA-256 and exact byte
length. A mirror may be cross-origin, but it is retrieval-only and never gains
source-authority semantics. The original URI, authority/version, digest, and
byte length are never rewritten.

## Replacement and succession

A replacement evidence record is created normally, with new identity, creator,
sequence, source, digest, and timestamp. `link_evidence_successor` stores one
successor per old evidence and one predecessor per new evidence. Neither object
is overwritten.
