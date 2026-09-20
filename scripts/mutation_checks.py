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
        "if severity[target_status] <= severity[current]:",
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
