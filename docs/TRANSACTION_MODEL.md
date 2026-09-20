# Application transaction model

PALINODE does not treat a wallet receipt or an `ACCEPTED` GenLayer status as
final application success. Current GenLayer documentation distinguishes
consensus acceptance, execution outcome, appeal/finalization, and the
transaction ID used to observe the same transaction.

The future frontend/API should persist one record per submitted transaction:

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

After a timeout or browser restart, the client resumes polling the persisted
`transaction_id`. It must not automatically submit the same PALINODE write
again, because doing so could create a second authority, challenge, retry, or
propagation transaction. Any resubmission must be an explicit user decision
after the original transaction reaches a terminal protocol state.

The contract remains canonical for PALINODE state. This document defines the
non-canonical application tracking envelope required for safe presentation and
resumption; it cannot change contract state or declare a transaction final.
