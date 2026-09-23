# Toolchain and target

## Current status

PALINODE V4 is deployed on Studionet and the production frontend is live at
`https://palinode-app.vercel.app`. The frozen contract is
`0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b`, sourced from
`contracts/palinode_v2.py` with SHA-256
`0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601`.
The reproducible release workflow is
`.github/workflows/palinode-v4.yml`; it runs contract, frontend, and browser
jobs from tracked source in clean environments. No V4 contract redeployment or
chain write is part of CI.

The release identities are intentionally separate:

- Contract source freeze: `14bb4574a8d248c978b55ff1fb70f32c0293f313`.
- Initial V4 release source: `be8a14b09f4ad1f40a9fdb0429dd16d3942795a9`.
- Current repository / frontend release HEAD: the final HEAD of this hardening
  pass, recorded in `evidence/studionet/v4/release-manifest.json` and the
  GitHub release.

## Target network

Phase 2.5 targets stable Studionet only:

```text
RPC: https://studio.genlayer.com/api
chain ID: 61999
alias: studionet
```

The repository does not target `studio-dev`, chain ID `61997`, or Bradbury.
The checked-in `gltest.config.yaml` selects the built-in `studionet` profile.

## Resolved versions

The clean release environment uses the stable compatible set:

| Tool | Version |
|---|---|
| Python | 3.14.3 |
| `genlayer-test[sim]` | 0.29.2 |
| `genlayer-py` | 0.16.3 |
| `genvm-linter` | 0.11.0 |
| pytest | 9.1.1 |
| pyright | 1.1.414 |
| GenVM runner artifact | v0.2.16, stable |
| `py-genlayer` dependency hash | `1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` |

The pre-existing global npm `genlayer` CLI reported `0.40.0-rc.3`; it is not
part of the release workflow. The workflow uses only the pinned stable Python
testing/linting stack and the explicit stable Studionet profile.

`genlayer-test 0.29.2` requires `genlayer-py >=0.13,<0.17`, which is why the
stable client is pinned to 0.16.3 rather than the incompatible 0.18.0 release.
The runner artifact is selected explicitly with `GENVM_VERSION=v0.2.16` for
linting and `sdk_version="v0.2.16"` in direct tests.

## Checks

The current stable linter commands are:

```powershell
$env:GENVM_VERSION = "v0.2.16"
.venv\Scripts\genvm-lint.exe lint contracts/palinode_v2.py
.venv\Scripts\genvm-lint.exe validate contracts/palinode_v2.py
.venv\Scripts\genvm-lint.exe typecheck contracts/palinode_v2.py
.venv\Scripts\genvm-lint.exe schema contracts/palinode_v2.py
```

The frozen V4 schema reports 46 public methods: 21 writes and 25 views. The
archived `contracts/palinode.py` source remains historical and is not part of
the current release gate.
The explicit `GENVM_VERSION` environment variable prevents the linter resolver
from silently selecting a cached release-candidate runtime.

Direct tests use `pytest`, with `genlayer-test`'s direct plugin, mock web/LLM
responses, validator capture, strict failure fixtures, and the stable runner.
The repository includes a small Windows/Python 3.14 compatibility shim in
`tests/conftest.py` because the installed direct harness otherwise unlinks its
temporary stdin file while Windows still has it open. It changes no contract
behavior.

## Documentation basis

Implementation choices follow the current official GenLayer documentation for
non-deterministic blocks, `gl.nondet.web`, `gl.nondet.exec_prompt`, custom
`run_nondet_unsafe` validators, direct-mode mocks, transaction context, stable
Studionet, and `genvm-lint` schema/typecheck commands.

One fresh isolated virtual environment was created with the same stable
`genlayer-test[sim]==0.29.2` and `genlayer-py==0.16.3` pins. Its GLSim
deployment/readback reproduction failed with the same compressed-stream error
as the existing environment, so `GLSIM_STATUS=KNOWN_LOCAL_BLOCKER` is recorded.

## Historical pre-deployment notes

Earlier review notes described V4 as pre-deployment and prohibited a V4
broadcast. Those statements describe the pre-release review phase only. The
archived V1/V2/V3 canaries and their deployment records remain historical; they
are not runtime defaults and are not redeployed by this workflow.

The stable `genlayer-js` `1.1.8` client path used by the frontend estimates gas
and reads `eth_gasPrice` through `writeContract`. PALINODE application writes
set value to `0`; current Studionet evidence records gas price `0`, so the
observed environment is gasless for this application-value policy. The
transaction-ID persistence and finality model is unchanged.
