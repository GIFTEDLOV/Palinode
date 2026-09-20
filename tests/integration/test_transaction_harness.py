from scripts.transaction_lifecycle import (
    ApplicationTransactionState,
    TransactionTracker,
    classify_transaction,
)


def test_finalized_success_requires_execution_success():
    assert classify_transaction({"status": "FINALIZED", "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}}) == ApplicationTransactionState.FINALIZED_SUCCESS
    assert classify_transaction({"status": "FINALIZED", "consensus_data": {"leader_receipt": [{"execution_result": "ERROR"}]}}) == ApplicationTransactionState.FINALIZED_ERROR
    assert classify_transaction({"status": "ACCEPTED", "consensus_data": {"leader_receipt": [{"execution_result": "SUCCESS"}]}}) == ApplicationTransactionState.ACCEPTED_PROVISIONAL


def test_documented_lifecycle_object_is_provisional_until_finalized():
    assert classify_transaction({"lifecycle": {"state": "decided", "outcome": "Accepted"}}) == ApplicationTransactionState.ACCEPTED_PROVISIONAL
    assert classify_transaction({"lifecycle": {"state": "processing", "phase": "Revealing"}}) == ApplicationTransactionState.REVEALING
    assert classify_transaction({"lifecycle": {"state": "finalized"}, "execution_result": "FINISHED_WITH_RETURN"}) == ApplicationTransactionState.FINALIZED_SUCCESS


def test_tracker_resumes_same_id_and_never_resubmits(tmp_path):
    tracker = TransactionTracker(tmp_path / "transaction.json")
    tracker.record_submission("0xabc")
    observed = []

    def fetch(transaction_id):
        observed.append(transaction_id)
        return {"status_name": "FINALIZED", "execution_result": "SUCCESS"}

    assert tracker.resume(fetch) == ApplicationTransactionState.FINALIZED_SUCCESS
    assert observed == ["0xabc"]
