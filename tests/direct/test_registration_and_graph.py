import hashlib
import json
import os
import re

import pytest


CONTRACT = os.environ.get("PALINODE_CONTRACT", "contracts/palinode.py")
EVIDENCE_URI = "https://evidence.example/e-1"
EVIDENCE_ORIGIN = "https://evidence.example"
AUTHORITY_POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def register_authority(contract, direct_vm, origin, nonce):
    sender = direct_vm.sender
    if isinstance(sender, bytes):
        sender = "0x" + sender.hex()
    else:
        sender = str(sender)
    challenge_uri = origin + "/.well-known/palinode.json"
    challenge = json.dumps(
        {
            "palinode": "1",
            "authority_address": sender,
            "canonical_origin": origin,
            "nonce": nonce,
            "verification_policy": AUTHORITY_POLICY,
        },
        separators=(",", ":"),
    ).encode()
    direct_vm.mock_web(re.escape(challenge_uri), {"status": 200, "body": challenge})
    return contract.register_source_authority(origin, AUTHORITY_POLICY, nonce)


def evidence(contract, authority_id, uri=EVIDENCE_URI, body=b"registered evidence", subject="case-1", title="Evidence"):
    return contract.register_evidence(uri, digest(body), len(body), subject, title, authority_id)


def test_registers_all_node_types_and_exposes_immutable_metadata(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "registration-1")
    evidence_id = evidence(contract, authority_id)
    claim_id = contract.register_claim("case-1", "Claim")
    decision_id = contract.register_decision("case-1", "Decision")
    attestation_id = contract.register_attestation("case-1", "Attestation")
    authorization_id = contract.register_authorization("case-1", "Authorization")

    records = [contract.get_node_record(node_id) for node_id in (
        evidence_id,
        claim_id,
        decision_id,
        attestation_id,
        authorization_id,
    )]
    assert [record["node_type"] for record in records] == [
        "EVIDENCE",
        "CLAIM",
        "DECISION",
        "ATTESTATION",
        "AUTHORIZATION",
    ]
    assert records[0]["content_sha256"] == digest(b"registered evidence")
    assert records[0]["byte_length"] == "19"
    assert records[0]["historical_validity"] == "HISTORICAL_ACCEPTED"
    assert all(record["status"] == "ACTIVE" for record in records)
    assert records[0]["assessment_status"] == "UNASSESSED"
    assert all(record["assessment_status"] == "UNASSESSED" for record in records)
    assert len(set(contract.get_node_ids())) == 5


def test_duplicate_and_malformed_registration_reverts(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "registration-2")
    evidence(contract, authority_id)
    with direct_vm.expect_revert("duplicate evidence identity"):
        evidence(contract, authority_id)
    with direct_vm.expect_revert("invalid HTTPS URI"):
        contract.register_evidence(
            "http://evidence.example/e-2",
            digest(b"other"),
            5,
            "case-2",
            "Other",
            authority_id,
        )
    with direct_vm.expect_revert("invalid content SHA-256"):
        contract.register_evidence(
            "https://evidence.example/e-2",
            "not-a-digest",
            5,
            "case-2",
            "Other",
            authority_id,
        )
    with direct_vm.expect_revert("evidence byte length must be non-zero"):
        contract.register_evidence(
            "https://evidence.example/e-2",
            digest(b""),
            0,
            "case-2",
            "Other",
            authority_id,
        )
    with direct_vm.expect_revert("invalid subject identifier"):
        contract.register_claim("bad subject", "Claim")
    with direct_vm.expect_revert("unsupported node type"):
        contract.register_node("UNSUPPORTED", "case-2", "Bad")


def test_every_edge_type_is_supported_and_duplicate_edges_are_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "registration-3")
    parent = evidence(contract, authority_id)
    children = [contract.register_claim("case-1", f"Child {index}") for index in range(7)]
    relationships = (
        "SUPPORTS",
        "REQUIRES",
        "DERIVED_FROM",
        "QUALIFIES",
        "AUTHORIZES",
        "CORROBORATES",
        "CONTRADICTS",
    )
    edge_ids = [
        contract.register_dependency(parent, child, relationship)
        for child, relationship in zip(children, relationships)
    ]
    assert len(edge_ids) == 7
    assert all(contract.get_dependency_record(edge_id)["active"] == "True" for edge_id in edge_ids)
    with direct_vm.expect_revert("duplicate dependency"):
        contract.register_dependency(parent, children[0], "SUPPORTS")


def test_self_dependency_ordering_and_cycle_attempts_fail(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "registration-4")
    first = evidence(contract, authority_id)
    second = contract.register_claim("case-1", "Second")
    third = contract.register_decision("case-1", "Third")
    contract.register_dependency(first, second, "SUPPORTS")
    contract.register_dependency(second, third, "REQUIRES")
    with direct_vm.expect_revert("self-dependency is forbidden"):
        contract.register_dependency(second, second, "SUPPORTS")
    with direct_vm.expect_revert("edge must point from earlier node to later node"):
        contract.register_dependency(third, first, "CONTRADICTS")
    # A would-be cycle is rejected by the same creation-order proof.
    with direct_vm.expect_revert("edge must point from earlier node to later node"):
        contract.register_dependency(third, second, "DERIVED_FROM")
    with direct_vm.expect_revert("unsupported dependency type"):
        contract.register_dependency(first, third, "ARBITRARY")


def test_lineage_preserves_old_evidence_and_marks_successor(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(contract, direct_vm, EVIDENCE_ORIGIN, "registration-5")
    old_body = b"old evidence"
    new_body = b"replacement evidence"
    old_id = evidence(contract, authority_id, body=old_body, title="Old")
    new_id = evidence(
        contract,
        uri="https://evidence.example/e-2",
        body=new_body,
        title="Replacement",
        authority_id=authority_id,
    )
    contract.link_evidence_successor(old_id, new_id)
    assert contract.get_node_record(old_id)["status"] == "SUPERSEDED"
    assert contract.get_node_record(old_id)["content_sha256"] == digest(old_body)
    assert contract.get_node_record(new_id)["status"] == "ACTIVE"
    with direct_vm.expect_revert("successor already recorded"):
        contract.link_evidence_successor(old_id, new_id)


def test_no_owner_or_arbitrary_status_setter_is_exposed(direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    assert not hasattr(contract, "set_node_status")
    assert not hasattr(contract, "override_verdict")
    assert not hasattr(contract, "delete_node")
import os
