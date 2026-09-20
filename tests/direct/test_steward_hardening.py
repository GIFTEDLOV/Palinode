import hashlib
import json
import os
import re

import pytest


CONTRACT = os.environ.get("PALINODE_CONTRACT", "contracts/palinode.py")
EVIDENCE_ORIGIN = "https://evidence.example"
NOTICE_ORIGIN = "https://notice.example"
EVIDENCE_URI = EVIDENCE_ORIGIN + "/e-1"
NOTICE_URI = NOTICE_ORIGIN + "/n-1"
POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
EVIDENCE_BODY = b"The registered evidence says the service completed."


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sender_text(direct_vm):
    sender = direct_vm.sender
    if isinstance(sender, bytes):
        return "0x" + sender.hex()
    return str(sender)


def register_authority(contract, direct_vm, origin, nonce):
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
    direct_vm.mock_web(
        re.escape(origin + "/.well-known/palinode.json"),
        {"status": 200, "body": challenge},
    )
    return contract.register_source_authority(origin, POLICY, nonce)


def authorities(contract, direct_vm, suffix):
    return (
        register_authority(contract, direct_vm, EVIDENCE_ORIGIN, suffix + "-e"),
        register_authority(contract, direct_vm, NOTICE_ORIGIN, suffix + "-n"),
    )


def evidence(contract, authority_id, uri=EVIDENCE_URI, body=EVIDENCE_BODY):
    return contract.register_evidence(
        uri,
        digest(body),
        len(body),
        "steward-subject",
        "Steward evidence",
        authority_id,
    )


def open_case(
    contract,
    evidence_authority,
    notice_authority,
    evidence_id,
    notice_uri=NOTICE_URI,
    notice_body=b"Correction notice",
):
    return contract.open_revocation_case(
        evidence_id,
        notice_authority,
        notice_uri,
        digest(notice_body),
        len(notice_body),
        "CORRECTED",
        "steward-hardening fixture",
    )


def mock_semantic(direct_vm, evidence_uri, notice_uri, notice_body, result):
    direct_vm.mock_web(re.escape(evidence_uri), {"status": 200, "body": EVIDENCE_BODY})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    direct_vm.mock_llm(r"PALINODE semantic adjudicator", json.dumps(result))


def immaterial_result():
    return {
        "result_status": "CONCLUSIVE",
        "result_status": "CONCLUSIVE",
        "change_authentic": False,
        "same_subject": True,
        "original_evidence_affected": False,
        "materiality": "IMMATERIAL",
        "root_effect": "NO_CHANGE",
        "reason_code": "NO_AUTHENTIC_CHANGE",
    }


def material_result():
    return {
        "result_status": "CONCLUSIVE",
        "result_status": "CONCLUSIVE",
        "change_authentic": True,
        "same_subject": True,
        "original_evidence_affected": True,
        "materiality": "MATERIAL",
        "root_effect": "INVALIDATE",
        "reason_code": "MATERIAL_CORRECTION",
    }


def test_registration_is_unassessed_and_cleared_is_distinct(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "assessment")
    evidence_id = evidence(contract, evidence_authority)
    initial = contract.get_node_record(evidence_id)
    assert initial["assessment_status"] == "UNASSESSED"
    assert initial["authentication_status"] == "UNASSESSED"
    assert initial["status"] == "ACTIVE"

    direct_vm.mock_web(re.escape(EVIDENCE_URI), {"status": 200, "body": EVIDENCE_BODY})
    contract.authenticate_evidence(evidence_id)
    direct_vm.clear_mocks()
    assert contract.get_node_record(evidence_id)["authentication_status"] == "CLEARED"
    notice_body = b"No authentic change was found."
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)
    assert contract.get_node_record(evidence_id)["authentication_status"] == "CLEARED"
    mock_semantic(direct_vm, EVIDENCE_URI, NOTICE_URI, notice_body, immaterial_result())
    contract.assess_revocation(case_id)
    cleared = contract.get_node_record(evidence_id)
    assert cleared["authentication_status"] == "CLEARED"
    assert cleared["status"] == "ACTIVE"
    assert cleared["reliance_status"] == "ACTIVE"


