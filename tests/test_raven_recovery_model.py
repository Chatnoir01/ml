"""Fault injection and negative-control experiments for RAVEN-004.

These tests intentionally model persistence and linearizability as assumptions:
they DO NOT establish real filesystem durability or multi-device consensus.
"""
from copy import deepcopy
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_recovery_model import (
    JournaledMachine, Pending, SimulatedCrash, VolatileStore,
)
from research.raven_signed_model import (
    InMemoryAnchor, Policy, Rejected, genesis, sign_transition,
)


def rig():
    signer = Ed25519PrivateKey.generate()
    anchor = InMemoryAnchor()
    state = genesis("research", "B", Policy(frozenset({"classical", "hybrid"}), 1))
    anchor.register(state)
    store = VolatileStore(state)
    machine = JournaledMachine(store, anchor, signer.public_key())
    return signer, anchor, store, machine


def signed(signer, store, *, event_id="event-1", policy=None, suite="hybrid"):
    return sign_transition(
        signer, state=store.state,
        next_policy=policy or Policy(frozenset({"hybrid"}), 2),
        selected_suite=suite, event_id=event_id,
    )


def test_uninterrupted_commit_and_restart():
    signer, anchor, store, machine = rig()
    machine.transition(signed(signer, store))
    assert store.state.epoch == 1 and store.pending is None
    assert JournaledMachine(store, anchor, signer.public_key()).recover() == "ready"


@pytest.mark.parametrize("phase,result,epoch", [
    ("prepared", "aborted_uncommitted", 0),
    ("anchored", "rolled_forward", 1),
    ("applied", "cleaned_committed", 1),
    ("cleared", "ready", 1),
])
def test_four_crash_boundaries(phase, result, epoch):
    signer, anchor, store, machine = rig()
    with pytest.raises(SimulatedCrash, match=phase):
        machine.transition(signed(signer, store), crash_at=phase)
    rebooted = JournaledMachine(store, anchor, signer.public_key())
    assert rebooted.recover() == result
    assert store.state.epoch == epoch
    assert store.pending is None
    assert rebooted.recover() == "ready"
    anchor.checkpoint(store.state)


def test_prepared_intent_may_be_aborted_and_retried():
    signer, anchor, store, machine = rig()
    change = signed(signer, store)
    with pytest.raises(SimulatedCrash):
        machine.transition(change, crash_at="prepared")
    assert machine.recover() == "aborted_uncommitted"
    machine.transition(change)
    assert store.state.epoch == 1


def test_cannot_start_new_transition_while_pending():
    signer, anchor, store, machine = rig()
    change = signed(signer, store)
    with pytest.raises(SimulatedCrash):
        machine.transition(change, crash_at="prepared")
    with pytest.raises(Rejected, match="pending"):
        machine.transition(change)


def test_signed_downgrade_rejected_without_staging():
    signer, anchor, store, machine = rig()
    machine.transition(signed(signer, store))
    downgrade = signed(signer, store, event_id="downgrade",
                       policy=Policy(frozenset({"classical"}), 1),
                       suite="classical")
    with pytest.raises(Rejected, match="floor"):
        machine.transition(downgrade)
    assert store.pending is None
    assert machine.recover() == "ready"


@pytest.mark.parametrize("phase", ["prepared", "anchored", "applied"])
def test_corrupted_journal_signature_fails_closed(phase):
    signer, anchor, store, machine = rig()
    with pytest.raises(SimulatedCrash):
        machine.transition(signed(signer, store), crash_at=phase)
    assert store.pending is not None
    p = store.pending
    store.pending = Pending(p.before, replace(p.change, signature=b"\x00" * 64))
    with pytest.raises(Rejected, match="signature"):
        machine.recover()


@pytest.mark.parametrize("phase", ["anchored", "applied"])
def test_missing_committed_journal_rejects_recovery_if_disk_is_old(phase):
    signer, anchor, store, machine = rig()
    old = deepcopy(store.state)
    with pytest.raises(SimulatedCrash):
        machine.transition(signed(signer, store), crash_at=phase)
    store.state = old
    store.pending = None
    with pytest.raises(Rejected, match="stale"):
        machine.recover()


