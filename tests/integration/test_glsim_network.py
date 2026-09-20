"""Real JSON-RPC GLSim integration harness.

Run explicitly with ``pytest tests/integration/test_glsim_network.py``.  The
test starts the installed GLSim binary on an isolated port, uses sim_deploy /
sim_call / sim_read, and records a precise runtime blocker when the installed
GenLayer runner cannot execute the source.  It never contacts Studionet.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests


ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _rpc(url: str, method: str, params):
    response = requests.post(
        url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise RuntimeError(body["error"].get("message", str(body["error"])))
    return body["result"]


@pytest.fixture(scope="module")
def glsim_url():
    port = _free_port()
    executable = ROOT / ".venv" / "Scripts" / "glsim.exe"
    if not executable.exists():
        pytest.skip("GLSim executable is not installed")
    process = subprocess.Popen(
        [str(executable), "--port", str(port), "--validators", "3", "--max-rotations", "2", "--chain-id", "61999", "--no-browser", "--seed", "palinode-integration"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}/api"
    deadline = time.time() + 30
    try:
        while time.time() < deadline:
            try:
                if _rpc(url, "ping", []) == "pong":
                    yield url
                    return
            except Exception:
                time.sleep(0.25)
        pytest.fail("GLSim did not become ready within 30 seconds")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def test_glsim_reports_target_chain_and_accepts_rpc(glsim_url):
    assert _rpc(glsim_url, "eth_chainId", []) == "0xf22f"
    assert _rpc(glsim_url, "ping", []) == "pong"


def test_glsim_deploy_schema_and_deterministic_readback(glsim_url):
    try:
        deployed = _rpc(
            glsim_url,
            "sim_deploy",
            {"code_path": "contracts/palinode.py", "sender": "0x" + "1" * 40},
        )
    except Exception as exc:
        message = str(exc)
        if "WinError 32" in message or "Compressed file ended" in message or "runner" in message.lower():
            pytest.skip("GLSIM_RUNTIME_BLOCKER: " + message)
        raise
    contract_address = deployed["contract_address"]
    schema = _rpc(glsim_url, "sim_getContractSchema", {"contract_address": contract_address})
    assert "methods" in schema
    sender = "0x" + "1" * 40
    node_id = _rpc(
        glsim_url,
        "sim_call",
        {"to": contract_address, "method": "register_claim", "args": ["integration", "GLSim claim"], "sender": sender},
    )["result"]
    decision_id = _rpc(
        glsim_url,
        "sim_call",
        {"to": contract_address, "method": "register_decision", "args": ["integration", "GLSim decision"], "sender": sender},
    )["result"]
    record = _rpc(glsim_url, "sim_read", {"to": contract_address, "method": "get_node_record", "args": [node_id]})["result"]
    assert record["assessment_status"] == "UNASSESSED"
    assert record["status"] == "ACTIVE"
    edge_id = _rpc(
        glsim_url,
        "sim_call",
        {
            "to": contract_address,
            "method": "register_dependency",
            "args": [node_id, decision_id, "SUPPORTS"],
            "sender": sender,
        },
    )["result"]
    edge = _rpc(glsim_url, "sim_read", {"to": contract_address, "method": "get_dependency_record", "args": [edge_id]})["result"]
    assert edge["parent_node_id"] == node_id
    assert edge["child_node_id"] == decision_id
