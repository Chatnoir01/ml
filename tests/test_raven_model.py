"""RAVEN-002 invariant tests. No cryptographic security claim."""
import copy
import itertools
import pytest

from raven_model import Model, Policy, State, Transition, TransitionRejected, TrustedAnchor


def setup():
    anchor = TrustedAnchor()
    state = State("B", 0, Policy("p0", frozenset({"hybrid"})))
    return anchor, state, Model(anchor)


def transition(state, **kw):
    args = dict(compartment=state.compartment, from_epoch=state.epoch,
                to_epoch=state.epoch + 1, old_policy_digest=state.policy.digest,
                new_policy=Policy("p1", frozenset({"hybrid"})),
                suite="hybrid", transcript_digest="t1", authorization="auth1")
    args.update(kw)
    return Transition(**args)


def test_valid_transition_and_replay_rejected():
    anchor, state, model = setup()
    change = transition(state)
    model.apply(state, change, {"auth1"})
    assert state.epoch == anchor.epoch("B") == 1
    with pytest.raises(TransitionRejected):
        model.apply(state, change, {"auth1"})


@pytest.mark.parametrize("mutation", [
    {"compartment": "A"}, {"from_epoch": -1}, {"to_epoch": 3},
    {"old_policy_digest": "evil"}, {"suite": "classical"},
    {"transcript_digest": ""}, {"transcript_digest": "genesis"},
    {"authorization": "forged"},
])
def test_mutations_rejected_without_state_change(mutation):
    anchor, state, model = setup()
    before = copy.deepcopy(state)
    with pytest.raises(TransitionRejected):
        model.apply(state, transition(state, **mutation), {"auth1"})
    assert state == before
    assert anchor.epoch("B") == 0


def test_restored_local_snapshot_rejected_with_independent_anchor():
    anchor, state, model = setup()
    stale = copy.deepcopy(state)
    model.apply(state, transition(state), {"auth1"})
    with pytest.raises(TransitionRejected, match="stale"):
        model.apply(stale, transition(stale, authorization="auth2"), {"auth2"})


def test_anchor_restored_together_with_state_is_not_protected():
    # Negative control: local in-memory anchor is NOT a secure external anchor.
    anchor, state, model = setup()
    model.apply(state, transition(state), {"auth1"})
    restored_anchor = TrustedAnchor()
    restored_state = State("B", 0, Policy("p0", frozenset({"hybrid"})))
    Model(restored_anchor).apply(restored_state, transition(restored_state), {"auth1"})
    assert restored_state.epoch == 1  # rollback was NOT detected


def test_independent_compartment_epoch_counters():
    anchor, state_b, model = setup()
    state_a = State("A", 0, Policy("p0", frozenset({"hybrid"})))
    model.apply(state_b, transition(state_b), {"auth1"})
    assert anchor.epoch("A") == state_a.epoch == 0
    assert anchor.epoch("B") == 1


def test_exhaustive_small_mutation_matrix():
    for epoch, suite, compartment in itertools.product([-1, 0, 1], ["hybrid", "classical"], ["A", "B"]):
        anchor, state, model = setup()
        change = transition(state, from_epoch=epoch, suite=suite, compartment=compartment)
        if (epoch, suite, compartment) == (0, "hybrid", "B"):
            model.apply(state, change, {"auth1"})
            assert state.epoch == 1
        else:
            with pytest.raises(TransitionRejected):
                model.apply(state, change, {"auth1"})
            assert state.epoch == anchor.epoch("B") == 0
