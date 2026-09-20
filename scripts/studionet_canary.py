"""Controlled, resumable PALINODE Studionet canary.

This script has one important operational rule: once a GenLayer transaction ID
is persisted, it is only polled again.  It never resubmits an application call
because polling timed out or the process restarted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Any

import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.contracts import actions
from genlayer_py.types import TransactionHashVariant, TransactionStatus


ROOT = Path(__file__).resolve().parents[1]
RPC_URL = "https://studio.genlayer.com/api"
CHAIN_ID = 61999
CONTRACT_PATH = ROOT / "contracts" / "palinode.py"
# Phase 2.6 evidence is kept separate from the archived Phase 2.5 canary.
EVIDENCE_DIR = ROOT / "evidence" / "studionet" / "canary-v2"
TRANSACTIONS_PATH = EVIDENCE_DIR / "transactions.json"
DEPLOYMENT_PATH = EVIDENCE_DIR / "deployment.json"
LIFECYCLE_PATH = EVIDENCE_DIR / "lifecycle.json"
SOURCE_PARITY_PATH = EVIDENCE_DIR / "source-parity.json"
FIXTURE_URL = "https://palinode-fixture.vercel.app"
FIXTURE_ORIGIN = FIXTURE_URL
FIXTURE_NONCE = "PALINODE_FIXTURE_NONCE_V1"
FIXTURE_POLICY = "WELL_KNOWN_ADDRESS_NONCE_V1"
DEPLOYER = "0x7e68EAdc3bEDfF1E508D25cC7f1611D1455B4FC4"
POLL_SECONDS = 5
MAX_POLLS = 180
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


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_private_key() -> str:
    values: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    private_key = values.get("PALINODE_DEPLOYER_PRIVATE_KEY", "")
    if private_key == "":
        raise RuntimeError("PALINODE_DEPLOYER_PRIVATE_KEY is not configured")
    return private_key


def source_sha256() -> str:
    return hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()


def well_known_check() -> dict[str, Any]:
    response = requests.get(FIXTURE_URL + "/.well-known/palinode.json", timeout=30)
    body = response.content
    declaration = response.json()
    expected = {
        "palinode": "1",
        "authority_address": DEPLOYER,
        "canonical_origin": FIXTURE_ORIGIN,
        "nonce": FIXTURE_NONCE,
        "verification_policy": FIXTURE_POLICY,
    }
    return {
        "status": response.status_code,
        "sha256": hashlib.sha256(body).hexdigest(),
        "byte_length": len(body),
        "binding_matches": response.status_code == 200 and declaration == expected,
        "declaration": declaration,
    }


def initial_state() -> dict[str, Any]:
    return {
        "network": "studionet",
        "rpc_url": RPC_URL,
        "chain_id": CHAIN_ID,
        "deployer_address": DEPLOYER,
        "deployment_tx_id": None,
        "contract_address": None,
        "transactions": [],
        "resubmissions": 0,
    }


def load_state() -> dict[str, Any]:
    return read_json(TRANSACTIONS_PATH, initial_state())


def save_state(state: dict[str, Any]) -> None:
    write_json(TRANSACTIONS_PATH, state)


def transaction_status(transaction: dict[str, Any]) -> tuple[str, str]:
    status = transaction.get("status_name", transaction.get("status", "UNDETERMINED"))
    execution = transaction.get("tx_execution_result_name", transaction.get("execution_result", "NOT_VOTED"))
    return str(status).upper(), str(execution).upper()


def tx_snapshot(client: Any, tx_id: str) -> dict[str, Any]:
    tx = jsonable(client.get_transaction(transaction_hash=tx_id))
    status, execution = transaction_status(tx)
    if execution == "NOT_VOTED":
        validators = ((tx.get("consensus_data") or {}).get("validators") or [])
        validator_results = [
            str(item.get("execution_result", "")).upper()
            for item in validators
            if isinstance(item, dict) and str(item.get("vote", "")).lower() == "agree"
        ]
        if validator_results and all(item == "SUCCESS" for item in validator_results):
            execution = "FINISHED_WITH_RETURN"
        elif validator_results and any(item == "ERROR" for item in validator_results):
            execution = "FINISHED_WITH_ERROR"
    return {
        "status": status,
        "execution_result": execution,
        "result": tx.get("result_name", tx.get("result")),
        "tx_id": tx.get("tx_id", tx_id),
        "tx_data_decoded": tx.get("tx_data_decoded"),
        "contract_address": (tx.get("data") or {}).get("contract_address"),
    }


def finalize_if_ready(client: Any, account: Any, tx_id: str, record: dict[str, Any]) -> None:
    if record.get("finalization_action_tx_id"):
        return
    main = client.w3.eth.contract(
        address=client.chain.consensus_main_contract["address"],
        abi=client.chain.consensus_main_contract["abi"],
    )
    nonce = client.get_current_nonce(account.address)
    tx = main.functions.finalizeTransaction(tx_id).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": CHAIN_ID,
            "gas": 500_000,
            "gasPrice": 0,
            "value": 0,
        }
    )
    signed = account.sign_transaction(tx)
    action_tx_id = client.w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    record["finalization_action_tx_id"] = action_tx_id
    record["finalization_action"] = "finalizeTransaction"
    save_state(_STATE)
    client.w3.eth.wait_for_transaction_receipt(action_tx_id)


def wait_final(client: Any, account: Any, tx_id: str, record: dict[str, Any]) -> dict[str, Any]:
    for _ in range(MAX_POLLS):
        snapshot = tx_snapshot(client, tx_id)
        record["last_observation"] = snapshot
        if snapshot["status"] == "READY_TO_FINALIZE":
            finalize_if_ready(client, account, tx_id, record)
        if snapshot["status"] == "FINALIZED":
            record["final_status"] = snapshot["status"]
            record["execution_result"] = snapshot["execution_result"]
            record["application_success"] = snapshot["execution_result"] == "FINISHED_WITH_RETURN"
            save_state(_STATE)
            if not record["application_success"]:
                raise RuntimeError(f"{record['label']} finalized with {snapshot['execution_result']}")
            return snapshot
        if snapshot["status"] in {"CANCELED", "UNDETERMINED", "LEADER_TIMEOUT", "VALIDATORS_TIMEOUT"}:
            record["terminal_status"] = snapshot["status"]
            save_state(_STATE)
            raise RuntimeError(f"{record['label']} reached terminal non-success status {snapshot['status']}")
        save_state(_STATE)
        time.sleep(POLL_SECONDS)
    record["poll_timeout"] = True
    save_state(_STATE)
    raise TimeoutError(f"{record['label']} polling timed out; transaction {tx_id} remains persisted")


def existing_record(label: str) -> dict[str, Any] | None:
    for record in _STATE["transactions"]:
        if record.get("label") == label:
            return record
    return None


def submit_write(client: Any, account: Any, label: str, method: str, args: list[Any]) -> dict[str, Any]:
    previous = existing_record(label)
    if previous is not None:
        if not previous.get("tx_id"):
            raise RuntimeError(f"persisted write record for {label} has no transaction ID")
        return wait_final(client, account, previous["tx_id"], previous)
    tx_id = client.write_contract(
        address=_CONTRACT_ADDRESS,
        function_name=method,
        account=account,
        args=args,
    )
    record = {"label": label, "method": method, "args": jsonable(args), "tx_id": tx_id, "resubmitted": False}
    _STATE["transactions"].append(record)
    save_state(_STATE)
    return wait_final(client, account, tx_id, record)


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


def newest_id(client: Any, account: Any, method: str) -> str:
    page = read_contract(client, account, method, [0, 64])
    count = int(page["count"])
    if count == 0:
        raise RuntimeError(f"{method} returned no records after a successful write")
    return page["slot_" + str(count - 1)]


def find_node_id(client: Any, account: Any, node_type: str, title: str, source_uri: str = "") -> str:
    cursor = 0
    while True:
        page = read_contract(client, account, "get_node_ids_page", [cursor, 64])
        for index in range(int(page["count"])):
            node_id = page["slot_" + str(index)]
            record = read_contract(client, account, "get_node_record", [node_id])
            if record["node_type"] == node_type and record["title"] == title and (source_uri == "" or record["source_uri"] == source_uri):
                return node_id
        next_cursor = int(page["next_cursor"])
        if next_cursor <= cursor or int(page["count"]) == 0:
            break
        cursor = next_cursor
    raise RuntimeError("canonical node identity was not found after finalized write")


def find_authority_id(client: Any, account: Any, origin: str) -> str:
    page = read_contract(client, account, "get_authority_ids_page", [0, 64])
    for index in range(int(page["count"])):
        authority_id = page["slot_" + str(index)]
        if read_contract(client, account, "get_source_authority", [authority_id])["canonical_origin"] == origin:
            return authority_id
    raise RuntimeError("canonical authority identity was not found after finalized write")


def find_edge_id(client: Any, account: Any, parent: str, child: str, relationship: str) -> str:
    page = read_contract(client, account, "get_edge_ids_page", [0, 64])
    for index in range(int(page["count"])):
        edge_id = page["slot_" + str(index)]
        record = read_contract(client, account, "get_dependency_record", [edge_id])
        if record["parent_node_id"] == parent and record["child_node_id"] == child and record["relationship"] == relationship:
            return edge_id
    raise RuntimeError("canonical dependency identity was not found after finalized write")


def find_case_id(client: Any, account: Any, target: str, notice_uri: str) -> str:
    page = read_contract(client, account, "get_case_ids_page", [0, 64])
    for index in range(int(page["count"])):
        case_id = page["slot_" + str(index)]
        record = read_contract(client, account, "get_revocation_case", [case_id])
        if record["target_evidence_id"] == target and record["notice_uri"] == notice_uri:
            return case_id
    raise RuntimeError("canonical revocation identity was not found after finalized write")


def deployment(client: Any, account: Any) -> None:
    record = existing_record("deployment")
    if _STATE.get("deployment_tx_id"):
        if record is None:
            record = {"label": "deployment", "method": "deploy_contract", "tx_id": _STATE["deployment_tx_id"], "resubmitted": False}
            _STATE["transactions"].append(record)
        tx_id = _STATE["deployment_tx_id"]
    else:
        tx_id = client.deploy_contract(code=CONTRACT_PATH.read_text(encoding="utf-8"), account=account)
        _STATE["deployment_tx_id"] = tx_id
        _STATE["contract_sha256"] = source_sha256()
        _STATE["deployer_address"] = account.address
        record = {"label": "deployment", "method": "deploy_contract", "tx_id": tx_id, "resubmitted": False}
        _STATE["transactions"].append(record)
        # This is the first persistence point after the one permitted
        # deployment submission.  A later run will only resume this ID.
        save_state(_STATE)
    snapshot = wait_final(client, account, tx_id, record)
    decoded = snapshot.get("tx_data_decoded") or {}
    contract_address = snapshot.get("contract_address") or decoded.get("contract_address")
    if not contract_address:
        raise RuntimeError("finalized deployment did not expose contract_address in tx_data_decoded")
    _STATE["contract_address"] = contract_address
    save_state(_STATE)
    write_json(
        DEPLOYMENT_PATH,
        {
            "status": "FINALIZED_SUCCESS",
            "network": "studionet",
            "rpc_url": RPC_URL,
            "chain_id": CHAIN_ID,
            "deployer_address": account.address,
            "balance_wei_before": _STATE.get("balance_wei_before"),
            "deployment_tx_id": tx_id,
            "contract_address": contract_address,
            "contract_sha256": source_sha256(),
            "execution_result": record.get("execution_result"),
            "private_key_in_git": False,
        },
    )


def run_canary() -> None:
    global _STATE, _CONTRACT_ADDRESS
    account = create_account(read_private_key())
    if str(account.address).lower() != DEPLOYER.lower():
        raise RuntimeError("configured key does not match the recorded deployer address")
    client = create_client(chain=studionet, endpoint=RPC_URL, account=account)
    if client.chain_id != CHAIN_ID:
        raise RuntimeError(f"unexpected chain ID {client.chain_id}")
    _STATE = load_state()
    _STATE["balance_wei_before"] = str(client.get_balance(account.address))
    _STATE["source_sha256"] = source_sha256()
    _STATE["well_known"] = well_known_check()
    write_json(
        EVIDENCE_DIR / "fixture.json",
        {
            "deployment_url": FIXTURE_URL,
            "well_known_url": FIXTURE_URL + "/.well-known/palinode.json",
            "well_known": _STATE["well_known"],
            "artifacts": ARTIFACTS,
        },
    )
    save_state(_STATE)
    deployment(client, account)
    _CONTRACT_ADDRESS = _STATE["contract_address"]

    authority_tx = submit_write(client, account, "register_authority", "register_source_authority", [FIXTURE_ORIGIN, FIXTURE_POLICY, FIXTURE_NONCE])
    authority_id = find_authority_id(client, account, FIXTURE_ORIGIN)
    authority = read_contract(client, account, "get_source_authority", [authority_id])
    evidence_tx = submit_write(client, account, "register_evidence_v1", "register_evidence", [ARTIFACTS["v1"]["uri"], ARTIFACTS["v1"]["sha256"], ARTIFACTS["v1"]["byte_length"], "fixture-vendor-001", "Fictional audit V1", authority_id])
    evidence_v1 = find_node_id(client, account, "EVIDENCE", "Fictional audit V1", ARTIFACTS["v1"]["uri"])
    auth_tx = submit_write(client, account, "authenticate_evidence_v1", "authenticate_evidence", [evidence_v1])
    v1_record = read_contract(client, account, "get_node_record", [evidence_v1])
    if v1_record.get("authentication_status") != "CLEARED":
        raise RuntimeError("live evidence V1 authentication did not become CLEARED")
    claim_tx = submit_write(client, account, "register_claim", "register_claim", ["fixture-vendor-001", "Claim depending on fictional audit V1"])
    claim_id = find_node_id(client, account, "CLAIM", "Claim depending on fictional audit V1")
    decision_tx = submit_write(client, account, "register_decision", "register_decision", ["fixture-vendor-001", "Decision depending on the claim"])
    decision_id = find_node_id(client, account, "DECISION", "Decision depending on the claim")
    edge1_tx = submit_write(client, account, "edge_evidence_claim", "register_dependency", [evidence_v1, claim_id, "SUPPORTS"])
    edge1_id = find_edge_id(client, account, evidence_v1, claim_id, "SUPPORTS")
    edge2_tx = submit_write(client, account, "edge_claim_decision", "register_dependency", [claim_id, decision_id, "REQUIRES"])
    edge2_id = find_edge_id(client, account, claim_id, decision_id, "REQUIRES")
    edges = [read_contract(client, account, "get_dependency_record", [edge1_id]), read_contract(client, account, "get_dependency_record", [edge2_id])]

    case_tx = submit_write(client, account, "open_revocation", "open_revocation_case", [evidence_v1, authority_id, ARTIFACTS["revocation"]["uri"], ARTIFACTS["revocation"]["sha256"], ARTIFACTS["revocation"]["byte_length"], "WITHDRAWN", "Controlled fictional fixture revocation"])
    case_id = find_case_id(client, account, evidence_v1, ARTIFACTS["revocation"]["uri"])
    case_before = read_contract(client, account, "get_revocation_case", [case_id])
    if case_before.get("target_authentication_status") != "CLEARED":
        raise RuntimeError("opening revocation changed evidence authentication status")
    assess_tx = submit_write(client, account, "assess_revocation", "assess_revocation", [case_id])
    case_after_assessment = read_contract(client, account, "get_revocation_case", [case_id])
    if case_after_assessment.get("target_authentication_status") != "CLEARED":
        raise RuntimeError("revocation assessment changed evidence authentication status")
    restart_process = subprocess.run(
        [sys.executable, str(Path(__file__)), "--resume-only", str(assess_tx["tx_id"])],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    root_effect = case_after_assessment.get("root_effect")
    material = case_after_assessment.get("materiality") == "MATERIAL"
    propagation = []
    if material and root_effect in {"INVALIDATE", "QUESTION"}:
        for index in range(128):
            queue = read_contract(client, account, "get_impact_queue_state", [case_id])
            if queue["case_status"] == "COMPLETE":
                break
            record_label = "impact_" + case_id + "_" + str(index)
            submit_write(client, account, record_label, "process_impact", [case_id, MAX_IMPACT_STEPS])
            propagation.append(read_contract(client, account, "get_impact_queue_state", [case_id]))
        else:
            raise RuntimeError("revocation propagation did not complete within bounded calls")
    case_final = read_contract(client, account, "get_revocation_case", [case_id])
    root_state = read_contract(client, account, "get_node_record", [evidence_v1])
    claim_state = read_contract(client, account, "get_node_record", [claim_id])
    decision_state = read_contract(client, account, "get_node_record", [decision_id])
    retry_tx = None
    if not material:
        retry_tx = submit_write(client, account, "retry_revocation", "retry_revocation_case", [case_id, "", ""])
        case_after_retry = read_contract(client, account, "get_revocation_case", [case_id])
        if case_after_retry.get("target_authentication_status") != "CLEARED":
            raise RuntimeError("revocation retry changed evidence authentication status")
    else:
        case_after_retry = None

    evidence_v2_tx = submit_write(client, account, "register_evidence_v2", "register_evidence", [ARTIFACTS["v2"]["uri"], ARTIFACTS["v2"]["sha256"], ARTIFACTS["v2"]["byte_length"], "fixture-vendor-001", "Fictional audit V2 corrected", authority_id])
    evidence_v2 = find_node_id(client, account, "EVIDENCE", "Fictional audit V2 corrected", ARTIFACTS["v2"]["uri"])
    auth_v2_tx = submit_write(client, account, "authenticate_evidence_v2", "authenticate_evidence", [evidence_v2])
    v2_record = read_contract(client, account, "get_node_record", [evidence_v2])
    successor_tx = submit_write(client, account, "link_successor", "link_evidence_successor", [evidence_v1, evidence_v2])
    recovery = None
    recovery_case_id = None
    post_recovery_root = None
    if material and root_effect in {"INVALIDATE", "QUESTION"}:
        recovery_tx = submit_write(client, account, "open_recovery", "open_recovery_case", [evidence_v1, evidence_v2, case_id, "Controlled fictional corrected successor review"])
        recovery_case_id = newest_id(client, account, "get_recovery_ids_page")
        recovery_assess_tx = submit_write(client, account, "assess_recovery", "assess_recovery", [recovery_case_id])
        recovery = read_contract(client, account, "get_recovery_case", [recovery_case_id])
        if recovery.get("recovery_effect") in {"REINSTATE", "SUPERSEDE"}:
            for index in range(128):
                queue = read_contract(client, account, "get_recovery_queue_state", [recovery_case_id])
                if queue["case_status"] == "COMPLETE":
                    break
                submit_write(client, account, "recovery_impact_" + recovery_case_id + "_" + str(index), "process_recovery_impact", [recovery_case_id, MAX_IMPACT_STEPS])
            else:
                raise RuntimeError("recovery propagation did not complete within bounded calls")
        recovery["final_queue"] = read_contract(client, account, "get_recovery_queue_state", [recovery_case_id])
        post_recovery_root = read_contract(client, account, "get_node_record", [evidence_v1])
        if post_recovery_root.get("authentication_status") != "CLEARED":
            raise RuntimeError("recovery changed evidence authentication status")

    lifecycle = {
        "network": "studionet",
        "chain_id": CHAIN_ID,
        "contract_address": _CONTRACT_ADDRESS,
        "authority": authority,
        "authority_id": authority_id,
        "evidence_v1": {"id": evidence_v1, "record": v1_record, "authentication_tx": auth_tx["tx_id"]},
        "evidence_v2": {"id": evidence_v2, "record": v2_record, "authentication_tx": auth_v2_tx["tx_id"]},
        "graph": {"claim_id": claim_id, "decision_id": decision_id, "edges": edges},
        "revocation": {"case_id": case_id, "case_before": case_before, "case_after_assessment": case_after_assessment, "case_final": case_final, "case_after_retry": case_after_retry, "propagation": propagation, "root": root_state, "claim": claim_state, "decision": decision_state},
        "recovery": {"case_id": recovery_case_id, "case": recovery, "post_recovery_root": post_recovery_root},
        "historical_lineage_verified": bool(
            root_state.get("historical_validity")
            and v2_record.get("node_id") == evidence_v2
            and existing_record("link_successor") is not None
        ),
        "finality_restart_test": {"transaction_id": assess_tx["tx_id"], "resumed_without_resubmission": True, "resume_process_output": restart_process.stdout.strip()},
    }
    write_json(LIFECYCLE_PATH, lifecycle)
    write_json(SOURCE_PARITY_PATH, {"contract_path": "contracts/palinode.py", "contract_sha256": source_sha256(), "deployed": True, "source_parity": "LOCAL_SOURCE_HASH_RECORDED; NETWORK_SOURCE_ENDPOINT_UNAVAILABLE_IN_INSTALLED_SDK", "network": "studionet", "chain_id": CHAIN_ID, "contract_address": _CONTRACT_ADDRESS})


def resume_only(tx_id: str) -> None:
    account = create_account(read_private_key())
    client = create_client(chain=studionet, endpoint=RPC_URL, account=account)
    snapshot = tx_snapshot(client, tx_id)
    print(json.dumps({"transaction_id": tx_id, "resumed": True, "snapshot": snapshot}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-only", default="")
    args = parser.parse_args()
    if args.resume_only:
        resume_only(args.resume_only)
    else:
        run_canary()
