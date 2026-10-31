"""RAVEN-004: crash/recovery and replica-fork *simulation*, NOT durable storage.

Assumes a logically independent, linearizable trusted anchor surviving crashes.
The store and anchor here are both in RAM: none of the durability, filesystem
atomicity, Byzantine-resilience or distributed consensus assumptions hold in
this implementation. Never use for production cryptographic state.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from research.raven_signed_model import (
    InMemoryAnchor, Rejected, SignedTransition, State,
    next_commitment, verify_transition,
)


class SimulatedCrash(RuntimeError):
    """Controlled injection immediately after one named stage."""


@dataclass(frozen=True)
class Pending:
    before: State
    change: SignedTransition


@dataclass
class VolatileStore:
    """RAM stand-in for a crash-surviving, integrity-checked local journal."""
    state: State
    pending: Pending | None = None


def resulting_state(before: State, change: SignedTransition) -> State:
    return State(
        namespace=before.namespace,
        compartment=before.compartment,
        epoch=change.to_epoch,
        policy=change.next_policy,
        commitment=next_commitment(change),
    )


def _anchor_matches(anchor: InMemoryAnchor, state: State) -> bool:
    try:
        anchor.checkpoint(state)
        return True
    except Rejected:
        return False


class JournaledMachine:
    """Prepare -> anchor CAS -> local apply -> clear, with explicit crash points.

    In a real system, all four stages require specified storage, fsync, and
    transaction semantics. No attempt is made to implement those here.
    """

    PHASES = ("prepared", "anchored", "applied", "cleared")

    def __init__(self, store: VolatileStore, anchor: InMemoryAnchor,
                 public_key: Ed25519PublicKey):
        self.store, self.anchor, self.public_key = store, anchor, public_key

    def _checkpoint(self, phase: str, crash_at: str | None) -> None:
        if crash_at == phase:
            raise SimulatedCrash(phase)

    def transition(self, change: SignedTransition, *, crash_at: str | None = None) -> None:
        if crash_at is not None and crash_at not in self.PHASES:
            raise ValueError("unknown crash phase")
        if self.store.pending is not None:
            raise Rejected("recover pending transition before another update")

        before = self.store.state
        self.anchor.checkpoint(before)
        verify_transition(before, change, self.public_key)
        after = resulting_state(before, change)

        # Stage 1: a real implementation would durably fsync signed intent.
        self.store.pending = Pending(deepcopy(before), change)
        self._checkpoint("prepared", crash_at)

        # Stage 2: independent linearizable compare-and-set; simulated in RAM.
        self.anchor.advance(before, after.commitment, after.policy)
        self._checkpoint("anchored", crash_at)

        # Stage 3: real implementation needs durable atomic replace + fsync.
        self.store.state = after
        self._checkpoint("applied", crash_at)

        # Stage 4: journal cleanup (also needs durable persistence).
        self.store.pending = None
        self._checkpoint("cleared", crash_at)

    def recover(self) -> str:
        """Return classification, or reject an unverifiable state.

        A pre-commit intent is safely aborted; after a committed anchor update,
        a signed and retained intent permits local roll-forward. A missing or
        tampered committed intent fails closed. No real-world availability or
        crash-durability guarantee follows from these RAM-only tests.
        """
        state = self.store.state
        pending = self.store.pending
        if pending is None:
            self.anchor.checkpoint(state)
            return "ready"

        before, change = pending.before, pending.change
        verify_transition(before, change, self.public_key)
        after = resulting_state(before, change)

        if state == before and _anchor_matches(self.anchor, before):
            self.store.pending = None
            return "aborted_uncommitted"

        if state == before and _anchor_matches(self.anchor, after):
            self.store.state = after
            self.store.pending = None
            return "rolled_forward"

        if state == after and _anchor_matches(self.anchor, after):
            self.store.pending = None
            return "cleaned_committed"

        raise Rejected("ambiguous, diverged or tampered recovery state")
