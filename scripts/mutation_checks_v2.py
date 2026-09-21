"""Bounded v2 security mutation harness.

Mutants are written only to temporary files. The v2 contract and repository
history are never modified by this script.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "palinode_v2.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    needle: str
    replacement: str
    test: str


MUTATIONS = (
    Mutation(
        "successor_controller_guard",
        "self._require_node_controller(old_evidence_id)",
        "pass",
        "tests/v2/test_reviewer_remediation.py::test_unauthorized_successor_is_rejected_and_link_does_not_change_reliance",
    ),
    Mutation(
        "dependency_parent_controller_guard",
        "self._require_node_controller(parent_node_id)",
        "pass",
        "tests/v2/test_reviewer_remediation.py::test_dependency_requires_both_endpoint_controllers_and_records_assertor",
    ),
    Mutation(
        "dependency_child_controller_guard",
        "self._require_node_controller(child_node_id)",
        "pass",
        "tests/v2/test_reviewer_remediation.py::test_dependency_requires_both_endpoint_controllers_and_records_assertor",
    ),
    Mutation(
        "evidence_digest_guard",
        "if _sha256_text(evidence_text) != evidence_digest:",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_changed_evidence_bytes_short_circuit_semantic_execution",
    ),
    Mutation(
        "evidence_length_guard",
        "if len(evidence_text.encode(\"utf-8\")) != int(evidence_byte_length):",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_declared_semantic_length_mismatch_short_circuits",
    ),
    Mutation(
        "revocation_clearance_guard",
        "self.node_assessment_status[target] == ASSESS_CLEARED",
        "True",
        "tests/v2/test_reviewer_remediation.py::test_non_cleared_evidence_cannot_be_semantically_revoked",
    ),
    Mutation(
        "third_party_invalidate_guard",
        "notice_kind == NOTICE_CHALLENGE\n            and semantic_result[\"materiality\"] == VERDICT_MATERIAL",
        "False",
        "tests/v2/test_reviewer_remediation.py::test_unrelated_authority_is_challenge_only_and_cannot_invalidate",
    ),
    Mutation(
        "late_edge_reconciliation",
        "self._apply_impact_status(\n                    child_node_id,",
        "pass\n                # self._apply_impact_status(\n                    child_node_id,",
        "tests/v2/test_reviewer_remediation.py::test_late_edge_inherits_active_cause_without_new_consensus",
    ),
    Mutation(
        "recovery_completion_guard",
        "self._require(self.case_status[adverse_case_id] == CASE_COMPLETE, \"adverse propagation is not complete\")\n        self._require(\n            self.case_cursor[adverse_case_id] >= u256(len(self.case_queue[adverse_case_id])),\n            \"adverse impact queue is not exhausted\",\n        )",
        "self._require(True, \"adverse propagation is not complete\")\n        self._require(True, \"adverse impact queue is not exhausted\")",
        "tests/v2/test_reviewer_remediation.py::test_recovery_is_blocked_until_adverse_propagation_is_complete",
    ),
    Mutation(
        "prompt_json_payload",
        "{payload}",
        "{evidence_text}",
        "tests/v2/test_reviewer_remediation.py::test_prompt_payload_is_json_serialized_and_semantic_scope_is_bounded",
    ),
    Mutation(
        "coherent_size_bound",
        "byte_length <= u256(MAX_DECLARED_SOURCE_BYTES)",
        "True",
        "tests/v2/test_reviewer_remediation.py::test_semantic_size_boundary_is_coherent",
    ),
    Mutation(
        "evidence_registration_controller_guard",
        "self._require_authority_controller(authority_id)",
        "pass",
        "tests/v2/test_reviewer_remediation.py::test_controller_authorization_is_required_for_evidence_registration",
    ),
    Mutation(
        "strict_materiality_enum",
        "if result[\"materiality\"] not in MATERIALITIES[1:]:",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_semantic_enums_are_exact_and_canonical_only",
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
        with tempfile.TemporaryDirectory(prefix="palinode-v2-mutant-") as temp:
            mutant = Path(temp) / "palinode_v2.py"
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
                timeout=120,
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
