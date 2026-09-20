# Integration testing

The direct suite proves contract behavior under `genlayer-test` mocks. It does
not prove JSON-RPC, deployment, transaction lifecycle, or Studionet behavior.
Those concerns are isolated under `tests/integration/`.

The local harness starts the installed `glsim` executable on a free localhost
port, checks `ping` and `eth_chainId == 61999`, and attempts the documented
simulation deployment/readback path. It also tests the reusable transaction
tracker independently. Run:

```powershell
.venv\Scripts\python.exe -m pytest tests/integration -q -rs
```

The current machine passes the JSON-RPC, deterministic graph readback, and
transaction-tracker checks. The deployment/readback test is skipped when the installed Windows GLSim runner
returns its observed `WinError 32`/compressed-runner failure. This is recorded
as an integration blocker, not converted into a successful deployment. Direct
mode and local GLSim also do not establish that the stable Studionet service
will accept a canary.
