$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$lint = Join-Path $repoRoot ".venv\Scripts\genvm-lint.exe"
$env:GENVM_VERSION = "v0.2.16"
$env:PYTHONIOENCODING = "utf-8"
$env:PATH = "$(Join-Path $repoRoot '.venv\Scripts');$env:PATH"

Push-Location $repoRoot
try {
    $expectedHash = "0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601"
    $actualHash = (Get-FileHash -Algorithm SHA256 (Join-Path $repoRoot "contracts\palinode_v2.py")).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) { throw "frozen V4 source hash mismatch: $actualHash" }
    & $python -m pytest tests/direct tests/invariants tests/adversarial tests/property tests/v2 -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }
    & $lint lint contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint lint failed with exit code $LASTEXITCODE" }
    & $lint validate contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint validate failed with exit code $LASTEXITCODE" }
    & $lint typecheck contracts/palinode_v2.py
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint typecheck failed with exit code $LASTEXITCODE" }
    New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot "artifacts") | Out-Null
    & $lint schema contracts/palinode_v2.py --output artifacts/palinode_schema.json
    if ($LASTEXITCODE -ne 0) { throw "genvm-lint schema failed with exit code $LASTEXITCODE" }
    & $python scripts/validate_release_manifest.py
    if ($LASTEXITCODE -ne 0) { throw "release manifest validation failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
