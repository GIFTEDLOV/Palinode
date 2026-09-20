"""Bounded security-guard mutation harness for PALINODE.

Each mutant changes one named guard in a temporary contract copy and runs the
smallest test that should kill it.  The repository contract is never modified.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "palinode.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    needle: str
    replacement: str
    test: str


MUTATIONS = (
    Mutation(
        "authority_active_check",
        "self.authority_status[authority_id] == AUTHORITY_ACTIVE",
        "True",
        "tests/adversarial/test_security_closure.py::test_authority_substitution_origin_confusion_and_private_targets_fail",
    ),
    Mutation(
        "origin_binding_check",
        "_uri_belongs_to_origin(normalised_uri, self.authority_origin[authority_id])",
        "True",
        "tests/adversarial/test_security_closure.py::test_authority_substitution_origin_confusion_and_private_targets_fail",
    ),
    Mutation(
        "mirror_digest_check",
        "len(body) != int(expected_byte_length) or hashlib.sha256(body).hexdigest() != expected_digest",
        "len(body) != int(expected_byte_length)",
        "tests/adversarial/test_security_closure.py::test_mirror_identity_digest_length_and_missing_target_guards",
    ),
    Mutation(
        "mirror_byte_length_check",
        "len(body) != int(expected_byte_length) or hashlib.sha256(body).hexdigest() != expected_digest",
        "hashlib.sha256(body).hexdigest() != expected_digest",
        "tests/adversarial/test_security_closure.py::test_mirror_identity_digest_length_and_missing_target_guards",
    ),
    Mutation(
        "creation_order_check",
        "self.node_sequence[parent_node_id] < self.node_sequence[child_node_id]",
        "True",
        "tests/adversarial/test_security_closure.py::test_duplicate_edges_and_forward_order_are_rejected",
    ),
    Mutation(
        "duplicate_edge_check",
        "identity not in self.edge_identity_to_id",
        "True",
        "tests/adversarial/test_security_closure.py::test_duplicate_edges_and_forward_order_are_rejected",
    ),
    Mutation(
        "duplicate_case_check",
        "identity not in self.case_identity_to_id",
        "True",
        "tests/direct/test_revocation_and_propagation.py::test_open_case_requires_evidence_and_rejects_exact_duplicates",
    ),
    Mutation(
        "case_id_binding_check",
        "self._require_case_id(case_id)\n        self._require(self.case_status[case_id] == CASE_INCONCLUSIVE",
        "self._require(self.case_status[case_id] == CASE_INCONCLUSIVE",
        "tests/adversarial/test_security_closure.py::test_forged_mirror_id_cannot_substitute_retrieval_location",
    ),
    Mutation(
        "materiality_guard",
        'self._require(materiality == VERDICT_MATERIAL, "unsupported materiality")',
        'self._require(True, "unsupported materiality")',
        "tests/adversarial/test_security_closure.py::test_immaterial_case_cannot_change_root_effect_even_if_internal_commit_is_malformed",
    ),
    Mutation(
        "immaterial_no_effect_guard",
        'self._require(root_effect == ROOT_NO_CHANGE, "immaterial result cannot change state")',
        'self._require(True, "immaterial result cannot change state")',
        "tests/adversarial/test_security_closure.py::test_immaterial_case_cannot_change_root_effect_even_if_internal_commit_is_malformed",
    ),
    Mutation(
        "inconclusive_fail_closed_guard",
        "if result_status == RESULT_RETRYABLE or materiality == VERDICT_INCONCLUSIVE:",
        "if False:",
        "tests/direct/test_revocation_and_propagation.py::test_immaterial_never_propagates_and_inconclusive_is_retryable",
    ),
    Mutation(
        "max_steps_enforcement",
        "max_steps <= u256(MAX_IMPACT_STEPS_PER_CALL)",
        "True",
        "tests/direct/test_revocation_and_propagation.py::test_question_root_and_typed_propagation_are_bounded_and_resumable",
    ),
    Mutation(
        "cross_case_queue_isolation",
        "key = case_id + \"|\" + edge_id",
        "key = edge_id",
        "tests/adversarial/test_security_closure.py::test_overlapping_case_queues_are_isolated_when_both_touch_same_descendant",
    ),
    Mutation(
        "status_downgrade_prevention",
        "if self._ordinary_severity(target_status) <= self._ordinary_severity(current):",
        "if False:",
        "tests/adversarial/test_security_closure.py::test_overlapping_case_queues_are_isolated_when_both_touch_same_descendant",
    ),
    Mutation(
        "mirror_identity_binding",
        'self._require(mirror_id in self.evidence_mirror_identity, "evidence mirror is not verified")',
        'self._require(True, "evidence mirror is not verified")',
        "tests/adversarial/test_security_closure.py::test_forged_mirror_id_cannot_substitute_retrieval_location",
    ),
    Mutation(
        "initial_authentication_digest_guard",
        "if not digest_matches:",
        "if False:",
        "tests/direct/test_steward_hardening.py::test_authenticate_evidence_is_the_only_cleared_path_and_checks_exact_identity",
    ),
    Mutation(
        "recovery_successor_clearance",
        "self.node_assessment_status[successor_evidence_id] == ASSESS_CLEARED",
        "True",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_rejects_wrong_or_uncleared_successors_and_preserves_identity",
    ),
    Mutation(
        "recovery_lineage_binding",
        "affected_node_id in self.evidence_successor\n            and self.evidence_successor[affected_node_id] == successor_evidence_id",
        "True",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_rejects_wrong_or_uncleared_successors_and_preserves_identity",
    ),
    Mutation(
        "recovery_material_cause_guard",
        "self.case_materiality[adverse_case_id] == VERDICT_MATERIAL",
        "True",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_requires_material_cause_and_rejects_unsupported_effect",
    ),
    Mutation(
        "recovery_case_identity_guard",
        "identity not in self.recovery_identity_to_id",
        "True",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_requires_cleared_linked_successor_and_is_permissionless",
    ),
    Mutation(
        "recovery_effect_guard",
        'recovery_effect in (RECOVERY_EFFECT_REINSTATE, RECOVERY_EFFECT_SUPERSEDE),\n            "unsupported recovery effect",',
        'True,\n            "unsupported recovery effect",',
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_requires_material_cause_and_rejects_unsupported_effect",
    ),
    Mutation(
        "recovery_no_change_guard",
        "if recovery_effect == RECOVERY_EFFECT_NO_CHANGE:",
        "if False:",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_is_consensus_backed_and_owner_cannot_self_reinstate",
    ),
    Mutation(
        "recovery_cause_registration",
        "self._register_active_cause(node_id, case_id, target_status)",
        'self._require(False, "mutant recovery cause")',
        "tests/adversarial/test_capacity_and_recovery.py::test_two_active_causes_require_two_successful_recoveries",
    ),
    Mutation(
        "recovery_cause_key_binding",
        "cause_key = node_id + \"|\" + adverse_case_id",
        "cause_key = node_id",
        "tests/adversarial/test_capacity_and_recovery.py::test_single_cause_recovery_restores_root_and_descendant",
    ),
    Mutation(
        "recovery_cause_slot_binding",
        "if causes[index] == adverse_case_id:",
        "if True:",
        "tests/adversarial/test_capacity_and_recovery.py::test_two_active_causes_require_two_successful_recoveries",
    ),
    Mutation(
        "recovery_retry_fail_closed",
        "if result_status == RESULT_RETRYABLE:",
        "if False:",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_failure_inconclusive_and_source_unavailable_are_retryable",
    ),
    Mutation(
        "recovery_max_steps_enforcement",
        "max_steps <= u256(MAX_RECOVERY_STEPS_PER_CALL)",
        "True",
        "tests/adversarial/test_capacity_and_recovery.py::test_recovery_processing_is_bounded_resumable_and_idempotent",
    ),
)


def main() -> int:
    killed = 0
    survivors: list[str] = []
    for mutation in MUTATIONS:
        source = CONTRACT.read_text(encoding="utf-8")
        if mutation.needle not in source:
            survivors.append(mutation.name + " (needle not found)")
            continue
        mutated = source.replace(mutation.needle, mutation.replacement, 1)
        with tempfile.TemporaryDirectory(prefix="palinode-mutant-") as temp:
            mutant = Path(temp) / "palinode.py"
            mutant.write_text(mutated, encoding="utf-8")
            environment = os.environ.copy()
            environment["PALINODE_CONTRACT"] = str(mutant)
            environment["GENVM_VERSION"] = "v0.2.16"
            environment["PYTHONIOENCODING"] = "utf-8"
            environment["PATH"] = str(ROOT / ".venv" / "Scripts") + os.pathsep + environment.get("PATH", "")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", mutation.test, "-q"],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=90,
            )
            if result.returncode != 0:
                killed += 1
                print(f"KILLED {mutation.name}")
            else:
                survivors.append(mutation.name)
                print(f"SURVIVED {mutation.name}")
    print(f"MUTATION_RESULT killed={killed}/{len(MUTATIONS)} survivors={survivors}")
    return 0 if killed == len(MUTATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
