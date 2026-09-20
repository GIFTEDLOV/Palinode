import hashlib
import json
import re

import pytest


CONTRACT = "contracts/palinode.py"
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
        "change_authentic": False,
        "same_subject": True,
        "original_evidence_affected": False,
        "materiality": "IMMATERIAL",
        "root_effect": "NO_CHANGE",
        "reason_code": "NO_AUTHENTIC_CHANGE",
    }


def material_result():
    return {
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
    assert initial["status"] == "ACTIVE"

    notice_body = b"No authentic change was found."
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)
    assert contract.get_node_record(evidence_id)["assessment_status"] == "PENDING"
    mock_semantic(direct_vm, EVIDENCE_URI, NOTICE_URI, notice_body, immaterial_result())
    contract.assess_revocation(case_id)
    cleared = contract.get_node_record(evidence_id)
    assert cleared["assessment_status"] == "CLEARED"
    assert cleared["status"] == "ACTIVE"
    assert cleared["assessment_status"] != cleared["status"]


def test_third_party_can_open_challenge_and_owner_has_no_suppression_path(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "permissionless")
    evidence_id = evidence(contract, evidence_authority)
    with direct_vm.prank("0x" + "b" * 40):
        case_id = open_case(contract, evidence_authority, notice_authority, evidence_id)
    case_record = contract.get_revocation_case(case_id)
    assert case_record["submitter"] == "0x" + "b" * 40
    assert contract.get_node_record(evidence_id)["assessment_status"] == "PENDING"
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
    assert contract.get_node_record(evidence_id)["assessment_status"] == "REJECTED"


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
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)

    contract.assess_revocation(case_id)
    unavailable = contract.get_node_record(evidence_id)
    assert unavailable["assessment_status"] == "SOURCE_UNAVAILABLE"
    locked = contract.get_revocation_case(case_id)
    assert locked["case_status"] == "INCONCLUSIVE"

    evidence_mirror = EVIDENCE_ORIGIN + "/mirror-e-1"
    notice_mirror = NOTICE_ORIGIN + "/mirror-n-1"
    direct_vm.mock_web(re.escape(evidence_mirror), {"status": 200, "body": EVIDENCE_BODY})
    direct_vm.mock_web(re.escape(notice_mirror), {"status": 200, "body": notice_body})
    with direct_vm.prank("0x" + "c" * 40):
        contract.retry_revocation_case(case_id, evidence_mirror, notice_mirror)
    recovered = contract.get_revocation_case(case_id)
    assert recovered["notice_uri"] == NOTICE_URI
    assert recovered["notice_sha256"] == locked["notice_sha256"]
    assert recovered["notice_byte_length"] == locked["notice_byte_length"]
    assert recovered["evidence_retrieval_uri"] == evidence_mirror
    assert recovered["notice_retrieval_uri"] == notice_mirror
    assert contract.get_node_record(evidence_id)["assessment_status"] == "PENDING"

    direct_vm.clear_mocks()
    mock_semantic(direct_vm, evidence_mirror, notice_mirror, notice_body, immaterial_result())
    contract.assess_revocation(case_id)
    assert contract.get_node_record(evidence_id)["assessment_status"] == "CLEARED"


def test_mirror_mismatch_cannot_rewrite_locked_identity(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority, notice_authority = authorities(contract, direct_vm, "mirror-mismatch")
    evidence_id = evidence(contract, evidence_authority)
    notice_body = b"Mismatch notice"
    case_id = open_case(contract, evidence_authority, notice_authority, evidence_id, notice_body=notice_body)
    contract.assess_revocation(case_id)
    before = contract.get_revocation_case(case_id)
    evidence_mirror = EVIDENCE_ORIGIN + "/bad-mirror"
    notice_mirror = NOTICE_ORIGIN + "/bad-notice-mirror"
    direct_vm.mock_web(re.escape(evidence_mirror), {"status": 200, "body": b"tampered"})
    direct_vm.mock_web(re.escape(notice_mirror), {"status": 200, "body": notice_body})
    with direct_vm.expect_revert("mirror content does not match locked identity"):
        contract.retry_revocation_case(case_id, evidence_mirror, notice_mirror)
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
