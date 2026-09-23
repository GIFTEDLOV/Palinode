# Application transaction model

PALINODE does not treat a wallet receipt or an `ACCEPTED` GenLayer status as
final application success. Current GenLayer documentation distinguishes
consensus acceptance, execution outcome, appeal/finalization, and the
transaction ID used to observe the same transaction.

The frontend persists one record per submitted transaction and restores the
same record after a browser restart:

```json
{
  "transaction_id": "0x...",
  "method": "open_revocation_case",
  "submission_state": "SUBMITTED",
  "consensus_state": "PENDING",
  "execution_state": "UNKNOWN",
  "finality_state": "NOT_FINAL",
  "last_observed_at": "...",
  "last_error": ""
}
```

The state dimensions are intentionally separate:

- `submission_state`: local submission tracking and whether an RPC hash was
  returned;
- `consensus_state`: pending, accepted, undetermined, timeout, or other
  protocol decision;
- `execution_state`: successful contract execution or an accepted execution
  error; and
- `finality_state`: appeal window open, finalized, or overturned/restarted.

The reusable helper in `scripts/transaction_lifecycle.py` normalizes the
application-facing states:

```text
SUBMITTED -> PENDING/PROPOSING/COMMITTING/REVEALING
           -> ACCEPTED_PROVISIONAL -> APPEAL_STATE
           -> FINALIZATION_ACTION_AVAILABLE -> FINALIZED_SUCCESS
                                               or FINALIZED_ERROR
```

Unknown or timeout conditions are represented as `UNDETERMINED` or
`TIMEOUT_CANCELED`. `FINALIZED_SUCCESS` requires both an appropriate finalized
consensus state and a successful execution result. `ACCEPTED_PROVISIONAL`
alone is never application success. The tracker persists and resumes the same
transaction ID and never resubmits automatically.

After a timeout or browser restart, the client resumes polling the persisted
transaction ID. `ACCEPTED` is provisional; only `FINALIZED` together with
`FINISHED_WITH_RETURN` is durable execution success. The client polls the same
ID and never automatically submits the same PALINODE write again, because that
could create a second authority, challenge, retry, or propagation transaction.
Any resubmission is an explicit user decision after the original transaction
reaches a terminal protocol state.

The contract remains canonical for PALINODE state. This document defines the
non-canonical application tracking envelope required for safe presentation and
resumption; it cannot change contract state or declare a transaction final.
