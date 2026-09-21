"""Complete v2 security mutation catalogue.

Every active mutation is applied to a temporary copy of the v2 contract and
must be killed by a named v2 regression. The archived 34-entry catalogue is
loaded and rerun against v2; only the three overflow-summary mutants are
retired because v2 replaced that unsafe lossy summary with individually keyed
active causes and severity counters. The repository contract is never edited.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.mutation_checks import MUTATIONS as ARCHIVED_MUTATIONS
except ModuleNotFoundError:
    from mutation_checks import MUTATIONS as ARCHIVED_MUTATIONS


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "palinode_v2.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    needle: str
    replacement: str
    test: str


RETIRED = {
    "active_cause_overflow_handling": "v2 has no lossy 64-slot overflow branch; every active cause has an identity.",
    "active_cause_overflow_severity_retention": "v2 replaced the overflow severity summary with per-cause severity counters.",
    "active_cause_overflow_safety_lock": "v2 computes reliance from exact active-cause counters, so this overflow lock no longer exists.",
}


def _historical_v2_mutations() -> tuple[Mutation, ...]:
    """Preserve every archived guard whose implementation still exists in v2."""
    result: list[Mutation] = []
    for mutation in ARCHIVED_MUTATIONS:
        if mutation.name in RETIRED:
            continue
        if mutation.name == "recovery_cause_registration":
            result.append(
                Mutation(
                    mutation.name,
                    "self._register_active_cause(node_id, case_id, target_status, root_effect)",
                    'self._require(False, "mutant recovery cause")',
                    mutation.test,
                )
            )
        elif mutation.name == "recovery_successor_clearance":
            result.append(
                Mutation(
                    mutation.name,
                    "        self._require(\n            self.node_assessment_status[successor_evidence_id] == ASSESS_CLEARED,\n            \"successor evidence is not independently cleared\",\n        )\n        self._require(\n            self.node_subject[affected_node_id]",
                    "        self._require(True, \"successor evidence is not independently cleared\")\n        self._require(\n            self.node_subject[affected_node_id]",
                    mutation.test,
                )
            )
        elif mutation.name == "recovery_cause_slot_binding":
            result.append(
                Mutation(
                    mutation.name,
                    "        for index in range(len(causes)):\n            if causes[index] == adverse_case_id:\n                found = True",
                    "        for index in range(len(causes)):\n            if True:\n                found = True",
                    "tests/v2/test_reviewer_remediation.py::test_active_cause_counters_match_identity_mapping_across_mixed_recovery_operations",
                )
            )
        else:
            result.append(Mutation(mutation.name, mutation.needle, mutation.replacement, mutation.test))
    return tuple(result)


NEW_MUTATIONS = (
    Mutation(
        "v2_dependency_child_controller_authorization",
        "        self._require_node_controller(child_node_id)\n        self._require(\n            self.node_status[parent_node_id]",
        "        self._require(True, \"mutant child authorization\")\n        self._require(\n            self.node_status[parent_node_id]",
        "tests/v2/test_reviewer_remediation.py::test_dependency_requires_child_controller_and_records_assertor",
    ),
    Mutation(
        "v2_dependency_parent_controller_not_required",
        "        self._require_node_controller(child_node_id)",
        "        self._require_node_controller(parent_node_id)\n        self._require_node_controller(child_node_id)",
        "tests/v2/test_reviewer_remediation.py::test_cross_owner_parent_can_be_cited_without_parent_consent",
    ),
    Mutation(
        "v2_successor_same_lineage_guard",
        "self.node_source_authority[old_evidence_id] == self.node_source_authority[successor_evidence_id]",
        "True",
        "tests/v2/test_reviewer_remediation.py::test_successor_requires_the_same_authority_lineage",
    ),
    Mutation(
        "v2_byte_identity_digest_verification",
        "if _sha256_text(evidence_text) != evidence_digest:",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_changed_evidence_bytes_short_circuit_semantic_execution",
    ),
    Mutation(
        "v2_byte_identity_length_verification",
        "if len(evidence_text.encode(\"utf-8\")) != int(evidence_byte_length):",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_declared_semantic_length_mismatch_short_circuits",
    ),
    Mutation(
        "v2_cleared_precondition",
        "self.node_assessment_status[target] == ASSESS_CLEARED",
        "True",
        "tests/v2/test_reviewer_remediation.py::test_non_cleared_evidence_cannot_be_semantically_revoked",
    ),
    Mutation(
        "v2_notice_standing_guard",
        "if notice_kind == NOTICE_CHALLENGE and semantic_result[\"materiality\"] == VERDICT_MATERIAL:",
        "if False:",
        "tests/v2/test_reviewer_remediation.py::test_unrelated_authority_cannot_impersonate_publisher_withdrawal",
    ),
    Mutation(
        "v2_late_edge_inheritance",
        "self._apply_impact_status(\n                    child_node_id,",
        "pass\n                # self._apply_impact_status(\n                    child_node_id,",
        "tests/v2/test_reviewer_remediation.py::test_late_edge_inherits_active_cause_without_new_consensus",
    ),
    Mutation(
        "v2_recovery_complete_requirement",
        "self._require(self.case_status[adverse_case_id] == CASE_COMPLETE, \"adverse propagation is not complete\")\n        self._require(\n            self.case_cursor[adverse_case_id] >= u256(len(self.case_queue[adverse_case_id])),\n            \"adverse impact queue is not exhausted\",\n        )",
        "self._require(True, \"adverse propagation is not complete\")\n        self._require(True, \"adverse impact queue is not exhausted\")",
        "tests/v2/test_reviewer_remediation.py::test_recovery_is_blocked_until_adverse_propagation_is_complete",
    ),
    Mutation(
        "v2_active_cause_counter_move",
        "if self._ordinary_severity(target_status) > self._ordinary_severity(previous):\n                    self._decrement_cause_counter(node_id, previous)",
        "if self._ordinary_severity(target_status) > self._ordinary_severity(previous):\n                    pass",
        "tests/v2/test_reviewer_remediation.py::test_active_cause_counters_match_identity_mapping_across_mixed_recovery_operations",
    ),
    Mutation(
        "v2_prompt_json_serialization",
        "payload = payload.replace(\"<\", \"\\\\u003c\").replace(\">\", \"\\\\u003e\")",
        "payload = payload",
        "tests/v2/test_reviewer_remediation.py::test_prompt_payload_is_json_serialized_and_semantic_scope_is_bounded",
    ),
    Mutation(
        "v2_size_bound_enforcement",
        "self._require(byte_length <= u256(MAX_DECLARED_SOURCE_BYTES), \"evidence byte length too large\")",
        "self._require(True, \"evidence byte length too large\")",
        "tests/v2/test_reviewer_remediation.py::test_semantic_size_boundary_is_coherent",
    ),
    Mutation(
        "v2_historical_authority_version_authentication",
        "self.authority_version_status[version_key] in (AUTHORITY_VERSION_ACTIVE, AUTHORITY_VERSION_SUPERSEDED),",
        "self.authority_version_status[version_key] == AUTHORITY_VERSION_ACTIVE,",
        "tests/v2/test_reviewer_remediation.py::test_benign_authority_rotation_preserves_historical_authentication",
    ),
    Mutation(
        "v2_evidence_mirror_authorization",
        "        self._require_node_controller(evidence_id)\n        normalised_uri = _normalise_https_uri(mirror_uri)",
        "        self._require(True, \"mutant mirror authorization\")\n        normalised_uri = _normalise_https_uri(mirror_uri)",
        "tests/v2/test_reviewer_remediation.py::test_mirror_registration_is_controller_authorized",
    ),
    Mutation(
        "v2_authority_revocation_historical_fail_closed",
        "self.authority_status[authority_id] != AUTHORITY_ACTIVE",
        "False",
        "tests/v2/test_reviewer_remediation.py::test_revoking_authority_blocks_historical_authentication_without_collapsing_version_status",
    ),
)


MUTATIONS = _historical_v2_mutations() + NEW_MUTATIONS


def main() -> int:
    killed = 0
    survivors: list[str] = []
    missing: list[str] = []
    for mutation in MUTATIONS:
        source = CONTRACT.read_text(encoding="utf-8")
        if mutation.needle not in source:
            missing.append(mutation.name)
            print(f"SURVIVED {mutation.name} (needle not found)")
            continue
        mutated = source.replace(mutation.needle, mutation.replacement, 1)
        with tempfile.TemporaryDirectory(prefix="palinode-v2-mutant-") as temp:
            mutant = Path(temp) / "palinode_v2.py"
            mutant.write_text(mutated, encoding="utf-8")
            test_artifacts = Path(temp) / "artifacts"
            environment = os.environ.copy()
            environment["PALINODE_CONTRACT"] = str(mutant)
            environment["GENVM_VERSION"] = "v0.2.16"
            environment["PYTHONIOENCODING"] = "utf-8"
            environment["PATH"] = str(ROOT / ".venv" / "Scripts") + os.pathsep + environment.get("PATH", "")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    mutation.test,
                    "-q",
                    "--artifacts-dir",
                    str(test_artifacts),
                ],
                cwd=ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                killed += 1
                print(f"KILLED {mutation.name}")
            else:
                survivors.append(mutation.name)
                print(f"SURVIVED {mutation.name}")
    total = len(MUTATIONS) + len(RETIRED)
    print(f"MUTATIONS_TOTAL={total}")
    print(f"MUTATIONS_KILLED={killed}")
    print(f"MUTATIONS_RETIRED={len(RETIRED)}")
    print(f"MUTATIONS_SURVIVED={len(survivors) + len(missing)}")
    print(f"SURVIVORS={survivors + missing}")
    print(f"RETIRED={sorted(RETIRED)}")
    return 0 if not survivors and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
