import hashlib
import json
import os
import re

import pytest


CONTRACT = os.environ.get("PALINODE_CONTRACT", "contracts/palinode.py")
POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
EVIDENCE_ORIGIN = "https://recovery-evidence.example"
NOTICE_ORIGIN = "https://recovery-notice.example"


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sender_text(direct_vm) -> str:
    sender = direct_vm.sender
    return "0x" + sender.hex() if isinstance(sender, bytes) else str(sender)


def authority(contract, direct_vm, origin: str, nonce: str) -> str:
    challenge = json.dumps(
        {
            "palinode": "1",
            "authority_address": sender_text(direct_vm),
            "canonical_origin": origin,
            "nonce": nonce,
            "verification_policy": POLICY,
        },
        separators=(",", ":"),
    ).encode()
    direct_vm.mock_web(re.escape(origin + "/.well-known/palinode.json"), {"status": 200, "body": challenge})
    return contract.register_source_authority(origin, POLICY, nonce)


def setup_recovery(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority = authority(contract, direct_vm, EVIDENCE_ORIGIN, "recovery-evidence")
    notice_authority = authority(contract, direct_vm, NOTICE_ORIGIN, "recovery-notice")
    old_body = b"fictional audit v1: condition X was reported as satisfied."
    successor_body = b"fictional audit v2: condition X was re-audited and corrected."
    old_uri = EVIDENCE_ORIGIN + "/old"
    successor_uri = EVIDENCE_ORIGIN + "/successor"
    direct_vm.mock_web(re.escape(old_uri), {"status": 200, "body": old_body})
    old_id = contract.register_evidence(
        old_uri,
        digest(old_body),
        len(old_body),
        "recovery-subject",
        "Fictional audit v1",
        evidence_authority,
    )
    contract.authenticate_evidence(old_id)
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(successor_uri), {"status": 200, "body": successor_body})
    successor_id = contract.register_evidence(
        successor_uri,
        digest(successor_body),
        len(successor_body),
        "recovery-subject",
        "Fictional audit v2",
        evidence_authority,
    )
    contract.authenticate_evidence(successor_id)
    direct_vm.clear_mocks()
    contract.link_evidence_successor(old_id, successor_id)
    child_id = contract.register_claim("recovery-subject", "Dependent claim")
    contract.register_dependency(old_id, child_id, "REQUIRES")
    return contract, evidence_authority, notice_authority, old_id, successor_id, child_id, old_body, successor_body


def open_material_case(contract, direct_vm, notice_authority, old_id, old_body, suffix: str):
    notice_uri = NOTICE_ORIGIN + "/notice-" + suffix
    notice_body = ("material correction " + suffix).encode()
    case_id = contract.open_revocation_case(
        old_id,
        notice_authority,
        notice_uri,
        digest(notice_body),
        len(notice_body),
        "CORRECTED",
        "fictional recovery test",
    )
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/old"), {"status": 200, "body": old_body})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    direct_vm.mock_llm(
        r"PALINODE semantic adjudicator",
        json.dumps(
            {
                "result_status": "CONCLUSIVE",
                "change_authentic": True,
                "same_subject": True,
                "original_evidence_affected": True,
                "materiality": "MATERIAL",
                "root_effect": "INVALIDATE",
                "reason_code": "MATERIAL_CORRECTION",
            }
        ),
    )
    contract.assess_revocation(case_id)
    contract.process_impact(case_id, 32)
    direct_vm.clear_mocks()
    return case_id, notice_uri, notice_body


def assess_recovery(contract, direct_vm, recovery_id, successor_uri, successor_body, notice_uri, notice_body, result):
    direct_vm.mock_web(re.escape(successor_uri), {"status": 200, "body": successor_body})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    direct_vm.mock_llm(r"PALINODE recovery adjudicator", json.dumps(result))
    contract.assess_recovery(recovery_id)
    direct_vm.clear_mocks()


def recovery_result(effect="REINSTATE", reason="RECOVERY_RESOLVED_REINSTATE"):
    return {
        "same_subject": True,
        "successor_relevant": True,
        "prior_defect_resolved": True,
        "recovery_effect": effect,
        "reason_code": reason,
    }


