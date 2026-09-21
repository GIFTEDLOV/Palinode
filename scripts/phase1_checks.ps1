$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$lint = Join-Path $repoRoot ".venv\Scripts\genvm-lint.exe"
$env:GENVM_VERSION = "v0.2.16"
$env:PATH = "$(Join-Path $repoRoot '.venv\Scripts');$env:PATH"

Push-Location $repoRoot
try {
    & $python -m pytest tests/direct tests/invariants tests/adversarial tests/property tests/v2 -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
    & $lint lint contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint lint failed with exit code $LASTEXITCODE" }
    & $lint validate contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint validate failed with exit code $LASTEXITCODE" }
    & $lint typecheck contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint typecheck failed with exit code $LASTEXITCODE" }
    & $lint schema contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint schema failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
