# PALINODE v2 Reviewer Remediation

This document maps the independent audit findings to the v2 correction. The
archived contract at `0x9c9d1993cd938846D1163Bba9AA81AC6d165de88` is not
upgradeable and is not represented as corrected by this work.

| Audit finding | Root cause | Fix in v2 | Regression test | Status |
|---|---|---|---|---|
| F-01 | Unrestricted successor link changed reliance and consumed both lineage slots. | Current authority-controller authorization; cleared/same-subject/same-lineage checks; lineage no longer changes reliance. | `test_unauthorized_successor_is_rejected_and_link_does_not_change_reliance` | Implemented; gates pending |
| F-02 | Any caller could create an active edge between unrelated nodes. | Caller must control both endpoints; edge assertor is stored and queryable. | `test_dependency_requires_both_endpoint_controllers_and_records_assertor` | Implemented; gates pending |
| F-03 | Semantic review only put current evidence digest in the prompt. | Exact evidence length and SHA-256 are checked before `exec_prompt`; mismatch is retryable and no LLM call occurs. | `test_changed_evidence_bytes_short_circuit_semantic_execution` | Implemented; gates pending |
| F-04 | Case assessment did not require authenticated evidence. | `assess_revocation` requires `CLEARED`; non-cleared cases remain open. | `test_non_cleared_evidence_cannot_be_semantically_revoked` | Implemented; gates pending |
| F-05 | New edges did not inherit active causes. | Successful bounded late-edge registration copies active causes according to the relationship table. | `test_late_edge_inherits_active_cause_without_new_consensus` | Implemented; gates pending |
| F-06 | Any active authority could appear source-authoritative. | Cases distinguish authoritative lineage notices from third-party challenges; unrelated challenges cannot invalidate. | `test_unrelated_authority_is_challenge_only_and_cannot_invalidate` | Implemented; gates pending |
| F-07 | Overflow summary had no recoverable cause identity. | Active causes are individually keyed with constant-size severity counters and bounded page views; no 64-cause overflow path exists. | `test_active_causes_are_individually_recoverable_beyond_64` | Implemented; gates pending |
| F-08 | Raw page text was interpolated into structural prompt delimiters. | Evidence, notice, and recovery payloads are JSON-serialized untrusted strings. | `test_prompt_payload_is_json_serialized_and_semantic_scope_is_bounded` | Implemented; gates pending |
| F-09 | Recovery could run before adverse propagation completed. | Recovery opening and assessment require the originating case to be `COMPLETE` with an exhausted queue. | `test_recovery_is_blocked_until_adverse_propagation_is_complete` | Implemented; gates pending |
| F-10 | Registration/authentication allowed 16 MiB while semantics allowed 64 KiB. | Registration, authentication, mirror, semantic, notice, and recovery artifact limits align at 64 KiB. | `test_semantic_size_boundary_is_coherent` | Implemented; gates pending |
| F-17/F-18 | Subject field was named as if it proved real-world identity; permissionless metadata could squat an identity. | Authentication field is described as metadata validity; evidence registration requires source controller authorization. | authentication and controller tests | Implemented; gates pending |
| F-19/F-28 | Authority rotation stopped at eight versions; stale versions could not authenticate. | No lifetime version cap; benign rotation marks old versions `SUPERSEDED` and preserves historical authentication. | `test_benign_authority_rotation_preserves_historical_authentication` | Implemented; gates pending |
| F-20 | Any caller could fill four mirror slots. | Evidence mirrors require the evidence authority controller; notice mirrors require the relevant authority controller. | `test_mirror_registration_is_controller_authorized` | Implemented; gates pending |
| F-21/F-29/F-30 | Result/history and lineage provenance were too thin. | Recent bounded case/recovery result histories and lineage creator/sequence/version are stored and exposed. | v2 history/lineage views | Implemented; gates pending |
| F-22 | Prompt claimed downstream context that was not supplied. | Semantic question is explicitly evidence-level; deterministic typed propagation supplies graph context. | prompt-scope regression | Implemented; gates pending |

## Remaining non-contract release work

This v2 correction does not change the frontend, deployment, archived canary,
or production address. Those remain separate release work after direct,
invariant, adversarial, property, mutation, lint, typecheck, and schema gates
pass.