def test_lifetime_caps_are_absent_and_pagination_is_bounded(direct_vm, direct_deploy):
    source = open(CONTRACT, encoding="utf-8").read()
    assert "MAX_NODES" not in source
    assert "MAX_EDGES" not in source
    assert "MAX_CASES" not in source
    assert "MAX_AUTHORITIES" not in source
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    for index in range(100):
        contract.register_claim("capacity", "Node " + str(index))
    first = contract.get_node_ids_page(0, 64)
    second = contract.get_node_ids_page(64, 64)
    assert first["count"] == "64"
    assert second["count"] == "36"
    with direct_vm.expect_revert("page limit exceeds bound"):
        contract.get_node_ids_page(0, 65)


def test_operation_after_former_node_cap_remains_possible(direct_deploy):
    """Exercise the former 4096 lifetime boundary instead of only inspecting source."""
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    for index in range(4097):
        contract.register_claim("former-cap", "Node " + str(index))
    page = contract.get_node_ids_page(4096, 4)
    assert page["count"] == "1"
    assert contract.get_node_record(page["slot_0"])["title"] == "Node 4096"


def test_65th_stronger_cause_is_retained_as_monotonic_overflow_safety_lock(direct_deploy):
    """A full slot set must not suppress a later, stronger adverse finding."""
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    node_id = contract.register_claim("cause-capacity", "Cause capacity boundary")
    cause_ids = [format(index, "064x") for index in range(1, 65)]
    for case_id in cause_ids:
        contract._apply_impact_status(node_id, "QUESTIONED", "BOUNDARY_TEST", case_id)

    full = contract.get_active_causes(node_id)
    assert full["active_count"] == "64"
    assert full["slot_count"] == "64"
    assert full["overflow_count"] == "0"

    stronger_case_id = format(65, "064x")
    contract._apply_impact_status(node_id, "INVALIDATED", "BOUNDARY_TEST", stronger_case_id)

    after_overflow = contract.get_active_causes(node_id)
    assert contract.get_node_record(node_id)["status"] == "INVALIDATED"
    assert after_overflow["active_count"] == "64"
    assert after_overflow["overflow_count"] == "1"
    assert after_overflow["overflow_severity"] == "INVALIDATED"
    assert after_overflow["overflow_latest_case"] == stronger_case_id
    assert len(after_overflow["overflow_commitment"]) == 64

    # Resolving every individually named slot must not clear the unresolvable
    # overflow safety summary or downgrade the node.
    for index, case_id in enumerate(cause_ids, start=1000):
        contract._resolve_active_cause(node_id, case_id, format(index, "064x"), "REINSTATE")
    final_state = contract.get_active_causes(node_id)
    assert final_state["active_count"] == "0"
    assert final_state["overflow_count"] == "1"
    assert final_state["overflow_severity"] == "INVALIDATED"
    assert contract.get_node_record(node_id)["status"] == "INVALIDATED"


def test_recovery_requires_cleared_linked_successor_and_is_permissionless(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, _ = setup_recovery(direct_vm, direct_deploy)
    case_id, _, _ = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "precondition")
    with direct_vm.prank("0x" + "a" * 40):
        recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "third-party review")
    assert contract.get_recovery_case(recovery_id)["submitter"] == "0x" + "a" * 40
    with direct_vm.expect_revert("duplicate recovery case"):
        contract.open_recovery_case(old_id, successor_id, case_id, "duplicate")


def test_recovery_is_consensus_backed_and_owner_cannot_self_reinstate(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "owner")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "owner cannot force")
    assess_recovery(
        contract,
        direct_vm,
        recovery_id,
        EVIDENCE_ORIGIN + "/successor",
        successor_body,
        notice_uri,
        notice_body,
        {"same_subject": False, "successor_relevant": False, "prior_defect_resolved": False, "recovery_effect": "NO_CHANGE", "reason_code": "RECOVERY_DEFECT_UNRESOLVED"},
    )
    assert contract.get_node_record(old_id)["status"] == "INVALIDATED"
    assert not hasattr(contract, "reinstate")


