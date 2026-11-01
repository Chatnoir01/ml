"""RAVEN-006: independent-witness quorum intersection and negative controls.

A passing test does NOT establish real consensus, finality, or durability.
"""
from dataclasses import replace
from hashlib import sha256
from itertools import combinations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_fork_evidence import CheckpointReceipt
from research.raven_quorum_model import (
    Attestation, HonestWitness, QuorumCertificate, Roster,
    prove_witness_double_vote, sign_witness_claim, verify_attestation,
    verify_quorum_certificate,
)
from research.raven_signed_model import Rejected


def digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def rig(n=4, f=1):
    issuer_sk = Ed25519PrivateKey.generate()
    keys = {f"w{i}": Ed25519PrivateKey.generate() for i in range(n)}
    roster = Roster(
        issuer="issuer", namespace="example", compartment="alpha",
        genesis_commitment=digest("genesis"), issuer_key=issuer_sk.public_key(),
        witnesses={key: sk.public_key() for key, sk in keys.items()},
        max_byzantine=f,
    )
    return issuer_sk, keys, roster


def receipt(issuer_sk, roster, child="A", *, parent_epoch=0, parent=None,
            namespace=None, policy="policy"):
    unsigned = CheckpointReceipt(
        issuer=roster.issuer, namespace=namespace or roster.namespace,
        compartment=roster.compartment, parent_epoch=parent_epoch,
        parent_commitment=parent or roster.genesis_commitment,
        child_epoch=parent_epoch + 1, child_commitment=digest(child),
        child_policy_digest=digest(policy), signature=b"",
    )
    return replace(unsigned, signature=issuer_sk.sign(unsigned.message()))


def honest_all(keys, roster):
    return {name: HonestWitness(name, key, roster) for name, key in keys.items()}


@pytest.mark.parametrize("n,f", [(1, 0), (4, 1), (7, 2), (10, 3)])
def test_quorum_formula_has_honest_intersection(n, f):
    issuer, keys, roster = rig(n, f)
    q = roster.quorum
    assert n >= 3 * f + 1
    assert q == n - f
    assert roster.intersection_lower_bound == n - 2 * f > f
    candidate = receipt(issuer, roster)
    signatures = tuple(h.endorse(candidate)
                       for h in list(honest_all(keys, roster).values())[:q])
    verify_quorum_certificate(QuorumCertificate(candidate, signatures), roster)


@pytest.mark.parametrize("n,f", [(4, 1), (7, 2)])
def test_every_quorum_pair_intersects_in_more_than_f(n, f):
    _, _, roster = rig(n, f)
    identities = tuple(roster.witnesses)
    groups = [set(x) for x in combinations(identities, roster.quorum)]
    assert min(len(a & b) for a in groups for b in groups) > f


def test_honest_double_vote_rejected_but_same_receipt_idempotent():
    sk, keys, roster = rig()
    witness = HonestWitness("w0", keys["w0"], roster)
    left = receipt(sk, roster, "left")
    right = receipt(sk, roster, "right")
    first = witness.endorse(left)
    assert witness.endorse(left) == first
    with pytest.raises(Rejected, match="double vote"):
        witness.endorse(right)
    assert len(witness.history.evidence) == 1


def test_two_witnesses_cannot_claim_quorum_of_three():
    sk, keys, roster = rig()
    item = receipt(sk, roster)
    honest = honest_all(keys, roster)
    endorsements = tuple(honest[k].endorse(item) for k in ("w0", "w1"))
    with pytest.raises(Rejected, match="insufficient"):
        verify_quorum_certificate(QuorumCertificate(item, endorsements), roster)


def test_duplicate_attestation_does_not_inflate_quorum():
    sk, keys, roster = rig()
    item = receipt(sk, roster)
    witness = HonestWitness("w0", keys["w0"], roster)
    single = witness.endorse(item)
    with pytest.raises(Rejected, match="duplicate"):
        verify_quorum_certificate(QuorumCertificate(item, (single,) * 3), roster)


