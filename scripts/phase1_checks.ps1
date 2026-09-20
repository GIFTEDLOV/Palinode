$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$lint = Join-Path $repoRoot ".venv\Scripts\genvm-lint.exe"
$env:GENVM_VERSION = "v0.2.16"
$env:PATH = "$(Join-Path $repoRoot '.venv\Scripts');$env:PATH"

Push-Location $repoRoot
try {
    & $python -m pytest tests/direct tests/invariants -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
    & $lint check contracts/palinode.py --json
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint check failed with exit code $LASTEXITCODE" }
    & $lint typecheck contracts/palinode.py --json
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint typecheck failed with exit code $LASTEXITCODE" }
    & $lint schema contracts/palinode.py --output artifacts/palinode_abi.json
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint schema failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
