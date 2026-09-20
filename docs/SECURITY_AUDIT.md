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

Selected security guards were mutation-tested. The final harness killed 16 of
16 targeted mutants; no surviving security mutant was accepted.
