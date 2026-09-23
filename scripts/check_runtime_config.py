"""Guard the frontend against network, address, and archived-runtime drift."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "frontend" / "src" / "config.ts"
RUNTIME_ROOTS = (ROOT / "frontend" / "src", ROOT / "frontend" / "api")
CURRENT_ADDRESS = "0x05243cB6db90EE210a22Aa3c16fdc4F893d7b13b"
ARCHIVED_ADDRESSES = {
    "0x9c9d1993cd938846D1163Bba9AA81AC6d165de88",
    "0x712Dbb59F950D0D300d3E89Ed2Ac52db715383E4",
    "0xDD918F99553717f6e157A7Ca2FfE902B4E3a438B",
}


def runtime_files() -> list[Path]:
    return [
        path
        for root in RUNTIME_ROOTS
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".ts", ".tsx", ".js", ".jsx"}
    ]


def main() -> int:
    config = CONFIG.read_text(encoding="utf-8")
    required = (
        "export const NETWORK = 'Studionet';",
        "export const CHAIN_ID = 61999;",
        "https://studio.genlayer.com/api",
        f"export const CONTRACT_ADDRESS = '{CURRENT_ADDRESS}'",
    )
    missing = [value for value in required if value not in config]
    if missing:
        print("RUNTIME_CONFIG=FAIL")
        print("Missing required frozen runtime values:")
        print("\n".join(missing))
        return 1

    findings: list[str] = []
    for path in runtime_files():
        text = path.read_text(encoding="utf-8")
        for address in ARCHIVED_ADDRESSES:
            if re.search(re.escape(address), text, re.IGNORECASE):
                findings.append(f"{path.relative_to(ROOT)} contains archived address {address}")
        if "61997" in text or "studio-dev" in text.lower() or "bradbury" in text.lower():
            findings.append(f"{path.relative_to(ROOT)} contains a non-Studionet runtime target")
    if findings:
        print("RUNTIME_CONFIG=FAIL")
        print("\n".join(findings))
        return 1
    print("RUNTIME_CONFIG=PASS")
    print(f"NETWORK=Studionet CHAIN_ID=61999 CONTRACT={CURRENT_ADDRESS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
