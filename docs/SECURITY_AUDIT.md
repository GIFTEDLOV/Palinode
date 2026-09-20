# Phase 2 security audit

This is an implementation audit record, not a claim that PALINODE is secure
against every deployment or governance risk.

| Finding | Severity | Exploitable before fix? | Fix | Proof |
|---|---|---|---|---|
| Registration had no first-class path to a defensible `CLEARED` assessment | High | Yes: clearance could be inferred or left undefined | Added deterministic `authenticate_evidence`; exact canonical fetch, SHA-256, byte length, HTTPS/origin/authority checks | `tests/direct/test_steward_hardening.py` authentication tests |
| Authority records had no lifecycle/version rotation | High | Yes: stale controller/origin trust could persist | Added versioned `ACTIVE`/`REVOKED` records, domain-declaration rotation, explicit revocation | authority rotation/revocation tests |
| One canonical origin could be registered under multiple stable authority IDs | High | Yes: origin-level policy could be split across competing records | Added one-origin-to-one-authority binding and duplicate-origin rejection | `test_authority_origin_cannot_be_registered_as_two_independent_authorities` |
| Revoked authorities could be reactivated through rotation | High | Yes: revocation would not lower trust monotonically | Rotation now requires the stable authority to be active | `test_revoked_authority_cannot_reactivate_through_rotation` |
| Mirrors were coupled to authority origin and were not a separate retrieval class | High | Availability failures could deadlock assessment; origin policy was overbroad | Added permissionless cross-origin mirror registration with independent exact digest/length verification; mirror cannot clear or rebind | adversarial mirror tests |
| History had a lifetime transition cap | High | Repeated legitimate reviews could brick a node | Replaced cap with monotonic total count plus fixed 16-slot recent ring | status/assessment stress tests |
| Retry telemetry could grow with repeated outages | Medium | Repeated permissionless retries could create storage growth | Added monotonic retry counter and fixed 8-entry ring; retry failures do not consume semantic attempts | retry storage stress test |
| Weaker later cases could overwrite stronger reliance impact | Critical | Last-writer-wins could restore safety after invalidation | Added monotonic severity lattice and explicit no-effect relationship policy; recovery remains separate | cross-case adversarial tests and mutation guard |
| A converging path within one case could let a first weak path suppress a later strong path | High | Yes: queue insertion order could under-propagate impact | Seen nodes remain idempotent, but later paths still apply stronger typed effects | `test_one_case_converging_paths_keep_the_stronger_effect` |
| Propagation semantics could fall through to an accidental default | High | `CONTRADICTS` or `CORROBORATES` could be over-propagated | Explicit table for all seven relationships under QUESTION and INVALIDATE; unsupported relationship raises | relation matrix tests |
| Tool resolver could select a cached release candidate | High | Lint/schema results could target the wrong runtime | Pin stable `GENVM_VERSION=v0.2.16` and record exact toolchain | `docs/TOOLCHAIN.md`, lint/type/schema runs |
| Local GLSim deploy is blocked by an installed Windows runner/temp-file failure | External | Network evidence would be falsely claimed from direct mode | Integration test starts GLSim and records a precise skip; no Studionet broadcast | `tests/integration/test_glsim_network.py` |

Selected security guards were mutation-tested. The Phase 2 baseline killed
16/16 mutants. Phase 2.5 added 11 recovery/capacity guards; the final harness
killed 27/27 targeted mutants with no survivors.

## Phase 2.5 release-blocker audit