def test_third_party_can_open_challenge_and_owner_has_no_suppression_path(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "permissionless")
    evidence_id = evidence(contract, evidence_authority)
    with direct_vm.prank("0x" + "b" * 40):
        case_id = open_case(contract, evidence_authority, notice_authority, evidence_id)
    case_record = contract.get_revocation_case(case_id)
    assert case_record["submitter"] == "0x" + "b" * 40
    assert contract.get_node_record(evidence_id)["assessment_status"] == "UNASSESSED"
    assert not hasattr(contract, "suppress_case")
    assert not hasattr(contract, "override_verdict")
    assert not hasattr(contract, "delete_case")


def test_unauthorized_authority_claims_and_wrong_origins_fail(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "authority-binding")
    with direct_vm.expect_revert("authority does not exist"):
        contract.register_evidence(
            EVIDENCE_URI,
            digest(EVIDENCE_BODY),
            len(EVIDENCE_BODY),
            "subject",
            "Unauthorized",
            "f" * 64,
        )
    with direct_vm.expect_revert("URI is outside registered authority origin"):
        contract.register_evidence(
            NOTICE_URI,
            digest(EVIDENCE_BODY),
            len(EVIDENCE_BODY),
            "subject",
            "Wrong origin",
            evidence_authority,
        )
    evidence_id = evidence(contract, evidence_authority)
    with direct_vm.expect_revert("URI is outside registered authority origin"):
        contract.open_revocation_case(
            evidence_id,
            notice_authority,
            EVIDENCE_URI,
            digest(b"wrong origin notice"),
            len(b"wrong origin notice"),
            "CORRECTED",
            "wrong origin",
        )


def test_domain_control_challenge_rejects_wrong_address_or_nonce(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    origin = "https://unowned.example"
    challenge = json.dumps(
        {
            "palinode": "1",
            "authority_address": "0x" + "d" * 40,
            "canonical_origin": origin,
            "nonce": "different-nonce",
            "verification_policy": POLICY,
        },
        separators=(",", ":"),
    ).encode()
    direct_vm.mock_web(
        re.escape(origin + "/.well-known/palinode.json"),
        {"status": 200, "body": challenge},
    )
    with direct_vm.expect_revert("authority challenge was not verified"):
        contract.register_source_authority(origin, POLICY, "expected-nonce")


def test_duplicate_and_different_notices_are_independent(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "repeated")
    evidence_id = evidence(contract, evidence_authority)
    first_notice = b"First correction notice"
    first_case = open_case(
        contract,
        evidence_authority,
        notice_authority,
        evidence_id,
        notice_body=first_notice,
    )
    with direct_vm.expect_revert("duplicate revocation case"):
        open_case(
            contract,
            evidence_authority,
            notice_authority,
            evidence_id,
            notice_body=first_notice,
        )
    second_notice = b"Second independently submitted notice"
    second_case = open_case(
        contract,
        evidence_authority,
        notice_authority,
        evidence_id,
        notice_uri=NOTICE_ORIGIN + "/n-2",
        notice_body=second_notice,
    )
    assert first_case != second_case
    assert contract.get_revocation_case(first_case)["notice_sha256"] != contract.get_revocation_case(second_case)["notice_sha256"]
    mock_semantic(direct_vm, EVIDENCE_URI, NOTICE_URI, first_notice, immaterial_result())
    contract.assess_revocation(first_case)
    direct_vm.clear_mocks()
    mock_semantic(direct_vm, EVIDENCE_URI, NOTICE_ORIGIN + "/n-2", second_notice, material_result())
    contract.assess_revocation(second_case)
    assert contract.get_revocation_case(first_case)["case_status"] == "COMPLETE"
    assert contract.get_revocation_case(second_case)["case_status"] == "COMPLETE"
    assert contract.get_node_record(evidence_id)["assessment_status"] == "UNASSESSED"


def test_reassessment_uses_locked_case_identity_not_caller_substitution(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "locked")
    evidence_id = evidence(contract, evidence_authority)
    notice_body = b"Locked notice"
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)
    before = contract.get_revocation_case(case_id)
    with pytest.raises(TypeError):
        contract.assess_revocation(case_id, "https://attacker.example/other")
    mock_semantic(direct_vm, EVIDENCE_URI, NOTICE_URI, notice_body, immaterial_result())
    contract.assess_revocation(case_id)
    after = contract.get_revocation_case(case_id)
    assert after["target_evidence_id"] == evidence_id == before["target_evidence_id"]
    assert after["notice_uri"] == before["notice_uri"] == NOTICE_URI
    assert after["notice_sha256"] == before["notice_sha256"]
    assert after["notice_byte_length"] == before["notice_byte_length"]