def test_recovery_requires_material_cause_and_rejects_unsupported_effect(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, _ = setup_recovery(direct_vm, direct_deploy)
    notice_uri = NOTICE_ORIGIN + "/immaterial"
    notice_body = b"no material change"
    case_id = contract.open_revocation_case(old_id, notice_authority, notice_uri, digest(notice_body), len(notice_body), "CHANGED", "not material")
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/old"), {"status": 200, "body": old_body})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    direct_vm.mock_llm(
        r"PALINODE semantic adjudicator",
        json.dumps({"result_status": "CONCLUSIVE", "change_authentic": False, "same_subject": True, "original_evidence_affected": False, "materiality": "IMMATERIAL", "root_effect": "NO_CHANGE", "reason_code": "NO_AUTHENTIC_CHANGE"}),
    )
    contract.assess_revocation(case_id)
    direct_vm.clear_mocks()
    with direct_vm.expect_revert("adverse case is not material"):
        contract.open_recovery_case(old_id, successor_id, case_id, "must not recover immaterial case")

    material_case, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "bad-effect")
    recovery_id = contract.open_recovery_case(old_id, successor_id, material_case, "bad consensus effect")
    with direct_vm.expect_revert("unsupported recovery effect"):
        contract._commit_recovery_result(
            recovery_id,
            {"result_status": "CONCLUSIVE", "same_subject": True, "successor_relevant": True, "prior_defect_resolved": True, "recovery_effect": "UNSUPPORTED", "reason_code": "RECOVERY_RESOLVED_REINSTATE"},
        )


def test_recovery_resolution_requires_all_bounded_proofs(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "false-proofs")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "false proof result")
    assess_recovery(
        contract,
        direct_vm,
        recovery_id,
        EVIDENCE_ORIGIN + "/successor",
        successor_body,
        notice_uri,
        notice_body,
        {"same_subject": False, "successor_relevant": False, "prior_defect_resolved": False, "recovery_effect": "REINSTATE", "reason_code": "RECOVERY_RESOLVED_REINSTATE"},
    )
    record = contract.get_recovery_case(recovery_id)
    assert record["result_status"] == "RETRYABLE"
    assert record["case_status"] == "INCONCLUSIVE"
    assert contract.get_node_record(old_id)["status"] == "INVALIDATED"


def test_single_cause_recovery_restores_root_and_descendant(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, child_id, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "single")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "resolve v1 defect")
    assess_recovery(contract, direct_vm, recovery_id, EVIDENCE_ORIGIN + "/successor", successor_body, notice_uri, notice_body, recovery_result())
    contract.process_recovery_impact(recovery_id, 1)
    assert contract.get_recovery_case(recovery_id)["case_status"] == "COMPLETE"
    assert contract.get_node_record(old_id)["status"] == "REINSTATED"
    assert contract.get_node_record(old_id)["authentication_status"] == "CLEARED"
    assert contract.get_node_record(successor_id)["authentication_status"] == "CLEARED"
    assert contract.get_node_record(child_id)["status"] == "REINSTATED"
    assert contract.get_revocation_case(case_id)["case_status"] == "COMPLETE"


def test_two_active_causes_require_two_successful_recoveries(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, child_id, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    first, notice_a, body_a = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "a")
    second, notice_b, body_b = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "b")
    assert contract.get_node_record(old_id)["status"] == "INVALIDATED"
    recovery_a = contract.open_recovery_case(old_id, successor_id, first, "resolve cause a")
    assess_recovery(contract, direct_vm, recovery_a, EVIDENCE_ORIGIN + "/successor", successor_body, notice_a, body_a, recovery_result())
    contract.process_recovery_impact(recovery_a, 32)
    assert contract.get_node_record(old_id)["status"] == "INVALIDATED"
    assert contract.get_node_record(child_id)["status"] == "QUARANTINED"
    recovery_b = contract.open_recovery_case(old_id, successor_id, second, "resolve cause b")
    assess_recovery(contract, direct_vm, recovery_b, EVIDENCE_ORIGIN + "/successor", successor_body, notice_b, body_b, recovery_result())
    contract.process_recovery_impact(recovery_b, 32)
    assert contract.get_node_record(old_id)["status"] == "REINSTATED"
    assert contract.get_node_record(old_id)["authentication_status"] == "CLEARED"
    assert contract.get_node_record(child_id)["status"] == "REINSTATED"
    active = contract.get_active_causes(old_id)
    assert active["active_count"] == "0"


