# Evidence model

## Immutable identity

`register_evidence` stores:

- contract-generated evidence/node ID;
- creator address;
- monotonic creation sequence;
- transaction datetime from `gl.message_raw["datetime"]`;
- HTTPS-only source URI;
- lowercase 64-character content SHA-256;
- non-zero exact byte length;
- bounded subject identifier;
- bounded human-readable title; and
- current node status, initialized to `ACTIVE`.

Full source bodies are not stored on-chain.

## Identity and duplicate policy

The evidence identity tuple is:

```text
(source_uri, content_sha256, byte_length, subject_id)
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

## Mutable URLs

The URL is a locator, not immutable storage. The registered digest remains the
historical identity. During assessment, the current evidence body is retrieved
only inside the nondeterministic boundary; the notice body must match its
registered digest and exact byte length. Current evidence digest drift is
provided as context for adjudication rather than silently rewritten into state.

## Replacement and succession

A replacement evidence record is created normally, with new identity, creator,
sequence, source, digest, and timestamp. `link_evidence_successor` stores one
successor per old evidence and one predecessor per new evidence. Neither object
is overwritten.
