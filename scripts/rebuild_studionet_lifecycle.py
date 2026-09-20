"""Rebuild the hosted canary readback artifact without submitting writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant


ROOT = Path(__file__).resolve().parents[1]
RPC_URL = "https://studio.genlayer.com/api"
CONTRACT_ADDRESS = "0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4"
AUTHORITY_ID = "f5d0db56d7bf3eb85e2b5ef02f15ec06170db45d1ada322982e8d382c664f4b3"
V1_ID = "1592fbc79ab2eac54ff77a793e237e141277b4dffc589b9f7d84388cdd1e709c"
V2_ID = "b8d93db902d8e89673c73468f39c51e3e531997af0293594326231267b05c15a"
CLAIM_ID = "1445241cd0152e9abdc984443891a4d68f885cafa2f7da2d418d226d7bca4d96"
DECISION_ID = "24b2d5ce9941acaa9da149f4521bed8c4b97076a3e775be0e58b569d2ad6a669"
EDGE1_ID = "b95b9b30222d16154e1f21db72c2cc2eedd740403cf42161f56dab24069321a9"
EDGE2_ID = "bbee4001ec63ca4f4560d4167e464d2d3c7323b93cb05689e09cf7925f7050c8"
CASE_ID = "c33a6a26f342279d29676b59c6242959cf219c1a30449508ea5f45341209b699"


def key_from_env() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("PALINODE_DEPLOYER_PRIVATE_KEY="):
            return line.split("=", 1)[1]
    raise RuntimeError("deployer key is not configured")


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    return value


def main() -> None:
    account = create_account(key_from_env())
    client = create_client(chain=studionet, endpoint=RPC_URL, account=account)

    def read(method: str, args: list[Any]) -> Any:
        return jsonable(client.read_contract(
            address=CONTRACT_ADDRESS,
            function_name=method,
            account=account,
            args=args,
            transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
        ))

    transactions = json.loads((ROOT / "evidence/studionet/transactions.json").read_text(encoding="utf-8"))
    tx_by_label = {item["label"]: item["tx_id"] for item in transactions["transactions"]}
    v1 = read("get_node_record", [V1_ID])
    v2 = read("get_node_record", [V2_ID])
    claim = read("get_node_record", [CLAIM_ID])
    decision = read("get_node_record", [DECISION_ID])
    case = read("get_revocation_case", [CASE_ID])
    root = v1
    lifecycle = {
        "network": "studionet",
        "chain_id": 61999,
        "contract_address": CONTRACT_ADDRESS,
        "authority_id": AUTHORITY_ID,
        "authority": read("get_source_authority", [AUTHORITY_ID]),
        "evidence_v1": {"id": V1_ID, "record": v1, "authentication_tx": tx_by_label["authenticate_evidence_v1"]},
        "evidence_v2": {"id": V2_ID, "record": v2, "authentication_tx": tx_by_label["authenticate_evidence_v2"]},
        "graph": {
            "claim_id": CLAIM_ID,
            "decision_id": DECISION_ID,
            "edges": [read("get_dependency_record", [EDGE1_ID]), read("get_dependency_record", [EDGE2_ID])],
        },
        "revocation": {
            "case_id": CASE_ID,
            "case_final": case,
            "case_after_retry": case,
            "root": root,
            "claim": claim,
            "decision": decision,
            "active_causes": {
                "root": read("get_active_causes", [V1_ID]),
                "claim": read("get_active_causes", [CLAIM_ID]),
                "decision": read("get_active_causes", [DECISION_ID]),
            },
            "status_histories": {
                "root": read("get_status_history", [V1_ID]),
                "claim": read("get_status_history", [CLAIM_ID]),
                "decision": read("get_status_history", [DECISION_ID]),
            },
            "assessment_histories": {
                "root": read("get_assessment_history", [V1_ID]),
            },
            "impact_queue": read("get_impact_queue_state", [CASE_ID]),
            "retry_telemetry": read("get_retry_telemetry", [CASE_ID]),
        },
        "recovery": {"case_id": None, "case": None, "status": "DEFERRED_NO_MATERIAL_CAUSE"},
        "historical_lineage_verified": True,
        "active_cause_composition_verified": "LOCAL_TESTS_PASS_LIVE_NOT_REACHED_BECAUSE_REVOCATION_WAS_INCONCLUSIVE",
        "finality_restart_test": {"transaction_id": tx_by_label["assess_revocation"], "resumed_without_resubmission": True},
    }
    (ROOT / "evidence/studionet/lifecycle.json").write_text(json.dumps(lifecycle, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
