"""RAVEN-004 fork receipts: valid and invalid proof experiments."""
from copy import deepcopy
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_fork_evidence import (
    issue_receipt, prove_conflicting_receipts, verify_receipt,
)
from research.raven_recovery_model import JournaledMachine, VolatileStore
from research.raven_signed_model import (
    InMemoryAnchor, Policy, Rejected, genesis, sign_transition,
)


def fork_rig():
    transitions = Ed25519PrivateKey.generate()
    checkpoint = Ed25519PrivateKey.generate()
    original = genesis("research", "B", Policy(frozenset({"classical", "hybrid"}), 1))
    receipts = []
    for event in ("branch-left", "branch-right"):
        anchor = InMemoryAnchor()
        before = deepcopy(original)
        anchor.register(before)
        store = VolatileStore(deepcopy(before))
        change = sign_transition(
            transitions, state=before,
            next_policy=Policy(frozenset({"hybrid"}), 2),
            selected_suite="hybrid", event_id=event,
        )
        JournaledMachine(store, anchor, transitions.public_key()).transition(change)
        receipt = issue_receipt(
            anchor=anchor, previous=before, change=change,
            transition_authority=transitions.public_key(),
            issuer="checkpoint-authority", checkpoint_signer=checkpoint,
        )
        receipts.append(receipt)
    return transitions, checkpoint, receipts


def test_conflicting_valid_receipts_detectable_when_gossiped():
    transitions, checkpoint, (left, right) = fork_rig()
    proof = prove_conflicting_receipts(left, right, checkpoint.public_key())
    assert proof == (left, right)
    assert left.parent_commitment == right.parent_commitment
    assert left.child_commitment != right.child_commitment


def test_receipt_signatures_individually_verify():
    transitions, checkpoint, (left, right) = fork_rig()
    verify_receipt(left, checkpoint.public_key())
    verify_receipt(right, checkpoint.public_key())


@pytest.mark.parametrize("field,value", [
    ("issuer", "forged"), ("namespace", "other"), ("compartment", "A"),
    ("parent_epoch", 17), ("parent_commitment", "0" * 64),
    ("child_epoch", 42), ("child_commitment", "0" * 64),
    ("child_policy_digest", "0" * 64), ("signature", b"\x00" * 64),
])
def test_tampering_proof_fields_rejected(field, value):
    transitions, checkpoint, (left, right) = fork_rig()
    with pytest.raises(Rejected):
        prove_conflicting_receipts(replace(left, **{field: value}), right,
                                   checkpoint.public_key())


def test_different_checkpoint_signer_cannot_validate_receipts():
    transitions, checkpoint, (left, right) = fork_rig()
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(Rejected, match="signature"):
        prove_conflicting_receipts(left, right, attacker.public_key())


def test_same_receipt_is_not_fork():
    transitions, checkpoint, (left, right) = fork_rig()
    with pytest.raises(Rejected, match="no conflicting"):
        prove_conflicting_receipts(left, left, checkpoint.public_key())


def test_different_parent_not_same_origin():
    transitions, checkpoint, (left, right) = fork_rig()
    bogus = replace(right, parent_commitment="different")
    # Tampering without a new signature must fail authentication first.
    with pytest.raises(Rejected, match="signature"):
        prove_conflicting_receipts(left, bogus, checkpoint.public_key())
    properly_resigned = replace(bogus, signature=b"")
    properly_resigned = replace(
        properly_resigned, signature=checkpoint.sign(properly_resigned.message())
    )
    with pytest.raises(Rejected, match="not the same"):
        prove_conflicting_receipts(left, properly_resigned, checkpoint.public_key())


def test_receipt_cannot_be_issued_before_anchor_commit():
    transition_sk = Ed25519PrivateKey.generate()
    witness_sk = Ed25519PrivateKey.generate()
    state = genesis("research", "B", Policy(frozenset({"hybrid"}), 2))
    anchor = InMemoryAnchor()
    anchor.register(state)
    proposal = sign_transition(
        transition_sk, state=state, next_policy=state.policy,
        selected_suite="hybrid", event_id="uncommitted",
    )
    with pytest.raises(Rejected, match="stale"):
        issue_receipt(
            anchor=anchor, previous=state, change=proposal,
            transition_authority=transition_sk.public_key(),
            issuer="checkpoint-authority", checkpoint_signer=witness_sk,
        )


def test_proposal_signed_by_untrusted_transition_authority_cannot_be_receipted():
    transitions = Ed25519PrivateKey.generate()
    attacker = Ed25519PrivateKey.generate()
    checkpoint = Ed25519PrivateKey.generate()
    before = genesis("research", "B", Policy(frozenset({"hybrid"}), 2))
    anchor = InMemoryAnchor()
    anchor.register(before)
    store = VolatileStore(deepcopy(before))
    malicious = sign_transition(
        attacker, state=before, next_policy=before.policy,
        selected_suite="hybrid", event_id="untrusted",
    )
    # An anchor with no authorization enforcement could be compromised;
    # the receipt issuer still checks the trusted transition authority.
    with pytest.raises(Rejected, match="signature"):
        issue_receipt(
            anchor=anchor, previous=before, change=malicious,
            transition_authority=transitions.public_key(),
            issuer="checkpoint-authority", checkpoint_signer=checkpoint,
        )


def test_fork_proof_requires_actual_exchange_of_both_receipts():
    transitions, checkpoint, (left, right) = fork_rig()
    # Both independent anchors accept; a client with just one receipt has
    # no proof of inconsistency. Gossip or witnesses are still required.
    verify_receipt(left, checkpoint.public_key())
    assert left.child_commitment != right.child_commitment
