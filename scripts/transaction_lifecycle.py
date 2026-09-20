"""Frontend-facing GenLayer transaction lifecycle helpers.

This module is client-side tracking only.  It is never canonical contract
state and it deliberately does not resubmit a transaction when polling times
out.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any


class ApplicationTransactionState(StrEnum):
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    PROPOSING = "PROPOSING"
    COMMITTING = "COMMITTING"
    REVEALING = "REVEALING"
    ACCEPTED_PROVISIONAL = "ACCEPTED_PROVISIONAL"
    APPEAL_STATE = "APPEAL_STATE"
    FINALIZATION_ACTION_AVAILABLE = "FINALIZATION_ACTION_AVAILABLE"
    FINALIZED_SUCCESS = "FINALIZED_SUCCESS"
    FINALIZED_ERROR = "FINALIZED_ERROR"
    UNDETERMINED = "UNDETERMINED"
    TIMEOUT_CANCELED = "TIMEOUT_CANCELED"


def _lifecycle_status(transaction: dict[str, Any]) -> str | None:
    """Read the current documented stored lifecycle when present.

    The RPC's stable lifecycle is state/phase/outcome-shaped rather than a
    single integer. Integer/status-name support remains for older receipts and
    test fixtures, but a lifecycle object takes precedence.
    """
    lifecycle = transaction.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return None
    state = str(lifecycle.get("state", "")).upper()
    phase = str(lifecycle.get("phase", "")).upper()
    outcome = str(lifecycle.get("outcome", "")).upper()
    if state == "PROCESSING":
        return phase or "PENDING"
    if state == "DECIDED":
        if outcome in ("ACCEPTED", "DECIDED"):
            return "ACCEPTED"
        if outcome in ("VALIDATORS_TIMEOUT", "LEADER_TIMEOUT", "UNDETERMINED"):
            return outcome
        return "UNDETERMINED"
    if state == "FINALIZED":
        return "FINALIZED"
    if state == "CANCELED":
        return "CANCELED"
    return "UNDETERMINED"


def _status_name(value: Any) -> str:
    text = str(value).upper()
    return text


def _execution_result(transaction: dict[str, Any]) -> str:
    if isinstance(transaction.get("execution_result"), str):
        return transaction["execution_result"].upper()
    consensus = transaction.get("consensus_data")
    if isinstance(consensus, dict):
        leaders = consensus.get("leader_receipt")
        if isinstance(leaders, list) and leaders and isinstance(leaders[0], dict):
            return str(leaders[0].get("execution_result", "UNKNOWN")).upper()
    return "UNKNOWN"


def classify_transaction(transaction: dict[str, Any]) -> ApplicationTransactionState:
    """Map protocol status plus execution result to application state."""
    status = _lifecycle_status(transaction)
    if status is None:
        status = _status_name(transaction.get("status_name", transaction.get("status", "UNDETERMINED")))
    if status in ("PENDING", "ACTIVATED"):
        return ApplicationTransactionState.PENDING
    if status in ("PROPOSING", "COMMITTING", "REVEALING"):
        return ApplicationTransactionState(status)
    if status in ("ACCEPTED", "DECIDED"):
        return ApplicationTransactionState.ACCEPTED_PROVISIONAL
    if status in ("VALIDATORS_TIMEOUT", "LEADER_TIMEOUT", "UNDETERMINED"):
        return ApplicationTransactionState.UNDETERMINED
    if status in ("APPEAL", "APPEALED", "APPEALING"):
        return ApplicationTransactionState.APPEAL_STATE
    if status == "FINALIZATION_ACTION_AVAILABLE":
        return ApplicationTransactionState.FINALIZATION_ACTION_AVAILABLE
    if status == "FINALIZED":
        return (
            ApplicationTransactionState.FINALIZED_SUCCESS
            if _execution_result(transaction) in ("SUCCESS", "RETURN", "FINISHED_WITH_RETURN")
            else ApplicationTransactionState.FINALIZED_ERROR
        )
    if status in ("TIMEOUT", "CANCELED", "CANCELLED"):
        return ApplicationTransactionState.TIMEOUT_CANCELED
    return ApplicationTransactionState.UNDETERMINED


class TransactionTracker:
    """Persist a transaction ID and resume polling the same ID after restart."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record_submission(self, transaction_id: str) -> None:
        self.path.write_text(json.dumps({"transaction_id": transaction_id}, indent=2), encoding="utf-8")

    def transaction_id(self) -> str:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        transaction_id = data.get("transaction_id")
        if not isinstance(transaction_id, str) or transaction_id == "":
            raise ValueError("missing persisted transaction ID")
        return transaction_id

    def resume(self, fetch_transaction) -> ApplicationTransactionState:
        transaction_id = self.transaction_id()
        transaction = fetch_transaction(transaction_id)
        if transaction is None:
            return ApplicationTransactionState.UNDETERMINED
        return classify_transaction(transaction)
