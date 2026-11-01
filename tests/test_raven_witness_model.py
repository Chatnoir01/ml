"""Adversarial model tests for RAVEN-005; not a security proof."""
from dataclasses import replace
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_fork_evidence import CheckpointReceipt
from research.raven_witness_model import Network, Witness, WitnessRejected


def h(value):
    return sha256(value.encode("ascii")).hexdigest()


def sign_receipt(sk, *, issuer="log", namespace="project", compartment="B",
                 parent_epoch=0, parent_commitment=None, child_commitment=None,
                 child_policy_digest=None, event="branch-a"):
    parent = parent_commitment or h("genesis")
    child = child_commitment or h(event)
    unsigned = CheckpointReceipt(
        issuer=issuer, namespace=namespace, compartment=compartment,
        parent_epoch=parent_epoch, parent_commitment=parent,
        child_epoch=parent_epoch + 1, child_commitment=child,
        child_policy_digest=child_policy_digest or h("policy"), signature=b"",
    )
    return replace(unsigned, signature=sk.sign(unsigned.message()))


def rig(names=("alice", "bob", "carol"), max_receipts=4096):
    sk = Ed25519PrivateKey.generate()
    witnesses = [Witness(name=n, issuer="log", namespace="project",
                         compartment="B", genesis_commitment=h("genesis"),
                         issuer_key=sk.public_key(), max_receipts=max_receipts)
                 for n in names]
    return sk, witnesses


def test_partition_hides_fork_then_gossip_exposes_signed_conflict():
    sk, (a, b, c) = rig()
    left, right = sign_receipt(sk, event="left"), sign_receipt(sk, event="right")
    a.observe(left)
    b.observe(right)
    network = Network((a, b, c))
    network.blocked.add(("alice", "carol"))
    network.blocked.add(("bob", "carol"))
    blocked = network.step([("alice", "carol"), ("bob", "carol")])
    assert all(r.blocked for r in blocked)
    assert not a.evidence and not b.evidence and not c.evidence
    assert network.first_evidence_round == {}
    network.blocked.clear()
    sent = network.step([("alice", "carol"), ("bob", "carol")])
    assert [r.sent for r in sent] == [1, 1]
    assert c.connected_count == 2 and len(c.evidence) == 1
    assert network.first_evidence_round == {"carol": 2}
    proof = c.evidence[0]
    assert proof[0].parent_commitment == proof[1].parent_commitment
    assert proof[0].child_commitment != proof[1].child_commitment
    assert network.bytes_sent > 0
    network.step([("carol", "alice"), ("carol", "bob")])
    assert len(a.evidence) == len(b.evidence) == 1
    assert network.first_evidence_round == {"carol": 2, "alice": 3, "bob": 3}


def test_orphan_child_is_not_trusted_until_parent_arrives():
    sk, (a, b, c) = rig()
    first = sign_receipt(sk, event="first")
    second = sign_receipt(sk, parent_epoch=1,
                          parent_commitment=first.child_commitment, event="second")
    fork = sign_receipt(sk, parent_epoch=1,
                        parent_commitment=first.child_commitment, event="fork")
    assert a.observe(second)
    assert a.observe(fork)
    assert a.orphan_count == 2
    assert a.connected_count == 0 and not a.evidence
    a.observe(first)
    assert a.orphan_count == 0
    assert a.connected_count == 3 and len(a.evidence) == 1


def test_sibling_branch_is_fork_but_descendant_is_not():
    sk, (a, b, c) = rig()
    first = sign_receipt(sk, event="first")
    descendant = sign_receipt(sk, parent_epoch=1,
                              parent_commitment=first.child_commitment, event="descendant")
    a.observe(first)
    a.observe(descendant)
    assert len(a.evidence) == 0 and a.connected_count == 2


def test_hidden_branch_indefinitely_undetectable_with_no_exchange():
    sk, (a, b, c) = rig()
    a.observe(sign_receipt(sk, event="left"))
    b.observe(sign_receipt(sk, event="right"))
    net = Network((a, b, c))
    for _ in range(30):
        net.step([("alice", "carol")])
    assert len(a.evidence) == len(b.evidence) == len(c.evidence) == 0
    assert c.receipt_count == 1
    assert net.first_evidence_round == {}


def test_mutations_of_signed_receipt_rejected_and_not_stored():
    sk, (a, b, c) = rig()
    base = sign_receipt(sk, event="one")
    for field, value in [
        ("compartment", "A"), ("namespace", "different"),
        ("parent_commitment", h("other")), ("child_commitment", h("invalid")),
        ("child_policy_digest", h("fake")), ("signature", b"\x00" * 64),
    ]:
        with pytest.raises(ValueError):
            a.observe(replace(base, **{field: value}))
    assert a.receipt_count == 0


def test_valid_signature_for_different_scope_rejected():
    sk, (a, b, c) = rig()
    with pytest.raises(WitnessRejected, match="scope"):
        a.observe(sign_receipt(sk, namespace="unrelated"))


def test_untrusted_signer_receipt_rejected():
    sk, (a, b, c) = rig()
    rogue = Ed25519PrivateKey.generate()
    with pytest.raises(ValueError, match="signature"):
        a.observe(sign_receipt(rogue))


