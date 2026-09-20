import hashlib
import json
import re

import pytest


CONTRACT = "contracts/palinode.py"
AUTHORITY_POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def register_authority(contract, direct_vm, origin, nonce):
    sender = direct_vm.sender
    if isinstance(sender, bytes):
        sender = "0x" + sender.hex()
    else:
        sender = str(sender)
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
    direct_vm.mock_web(
        re.escape(origin + "/.well-known/palinode.json"),
        {"status": 200, "body": challenge},
    )
    return contract.register_source_authority(origin, AUTHORITY_POLICY, nonce)


def test_node_sequences_prove_dag_for_generated_forward_edges(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    authority_id = register_authority(
        contract, direct_vm, "https://evidence.example", "invariant-dag"
    )
    nodes = [
        contract.register_evidence(
            f"https://evidence.example/{index}",
            sha(f"evidence-{index}".encode()),
            len(f"evidence-{index}"),
            f"subject-{index}",
            f"Evidence {index}",
            authority_id,
        )
        for index in range(12)
    ]
    for index in range(1, len(nodes)):
        contract.register_dependency(nodes[index - 1], nodes[index], "DERIVED_FROM")
    records = [contract.get_node_record(node_id) for node_id in nodes]
    sequences = [int(record["creation_sequence"]) for record in records]
    assert sequences == sorted(sequences)
    for edge_id in contract.get_edge_ids():
        edge = contract.get_dependency_record(edge_id)
        parent_sequence = int(contract.get_node_record(edge["parent_node_id"])["creation_sequence"])
        child_sequence = int(contract.get_node_record(edge["child_node_id"])["creation_sequence"])
        assert parent_sequence < child_sequence


def test_canonical_ids_are_digest_shaped_and_not_frontend_supplied(direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    first = contract.register_claim("subject", "One")
    second = contract.register_claim("subject", "One")
    assert first != second
    assert len(first) == 64 and all(character in "0123456789abcdef" for character in first)
    assert len(second) == 64 and all(character in "0123456789abcdef" for character in second)
    assert contract.get_node_record(first)["node_id"] == first
    assert contract.get_node_record(second)["node_id"] == second


def test_status_machine_rejects_skips_and_allows_only_declared_edges(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    node_id = contract.register_claim("status", "Status node")
    with direct_vm.expect_revert("status transition is not allowed"):
        contract._transition_node(node_id, "REINSTATED", "TEST", "")
    contract._transition_node(node_id, "QUESTIONED", "TEST", "")
    with direct_vm.expect_revert("status transition is not allowed"):
        contract._transition_node(node_id, "REINSTATED", "TEST", "")
    contract._transition_node(node_id, "UNDER_REVIEW", "TEST", "")
    contract._transition_node(node_id, "QUARANTINED", "TEST", "")
    contract._transition_node(node_id, "REINSTATED", "TEST", "")
    assert contract.get_node_record(node_id)["status"] == "REINSTATED"


def test_status_labels_have_explicit_recovery_and_review_paths(direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    node_id = contract.register_claim("status-path", "Status path")
    contract._transition_node(node_id, "QUESTIONED", "TEST", "")
    contract._transition_node(node_id, "INCONCLUSIVE", "TEST", "")
    contract._transition_node(node_id, "UNDER_REVIEW", "TEST", "")
    contract._transition_node(node_id, "QUARANTINED", "TEST", "")
    contract._transition_node(node_id, "REINSTATED", "TEST", "")
    contract._transition_node(node_id, "SUPERSEDED", "TEST", "")
    contract._transition_node(node_id, "INVALIDATED", "TEST", "")
    assert contract.get_node_record(node_id)["status"] == "INVALIDATED"


def test_case_queue_is_scoped_and_cursor_is_monotonic(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    evidence_authority = register_authority(
        contract, direct_vm, "https://evidence.example", "invariant-queue-e"
    )
    notice_authority = register_authority(
        contract, direct_vm, "https://notice.example", "invariant-queue-n"
    )
    body = b"evidence"
    notice = b"notice"
    evidence_id = contract.register_evidence(
        "https://evidence.example/queue",
        sha(body),
        len(body),
        "queue",
        "Queue evidence",
        evidence_authority,
    )
    child = contract.register_claim("queue", "Queue child")
    contract.register_dependency(evidence_id, child, "REQUIRES")
    case_id = contract.open_revocation_case(
        evidence_id,
        notice_authority,
        "https://notice.example/queue",
        sha(notice),
        len(notice),
        "CHANGED",
        "queue",
    )
    direct_vm.mock_web(r"evidence\.example/queue", {"status": 200, "body": body})
    direct_vm.mock_web(r"notice\.example/queue", {"status": 200, "body": notice})
    direct_vm.mock_llm(
        r"PALINODE semantic adjudicator",
        '{"change_authentic":true,"same_subject":true,"original_evidence_affected":true,'
        '"materiality":"MATERIAL","root_effect":"INVALIDATE",'
        '"reason_code":"MATERIAL_CORRECTION"}',
    )
    contract.assess_revocation(case_id)
    before = contract.get_impact_queue_state(case_id)
    assert before["cursor"] == "0"
    contract.process_impact(case_id, 1)
    after = contract.get_impact_queue_state(case_id)
    assert int(after["cursor"]) > int(before["cursor"])
    assert int(after["processed_steps"]) == 1
