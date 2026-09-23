"""Scan tracked repository files for high-confidence secret material."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP|DSA|PRIVATE) KEY-----"),
    re.compile(r"\b(?:ghp_|github_pat_|xox[baprs]-|AKIA[0-9A-Z]{16})[A-Za-z0-9_-]{12,}\b"),
    re.compile(
        r"\b(?:VERCEL_TOKEN|GH_TOKEN|GITHUB_TOKEN|OPENAI_API_KEY|PRIVATE_KEY|SECRET_KEY)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{20,}"
    ),
)


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    findings: list[str] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = ROOT / raw_path.decode("utf-8")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    if findings:
        print("Potential secrets found in tracked files:")
        print("\n".join(sorted(findings)))
        return 1
    print("SECRET_SCAN=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