def test_certificate_does_not_prove_commit_or_durable_anchor():
    sk, keys, roster = rig()
    item = receipt(sk, roster)
    votes = tuple(h.endorse(item) for h in list(honest_all(keys, roster).values())[:3])
    verify_quorum_certificate(QuorumCertificate(item, votes), roster)
    # No RAVEN-004 anchor was advanced or consulted. This test deliberately
    # demonstrates that quorum signatures alone DO NOT prove finality.


def test_one_byzantine_witness_insufficient_for_two_conflicting_quorums():
    sk, keys, roster = rig()
    left, right = receipt(sk, roster, "left"), receipt(sk, roster, "right")
    honest = honest_all(keys, roster)
    left_votes = [sign_witness_claim(keys["w0"], roster, "w0", left)]
    left_votes += [honest[k].endorse(left) for k in ("w1", "w2")]
    verify_quorum_certificate(QuorumCertificate(left, tuple(left_votes)), roster)
    right_votes = [sign_witness_claim(keys["w0"], roster, "w0", right)]
    right_votes.append(honest["w3"].endorse(right))
    with pytest.raises(Rejected, match="insufficient"):
        verify_quorum_certificate(QuorumCertificate(right, tuple(right_votes)), roster)
    with pytest.raises(Rejected, match="double vote"):
        honest["w1"].endorse(right)
    with pytest.raises(Rejected, match="double vote"):
        honest["w2"].endorse(right)


def test_two_compromised_keys_can_form_conflicting_quorums_negative_control():
    sk, keys, roster = rig(n=4, f=1)
    left, right = receipt(sk, roster, "left"), receipt(sk, roster, "right")
    honest = honest_all(keys, roster)
    a1 = sign_witness_claim(keys["w0"], roster, "w0", left)
    b1 = sign_witness_claim(keys["w0"], roster, "w0", right)
    a2 = sign_witness_claim(keys["w1"], roster, "w1", left)
    b2 = sign_witness_claim(keys["w1"], roster, "w1", right)
    left_qc = QuorumCertificate(left, (a1, a2, honest["w2"].endorse(left)))
    right_qc = QuorumCertificate(right, (b1, b2, honest["w3"].endorse(right)))
    verify_quorum_certificate(left_qc, roster)
    verify_quorum_certificate(right_qc, roster)
    proof = prove_witness_double_vote(a1, left, b1, right, roster)
    assert proof == (a1, b1)
    # The f=1 assumption was violated (two keys compromised).
    # Both certificates validate: signatures alone cannot fix a false trust assumption.


def test_honest_guard_rollback_allows_double_vote_negative_control():
    sk, keys, roster = rig()
    left, right = receipt(sk, roster, "left"), receipt(sk, roster, "right")
    original = HonestWitness("w0", keys["w0"], roster)
    first = original.endorse(left)
    # Simulate rollback/restart that loses the non-durable one-vote memory.
    restarted = HonestWitness("w0", keys["w0"], roster)
    second = restarted.endorse(right)
    prove_witness_double_vote(first, left, second, right, roster)


@pytest.mark.parametrize("field,value", [
    ("witness", "w3"),
    ("issuer", "other"),
    ("namespace", "foreign"),
    ("compartment", "different"),
    ("genesis_commitment", "0" * 64),
    ("parent_epoch", 7),
    ("parent_commitment", "0" * 64),
    ("child_epoch", 99),
    ("receipt_hash", "0" * 64),
    ("signature", b"\x00" * 64),
])
def test_tampered_attestation_rejected(field, value):
    issuer, keys, roster = rig()
    item = receipt(issuer, roster)
    signed = HonestWitness("w0", keys["w0"], roster).endorse(item)
    with pytest.raises(Rejected):
        verify_attestation(replace(signed, **{field: value}), item, roster)


def test_wrong_signer_key_cannot_impersonate_roster_member():
    issuer, keys, roster = rig()
    with pytest.raises(Rejected, match="wrong witness"):
        sign_witness_claim(keys["w1"], roster, "w0", receipt(issuer, roster))


