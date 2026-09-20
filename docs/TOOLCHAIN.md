# Toolchain and target

## Target network

Phase 1 targets stable Studionet only:

```text
RPC: https://studio.genlayer.com/api
chain ID: 61999
alias: studionet
```

The repository does not target `studio-dev`, chain ID `61997`, Bradbury, or
deployment. The checked-in `gltest.config.yaml` selects the built-in
`studionet` profile for any future integration run.

## Resolved versions

The machine was inspected before installation. Preinstalled RC packages were
not reused. The project-local virtual environment uses the stable compatible
set:

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

The pre-existing global npm `genlayer` CLI reported `0.40.0-rc.3`; it was not
used, upgraded, or used for deployment because this phase does not deploy and
must not target the release-candidate Studio environment. The checked-in
workflow uses the stable Python testing/linting stack and the explicit stable
Studionet profile.

`genlayer-test 0.29.2` requires `genlayer-py >=0.13,<0.17`, which is why the
stable client is pinned to 0.16.3 rather than the incompatible 0.18.0 release.
The runner artifact is selected explicitly with `GENVM_VERSION=v0.2.16` for
linting and `sdk_version="v0.2.16"` in direct tests.

## Checks

The current stable linter commands are:

```powershell
$env:GENVM_VERSION = "v0.2.16"
.venv\Scripts\genvm-lint.exe check contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe typecheck contracts/palinode.py --json
.venv\Scripts\genvm-lint.exe schema contracts/palinode.py --output artifacts/palinode_schema.json --json
```

The final checked schema reports 33 public methods: 18 writes and 15 views.
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