| Finding | Severity | Exploitable before fix? | Fix | Proof |
|---|---|---|---|---|
| Protocol-wide node/edge/case/authority lifetime caps could brick future writes | Critical | Yes | Removed global caps; retained local fan-out, queue, body, mirror, history, telemetry, and page bounds | 4,097-node N+1 test and paginated view tests |
| Full lifetime ID getters could require unbounded execution/return data | High | Yes | Replaced them with maximum-64 page views including bounded cursor/next-cursor metadata | `test_lifetime_caps_are_absent_and_pagination_is_bounded` |
| Recovery was only lineage/status scaffolding, not a consensus-backed lifecycle | Critical | Yes | Added immutable recovery cases, strict leader/validator result, deterministic recovery queue, and explicit retry state | `tests/adversarial/test_capacity_and_recovery.py` recovery suite |
| Recovery of one cause could restore a node despite another active adverse cause | Critical | Yes | Added per-node bounded active-cause slots and cause-specific recovery resolution | `test_two_active_causes_require_two_successful_recoveries` |
| Recovery could be attempted without an independently cleared linked successor | High | Yes | Deterministic preconditions require `CLEARED` successor, same subject, and explicit successor lineage | successor precondition tests and recovery mutants |
| Recovery outage/malformed semantic result could become a successful resolution | High | Yes | Retryable result and `INCONCLUSIVE` recovery state with bounded retry ring; no cause mutation | `test_recovery_failure_inconclusive_and_source_unavailable_are_retryable` |
| Recovery retry telemetry could grow without bound | Medium | Yes | Eight-entry ring plus monotonic counter; retry does not consume conclusive attempt budget | `test_recovery_history_and_retry_storage_remain_bounded` |
| Local GLSim failure could be misreported as hosted network proof | High | No protocol exploit; evidence-quality risk | One clean isolated reproduction; record `KNOWN_LOCAL_BLOCKER`; continue only with hosted Studionet gate | `tests/integration/test_glsim_network.py`, isolated venv run |
| Controlled authority fixture was absent for live proof | High | Would force unsafe test weakening | Deployed fictional static fixture and verified exact public bytes; well-known declaration binds the resolved public address | fixture manifest and remote byte parity checks |
| A 64-slot active-cause set could reject a later stronger finding and suppress its impact | Critical | Yes: a 65th material/invalidating case could revert before recording or escalating its cause | Added a bounded monotonic overflow summary with count, strongest severity, latest strongest case, and rolling commitment; named recovery cannot clear the summary | `test_65th_stronger_cause_is_retained_as_monotonic_overflow_safety_lock` and three active-cause mutation guards |

The later controlled Studionet canary used the exact fixture and source hash
recorded in `evidence/studionet/`. The single deployment finalized successfully
and all deterministic setup writes finalized with `FINISHED_WITH_RETURN`.
The real revocation assessment finalized with `RETRYABLE` / `INCONCLUSIVE` and
reason `LLM_MALFORMED`; deterministic logic left reliance unchanged, and the
permissionless retry path finalized without substituting a new notice. No
recovery case was opened because recovery requires a conclusive material active
cause. The result is deliberately recorded as a live limitation, not hidden as
a successful semantic verdict.

## Phase 2.6 closure findings

| Finding | Severity | Exploitable before fix? | Fix | Proof |
|---|---|---|---|---|
| Revocation opening, retry, and semantic commit reused the evidence authentication state | Critical | Yes: a later review could make genuinely authenticated bytes appear unauthenticated or falsely cleared | Removed every review-path authentication transition; added explicit `authentication_status`/`reliance_status` view fields and kept review state on the case | direct authentication/revocation separation tests and the three review-path mutation guards |
| Live semantic output was normalized into accepted `RETRYABLE/LLM_MALFORMED` state before validator rejection | Critical | Yes: a malformed provider response could become consensus state instead of causing rotation/rejection | Shared exact seven-field validator; valid decoded JSON is accepted, malformed candidates are returned for validator rejection, and only explicit infrastructure failures create validated retryable results | live seven-field regression, malformed leader rejection, validator disagreement, and malformed-output mutations |
| Archived canary evidence could be mistaken for the corrected deployment | High | Evidence-quality risk | Archive canary-v1 separately and require canary-v2 artifacts/address for the corrected source | `evidence/studionet/canary-v1/` plus Phase 2.6 deployment gate |
| The first corrected-canary leader used an unlisted `MATERIAL_REVOCATION` reason code | High | No fail-open impact; the strict validator caused a safe `UNDETERMINED` result and left the case open | Add the observed token as an explicit enum and enumerate all allowed reason codes in the semantic prompt; do not add fuzzy parsing | `evidence/studionet/canary-v2/semantic-failure.json`, `docs/LIVE_SEMANTIC_FAILURE_ANALYSIS.md`, and the live transaction trace |

The archived malformed transaction was traceable to the contract's strict
normalizer fallback. The corrected canary then exposed a second, distinct
schema-enum mismatch: the provider returned a parsed seven-field result with
the unlisted token `MATERIAL_REVOCATION`, so validators rejected it and the
transaction became `UNDETERMINED`. The complete analysis and evidence
limitation are recorded in `docs/LIVE_SEMANTIC_FAILURE_ANALYSIS.md`. No
semantic retry or second deployment was submitted in this run.
