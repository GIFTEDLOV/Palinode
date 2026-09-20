import hashlib
import json
import os
import re

import pytest


CONTRACT = os.environ.get("PALINODE_CONTRACT", "contracts/palinode.py")
POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
EVIDENCE_ORIGIN = "https://evidence.example"
NOTICE_ORIGIN = "https://notice.example"
EVIDENCE_URI = EVIDENCE_ORIGIN + "/e-1"
NOTICE_URI = NOTICE_ORIGIN + "/n-1"
EVIDENCE_BODY = b"adversarial evidence bytes"


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sender_text(direct_vm):
    sender = direct_vm.sender
    return "0x" + sender.hex() if isinstance(sender, bytes) else str(sender)


def authority(contract, direct_vm, origin, nonce):
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


def evidence(contract, authority_id, uri=EVIDENCE_URI, body=EVIDENCE_BODY):
    return contract.register_evidence(uri, digest(body), len(body), "adversarial", "Adversarial evidence", authority_id)


def open_case(contract, evidence_id, notice_authority, uri=NOTICE_URI, body=b"adverse notice", reason="CORRECTED"):
    return contract.open_revocation_case(
        evidence_id,
        notice_authority,
        uri,
        digest(body),
        len(body),
        reason,
        "adversarial case",
    )


def semantic_sources(direct_vm, evidence_uri, notice_uri, notice_body, result):
    direct_vm.mock_web(re.escape(evidence_uri), {"status": 200, "body": EVIDENCE_BODY})
    direct_vm.mock_web(re.escape(notice_uri), {"status": 200, "body": notice_body})
    direct_vm.mock_llm(r"PALINODE semantic adjudicator", json.dumps(result))


def material(root="INVALIDATE"):
    return {
        "result_status": "CONCLUSIVE",
        "change_authentic": True,
        "same_subject": True,
        "original_evidence_affected": True,
        "materiality": "MATERIAL",
        "root_effect": root,
        "reason_code": "MATERIAL_CORRECTION",
    }


def immaterial():
    return {
        "result_status": "CONCLUSIVE",
        "change_authentic": False,
        "same_subject": True,
        "original_evidence_affected": False,
        "materiality": "IMMATERIAL",
        "root_effect": "NO_CHANGE",
        "reason_code": "NO_AUTHENTIC_CHANGE",
    }