def test_source_unavailable_has_permissionless_mirror_recovery_without_identity_rewrite(
    direct_vm, direct_deploy
):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "recovery")
    evidence_id = evidence(contract, evidence_authority)
    notice_body = b"Recoverable notice"
    direct_vm.mock_web(re.escape(EVIDENCE_URI), {"status": 200, "body": EVIDENCE_BODY})
    contract.authenticate_evidence(evidence_id)
    direct_vm.clear_mocks()
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)

    contract.assess_revocation(case_id)
    unavailable = contract.get_node_record(evidence_id)
    assert unavailable["authentication_status"] == "CLEARED"
    locked = contract.get_revocation_case(case_id)
    assert locked["case_status"] == "INCONCLUSIVE"

    evidence_mirror = EVIDENCE_ORIGIN + "/mirror-e-1"
    notice_mirror = NOTICE_ORIGIN + "/mirror-n-1"
    direct_vm.mock_web(re.escape(evidence_mirror), {"status": 200, "body": EVIDENCE_BODY})
    direct_vm.mock_web(re.escape(notice_mirror), {"status": 200, "body": notice_body})
    evidence_mirror_id = contract.add_evidence_mirror(evidence_id, evidence_mirror)
    notice_mirror_id = contract.add_notice_mirror(case_id, notice_mirror)
    with direct_vm.prank("0x" + "c" * 40):
        contract.retry_revocation_case(case_id, evidence_mirror_id, notice_mirror_id)
    recovered = contract.get_revocation_case(case_id)
    assert recovered["notice_uri"] == NOTICE_URI
    assert recovered["notice_sha256"] == locked["notice_sha256"]
    assert recovered["notice_byte_length"] == locked["notice_byte_length"]
    assert recovered["evidence_retrieval_uri"] == evidence_mirror
    assert recovered["notice_retrieval_uri"] == notice_mirror
    assert contract.get_node_record(evidence_id)["authentication_status"] == "CLEARED"

    direct_vm.clear_mocks()
    mock_semantic(direct_vm, evidence_mirror, notice_mirror, notice_body, immaterial_result())
    contract.assess_revocation(case_id)
    assert contract.get_node_record(evidence_id)["authentication_status"] == "CLEARED"


def test_mirror_mismatch_cannot_rewrite_locked_identity(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "mirror-mismatch")
    evidence_id = evidence(contract, evidence_authority)
    notice_body = b"Mismatch notice"
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)
    contract.assess_revocation(case_id)
    before = contract.get_revocation_case(case_id)
    evidence_mirror = EVIDENCE_ORIGIN + "/bad-mirror"
    direct_vm.mock_web(re.escape(evidence_mirror), {"status": 200, "body": b"tampered"})
    with direct_vm.expect_revert("mirror content does not match locked evidence identity"):
        contract.add_evidence_mirror(evidence_id, evidence_mirror)
    after = contract.get_revocation_case(case_id)
    assert after["notice_uri"] == before["notice_uri"]
    assert after["notice_sha256"] == before["notice_sha256"]
    assert after["evidence_retrieval_uri"] == before["evidence_retrieval_uri"]