def test_pinned_genesis_disallows_unconnected_fork_evidence():
    sk, (a, b, c) = rig()
    a.observe(sign_receipt(sk, parent_epoch=5, parent_commitment=h("foreign"), event="x"))
    a.observe(sign_receipt(sk, parent_epoch=5, parent_commitment=h("foreign"), event="y"))
    assert a.orphan_count == 2 and a.connected_count == 0
    assert not a.evidence


def test_duplicate_receipts_are_idempotent_and_gossip_deduplicated():
    sk, (a, b, c) = rig()
    receipt = sign_receipt(sk, event="one")
    assert a.observe(receipt) is True
    assert a.observe(receipt) is False
    assert a.send_to(b).sent == 1
    assert a.send_to(b).sent == 0
    assert b.receipt_count == 1


def test_capacity_limit_is_fail_closed():
    sk, (a, b, c) = rig(max_receipts=1)
    a.observe(sign_receipt(sk, event="one"))
    with pytest.raises(WitnessRejected, match="capacity"):
        a.observe(sign_receipt(sk, event="two"))
    assert a.receipt_count == 1


def test_different_trust_roots_cannot_gossip():
    sk, (a, b, c) = rig()
    other_sk = Ed25519PrivateKey.generate()
    rogue = Witness(name="rogue", issuer="log", namespace="project",
                    compartment="B", genesis_commitment=h("genesis"),
                    issuer_key=other_sk.public_key())
    with pytest.raises(WitnessRejected, match="different"):
        a.send_to(rogue)


def test_wrong_genesis_is_rejected_for_gossip():
    sk, (a, b, c) = rig()
    other = Witness(name="other", issuer="log", namespace="project",
                    compartment="B", genesis_commitment=h("different"),
                    issuer_key=sk.public_key())
    with pytest.raises(WitnessRejected):
        a.send_to(other)


def test_bad_digest_format_cannot_enter_even_with_valid_signature():
    sk, (a, b, c) = rig()
    with pytest.raises(WitnessRejected, match="digest"):
        a.observe(sign_receipt(sk, child_commitment="not-sha256-hex"))


def test_cyclic_commitment_rejected_even_when_signed():
    sk, (a, b, c) = rig()
    with pytest.raises(WitnessRejected, match="self-commitment"):
        a.observe(sign_receipt(sk, child_commitment=h("genesis")))


def test_gossip_limit_bounds_transmissions():
    sk, (a, b, c) = rig()
    for x in range(10):
        a.observe(sign_receipt(sk, event=f"child-{x}"))
    assert a.send_to(b, limit=3).sent == 3
    assert b.receipt_count == 3
    assert a.send_to(b, limit=0).sent == 0
    with pytest.raises(ValueError):
        a.send_to(b, limit=-1)
    while b.receipt_count < 10:
        a.send_to(b, limit=3)
    assert b.receipt_count == 10


def test_competing_children_different_policy_digest_detected():
    sk, (a, b, c) = rig()
    x = sign_receipt(sk, event="same", child_policy_digest=h("one"))
    y = sign_receipt(sk, event="same", child_policy_digest=h("two"))
    a.observe(x)
    a.observe(y)
    assert len(a.evidence) == 1


def test_bad_network_setup_rejects_duplicate_names():
    sk, (a, b, c) = rig()
    with pytest.raises(ValueError, match="duplicate"):
        Network((a, a))


def test_untrusted_origin_namespace_not_shared():
    sk, (a, b, c) = rig()
    w = Witness(name="different", issuer="log", namespace="other",
                compartment="B", genesis_commitment=h("genesis"),
                issuer_key=sk.public_key())
    with pytest.raises(WitnessRejected):
        a.send_to(w)


@pytest.mark.parametrize("count", [4, 8, 16])
def test_bidirectional_ring_eventually_propagates_signed_fork(count):
    labels = tuple(f"w{i}" for i in range(count))
    sk, witnesses = rig(labels)
    witnesses[0].observe(sign_receipt(sk, event="left"))
    witnesses[count // 2].observe(sign_receipt(sk, event="right"))
    net = Network(witnesses)
    ring = [(labels[i], labels[(i + 1) % count]) for i in range(count)]
    ring += [(labels[(i + 1) % count], labels[i]) for i in range(count)]
    for _ in range(count + 2):
        net.step(ring)
    assert all(len(w.evidence) == 1 for w in witnesses)
    assert len(net.first_evidence_round) == count
    assert net.bytes_sent > 0


def test_asymmetric_partition_witness_cannot_invent_fork():
    sk, (a, b, c) = rig()
    a.observe(sign_receipt(sk, event="left"))
    b.observe(sign_receipt(sk, event="right"))
    net = Network((a, b, c))
    net.blocked.add(("bob", "carol"))
    for i in range(15):
        net.step([("alice", "carol"), ("bob", "carol")])
    assert c.receipt_count == 1 and c.evidence == ()
    assert net.deliveries == 1
    net.blocked.clear()
    net.step([("bob", "carol")])
    assert len(c.evidence) == 1


def test_one_network_round_does_not_forward_newly_received_receipts():
    sk, (a, b, c) = rig()
    a.observe(sign_receipt(sk, event="left"))
    net = Network((a, b, c))
    net.step([("alice", "bob"), ("bob", "carol")])
    assert b.receipt_count == 1
    assert c.receipt_count == 0  # no same-round cascading relay
    net.step([("bob", "carol")])
    assert c.receipt_count == 1
