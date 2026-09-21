"""One-shot PALINODE V4 Studionet deployment and live review proof.

This runner is intentionally separate from the archived canary runner.  It is
hard-bound to contracts/palinode_v2.py and to the sealed release commit.  A
submitted transaction ID is persisted before polling and is never resubmitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant


ROOT = Path(__file__).resolve().parents[1]
RPC_URL = "https://studio.genlayer.com/api"
CHAIN_ID = 61999
EXPECTED_HEAD = "14bb4574a8d248c978b55ff1fb70f32c0293f313"
EXPECTED_SOURCE_SHA256 = "0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601"
SOURCE_PATH = ROOT / "contracts" / "palinode_v2.py"
ARCHIVED_SOURCE_PATH = ROOT / "contracts" / "palinode.py"
EVIDENCE_DIR = ROOT / "evidence" / "studionet" / "v4"
STATE_PATH = EVIDENCE_DIR / "transactions.json"
FIXTURE_URL = "https://palinode-fixture.vercel.app"
FIXTURE_ORIGIN = FIXTURE_URL
FIXTURE_NONCE = "PALINODE_FIXTURE_NONCE_V1"
FIXTURE_POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
POLL_SECONDS = 5
MAX_POLLS = 240
MAX_IMPACT_STEPS = 32

ARTIFACTS = {
    "v1": {
        "uri": FIXTURE_URL + "/evidence/vendor-audit-v1.json",
        "sha256": "29084e2b0430225ef85d81da3422c0b4a7bdfdf0357845eaec7e1ac0df45e5c2",
        "byte_length": 241,
    },
    "v2": {
        "uri": FIXTURE_URL + "/evidence/vendor-audit-v2.json",
        "sha256": "c005ac1d5de56b14cb95fbacf6ecddc81386846a3df5bd5a3e28f0498b509ab3",
        "byte_length": 328,
    },
    "revocation": {
        "uri": FIXTURE_URL + "/notices/vendor-audit-v1-revoked.json",
        "sha256": "0a735d8344897f0406bf84f2bd62b9bae55898d0e45ca670a001597a6a53492f",
        "byte_length": 278,
    },
    "correction": {
        "uri": FIXTURE_URL + "/notices/vendor-audit-v1-correction.json",
        "sha256": "43110fe3ce4dc9d5b2158c0892758559c21903ef9e50731b8b6cabdb8aca6212",
        "byte_length": 326,
    },
}

_STATE: dict[str, Any] = {}
_CONTRACT_ADDRESS = ""


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump())
    if hasattr(value, "dict"):
        return jsonable(value.dict())
    if hasattr(value, "value"):
        return jsonable(value.value)
    if hasattr(value, "__dict__"):
        return jsonable(vars(value))
    return str(value)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_private_key() -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("PALINODE_DEPLOYER_PRIVATE_KEY="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    raise RuntimeError("PALINODE_DEPLOYER_PRIVATE_KEY is not configured")


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def source_lock() -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    committed = subprocess.check_output(["git", "show", f"{head}:contracts/palinode_v2.py"], cwd=ROOT)
    working = SOURCE_PATH.read_bytes()
    committed_hash = hashlib.sha256(committed).hexdigest()
    working_hash = hashlib.sha256(working).hexdigest()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"source lock HEAD mismatch: {head}")
    if committed_hash != EXPECTED_SOURCE_SHA256 or working_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source lock hash mismatch: committed={committed_hash} working={working_hash}")
    if committed != working or working == ARCHIVED_SOURCE_PATH.read_bytes():
        raise RuntimeError("V2 source parity or archived-source distinction failed")
    return {
        "deployment_source_path": "contracts/palinode_v2.py",
        "deployment_source_commit": head,
        "deployment_source_sha256": working_hash,
        "committed_sha256": committed_hash,
        "archived_source_path": "contracts/palinode.py",
        "archived_source_is_deployment_source": False,
        "source_parity": "PASS",
    }


def artifact_counts() -> dict[str, int]:
    schema = json.loads((ROOT / "artifacts" / "palinode_schema.json").read_text(encoding="utf-8"))
    methods = schema["methods"]
    writes = sum(1 for item in methods.values() if not bool(item.get("readonly")))
    views = sum(1 for item in methods.values() if bool(item.get("readonly")))
    counts = {"total": len(methods), "writes": writes, "views": views}
    if counts != {"total": 46, "writes": 21, "views": 25}:
        raise RuntimeError(f"unexpected V2 API counts: {counts}")
    return counts


def initial_state() -> dict[str, Any]:
    return {
        "network": "studionet",
        "rpc_url": RPC_URL,
        "chain_id": CHAIN_ID,
        "deployment_source_path": "contracts/palinode_v2.py",
        "deployment_source_commit": EXPECTED_HEAD,
        "deployment_source_sha256": EXPECTED_SOURCE_SHA256,
        "deployment_tx_id": None,
        "contract_address": None,
        "transactions": [],
        "resubmissions": 0,
    }


def save_state() -> None:
    write_json(STATE_PATH, _STATE)


def transaction_status(transaction: dict[str, Any]) -> tuple[str, str]:
    status = transaction.get("status_name", transaction.get("status", "UNDETERMINED"))
    execution = transaction.get("tx_execution_result_name", transaction.get("execution_result", "NOT_VOTED"))
    return str(status).upper(), str(execution).upper()


def tx_snapshot(client: Any, tx_id: str) -> dict[str, Any]:
    tx = jsonable(client.get_transaction(transaction_hash=tx_id))
    if not isinstance(tx, dict):
        tx = {"raw": tx}
    status, execution = transaction_status(tx)
    if execution == "NOT_VOTED":
        validators = ((tx.get("consensus_data") or {}).get("validators") or [])
        results = [
            str(item.get("execution_result", "")).upper()
            for item in validators
            if isinstance(item, dict) and str(item.get("vote", "")).lower() == "agree"
        ]
        if results and all(item == "SUCCESS" for item in results):
            execution = "FINISHED_WITH_RETURN"
        elif results and any(item == "ERROR" for item in results):
            execution = "FINISHED_WITH_ERROR"
    return {
        "status": status,
        "execution_result": execution,
        "result": tx.get("result_name", tx.get("result")),
        "tx_id": tx.get("tx_id", tx_id),
        "tx_data_decoded": tx.get("tx_data_decoded"),
        "contract_address": (tx.get("data") or {}).get("contract_address"),
        "raw": tx,
    }


def finalize_if_ready(client: Any, account: Any, tx_id: str, record: dict[str, Any]) -> None:
    if record.get("finalization_action_tx_id"):
        return
    main = client.w3.eth.contract(
        address=client.chain.consensus_main_contract["address"],
        abi=client.chain.consensus_main_contract["abi"],
    )
    nonce = client.get_current_nonce(account.address, "pending")
    tx = main.functions.finalizeTransaction(tx_id).build_transaction(
        {"from": account.address, "nonce": nonce, "chainId": CHAIN_ID, "gas": 500_000, "gasPrice": 0, "value": 0}
    )
    signed = account.sign_transaction(tx)
    action_tx_id = client.w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    record["finalization_action_tx_id"] = action_tx_id
    record["finalization_action"] = "finalizeTransaction"
    save_state()
    client.w3.eth.wait_for_transaction_receipt(action_tx_id)


def wait_final(client: Any, account: Any, tx_id: str, record: dict[str, Any], expect_success: bool) -> dict[str, Any]:
    for _ in range(MAX_POLLS):
        snapshot = tx_snapshot(client, tx_id)
        record["last_observation"] = snapshot
        if snapshot["status"] == "READY_TO_FINALIZE":
            finalize_if_ready(client, account, tx_id, record)
        if snapshot["status"] == "FINALIZED":
            record["final_status"] = snapshot["status"]
            record["execution_result"] = snapshot["execution_result"]
            record["application_success"] = snapshot["execution_result"] == "FINISHED_WITH_RETURN"
            save_state()
            if expect_success and not record["application_success"]:
                raise RuntimeError(f"{record['label']} finalized with {snapshot['execution_result']}")
            if not expect_success and record["application_success"]:
                raise RuntimeError(f"{record['label']} unexpectedly succeeded")
            return snapshot
        if snapshot["status"] in {"CANCELED", "UNDETERMINED", "LEADER_TIMEOUT", "VALIDATORS_TIMEOUT"}:
            record["terminal_status"] = snapshot["status"]
            save_state()
            if expect_success:
                raise RuntimeError(f"{record['label']} reached terminal status {snapshot['status']}")
            return snapshot
        save_state()
        time.sleep(POLL_SECONDS)
    record["poll_timeout"] = True
    save_state()
    raise TimeoutError(f"{record['label']} polling timed out; transaction {tx_id} remains persisted")


def existing_record(label: str) -> dict[str, Any] | None:
    for record in _STATE["transactions"]:
        if record.get("label") == label:
            return record
    return None


def submit(client: Any, account: Any, label: str, method: str, args: list[Any], expect_success: bool = True) -> dict[str, Any]:
    previous = existing_record(label)
    if previous is not None:
        if not previous.get("tx_id"):
            raise RuntimeError(f"persisted record {label} has no transaction ID")
        return wait_final(client, account, previous["tx_id"], previous, expect_success)
    tx_id = client.write_contract(address=_CONTRACT_ADDRESS, function_name=method, account=account, args=args)
    record = {"label": label, "method": method, "args": jsonable(args), "tx_id": tx_id, "resubmitted": False}
    _STATE["transactions"].append(record)
    save_state()
    return wait_final(client, account, tx_id, record, expect_success)


def submit_deployment(client: Any, account: Any) -> dict[str, Any]:
    if _STATE.get("deployment_tx_id"):
        raise RuntimeError("deployment transaction already exists; refusing any deployment resubmission")
    tx_id = client.deploy_contract(code=SOURCE_PATH.read_text(encoding="utf-8"), account=account)
    _STATE["deployment_tx_id"] = tx_id
    _STATE["deployment_source_sha256"] = source_sha256()
    _STATE["deployer_address"] = account.address
    record = {"label": "deployment", "method": "deploy_contract", "tx_id": tx_id, "resubmitted": False}
    _STATE["transactions"].append(record)
    save_state()
    snapshot = wait_final(client, account, tx_id, record, True)
    decoded = snapshot.get("tx_data_decoded") or {}
    address = snapshot.get("contract_address") or (decoded.get("contract_address") if isinstance(decoded, dict) else None)
    if not address:
        raise RuntimeError("finalized deployment did not expose contract_address")
    _STATE["contract_address"] = address
    save_state()
    return snapshot


def read_contract(client: Any, account: Any, method: str, args: list[Any]) -> Any:
    return jsonable(
        client.read_contract(
            address=_CONTRACT_ADDRESS,
            function_name=method,
            account=account,
            args=args,
            transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
        )
    )


def page(client: Any, account: Any, method: str) -> dict[str, Any]:
    return read_contract(client, account, method, [0, 64])


def newest_id(client: Any, account: Any, method: str) -> str:
    result = page(client, account, method)
    count = int(result["count"])
    if count == 0:
        raise RuntimeError(f"{method} returned no records")
    return result["slot_" + str(count - 1)]


def find_authority(client: Any, account: Any, origin: str) -> str:
    result = page(client, account, "get_authority_ids_page")
    for index in range(int(result["count"])):
        authority_id = result["slot_" + str(index)]
        if read_contract(client, account, "get_source_authority", [authority_id])["canonical_origin"] == origin:
            return authority_id
    raise RuntimeError("authority not found")


def find_node(client: Any, account: Any, node_type: str, title: str, source_uri: str = "") -> str:
    result = page(client, account, "get_node_ids_page")
    for index in range(int(result["count"])):
        node_id = result["slot_" + str(index)]
        record = read_contract(client, account, "get_node_record", [node_id])
        if record["node_type"] == node_type and record["title"] == title and (not source_uri or record["source_uri"] == source_uri):
            return node_id
    raise RuntimeError(f"node not found: {node_type} {title}")


def find_edge(client: Any, account: Any, parent: str, child: str, relationship: str) -> str:
    result = page(client, account, "get_edge_ids_page")
    for index in range(int(result["count"])):
        edge_id = result["slot_" + str(index)]
        record = read_contract(client, account, "get_dependency_record", [edge_id])
        if record["parent_node_id"] == parent and record["child_node_id"] == child and record["relationship"] == relationship:
            return edge_id
    raise RuntimeError("edge not found")


def find_case(client: Any, account: Any, target: str, notice_uri: str) -> str:
    result = page(client, account, "get_case_ids_page")
    for index in range(int(result["count"])):
        case_id = result["slot_" + str(index)]
        record = read_contract(client, account, "get_revocation_case", [case_id])
        if record["target_evidence_id"] == target and record["notice_uri"] == notice_uri:
            return case_id
    raise RuntimeError("case not found")


def find_recovery(client: Any, account: Any, affected: str, successor: str, adverse: str) -> str:
    result = page(client, account, "get_recovery_ids_page")
    for index in range(int(result["count"])):
        recovery_id = result["slot_" + str(index)]
        record = read_contract(client, account, "get_recovery_case", [recovery_id])
        if record["affected_node_id"] == affected and record["successor_evidence_id"] == successor and record["adverse_case_id"] == adverse:
            return recovery_id
    raise RuntimeError("recovery not found")


def error_result(error: Exception) -> dict[str, Any]:
    return {"error_type": type(error).__name__, "error": str(error)}


def attempt_expected_failure(client: Any, account: Any, label: str, method: str, args: list[Any]) -> dict[str, Any]:
    try:
        snapshot = submit(client, account, label, method, args, expect_success=False)
        return {"expected_rejection": True, "snapshot": snapshot}
    except Exception as error:
        return {"expected_rejection": False, **error_result(error)}


def process_impact(client: Any, account: Any, case_id: str, prefix: str) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index in range(128):
        queue = read_contract(client, account, "get_impact_queue_state", [case_id])
        observations.append(queue)
        if queue["case_status"] == "COMPLETE":
            return observations
        submit(client, account, f"{prefix}_{index}", "process_impact", [case_id, MAX_IMPACT_STEPS])
    raise RuntimeError(f"impact queue did not complete for {case_id}")


def process_recovery(client: Any, account: Any, recovery_id: str) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index in range(128):
        queue = read_contract(client, account, "get_recovery_queue_state", [recovery_id])
        observations.append(queue)
        if queue["case_status"] == "COMPLETE":
            return observations
        submit(client, account, f"recovery_impact_{recovery_id}_{index}", "process_recovery_impact", [recovery_id, MAX_IMPACT_STEPS])
    raise RuntimeError(f"recovery queue did not complete for {recovery_id}")


def probe_third_party_fixture() -> dict[str, Any]:
    candidates = [
        FIXTURE_URL + "/third-party/.well-known/palinode.json",
        FIXTURE_URL + "/challenge/.well-known/palinode.json",
        FIXTURE_URL + "/authority-c/.well-known/palinode.json",
    ]
    observations = []
    for uri in candidates:
        try:
            response = requests.get(uri, timeout=20)
            observations.append({"uri": uri, "status": response.status_code, "byte_length": len(response.content)})
        except Exception as error:
            observations.append({"uri": uri, **error_result(error)})
    return {
        "live_status": "BLOCKED_NO_SEPARATE_AUTHORITY_DECLARATION",
        "third_party_authority_id": None,
        "probe": observations,
        "reason": "The controlled public fixture exposes only Authority A's declaration; no deployer/fixture credential for an Authority C origin is available. No fake unrelated authority was created.",
        "local_standing_regression": "tests/v2/test_reviewer_remediation.py::test_unrelated_authority_cannot_impersonate_publisher_withdrawal",
    }


def probe_mutable_fixture() -> dict[str, Any]:
    uri = FIXTURE_URL + "/reviewer/mutable-evidence-v4.txt"
    try:
        response = requests.get(uri, timeout=20)
        status = response.status_code
        size = len(response.content)
    except Exception as error:
        return {"live_status": "BLOCKED", "uri": uri, **error_result(error)}
    return {
        "live_status": "BLOCKED_NO_MUTABLE_FIXTURE" if status == 404 else "BLOCKED_NO_SAFE_MUTATION_AUTHORITY",
        "uri": uri,
        "probe_status": status,
        "probe_byte_length": size,
        "semantic_call_submitted": False,
        "semantic_call_prevented": True,
        "reason": "The dedicated mutable path is not published, and this run has no authorized fixture deployment/mutation credential. The live mismatch was not faked.",
        "local_regression": "tests/v2/test_reviewer_remediation.py::test_changed_evidence_bytes_short_circuit_semantic_execution",
    }


def resume_only(tx_id: str) -> None:
    account = create_account(read_private_key())
    client = create_client(chain=studionet, endpoint=RPC_URL, account=account)
    snapshot = tx_snapshot(client, tx_id)
    print(json.dumps({"transaction_id": tx_id, "resumed": True, "resubmissions": 0, "snapshot": snapshot}, sort_keys=True))


def run_v4() -> int:
    global _STATE, _CONTRACT_ADDRESS
    if EVIDENCE_DIR.exists():
        raise RuntimeError("evidence/studionet/v4 already exists; refusing an unreviewed second deployment run")
    lock = source_lock()
    counts = artifact_counts()
    account_a = create_account(read_private_key())
    account_b = create_account()
    account_x = create_account()
    client = create_client(chain=studionet, endpoint=RPC_URL, account=account_a)
    if client.chain_id != CHAIN_ID or client.w3.eth.chain_id != CHAIN_ID:
        raise RuntimeError(f"unexpected chain ID: client={client.chain_id} rpc={client.w3.eth.chain_id}")
    preflight = {
        "rpc_url": RPC_URL,
        "chain_id": CHAIN_ID,
        "client_chain_id": client.chain_id,
        "rpc_chain_id": client.w3.eth.chain_id,
        "deployer_address": account_a.address,
        "balance_wei_before": str(client.get_balance(account_a.address)),
        "latest_nonce": client.w3.eth.get_transaction_count(account_a.address, "latest"),
        "pending_nonce": client.w3.eth.get_transaction_count(account_a.address, "pending"),
        "gas_price": str(client.w3.eth.gas_price),
        "latest_block": client.w3.eth.block_number,
        "fee_behavior": "zero gas price; prior successful Studionet mechanism; no private key recorded",
    }
    _STATE = initial_state()
    _STATE.update({"deployer_address": account_a.address, "preflight": preflight})
    save_state()

    deployment_snapshot = submit_deployment(client, account_a)
    _CONTRACT_ADDRESS = _STATE["contract_address"]
    write_json(
        EVIDENCE_DIR / "deployment.json",
        {
            **preflight,
            "deployment_source_path": "contracts/palinode_v2.py",
            "deployment_source_commit": EXPECTED_HEAD,
            "deployment_source_sha256": EXPECTED_SOURCE_SHA256,
            "deployment_tx_id": _STATE["deployment_tx_id"],
            "contract_address": _CONTRACT_ADDRESS,
            "consensus_status": deployment_snapshot["status"],
            "execution_result": deployment_snapshot["execution_result"],
            "final_status": "FINALIZED_SUCCESS",
            "api_counts_expected": counts,
            "private_key_in_evidence": False,
        },
    )
    write_json(EVIDENCE_DIR / "source-parity.json", {**lock, "network": "studionet", "chain_id": CHAIN_ID, "contract_address": _CONTRACT_ADDRESS, "deployment_tx_id": _STATE["deployment_tx_id"]})

    write_json(
        EVIDENCE_DIR / "actors.json",
        {
            "AUTHORITY_A": {"address": account_a.address, "role": "fixture authority controller and deployer"},
            "DEPENDENT_B": {"address": account_b.address, "role": "child controller and independent dependent"},
            "ATTACKER_X": {"address": account_x.address, "role": "unauthorized graph/lineage attacker"},
            "private_keys_recorded": False,
        },
    )

    well_known = requests.get(FIXTURE_URL + "/.well-known/palinode.json", timeout=30)
    authority_tx = submit(client, account_a, "register_authority_a", "register_source_authority", [FIXTURE_ORIGIN, FIXTURE_POLICY, FIXTURE_NONCE])
    authority_id = find_authority(client, account_a, FIXTURE_ORIGIN)
    authority = read_contract(client, account_a, "get_source_authority", [authority_id])
    write_json(EVIDENCE_DIR / "authority.json", {"authority_id": authority_id, "authority": authority, "well_known_status": well_known.status_code, "well_known_sha256": hashlib.sha256(well_known.content).hexdigest(), "registration_tx_id": _STATE["deployment_tx_id"] if False else authority_tx.get("tx_id"), "expected_origin": FIXTURE_ORIGIN, "expected_controller": account_a.address, "expected_policy": FIXTURE_POLICY})

    v1_tx = submit(client, account_a, "register_evidence_v1", "register_evidence", [ARTIFACTS["v1"]["uri"], ARTIFACTS["v1"]["sha256"], ARTIFACTS["v1"]["byte_length"], "fixture-vendor-001", "Fictional audit V1", authority_id])
    v1_id = find_node(client, account_a, "EVIDENCE", "Fictional audit V1", ARTIFACTS["v1"]["uri"])
    auth_v1 = submit(client, account_a, "authenticate_evidence_v1", "authenticate_evidence", [v1_id])
    v1_record = read_contract(client, account_a, "get_node_record", [v1_id])
    if v1_record["authentication_status"] != "CLEARED" or v1_record["reliance_status"] != "ACTIVE":
        raise RuntimeError("V1 did not authenticate CLEARED with ACTIVE reliance")

    claim_tx = submit(client, account_b, "register_claim_c", "register_claim", ["fixture-vendor-001", "Claim depending on fictional audit V1"])
    claim_id = find_node(client, account_b, "CLAIM", "Claim depending on fictional audit V1")
    decision_tx = submit(client, account_b, "register_decision_d", "register_decision", ["fixture-vendor-001", "Decision depending on the claim"])
    decision_id = find_node(client, account_b, "DECISION", "Decision depending on the claim")
    edge1_tx = submit(client, account_b, "edge_v1_claim", "register_dependency", [v1_id, claim_id, "SUPPORTS"])
    edge1_id = find_edge(client, account_b, v1_id, claim_id, "SUPPORTS")
    edge2_tx = submit(client, account_b, "edge_claim_decision", "register_dependency", [claim_id, decision_id, "REQUIRES"])
    edge2_id = find_edge(client, account_b, claim_id, decision_id, "REQUIRES")
    edges = [read_contract(client, account_b, "get_dependency_record", [edge1_id]), read_contract(client, account_b, "get_dependency_record", [edge2_id])]
    write_json(EVIDENCE_DIR / "cross-party-dependency.json", {"authority_a": account_a.address, "dependent_b": account_b.address, "claim_id": claim_id, "decision_id": decision_id, "edges": edges, "edge_assertors": [edges[0]["assertor"], edges[1]["assertor"]], "expected_assertor": account_b.address, "transactions": [claim_tx, decision_tx, edge1_tx, edge2_tx], "result": "PASS" if all(e["assertor"].lower() == account_b.address.lower() for e in edges) else "FAIL"})

    edge_count_before = int(page(client, account_x, "get_edge_ids_page")["count"])
    child_before = read_contract(client, account_x, "get_node_record", [claim_id])
    unauthorized_dependency = attempt_expected_failure(client, account_x, "unauthorized_dependency_x", "register_dependency", [v1_id, claim_id, "SUPPORTS"])
    edge_count_after = int(page(client, account_x, "get_edge_ids_page")["count"])
    child_after = read_contract(client, account_x, "get_node_record", [claim_id])
    write_json(EVIDENCE_DIR / "unauthorized-dependency.json", {"attacker": account_x.address, "before_edge_count": edge_count_before, "after_edge_count": edge_count_after, "child_before": child_before, "child_after": child_after, "attempt": unauthorized_dependency, "result": "PASS" if unauthorized_dependency.get("expected_rejection") and edge_count_before == edge_count_after else "FAIL"})

    v2_tx = submit(client, account_a, "register_evidence_v2", "register_evidence", [ARTIFACTS["v2"]["uri"], ARTIFACTS["v2"]["sha256"], ARTIFACTS["v2"]["byte_length"], "fixture-vendor-001", "Fictional audit V2 corrected", authority_id])
    v2_id = find_node(client, account_a, "EVIDENCE", "Fictional audit V2 corrected", ARTIFACTS["v2"]["uri"])
    auth_v2 = submit(client, account_a, "authenticate_evidence_v2", "authenticate_evidence", [v2_id])
    v2_record = read_contract(client, account_a, "get_node_record", [v2_id])
    if v2_record["authentication_status"] != "CLEARED":
        raise RuntimeError("V2 did not authenticate CLEARED")
    v1_before_link = read_contract(client, account_a, "get_node_record", [v1_id])
    attacker_successor = attempt_expected_failure(client, account_x, "unauthorized_successor_x", "link_evidence_successor", [v1_id, v2_id])
    v1_after_attack = read_contract(client, account_a, "get_node_record", [v1_id])
    valid_link = submit(client, account_a, "valid_successor_link", "link_evidence_successor", [v1_id, v2_id])
    link_record = read_contract(client, account_a, "get_evidence_successor_link", [v1_id])
    v1_after_link = read_contract(client, account_a, "get_node_record", [v1_id])
    write_json(EVIDENCE_DIR / "unauthorized-successor.json", {"attacker": account_x.address, "v1_id": v1_id, "v2_id": v2_id, "attempt": attacker_successor, "v1_before": v1_before_link, "v1_after_attack": v1_after_attack, "valid_link_tx": valid_link, "link_record": link_record, "v1_after_valid_link": v1_after_link, "attacker_successor_absent_before_valid_link": attacker_successor.get("expected_rejection", False), "reliance_unchanged_by_link": v1_after_link["reliance_status"] == "ACTIVE", "result": "PASS" if attacker_successor.get("expected_rejection") and v1_after_link["reliance_status"] == "ACTIVE" else "FAIL"})

    u_tx = submit(client, account_a, "register_uncleared_u", "register_evidence", [ARTIFACTS["v2"]["uri"], ARTIFACTS["v2"]["sha256"], ARTIFACTS["v2"]["byte_length"], "fixture-vendor-001-u", "Uncleared U", authority_id])
    u_id = find_node(client, account_a, "EVIDENCE", "Uncleared U", ARTIFACTS["v2"]["uri"])
    u_case_tx = submit(client, account_b, "open_uncleared_case", "open_revocation_case", [u_id, authority_id, ARTIFACTS["revocation"]["uri"], ARTIFACTS["revocation"]["sha256"], ARTIFACTS["revocation"]["byte_length"], "WITHDRAWN", "Live non-cleared assessment guard"])
    u_case_id = find_case(client, account_b, u_id, ARTIFACTS["revocation"]["uri"])
    u_before_assess = read_contract(client, account_b, "get_revocation_case", [u_case_id])
    u_assess = attempt_expected_failure(client, account_b, "assess_uncleared_case", "assess_revocation", [u_case_id])
    u_after_assess = read_contract(client, account_b, "get_revocation_case", [u_case_id])
    u_record = read_contract(client, account_b, "get_node_record", [u_id])
    write_json(EVIDENCE_DIR / "non-cleared-revocation.json", {"evidence_id": u_id, "case_id": u_case_id, "registration_tx": u_tx, "case_open_tx": u_case_tx, "before_assessment": u_before_assess, "assessment_attempt": u_assess, "after_assessment": u_after_assess, "node_after_assessment": u_record, "result": "PASS" if u_record["authentication_status"] == "UNASSESSED" and u_record["reliance_status"] == "ACTIVE" and u_assess.get("expected_rejection") else "FAIL"})

    byte_mismatch = probe_mutable_fixture()
    write_json(EVIDENCE_DIR / "byte-mismatch.json", byte_mismatch)
    third_party = probe_third_party_fixture()
    write_json(EVIDENCE_DIR / "third-party-challenge.json", third_party)

    revocation_open_tx = submit(client, account_b, "open_material_revocation", "open_revocation_case", [v1_id, authority_id, ARTIFACTS["revocation"]["uri"], ARTIFACTS["revocation"]["sha256"], ARTIFACTS["revocation"]["byte_length"], "WITHDRAWN", "Controlled fictional fixture withdrawal"])
    revocation_case_id = find_case(client, account_b, v1_id, ARTIFACTS["revocation"]["uri"])
    case_before = read_contract(client, account_b, "get_revocation_case", [revocation_case_id])
    revocation_assess_tx = submit(client, account_b, "assess_material_revocation", "assess_revocation", [revocation_case_id])
    restart = subprocess.run([sys.executable, str(Path(__file__)), "--resume-only", revocation_assess_tx["tx_id"]], cwd=ROOT, check=True, capture_output=True, text=True)
    case_after_assessment = read_contract(client, account_b, "get_revocation_case", [revocation_case_id])
    v1_after_assessment = read_contract(client, account_b, "get_node_record", [v1_id])
    write_json(EVIDENCE_DIR / "finality-restart.json", {"transaction_id": revocation_assess_tx["tx_id"], "resumed_without_resubmission": True, "resubmissions": 0, "resume_output": restart.stdout.strip()})
    write_json(EVIDENCE_DIR / "material-revocation.json", {"case_id": revocation_case_id, "open_tx": revocation_open_tx, "assessment_tx": revocation_assess_tx, "case_before": case_before, "case_after_assessment": case_after_assessment, "v1_after_assessment": v1_after_assessment, "result": "PASS" if case_after_assessment["result_status"] == "CONCLUSIVE" and case_after_assessment["materiality"] == "MATERIAL" and case_after_assessment["root_effect"] == "INVALIDATE" and case_after_assessment["reason_code"] in {"MATERIAL_WITHDRAWAL", "MATERIAL_REVOCATION"} else "FAIL", "reason_code_acceptance": "MATERIAL_WITHDRAWAL or exact V2 equivalent MATERIAL_REVOCATION"})
    if case_after_assessment["materiality"] != "MATERIAL" or case_after_assessment["root_effect"] != "INVALIDATE":
        raise RuntimeError(f"controlled material revocation did not produce expected result: {case_after_assessment}")

    early_recovery = attempt_expected_failure(client, account_b, "early_recovery_before_propagation", "open_recovery_case", [v1_id, v2_id, revocation_case_id, "Must fail until adverse propagation completes"])
    write_json(EVIDENCE_DIR / "recovery-ordering.json", {"case_id": revocation_case_id, "attempt": early_recovery, "queue_before_completion": read_contract(client, account_b, "get_impact_queue_state", [revocation_case_id]), "result": "PASS" if early_recovery.get("expected_rejection") else "FAIL"})

    propagation = process_impact(client, account_b, revocation_case_id, "impact_" + revocation_case_id)
    v1_prop = read_contract(client, account_b, "get_node_record", [v1_id])
    claim_prop = read_contract(client, account_b, "get_node_record", [claim_id])
    decision_prop = read_contract(client, account_b, "get_node_record", [decision_id])
    queue_final = read_contract(client, account_b, "get_impact_queue_state", [revocation_case_id])
    write_json(EVIDENCE_DIR / "propagation.json", {"case_id": revocation_case_id, "observations": propagation, "queue_final": queue_final, "v1": v1_prop, "claim": claim_prop, "decision": decision_prop, "result": "PASS" if queue_final["case_status"] == "COMPLETE" and claim_prop["reliance_status"] == "QUESTIONED" and decision_prop["reliance_status"] == "QUARANTINED" else "FAIL"})

    c2_tx = submit(client, account_b, "register_late_claim_c2", "register_claim", ["fixture-vendor-001", "Late claim after V1 adverse completion"])
    c2_id = find_node(client, account_b, "CLAIM", "Late claim after V1 adverse completion")
    late_edge_tx = submit(client, account_b, "late_edge_v1_c2", "register_dependency", [v1_id, c2_id, "SUPPORTS"])
    late_edge_id = find_edge(client, account_b, v1_id, c2_id, "SUPPORTS")
    c2_after_edge = read_contract(client, account_b, "get_node_record", [c2_id])
    late_queue = process_impact(client, account_b, revocation_case_id, "late_impact_" + revocation_case_id)
    late_queue_final = read_contract(client, account_b, "get_impact_queue_state", [revocation_case_id])
    late_edge_record = read_contract(client, account_b, "get_dependency_record", [late_edge_id])
    write_json(EVIDENCE_DIR / "late-edge.json", {"claim_id": c2_id, "edge_id": late_edge_id, "register_claim_tx": c2_tx, "late_edge_tx": late_edge_tx, "edge": late_edge_record, "child_after_edge": c2_after_edge, "queue_after_reconciliation": late_queue_final, "observations": late_queue, "result": "PASS" if c2_after_edge["reliance_status"] == "QUESTIONED" and late_queue_final["case_status"] == "COMPLETE" else "FAIL"})
    if c2_after_edge["reliance_status"] != "QUESTIONED":
        raise RuntimeError("late edge did not inherit QUESTIONED effect")

    recovery_open_tx = submit(client, account_b, "open_recovery", "open_recovery_case", [v1_id, v2_id, revocation_case_id, "Controlled fictional corrected successor review"])
    recovery_id = find_recovery(client, account_b, v1_id, v2_id, revocation_case_id)
    recovery_assess_tx = submit(client, account_b, "assess_recovery", "assess_recovery", [recovery_id])
    recovery_case = read_contract(client, account_b, "get_recovery_case", [recovery_id])
    if recovery_case["recovery_effect"] not in {"SUPERSEDE", "REINSTATE"}:
        raise RuntimeError(f"recovery did not produce a resolving effect: {recovery_case}")
    recovery_queue = process_recovery(client, account_b, recovery_id)
    recovery_queue_final = read_contract(client, account_b, "get_recovery_queue_state", [recovery_id])
    after_recovery = {"v1": read_contract(client, account_b, "get_node_record", [v1_id]), "claim": read_contract(client, account_b, "get_node_record", [claim_id]), "decision": read_contract(client, account_b, "get_node_record", [decision_id]), "late_claim": read_contract(client, account_b, "get_node_record", [c2_id])}
    causes_after_recovery = {name: read_contract(client, account_b, "get_active_causes", [node_id]) for name, node_id in [("v1", v1_id), ("claim", claim_id), ("decision", decision_id), ("late_claim", c2_id)]}
    write_json(EVIDENCE_DIR / "recovery.json", {"recovery_id": recovery_id, "open_tx": recovery_open_tx, "assessment_tx": recovery_assess_tx, "case": recovery_case, "queue_observations": recovery_queue, "queue_final": recovery_queue_final, "after_recovery": after_recovery, "active_causes_after_recovery": causes_after_recovery, "result": "PASS" if recovery_case["result_status"] == "CONCLUSIVE" and recovery_case["recovery_effect"] in {"SUPERSEDE", "REINSTATE"} and recovery_queue_final["case_status"] == "COMPLETE" else "FAIL"})

    active_causes = {}
    for name, node_id in [("v1", v1_id), ("claim", claim_id), ("decision", decision_id), ("late_claim", c2_id)]:
        active_causes[name] = {"summary": read_contract(client, account_b, "get_active_causes", [node_id]), "page": read_contract(client, account_b, "get_active_causes_page", [node_id, 0, 64])}
    write_json(EVIDENCE_DIR / "final-state.json", {"contract_address": _CONTRACT_ADDRESS, "authority_id": authority_id, "v1_id": v1_id, "v2_id": v2_id, "claim_id": claim_id, "decision_id": decision_id, "late_claim_id": c2_id, "revocation_case_id": revocation_case_id, "recovery_id": recovery_id, "v1": after_recovery["v1"], "v2": v2_record, "claim": after_recovery["claim"], "decision": after_recovery["decision"], "late_claim": after_recovery["late_claim"], "revocation_case": read_contract(client, account_b, "get_revocation_case", [revocation_case_id]), "recovery_case": read_contract(client, account_b, "get_recovery_case", [recovery_id]), "successor_link": link_record, "active_causes": active_causes, "authority_rotation": "SKIPPED_SAFE_FIXTURE_LACKS_VERSIONED_DECLARATION", "source_path": "contracts/palinode_v2.py", "source_sha256": source_sha256(), "frozen_commit": EXPECTED_HEAD})
    write_json(EVIDENCE_DIR / "authority.json", {"authority_id": authority_id, "authority": read_contract(client, account_a, "get_source_authority", [authority_id]), "version_1": read_contract(client, account_a, "get_source_authority_version", [authority_id, 1]), "well_known_status": well_known.status_code, "well_known_sha256": hashlib.sha256(well_known.content).hexdigest(), "registration_tx_id": existing_record("register_authority_a")["tx_id"], "expected_origin": FIXTURE_ORIGIN, "expected_controller": account_a.address, "expected_policy": FIXTURE_POLICY})
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-only", default="")
    args = parser.parse_args()
    if args.resume_only:
        resume_only(args.resume_only)
    else:
        raise SystemExit(run_v4())