def test_prepared_intent_missing_before_commit_does_not_advance_state():
    signer, anchor, store, machine = rig()
    with pytest.raises(SimulatedCrash):
        machine.transition(signed(signer, store), crash_at="prepared")
    store.pending = None
    assert machine.recover() == "ready"
    assert store.state.epoch == 0


def test_local_state_tampering_detected_without_pending_record():
    signer, anchor, store, machine = rig()
    store.state.policy = Policy(frozenset({"legacy"}), 0)
    with pytest.raises(Rejected, match="tampered"):
        machine.recover()


def test_corrupt_post_anchor_local_state_fails_closed():
    signer, anchor, store, machine = rig()
    with pytest.raises(SimulatedCrash):
        machine.transition(signed(signer, store), crash_at="anchored")
    store.state.epoch = 42
    with pytest.raises(Rejected, match="ambiguous"):
        machine.recover()


def test_restored_old_snapshot_after_clean_commit_rejected():
    signer, anchor, store, machine = rig()
    old = deepcopy(store.state)
    machine.transition(signed(signer, store))
    restored = VolatileStore(state=old)
    with pytest.raises(Rejected, match="stale"):
        JournaledMachine(restored, anchor, signer.public_key()).recover()


def test_competing_devices_sharing_anchor_cannot_both_commit():
    signer, anchor, store, machine = rig()
    second_store = deepcopy(store)
    second = JournaledMachine(second_store, anchor, signer.public_key())
    first_change = signed(signer, store, event_id="first")
    second_change = signed(signer, second_store, event_id="second")
    machine.transition(first_change)
    with pytest.raises(Rejected, match="stale"):
        second.transition(second_change)
    assert second_store.state.epoch == 0
    assert second_store.pending is None
    assert store.state.epoch == 1


def test_prepared_competing_device_fails_closed_after_other_commit():
    signer, anchor, store, machine = rig()
    second_store = deepcopy(store)
    second = JournaledMachine(second_store, anchor, signer.public_key())
    with pytest.raises(SimulatedCrash):
        machine.transition(signed(signer, store, event_id="first"), crash_at="prepared")
    second.transition(signed(signer, second_store, event_id="second"))
    with pytest.raises(Rejected, match="ambiguous"):
        machine.recover()


def test_split_view_with_independent_anchors_undetected_negative_control():
    signer = Ed25519PrivateKey.generate()
    original = genesis("research", "B", Policy(frozenset({"classical", "hybrid"}), 1))
    a1, a2 = InMemoryAnchor(), InMemoryAnchor()
    a1.register(deepcopy(original))
    a2.register(deepcopy(original))
    s1, s2 = VolatileStore(deepcopy(original)), VolatileStore(deepcopy(original))
    m1 = JournaledMachine(s1, a1, signer.public_key())
    m2 = JournaledMachine(s2, a2, signer.public_key())
    m1.transition(signed(signer, s1, event_id="fork-left"))
    m2.transition(signed(signer, s2, event_id="fork-right"))
    assert s1.state.epoch == s2.state.epoch == 1
    assert s1.state.commitment != s2.state.commitment
    assert m1.recover() == m2.recover() == "ready"
    # This is an EXISTING LIMITATION: without shared consistency, forks are accepted.


def test_unknown_crash_point_rejected_before_any_change():
    signer, anchor, store, machine = rig()
    with pytest.raises(ValueError, match="unknown"):
        machine.transition(signed(signer, store), crash_at="made-up")
    assert store.state.epoch == 0 and store.pending is None


def test_ten_consecutive_commits_and_recovery():
    signer, anchor, store, machine = rig()
    for i in range(10):
        phase = ("prepared", "anchored", "applied", "cleared")[i % 4]
        with pytest.raises(SimulatedCrash):
            machine.transition(signed(signer, store, event_id=f"event-{i}"), crash_at=phase)
        machine.recover()
        anchor.checkpoint(store.state)
    # Every fourth 'prepared' intent was aborted; others were committed.
    assert store.state.epoch == 7