def test_authority_substitution_origin_confusion_and_private_targets_fail(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority = authority(contract, direct_vm, EVIDENCE_ORIGIN, "authority-substitution")
    with direct_vm.expect_revert("URI is outside registered authority origin"):
        contract.register_evidence(
            "https://evil.example/e-1",
            digest(EVIDENCE_BODY),
            len(EVIDENCE_BODY),
            "adversarial",
            "Origin confusion",
            evidence_authority,
        )
    with direct_vm.expect_revert("invalid canonical HTTPS origin"):
        contract.register_source_authority("https://127.0.0.1", POLICY, "private")
    with direct_vm.expect_revert("invalid canonical HTTPS origin"):
        contract.register_source_authority("https://authority.local", POLICY, "local")
    contract.revoke_source_authority(evidence_authority)
    with direct_vm.prank("0x" + "f" * 40):
        with direct_vm.expect_revert("authority is not active"):
            contract.register_evidence(
                EVIDENCE_URI,
                digest(EVIDENCE_BODY),
                len(EVIDENCE_BODY),
                "adversarial",
                "Revoked authority reuse",
                evidence_authority,
            )


def test_authority_origin_cannot_be_registered_as_two_independent_authorities(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    first = authority(contract, direct_vm, EVIDENCE_ORIGIN, "unique-origin-1")
    assert first
    with direct_vm.prank("0x" + "b" * 40):
        with direct_vm.expect_revert("authority origin already registered"):
            contract.register_source_authority(EVIDENCE_ORIGIN, POLICY, "unique-origin-2")


def test_case_id_and_notice_identity_are_locked_on_reassessment(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "case-lock-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "case-lock-n")
    evidence_id = evidence(contract, ea)
    notice = b"locked notice"
    case_id = open_case(contract, evidence_id, na, body=notice)
    direct_vm.mock_web(re.escape(EVIDENCE_URI), {"status": 200, "body": EVIDENCE_BODY})
    direct_vm.mock_web(re.escape(NOTICE_URI), {"status": 200, "body": notice})
    direct_vm.mock_llm(r"PALINODE semantic adjudicator", json.dumps(immaterial()))
    contract.assess_revocation(case_id)
    locked = contract.get_revocation_case(case_id)
    assert locked["case_id"] == case_id
    assert locked["notice_uri"] == NOTICE_URI
    assert locked["notice_sha256"] == digest(notice)
    assert locked["target_evidence_id"] == evidence_id
    with direct_vm.expect_revert("case is not assessable"):
        contract.assess_revocation(case_id)


def test_cross_case_severity_is_monotonic_and_order_safe(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "composition-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "composition-n")
    evidence_id = evidence(contract, ea)
    first_body = b"material notice"
    first = open_case(contract, evidence_id, na, body=first_body)
    semantic_sources(direct_vm, EVIDENCE_URI, NOTICE_URI, first_body, material())
    contract.assess_revocation(first)
    assert contract.get_node_record(evidence_id)["status"] == "INVALIDATED"

    second_body = b"immaterial later notice"
    second = open_case(contract, evidence_id, na, uri=NOTICE_ORIGIN + "/n-2", body=second_body)
    direct_vm.clear_mocks()
    semantic_sources(direct_vm, EVIDENCE_URI, NOTICE_ORIGIN + "/n-2", second_body, immaterial())
    contract.assess_revocation(second)
    assert contract.get_node_record(evidence_id)["status"] == "INVALIDATED"

    third_body = b"question notice"
    third = open_case(contract, evidence_id, na, uri=NOTICE_ORIGIN + "/n-3", body=third_body)
    direct_vm.clear_mocks()
    semantic_sources(direct_vm, EVIDENCE_URI, NOTICE_ORIGIN + "/n-3", third_body, material("QUESTION"))
    contract.assess_revocation(third)
    assert contract.get_node_record(evidence_id)["status"] == "INVALIDATED"
    assert contract.get_revocation_case(first)["case_status"] == "COMPLETE"
    assert contract.get_revocation_case(second)["case_status"] == "COMPLETE"


def test_overlapping_case_queues_are_isolated_when_both_touch_same_descendant(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "queue-isolation-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "queue-isolation-n")
    root = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/queue-isolation")
    child = contract.register_claim("queue", "Shared descendant")
    contract.register_dependency(root, child, "REQUIRES")
    first_body = b"first queued notice"
    first = open_case(contract, root, na, uri=NOTICE_ORIGIN + "/queue-1", body=first_body)
    semantic_sources(direct_vm, EVIDENCE_ORIGIN + "/queue-isolation", NOTICE_ORIGIN + "/queue-1", first_body, material("QUESTION"))
    contract.assess_revocation(first)
    second_body = b"second queued notice"
    second = open_case(contract, root, na, uri=NOTICE_ORIGIN + "/queue-2", body=second_body)
    direct_vm.clear_mocks()
    semantic_sources(direct_vm, EVIDENCE_ORIGIN + "/queue-isolation", NOTICE_ORIGIN + "/queue-2", second_body, material("INVALIDATE"))
    contract.assess_revocation(second)
    contract.process_impact(second, 1)
    assert contract.get_node_record(child)["status"] == "QUARANTINED"
    contract._apply_impact_status(child, "UNDER_REVIEW", "DIRECT_LOWER_SEVERITY", second)
    assert contract.get_node_record(child)["status"] == "QUARANTINED"
    third_body = b"third lower severity notice"
    third = open_case(contract, root, na, uri=NOTICE_ORIGIN + "/queue-3", body=third_body)
    direct_vm.clear_mocks()
    semantic_sources(direct_vm, EVIDENCE_ORIGIN + "/queue-isolation", NOTICE_ORIGIN + "/queue-3", third_body, material("QUESTION"))
    contract.assess_revocation(third)
    contract.process_impact(third, 1)
    assert contract.get_node_record(child)["status"] == "QUARANTINED"


def test_one_case_converging_paths_keep_the_stronger_effect(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "converging-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "converging-n")
    root = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/converging-root")
    first_path = contract.register_claim("converging", "First path")
    second_path = contract.register_claim("converging", "Second path")
    descendant = contract.register_claim("converging", "Converging descendant")
    contract.register_dependency(root, first_path, "SUPPORTS")
    contract.register_dependency(root, second_path, "REQUIRES")
    contract.register_dependency(first_path, descendant, "SUPPORTS")
    contract.register_dependency(second_path, descendant, "REQUIRES")
    body = b"converging material notice"
    case_id = open_case(contract, root, na, uri=NOTICE_ORIGIN + "/converging", body=body)
    semantic_sources(direct_vm, EVIDENCE_ORIGIN + "/converging-root", NOTICE_ORIGIN + "/converging", body, material("INVALIDATE"))
    contract.assess_revocation(case_id)
    contract.process_impact(case_id, 32)
    assert contract.get_node_record(descendant)["status"] == "QUARANTINED"


def test_revoked_authority_cannot_reactivate_through_rotation(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = authority(contract, direct_vm, EVIDENCE_ORIGIN, "revoked-rotation")
    contract.revoke_source_authority(authority_id)
    with direct_vm.expect_revert("authority is not active"):
        contract.rotate_source_authority(authority_id, "attempt-after-revoke")


def test_immaterial_case_cannot_change_root_effect_even_if_internal_commit_is_malformed(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "immaterial-guard-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "immaterial-guard-n")
    root = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/immaterial-guard")
    case_id = open_case(contract, root, na, uri=NOTICE_ORIGIN + "/immaterial-guard")
    malformed = {
        "result_status": "CONCLUSIVE",
        "change_authentic": False,
        "same_subject": True,
        "original_evidence_affected": False,
        "materiality": "IMMATERIAL",
        "root_effect": "INVALIDATE",
        "reason_code": "NO_AUTHENTIC_CHANGE",
    }
    with direct_vm.expect_revert("immaterial result cannot change state"):
        contract._commit_semantic_result(case_id, malformed)
    unsupported = dict(malformed)
    unsupported["materiality"] = "UNSUPPORTED"
    with direct_vm.expect_revert("unsupported materiality"):
        contract._commit_semantic_result(case_id, unsupported)


def test_semantic_schema_rejects_markdown_missing_fields_wrong_types_and_enums(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    valid = material()
    invalid_candidates = [
        "```json\n" + json.dumps(valid) + "\n```",
        {key: value for key, value in valid.items() if key != "reason_code"},
        dict(valid, materiality="material"),
        dict(valid, change_authentic="true"),
        dict(valid, root_effect=None),
        dict(valid, unsupported="extra"),
    ]
    for candidate in invalid_candidates:
        assert contract._validate_semantic_result(candidate) is False


@pytest.mark.parametrize(
    ("relationship", "question_status", "invalidate_status"),
    [
        ("SUPPORTS", "QUESTIONED", "QUESTIONED"),
        ("REQUIRES", "UNDER_REVIEW", "QUARANTINED"),
        ("DERIVED_FROM", "UNDER_REVIEW", "UNDER_REVIEW"),
        ("QUALIFIES", "QUESTIONED", "QUESTIONED"),
        ("AUTHORIZES", "UNDER_REVIEW", "QUARANTINED"),
        ("CORROBORATES", "ACTIVE", "ACTIVE"),
        ("CONTRADICTS", "ACTIVE", "ACTIVE"),
    ],
)
def test_every_relationship_has_explicit_question_and_invalidate_semantics(
    direct_vm, direct_deploy, relationship, question_status, invalidate_status
):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "relation-" + relationship.lower())
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "notice-" + relationship.lower())
    root = evidence(contract, ea)
    child = contract.register_claim("relation", relationship + " child")
    contract.register_dependency(root, child, relationship)
    body = (relationship + " question").encode()
    case_id = open_case(contract, root, na, body=body)
    semantic_sources(direct_vm, EVIDENCE_URI, NOTICE_URI, body, material("QUESTION"))
    contract.assess_revocation(case_id)
    contract.process_impact(case_id, 32)
    assert contract.get_node_record(child)["status"] == question_status

    root2 = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/" + relationship.lower() + "-2")
    child2 = contract.register_claim("relation", relationship + " invalidate child")
    contract.register_dependency(root2, child2, relationship)
    body2 = (relationship + " invalidate").encode()
    case2 = open_case(contract, root2, na, uri=NOTICE_ORIGIN + "/" + relationship.lower() + "-2", body=body2)
    direct_vm.clear_mocks()
    semantic_sources(direct_vm, EVIDENCE_ORIGIN + "/" + relationship.lower() + "-2", NOTICE_ORIGIN + "/" + relationship.lower() + "-2", body2, material("INVALIDATE"))
    contract.assess_revocation(case2)
    contract.process_impact(case2, 32)
    assert contract.get_node_record(child2)["status"] == invalidate_status


def test_status_and_assessment_history_are_bounded_but_liveness_is_not_limited_to_sixteen(
    direct_vm, direct_deploy
):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    node_id = contract.register_claim("history", "Bounded history")
    for _ in range(24):
        contract._transition_node(node_id, "QUESTIONED", "TEST", "")
        contract._transition_node(node_id, "ACTIVE", "TEST", "")
    status_history = contract.get_status_history(node_id)
    assert int(status_history["total_count"]) == 48
    assert int(status_history["recent_count"]) == 16

    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "assessment-history-e")
    evidence_id = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/history-e")
    for _ in range(12):
        contract._transition_assessment(evidence_id, "PENDING", "")
        contract._transition_assessment(evidence_id, "INCONCLUSIVE", "")
    assessment_history = contract.get_assessment_history(evidence_id)
    assert int(assessment_history["total_count"]) == 24
    assert int(assessment_history["recent_count"]) == 16


def test_retry_telemetry_is_bounded_and_retryable_failures_do_not_consume_semantic_budget(
    direct_vm, direct_deploy
):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "retry-bound-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "retry-bound-n")
    evidence_id = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/retry-bound")
    notice = b"retry bounded notice"
    case_id = open_case(contract, evidence_id, na, uri=NOTICE_ORIGIN + "/retry-bound", body=notice)
    direct_vm.strict_mocks = True
    for _ in range(12):
        contract.assess_revocation(case_id)
        contract.retry_revocation_case(case_id, "", "")
    telemetry = contract.get_retry_telemetry(case_id)
    assert int(telemetry["total_count"]) == 24
    assert int(telemetry["recent_count"]) == 8
    assert contract.get_revocation_case(case_id)["assessment_count"] == "0"


def test_mirror_identity_digest_length_and_missing_target_guards(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "mirror-guards")
    evidence_id = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/mirror-guards")
    wrong_digest_uri = "https://mirror-one.example/e"
    direct_vm.mock_web(re.escape(wrong_digest_uri), {"status": 200, "body": b"X" * len(EVIDENCE_BODY)})
    with direct_vm.expect_revert("mirror content does not match locked evidence identity"):
        contract.add_evidence_mirror(evidence_id, wrong_digest_uri)
    missing_id = "f" * 64
    with direct_vm.expect_revert("node does not exist"):
        contract.add_evidence_mirror(missing_id, wrong_digest_uri)
    with direct_vm.expect_revert("invalid HTTPS mirror URI"):
        contract.add_evidence_mirror(evidence_id, "https://user:pass@mirror.example/e")
    wrong_length_uri = "https://mirror-two.example/e"
    direct_vm.mock_web(re.escape(wrong_length_uri), {"status": 200, "body": EVIDENCE_BODY})
    wrong_length_id = contract.register_evidence(
        EVIDENCE_ORIGIN + "/wrong-length",
        digest(EVIDENCE_BODY),
        len(EVIDENCE_BODY) + 1,
        "adversarial",
        "Wrong length",
        ea,
    )
    with direct_vm.expect_revert("mirror content does not match locked evidence identity"):
        contract.add_evidence_mirror(wrong_length_id, wrong_length_uri)


def test_duplicate_edges_and_forward_order_are_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    parent = contract.register_claim("edges", "Parent")
    child = contract.register_claim("edges", "Child")
    contract.register_dependency(parent, child, "SUPPORTS")
    with direct_vm.expect_revert("duplicate dependency"):
        contract.register_dependency(parent, child, "SUPPORTS")
    with direct_vm.expect_revert("edge must point from earlier node to later node"):
        contract.register_dependency(child, parent, "SUPPORTS")


def test_forged_mirror_id_cannot_substitute_retrieval_location(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    ea = authority(contract, direct_vm, EVIDENCE_ORIGIN, "forged-mirror-e")
    na = authority(contract, direct_vm, NOTICE_ORIGIN, "forged-mirror-n")
    evidence_id = evidence(contract, ea, uri=EVIDENCE_ORIGIN + "/forged-mirror")
    valid_mirror_uri = "https://independent-mirror.example/forged-mirror"
    direct_vm.mock_web(re.escape(valid_mirror_uri), {"status": 200, "body": EVIDENCE_BODY})
    contract.add_evidence_mirror(evidence_id, valid_mirror_uri)
    notice = b"forged mirror notice"
    case_id = open_case(contract, evidence_id, na, uri=NOTICE_ORIGIN + "/forged-mirror", body=notice)
    direct_vm.clear_mocks()
    direct_vm.strict_mocks = True
    contract.assess_revocation(case_id)
    forged = "a" * 64
    with direct_vm.expect_revert("mirror is not verified"):
        contract.retry_revocation_case(case_id, forged, "")
    with direct_vm.expect_revert("case does not exist"):
        contract.retry_revocation_case("a" * 64, "", "")
