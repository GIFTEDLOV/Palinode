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
transaction-tracker checks. The installed Windows GLSim deployment/readback
test and one fresh isolated `genlayer-test[sim]` reproduction both fail with
`Compressed file ended before the end-of-stream marker was reached`.
`GLSIM_STATUS=KNOWN_LOCAL_BLOCKER` records this local simulator limitation; a
local chain ID of 61999 is not treated as Studionet equivalence. Direct mode
and local GLSim do not establish that the stable Studionet service will accept
a canary.

The hosted canary must use the documented `genlayer-py` stable client profile
for `https://studio.genlayer.com/api` and chain 61999, persist the original
transaction ID, and require both final consensus and successful execution.