def test_assessment_state_machine_has_no_arbitrary_skip(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, _notice_authority = authorities(contract, direct_vm, "assessment-machine")
    evidence_id = evidence(contract, evidence_authority)
    with direct_vm.expect_revert("assessment transition is not allowed"):
        contract._transition_assessment(evidence_id, "CLEARED", "")
    contract._transition_assessment(evidence_id, "PENDING", "")
    with direct_vm.expect_revert("assessment transition is not allowed"):
        contract._transition_assessment(evidence_id, "UNASSESSED", "")
    contract._transition_assessment(evidence_id, "INCONCLUSIVE", "")
    contract._transition_assessment(evidence_id, "PENDING", "")
    contract._transition_assessment(evidence_id, "SOURCE_UNAVAILABLE", "")
    assert contract.get_node_record(evidence_id)["assessment_status"] == "SOURCE_UNAVAILABLE"


def test_authenticate_evidence_is_the_only_cleared_path_and_checks_exact_identity(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, _notice_authority = authorities(contract, direct_vm, "authenticate")
    evidence_id = evidence(contract, evidence_authority)
    assert contract.get_node_record(evidence_id)["assessment_status"] == "UNASSESSED"
    direct_vm.mock_web(re.escape(EVIDENCE_URI), {"status": 200, "body": EVIDENCE_BODY})
    contract.authenticate_evidence(evidence_id)
    record = contract.get_node_record(evidence_id)
    assert record["assessment_status"] == "CLEARED"
    assert record["status"] == "ACTIVE"

    wrong_id = contract.register_evidence(
        EVIDENCE_ORIGIN + "/wrong-bytes",
        digest(b"committed bytes"),
        len(b"committed bytes"),
        "auth-subject",
        "Wrong bytes",
        evidence_authority,
    )
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/wrong-bytes"), {"status": 200, "body": b"different bytes"})
    contract.authenticate_evidence(wrong_id)
    assert contract.get_node_record(wrong_id)["assessment_status"] == "REJECTED"


def test_authentication_source_unavailable_is_retryable_and_never_cleared(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, _notice_authority = authorities(contract, direct_vm, "authenticate-retry")
    evidence_id = evidence(contract, evidence_authority)
    direct_vm.strict_mocks = True
    contract.authenticate_evidence(evidence_id)
    assert contract.get_node_record(evidence_id)["assessment_status"] == "SOURCE_UNAVAILABLE"
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(EVIDENCE_URI), {"status": 200, "body": EVIDENCE_BODY})
    with direct_vm.prank("0x" + "d" * 40):
        contract.authenticate_evidence(evidence_id)
    assert contract.get_node_record(evidence_id)["assessment_status"] == "CLEARED"


def test_cross_origin_mirror_is_verified_but_has_no_authority_or_clearance_effect(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, _notice_authority = authorities(contract, direct_vm, "mirror-cross-origin")
    evidence_id = evidence(contract, evidence_authority)
    mirror_uri = "https://independent-mirror.example/e-1"
    direct_vm.mock_web(re.escape(mirror_uri), {"status": 200, "body": EVIDENCE_BODY})
    mirror_id = contract.add_evidence_mirror(evidence_id, mirror_uri)
    record = contract.get_node_record(evidence_id)
    expected_mirror_id = hashlib.sha256(
        ("palinode/evidence-mirror/v1|" + evidence_id + "|" + mirror_uri + "|" + digest(EVIDENCE_BODY) + "|" + str(len(EVIDENCE_BODY))).encode()
    ).hexdigest()
    assert mirror_id == expected_mirror_id
    assert record["source_uri"] == EVIDENCE_URI
    assert record["authority_id"] == evidence_authority
    assert record["assessment_status"] == "UNASSESSED"
    with direct_vm.expect_revert("duplicate evidence mirror"):
        contract.add_evidence_mirror(evidence_id, mirror_uri)
    with direct_vm.expect_revert("invalid HTTPS mirror URI"):
        contract.add_evidence_mirror(evidence_id, "http://independent-mirror.example/e-1")


def test_authority_versions_rotate_from_domain_declaration_and_preserve_history(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "rotation-1")
    initial = contract.get_source_authority(authority_id)
    assert initial["status"] == "ACTIVE"
    assert initial["current_version"] == "1"
    evidence_id = evidence(contract, authority_id)
    new_controller = "0x" + "e" * 40
    rotation = json.dumps(
        {
            "palinode": "1",
            "authority_id": authority_id,
            "authority_version": "2",
            "authority_address": new_controller,
            "canonical_origin": EVIDENCE_ORIGIN,
            "nonce": "rotation-2",
            "verification_policy": POLICY,
        },
        separators=(",", ":"),
    ).encode()
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(EVIDENCE_ORIGIN + "/.well-known/palinode.json"), {"status": 200, "body": rotation})
    assert contract.rotate_source_authority(authority_id, "rotation-2") == 2
    rotated = contract.get_source_authority(authority_id)
    assert rotated["current_version"] == "2"
    assert rotated["authority_address"] == new_controller
    assert contract.get_source_authority_version(authority_id, 1)["status"] == "REVOKED"
    assert contract.get_node_record(evidence_id)["authority_version"] == "1"
    with direct_vm.expect_revert("authority rotation was not verified"):
        contract.rotate_source_authority(authority_id, "old-controller-attempt")
    with direct_vm.expect_revert("not current authority controller"):
        with direct_vm.prank("0x" + "a" * 40):
            contract.revoke_source_authority(authority_id)
    with direct_vm.prank(new_controller):
        contract.revoke_source_authority(authority_id)
    assert contract.get_source_authority(authority_id)["status"] == "REVOKED"
    assert contract.get_node_record(evidence_id)["authority_id"] == authority_id
