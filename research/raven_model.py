"""RAVEN-002: deterministic authorization state machine; NO cryptography.

This model studies invariants, not confidentiality. Secrets and ciphertexts
are deliberately absent. Never deploy this as a security boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet


class TransitionRejected(ValueError):
    pass


@dataclass(frozen=True)
class Policy:
    digest: str
    suites: FrozenSet[str]

    def __post_init__(self):
        if not self.digest or not self.suites:
            raise ValueError("nonempty digest and suites required")


@dataclass(frozen=True)
class Transition:
    compartment: str
    from_epoch: int
    to_epoch: int
    old_policy_digest: str
    new_policy: Policy
    suite: str
    transcript_digest: str
    authorization: str


@dataclass
class State:
    compartment: str
    epoch: int
    policy: Policy
    transcript_digest: str = "genesis"
    seen_authorizations: set[str] = field(default_factory=set)


class TrustedAnchor:
    """In-memory stand-in for a trusted, independent monotonic anchor.

    Deliberately NOT durable, hardware-backed, or rollback-resistant.
    """

    def __init__(self):
        self._epochs: dict[str, int] = {}

    def epoch(self, compartment: str) -> int:
        return self._epochs.get(compartment, 0)

    def advance(self, compartment: str, expected: int, new: int) -> None:
        if self.epoch(compartment) != expected or new != expected + 1:
            raise TransitionRejected("anchor compare-and-set rejected")
        self._epochs[compartment] = new


class Model:
    def __init__(self, anchor: TrustedAnchor):
        self.anchor = anchor

    def apply(self, state: State, change: Transition, authorized_tokens: set[str]) -> None:
        """Validate, then mutate; token set is a trusted test oracle, NOT a signature.

        No real authenticated channel, atomic persistence, or cross-process lock.
        """
        if state.compartment != change.compartment:
            raise TransitionRejected("wrong compartment")
        if state.epoch != self.anchor.epoch(state.compartment):
            raise TransitionRejected("stale local state")
        if change.from_epoch != state.epoch or change.to_epoch != state.epoch + 1:
            raise TransitionRejected("non-monotonic transition")
        if change.old_policy_digest != state.policy.digest:
            raise TransitionRejected("old policy mismatch")
        if not change.transcript_digest or change.transcript_digest == state.transcript_digest:
            raise TransitionRejected("invalid transcript progression")
        if change.suite not in change.new_policy.suites:
            raise TransitionRejected("suite not permitted")
        if change.authorization not in authorized_tokens:
            raise TransitionRejected("unauthorized transition")
        if change.authorization in state.seen_authorizations:
            raise TransitionRejected("reused authorization")
        # In a real implementation the authorization MUST cryptographically bind
        # *all* fields above; the token oracle here is only an abstract model.
        self.anchor.advance(state.compartment, state.epoch, change.to_epoch)
        state.epoch = change.to_epoch
        state.policy = change.new_policy
        state.transcript_digest = change.transcript_digest
        state.seen_authorizations.add(change.authorization)
