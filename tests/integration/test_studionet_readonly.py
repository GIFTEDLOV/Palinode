"""Read-only hosted Studionet and fixture checks.

These tests never submit a transaction. The broadcast canary is intentionally
separate and remains gated on explicit funding/preflight.
"""

from pathlib import Path

import requests


RPC_URL = "https://studio.genlayer.com/api"
CHAIN_ID = 61999
FIXTURE_ORIGIN = "https://palinode-fixture.vercel.app"
ROOT = Path(__file__).resolve().parents[2]


def rpc(method: str, params: list[object]):
    response = requests.post(
        RPC_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    assert "error" not in body, body
    return body["result"]


def test_studionet_chain_identity_is_readable_without_broadcast():
    assert rpc("eth_chainId", []) == hex(CHAIN_ID)


def test_live_fixture_matches_committed_bytes_without_broadcast():
    paths = (
        ".well-known/palinode.json",
        "evidence/vendor-audit-v1.json",
        "evidence/vendor-audit-v2.json",
        "notices/vendor-audit-v1-revoked.json",
        "notices/vendor-audit-v1-correction.json",
    )
    for relative in paths:
        expected = (ROOT / "fixture" / relative).read_bytes()
        response = requests.get(FIXTURE_ORIGIN + "/" + relative, timeout=30)
        assert response.status_code == 200
        assert response.content == expected