def test_receipt_signed_by_wrong_issuer_rejected():
    issuer, keys, roster = rig()
    attacker = Ed25519PrivateKey.generate()
    item = receipt(attacker, roster)
    with pytest.raises(Rejected, match="signature"):
        HonestWitness("w0", keys["w0"], roster).endorse(item)


def test_attestation_cannot_be_reused_for_other_signed_child():
    issuer, keys, roster = rig()
    left, right = receipt(issuer, roster, "left"), receipt(issuer, roster, "right")
    att = HonestWitness("w0", keys["w0"], roster).endorse(left)
    with pytest.raises(Rejected, match="checkpoint mismatch"):
        verify_attestation(att, right, roster)


def test_valid_issuer_receipt_wrong_namespace_rejected():
    issuer, keys, roster = rig()
    different = receipt(issuer, roster, namespace="other")
    with pytest.raises(Rejected, match="scope"):
        HonestWitness("w0", keys["w0"], roster).endorse(different)


def test_only_genesis_transition_certified():
    issuer, keys, roster = rig()
    future = receipt(issuer, roster, "future",
                     parent_epoch=1, parent=digest("root-child"))
    with pytest.raises(Rejected, match="pinned-genesis"):
        HonestWitness("w0", keys["w0"], roster).endorse(future)


def test_roster_rejects_duplicate_public_keys_and_impossible_thresholds():
    issuer, keys, roster = rig()
    with pytest.raises(ValueError, match="independently distinct"):
        Roster(roster.issuer, roster.namespace, roster.compartment,
               roster.genesis_commitment, issuer.public_key(),
               {"w0": keys["w0"].public_key(), "w1": keys["w0"].public_key()}, 0)
    with pytest.raises(ValueError, match="3f"):
        Roster(roster.issuer, roster.namespace, roster.compartment,
               roster.genesis_commitment, issuer.public_key(),
               {k: v.public_key() for k, v in keys.items()}, 2)


def test_new_roster_with_other_public_key_rejects_old_signature():
    issuer, keys, roster = rig()
    item = receipt(issuer, roster)
    original = HonestWitness("w0", keys["w0"], roster).endorse(item)
    keys2 = dict(roster.witnesses)
    keys2["w0"] = Ed25519PrivateKey.generate().public_key()
    changed = Roster(roster.issuer, roster.namespace, roster.compartment,
                     roster.genesis_commitment, roster.issuer_key, keys2, 1)
    with pytest.raises(Rejected, match="signature"):
        verify_attestation(original, item, changed)


def test_signed_double_vote_evidence_rejects_other_signer():
    issuer, keys, roster = rig()
    left, right = receipt(issuer, roster, "left"), receipt(issuer, roster, "right")
    a = sign_witness_claim(keys["w0"], roster, "w0", left)
    b = sign_witness_claim(keys["w1"], roster, "w1", right)
    with pytest.raises(Rejected, match="same witness"):
        prove_witness_double_vote(a, left, b, right, roster)


def test_same_receipt_not_double_vote():
    issuer, keys, roster = rig()
    item = receipt(issuer, roster)
    att = sign_witness_claim(keys["w0"], roster, "w0", item)
    with pytest.raises(Rejected, match="not conflicting"):
        prove_witness_double_vote(att, item, att, item, roster)


def test_network_partition_blocks_quorum_until_witnesses_share_signatures():
    issuer, keys, roster = rig(n=7, f=2)
    item = receipt(issuer, roster)
    honest = honest_all(keys, roster)
    # Partitions are conceptual subsets of the same pinned roster.
    group_a = tuple(honest[f"w{i}"].endorse(item) for i in range(4))
    group_b = tuple(honest[f"w{i}"].endorse(item) for i in range(4, 7))
    with pytest.raises(Rejected, match="insufficient"):
        verify_quorum_certificate(QuorumCertificate(item, group_a), roster)
    with pytest.raises(Rejected, match="insufficient"):
        verify_quorum_certificate(QuorumCertificate(item, group_b), roster)
    verify_quorum_certificate(QuorumCertificate(item, group_a + group_b[:1]), roster)
