"""Validate the canonical machine-readable V4 release manifest."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence" / "studionet" / "v4" / "release-manifest.json"
CONTRACT = ROOT / "contracts" / "palinode_v2.py"
EXPECTED_HASH = "0f23a120776b09be989e6112b34d27ae415e1808232be591f94d1e17d80c5601"
EXPECTED_ADDRESS = "0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b"
EXPECTED_RPC = "https://studio.genlayer.com/api"
EXPECTED_FREEZE = "14bb4574a8d248c978b55ff1fb70f32c0293f313"
EXPECTED_INITIAL_V4 = "be8a14b09f4ad1f40a9fdb0429dd16d3942795a9"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TX_RE = re.compile(r"^0x[0-9a-f]{64}$")


def fail(message: str) -> int:
    print(f"RELEASE_MANIFEST=FAIL: {message}")
    return 1


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot read JSON: {exc}")

    required = {
        "version",
        "network",
        "chainId",
        "rpc",
        "contractAddress",
        "sourcePath",
        "sourceSha256",
        "contractFreezeCommit",
        "initialV4ReleaseSourceCommit",
        "currentRepositoryReleaseHead",
        "productionUrl",
        "productionDeploymentId",
        "productionAlias",
        "schema",
        "testSummary",
        "walletProofTransaction",
        "canonicalV4ProofState",
        "evidenceFiles",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        return fail(f"missing fields: {missing}")
    if manifest["version"] != "4.0.0":
        return fail("version is not 4.0.0")
    if manifest["network"] != "Studionet" or manifest["chainId"] != 61999:
        return fail("network or chain ID drifted")
    if manifest["rpc"] != EXPECTED_RPC or manifest["contractAddress"] != EXPECTED_ADDRESS:
        return fail("RPC or contract address drifted")
    if manifest["sourcePath"] != "contracts/palinode_v2.py":
        return fail("source path is not the frozen V4 source")
    actual_hash = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_HASH or manifest["sourceSha256"] != EXPECTED_HASH:
        return fail(f"source hash mismatch: {actual_hash}")
    if manifest["contractFreezeCommit"] != EXPECTED_FREEZE:
        return fail("contract freeze commit drifted")
    if manifest["initialV4ReleaseSourceCommit"] != EXPECTED_INITIAL_V4:
        return fail("initial V4 release source identity drifted")
    release_head = str(manifest["currentRepositoryReleaseHead"])
    if not SHA_RE.fullmatch(release_head):
        return fail("current repository release HEAD is not a commit SHA")
    subprocess.run(["git", "cat-file", "-e", f"{release_head}^{{commit}}"], cwd=ROOT, check=True)
    if not str(manifest["productionUrl"]).startswith("https://"):
        return fail("production URL must be HTTPS")
    if not re.fullmatch(r"dpl_[A-Za-z0-9]+", str(manifest["productionDeploymentId"])):
        return fail("production deployment ID is not a Vercel deployment ID")
    if manifest["productionAlias"] != "palinode-app.vercel.app":
        return fail("production alias drifted")
    if manifest["schema"] != {"total": 46, "writes": 21, "views": 25}:
        return fail("schema method counts drifted")
    tests = manifest["testSummary"]
    if tests.get("contract") != {
        "direct": 28,
        "invariants": 5,
        "adversarial": 34,
        "property": 2,
        "v2": 27,
        "total": 96,
    }:
        return fail("contract test counts are not reconciled")
    if tests.get("mutation") != {"total": 49, "killed": 46, "retired": 3, "survived": 0}:
        return fail("mutation result drifted")
    if tests.get("frontend", {}).get("tests") != 57:
        return fail("frontend test count is not reconciled")
    if tests.get("browser", {}).get("deterministicRouteAssertions") != 96:
        return fail("browser assertion count is not reconciled")
    if manifest["walletProofTransaction"] != "0x5550723fae8da058933a3b8adc7a54280170573132ad224b2e00756ff0e63451":
        return fail("wallet proof transaction drifted")
    if not isinstance(manifest["canonicalV4ProofState"], dict):
        return fail("canonical proof state must be an object")
    for relative in manifest["evidenceFiles"]:
        posix_path = PurePosixPath(str(relative))
        path = Path(*posix_path.parts)
        if posix_path.is_absolute() or ".." in posix_path.parts or not str(posix_path).startswith("evidence/studionet/v4/"):
            return fail(f"invalid evidence reference: {relative}")
        if not (ROOT / path).is_file():
            return fail(f"missing evidence reference: {relative}")
    serialized = json.dumps(manifest, sort_keys=True)
    if re.search(r"BEGIN (?:RSA|EC|OPENSSH|PGP|DSA|PRIVATE) KEY|private[_ -]?key|vercel[_ -]?token", serialized, re.IGNORECASE):
        return fail("manifest contains a secret-like field")
    print("RELEASE_MANIFEST=PASS")
    print(f"SOURCE_SHA256={actual_hash}")
    print("SCHEMA_METHODS=46 SCHEMA_WRITES=21 SCHEMA_VIEWS=25")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