def test_recovery_failure_inconclusive_and_source_unavailable_are_retryable(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "retry")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "retry recovery")
    direct_vm.mock_llm(r"PALINODE recovery adjudicator", "{malformed")
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/successor"), {"status": 200, "body": successor_body})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    contract.assess_recovery(recovery_id)
    telemetry = contract.get_recovery_retry_telemetry(recovery_id)
    assert contract.get_recovery_case(recovery_id)["case_status"] == "INCONCLUSIVE"
    assert telemetry["total_count"] == "1"
    direct_vm.clear_mocks()
    contract.assess_recovery(recovery_id)
    assert contract.get_recovery_case(recovery_id)["reason_code"] == "RECOVERY_SOURCE_UNAVAILABLE"
    assert contract.get_node_record(old_id)["status"] == "INVALIDATED"


def test_recovery_rejects_wrong_or_uncleared_successors_and_preserves_identity(direct_vm, direct_deploy):
    contract, evidence_authority, notice_authority, old_id, successor_id, _, old_body, _ = setup_recovery(direct_vm, direct_deploy)
    case_id, _, _ = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "wrong-successor")
    unrelated_body = b"unrelated subject evidence"
    unrelated = contract.register_evidence(EVIDENCE_ORIGIN + "/unrelated", digest(unrelated_body), len(unrelated_body), "other-subject", "Other", evidence_authority)
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/unrelated"), {"status": 200, "body": unrelated_body})
    contract.authenticate_evidence(unrelated)
    direct_vm.clear_mocks()
    with direct_vm.expect_revert("successor subject does not match"):
        contract.open_recovery_case(old_id, unrelated, case_id, "wrong")
    alternate_body = b"same subject alternate evidence"
    alternate = contract.register_evidence(EVIDENCE_ORIGIN + "/alternate", digest(alternate_body), len(alternate_body), "recovery-subject", "Alternate", evidence_authority)
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/alternate"), {"status": 200, "body": alternate_body})
    contract.authenticate_evidence(alternate)
    direct_vm.clear_mocks()
    uncleared_body = b"same subject but not authenticated"
    uncleared = contract.register_evidence(EVIDENCE_ORIGIN + "/uncleared", digest(uncleared_body), len(uncleared_body), "recovery-subject", "Uncleared", evidence_authority)
    with direct_vm.expect_revert("successor relationship is not registered"):
        contract.open_recovery_case(old_id, alternate, case_id, "not linked")
    with direct_vm.expect_revert("successor evidence is not independently cleared"):
        contract.open_recovery_case(old_id, uncleared, case_id, "uncleared")


def test_recovery_processing_is_bounded_resumable_and_idempotent(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, child_id, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    grandchild_id = contract.register_decision("recovery-subject", "Dependent decision")
    contract.register_dependency(child_id, grandchild_id, "REQUIRES")
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "bounded")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "bounded recovery")
    assess_recovery(contract, direct_vm, recovery_id, EVIDENCE_ORIGIN + "/successor", successor_body, notice_uri, notice_body, recovery_result())
    with direct_vm.expect_revert("max_steps exceeds per-call bound"):
        contract.process_recovery_impact(recovery_id, 33)
    assert contract.process_recovery_impact(recovery_id, 1) == 1
    state = contract.get_recovery_queue_state(recovery_id)
    assert state["case_status"] == "PROPAGATING"
    assert contract.process_recovery_impact(recovery_id, 1) == 1
    assert contract.get_node_record(child_id)["status"] == "REINSTATED"
    assert contract.get_recovery_queue_state(recovery_id)["case_status"] == "COMPLETE"
    assert contract.process_recovery_impact(recovery_id, 32) == 0


def test_recovery_history_and_retry_storage_remain_bounded(direct_vm, direct_deploy):
    contract, _, notice_authority, old_id, successor_id, _, old_body, successor_body = setup_recovery(direct_vm, direct_deploy)
    case_id, notice_uri, notice_body = open_material_case(contract, direct_vm, notice_authority, old_id, old_body, "history")
    recovery_id = contract.open_recovery_case(old_id, successor_id, case_id, "bounded retries")
    for _ in range(12):
        direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/successor"), {"status": 200, "body": successor_body})
        direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
        direct_vm.mock_llm(r"PALINODE recovery adjudicator", "{malformed")
        contract.assess_recovery(recovery_id)
        direct_vm.clear_mocks()
    telemetry = contract.get_recovery_retry_telemetry(recovery_id)
    assert int(telemetry["total_count"]) == 12
    assert int(telemetry["recent_count"]) <= 8
    assert int(contract.get_recovery_case(recovery_id)["retry_count"]) == 12
