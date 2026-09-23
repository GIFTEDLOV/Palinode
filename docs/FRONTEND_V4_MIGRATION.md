# PALINODE frontend V4 migration

The frontend now reads and writes the frozen V4 deployment only:

| Field | V4 value |
|---|---|
| Contract | `0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b` |
| Source | `contracts/palinode_v2.py` |
| Source SHA-256 | `0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601` |
| Network | Studionet / `61999` |
| Public API | 46 methods: 21 writes, 25 views |

The former V1 address is historical documentation only. It is not used by the
frontend runtime, read smoke, graph, proof page, or wallet transaction path.

## Migration matrix

| Frontend concern | V1 assumption | V4 contract surface | Frontend action |
|---|---|---|---|
| Dependency authorization | Both endpoints had to be controlled | Child controller asserts incoming reliance; parent only needs to exist and satisfy graph preconditions | Explain child authorization and display `edge_assertor` |
| Blast radius | Generic downstream reachability was called impact | Active causes and relationship-specific propagation are canonical | Render affected nodes only from bounded cause pages; label other descendants `RELATED / DOWNSTREAM` |
| Pagination | Global reads silently stopped at 256 | Every registry has bounded cursor pages | Read until `next_cursor` exhaustion with a non-progress guard |
| Evidence identity | URI and current metadata could be conflated | SHA-256, exact byte length, subject, source, and historical authority binding are immutable | Show byte identity and bound authority version separately |
| Authority versions | Current controller appeared beside old evidence | Evidence is bound to an exact historical version; current state is separate | Read `get_source_authority_version` for evidence detail |
| Challenge standing | All review notices looked like revocations | Source-authoritative notices and third-party challenges have distinct legal effects | Display `MATERIAL_THIRD_PARTY_CHALLENGE` / `QUESTION` without implying publisher withdrawal |
| Active causes | Aggregate severity could look like an unnamed state | Individually keyed causes plus severity counters determine current reliance | Display case/cause slots, counters, and queue state |
| Successors | Linking could be mistaken for immediate supersession | Lineage provenance does not mutate reliance; completed recovery may produce `SUPERSEDED` | Keep successor link and recovery state separate |
| Finality | `READY_TO_FINALIZE` was treated as a status | `Finalize` is a resolution action; `ACCEPTED` remains provisional | Display exact lifecycle status and require final execution success |
| Wallet | Client could be created from an address alone | Browser writes require connected EIP-1193 provider | Pass `window.ethereum` into `createClient`, check accounts and chain before enabling writes |
| Cached wallet | LocalStorage address was treated as connected | Provider account/chain are authoritative | Show `LAST USED ACCOUNT` separately from current connection |
| Transactions | Newest 20 could evict unresolved IDs | All unresolved IDs must resume by original hash | Bound completed display history only |
| Canonical freshness | Session cache looked live | Cache is derived state | Label `LIVE`, `CACHED SNAPSHOT`, `REFRESHING`, or `RPC UNAVAILABLE` |
| Public RPC relay | Arbitrary JSON-RPC forwarding | Reads/status only, bounded JSON, timeout, strict CORS | Block generic write methods and malformed/batch/oversized bodies |

## Reviewer proof surfaces

The Proof & Security page records the frozen local gates (28 direct, 5
invariant, 34 adversarial, 2 property, 27 reviewer-remediation V2 tests; 96
total), the 49-mutation catalogue (46 killed,
3 retired, 0 survived), the live Authority C third-party standing proof, and
the BODY A/B same-URL `SOURCE_DIGEST_MISMATCH` proof. The UI does not claim that
the model detected a byte mismatch; deterministic contract identity checking
precedes semantic adjudication.

## Browser and write safety

Forms validate IDs, digests, URLs, enum values, and bounded step counts before
broadcast. The wallet path is provider-backed and chain-gated. A finalized
execution error is a failure, and transaction polling never resubmits an
unresolved hash automatically. The frontend remains a derived client; the
frozen Intelligent Contract remains canonical.
