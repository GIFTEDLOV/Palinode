import hashlib
import os
import random


CONTRACT = os.environ.get("PALINODE_CONTRACT", "contracts/palinode.py")


def test_generated_forward_graphs_preserve_creation_order(direct_deploy):
    rng = random.Random(61999)
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    nodes = [contract.register_claim("property", "Node " + str(index)) for index in range(40)]
    for _ in range(80):
        parent_index = rng.randrange(0, len(nodes) - 1)
        child_index = rng.randrange(parent_index + 1, len(nodes))
        relationship = rng.choice(("SUPPORTS", "REQUIRES", "DERIVED_FROM", "QUALIFIES", "AUTHORIZES", "CORROBORATES", "CONTRADICTS"))
        identity = (nodes[parent_index], nodes[child_index], relationship)
        try:
            contract.register_dependency(*identity)
        except Exception:
            # The generated set can repeat an identity; duplicate rejection is
            # part of the invariant and does not alter the forward-order proof.
            pass
    edge_page = contract.get_edge_ids_page(0, 64)
    for index in range(int(edge_page["count"])):
        edge_id = edge_page["slot_" + str(index)]
        edge = contract.get_dependency_record(edge_id)
        parent = contract.get_node_record(edge["parent_node_id"])
        child = contract.get_node_record(edge["child_node_id"])
        assert int(parent["creation_sequence"]) < int(child["creation_sequence"])


def test_generated_identifiers_are_contract_derived_and_unique(direct_deploy):
    contract = direct_deploy(CONTRACT, sdk_version="v0.2.16")
    identifiers = [contract.register_claim("property", "Repeated") for _ in range(32)]
    assert len(set(identifiers)) == len(identifiers)
    assert all(len(identifier) == 64 for identifier in identifiers)
    assert all(all(character in "0123456789abcdef" for character in identifier) for identifier in identifiers)
