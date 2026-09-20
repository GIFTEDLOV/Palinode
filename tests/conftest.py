"""Small Windows/Python 3.14 compatibility shim for genlayer-test direct mode.

genlayer-test 0.29.2 unlinks its temporary stdin file while fd 0 is still
open. Windows rejects that operation. The shim preserves the SDK behavior and
defers cleanup until the VM restores stdin.
"""

import os
import tempfile

import pytest

import gltest.direct.loader as direct_loader


def _inject_message_without_early_unlink(vm):
    import genlayer.py.calldata as calldata
    from genlayer.py.types import Address

    sender_addr = vm.sender
    if isinstance(sender_addr, bytes):
        sender_addr = Address(sender_addr)
    contract_addr = vm._contract_address
    if isinstance(contract_addr, bytes):
        contract_addr = Address(contract_addr)
    origin_addr = vm.origin
    if isinstance(origin_addr, bytes):
        origin_addr = Address(origin_addr)
    message_data = {
        "contract_address": contract_addr,
        "sender_address": sender_addr,
        "origin_address": origin_addr,
        "stack": [],
        "value": vm._value,
        "datetime": vm._datetime,
        "is_init": False,
        "chain_id": vm._chain_id,
        "entry_kind": 0,
        "entry_data": b"",
        "entry_stage_data": None,
    }
    encoded = calldata.encode(message_data)
    fd, path = tempfile.mkstemp()
    os.write(fd, encoded)
    os.lseek(fd, 0, os.SEEK_SET)
    original_stdin = os.dup(0)
    vm._original_stdin_fd = original_stdin
    os.dup2(fd, 0)
    os.close(fd)
    vm._palinode_stdin_path = path


direct_loader._inject_message_to_fd0 = _inject_message_without_early_unlink


@pytest.fixture(autouse=True)
def configure_direct_runtime(direct_vm):
    """Use the harness' strict mock and serialization checks by default."""
    direct_vm.strict_mocks = True
    direct_vm.check_pickling = True
    yield
