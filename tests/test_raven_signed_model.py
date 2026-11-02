"""Adversarial tests of the RAVEN-003 state model, NOT a cryptographic proof."""
from dataclasses import replace
import copy
import itertools
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from research.raven_signed_model import (
    InMemoryAnchor, Policy, Rejected, SignedModel, genesis, sign_transition,
)


def setup():
    signer = Ed25519PrivateKey.generate()
    anchor = InMemoryAnchor()
    state = genesis("project", "B", Policy(frozenset({"classical", "hybrid"}), 1))
    anchor.register(state)
    return signer, anchor, state, SignedModel(anchor, signer.public_key())


def proposed(signer, state, **kwargs):
    args = dict(next_policy=Policy(frozenset({"hybrid"}), 2),
                selected_suite="hybrid", event_id="ev-1")
    args.update(kwargs)
    return sign_transition(signer, state=state, **args)


def test_valid_signed_transition_and_replay():
    sk, anchor, state, model = setup()
    step = proposed(sk, state)
    model.apply(state, step)
    assert state.epoch == 1
    with pytest.raises(Rejected):
        model.apply(state, step)


@pytest.mark.parametrize("field,mutated", [
    ("namespace", "other"), ("compartment", "A"), ("from_epoch", 4),
    ("to_epoch", 4), ("prev_commitment", "0" * 64),
    ("old_policy_digest", "0" * 64), ("selected_suite", "classical"),
    ("event_id", "changed"),
    ("next_policy", Policy(frozenset({"classical"}), 1)),
    ("signature", b"\x00" * 64),
])
def test_tampering_signed_fields_rejected(field, mutated):
    sk, anchor, state, model = setup()
    signed = proposed(sk, state)
    before = copy.deepcopy(state)
    with pytest.raises(Rejected):
        model.apply(state, replace(signed, **{field: mutated}))
    assert state == before
    anchor.checkpoint(state)


def test_attacker_cannot_sign_with_untrusted_authority():
    sk, anchor, state, model = setup()
    other = Ed25519PrivateKey.generate()
    with pytest.raises(Rejected, match="signature"):
        model.apply(state, proposed(other, state))


def test_authority_signed_downgrade_still_rejected_by_local_floor():
    sk, anchor, state, model = setup()
    model.apply(state, proposed(sk, state))  # floor becomes 2
    downgraded = proposed(sk, state, next_policy=Policy(frozenset({"classical"}), 1),
                          selected_suite="classical", event_id="ev-2")
    with pytest.raises(Rejected, match="floor"):
        model.apply(state, downgraded)


def test_signed_selection_below_existing_floor_rejected():
    sk, anchor, state, model = setup()
    model.apply(state, proposed(sk, state))
    next_policy = Policy(frozenset({"classical", "hybrid"}), 2)
    change = proposed(sk, state, next_policy=next_policy,
                      selected_suite="classical", event_id="ev-2")
    with pytest.raises(Rejected, match="suite below"):
        model.apply(state, change)


def test_same_epoch_state_tampering_detected_by_anchor_commitment():
    sk, anchor, state, model = setup()
    state.policy = Policy(frozenset({"legacy"}), 0)
    with pytest.raises(Rejected, match="stale or tampered"):
        model.apply(state, proposed(sk, state))


def test_stale_snapshot_rejected_after_valid_authorized_transition():
    sk, anchor, state, model = setup()
    old = copy.deepcopy(state)
    model.apply(state, proposed(sk, state))
    with pytest.raises(Rejected, match="stale"):
        model.apply(old, proposed(sk, old, event_id="ev-2"))


def test_compartment_independence_and_signature_cross_target():
    sk, anchor, b, model = setup()
    a = genesis("project", "A", Policy(frozenset({"classical"}), 1))
    anchor.register(a)
    step_b = proposed(sk, b)
    with pytest.raises(Rejected, match="target"):
        model.apply(a, step_b)
    model.apply(b, step_b)
    anchor.checkpoint(a)
    assert a.epoch == 0 and b.epoch == 1


def test_anchor_loss_defeats_rollback_detection_negative_control():
    sk, anchor, state, model = setup()
    old = copy.deepcopy(state)
    model.apply(state, proposed(sk, state))
    restored_anchor = InMemoryAnchor()
    restored_anchor.register(old)
    restored_model = SignedModel(restored_anchor, sk.public_key())
    restored_model.apply(old, proposed(sk, old))
    assert old.epoch == 1  # Local simulation has no durable anti-rollback guarantee!


def test_sequence_of_authorized_steps_then_stale_replay():
    sk, anchor, state, model = setup()
    seen = []
    for i in range(10):
        snapshot = copy.deepcopy(state)
        seen.append((snapshot, proposed(sk, state, event_id=f"event-{i}")))
        model.apply(state, seen[-1][1])
    assert state.epoch == 10
    for snapshot, step in seen:
        with pytest.raises(Rejected):
            model.apply(snapshot, step)


def test_exhaustive_signed_mutation_matrix():
    sk, anchor, state, model = setup()
    signed = proposed(sk, state)
    for field, choices in {
        "from_epoch": [-1, 0, 1],
        "to_epoch": [0, 1, 2],
        "compartment": ["A", "B", "C"],
        "selected_suite": ["legacy", "classical", "hybrid"],
    }.items():
        for value in choices:
            if value == getattr(signed, field):
                continue
            with pytest.raises(Rejected):
                model.apply(state, replace(signed, **{field: value}))
            anchor.checkpoint(state)
