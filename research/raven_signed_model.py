"""RAVEN-003: signed transition *research model*, not a secure protocol.

Ed25519 signatures authenticate exact canonical transition bytes. Hash commitments
and the simulated anchor provide an abstract rollback experiment. There is NO
persistence, key management, encryption, or post-compromise recovery here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

DOMAIN = "RAVEN-003/transition/v1"
# These are DEMO POLICY TIERS, not a ranking of actual cryptographic security.
SUITE_TIER = {"legacy": 0, "classical": 1, "hybrid": 2}


class Rejected(ValueError):
    """Transition violates the experiment's rules."""


def canonical(value: dict) -> bytes:
    """Deterministic internal JSON encoder. NOT a general-purpose wire standard."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


@dataclass(frozen=True)
class Policy:
    suites: frozenset[str]
    floor: int

    def __post_init__(self) -> None:
        if not self.suites or not self.suites.issubset(SUITE_TIER):
            raise ValueError("unknown or empty suite set")
        if type(self.floor) is not int or not 0 <= self.floor <= 2:
            raise ValueError("invalid policy floor")
        if not any(SUITE_TIER[s] >= self.floor for s in self.suites):
            raise ValueError("no permitted suite meets floor")

    def encoded(self) -> dict:
        return {"suites": sorted(self.suites), "floor": self.floor}

    def digest(self) -> str:
        return sha256(b"RAVEN-003/policy/v1\0" + canonical(self.encoded())).hexdigest()


@dataclass(frozen=True)
class SignedTransition:
    namespace: str
    compartment: str
    from_epoch: int
    to_epoch: int
    prev_commitment: str
    old_policy_digest: str
    next_policy: Policy
    selected_suite: str
    event_id: str
    signature: bytes

    def body(self) -> dict:
        return {
            "domain": DOMAIN,
            "namespace": self.namespace,
            "compartment": self.compartment,
            "from_epoch": self.from_epoch,
            "to_epoch": self.to_epoch,
            "prev_commitment": self.prev_commitment,
            "old_policy_digest": self.old_policy_digest,
            "new_policy": self.next_policy.encoded(),
            "new_policy_digest": self.next_policy.digest(),
            "selected_suite": self.selected_suite,
            "event_id": self.event_id,
        }

    def message(self) -> bytes:
        return canonical(self.body())


def sign_transition(private: Ed25519PrivateKey, *, state: State, next_policy: Policy,
                    selected_suite: str, event_id: str) -> SignedTransition:
    """Test authority: signs a fully specified transition; do not expose to attackers."""
    unsigned = SignedTransition(
        namespace=state.namespace, compartment=state.compartment,
        from_epoch=state.epoch, to_epoch=state.epoch + 1,
        prev_commitment=state.commitment,
        old_policy_digest=state.policy.digest(), next_policy=next_policy,
        selected_suite=selected_suite, event_id=event_id, signature=b"",
    )
    return SignedTransition(**{**unsigned.__dict__, "signature": private.sign(unsigned.message())})


def next_commitment(change: SignedTransition) -> str:
    message = change.message()
    return sha256(b"RAVEN-003/commitment/v1\0" + len(message).to_bytes(4, "big")
                  + message + change.signature).hexdigest()


@dataclass
class State:
    namespace: str
    compartment: str
    epoch: int
    policy: Policy
    commitment: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.namespace, self.compartment)


def genesis(namespace: str, compartment: str, policy: Policy) -> State:
    if not namespace or not compartment:
        raise ValueError("nonempty namespace and compartment required")
    commitment = sha256(b"RAVEN-003/genesis/v1\0" + canonical({
        "namespace": namespace, "compartment": compartment, "policy": policy.encoded(),
    })).hexdigest()
    return State(namespace, compartment, 0, policy, commitment)


class InMemoryAnchor:
    """Trusted for this experiment; neither persistent nor rollback-resistant in reality."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], tuple[int, str, str]] = {}

    def register(self, state: State) -> None:
        if state.key in self._records or state.epoch != 0:
            raise Rejected("already registered or non-genesis state")
        expected = genesis(state.namespace, state.compartment, state.policy)
        if state.commitment != expected.commitment:
            raise Rejected("invalid genesis")
        self._records[state.key] = (state.epoch, state.commitment, state.policy.digest())

    def checkpoint(self, state: State) -> None:
        if self._records.get(state.key) != (state.epoch, state.commitment, state.policy.digest()):
            raise Rejected("stale or tampered local state")

    def advance(self, state: State, new_commitment: str, new_policy: Policy) -> None:
        self.checkpoint(state)
        self._records[state.key] = (state.epoch + 1, new_commitment, new_policy.digest())


class SignedModel:
    def __init__(self, anchor: InMemoryAnchor, public_key: Ed25519PublicKey):
        self.anchor, self.public_key = anchor, public_key

    def apply(self, state: State, change: SignedTransition) -> None:
        self.anchor.checkpoint(state)
        if (change.namespace, change.compartment) != state.key:
            raise Rejected("wrong target")
        if change.from_epoch != state.epoch or change.to_epoch != state.epoch + 1:
            raise Rejected("epoch mismatch")
        if change.prev_commitment != state.commitment:
            raise Rejected("previous commitment mismatch")
        if change.old_policy_digest != state.policy.digest():
            raise Rejected("policy mismatch")
        if not change.event_id or change.selected_suite not in change.next_policy.suites:
            raise Rejected("invalid event or suite")
        if change.next_policy.floor < state.policy.floor:
            raise Rejected("policy floor rollback")
        if SUITE_TIER[change.selected_suite] < max(state.policy.floor, change.next_policy.floor):
            raise Rejected("suite below floor")
        try:
            self.public_key.verify(change.signature, change.message())
        except (InvalidSignature, ValueError, TypeError) as exc:
            raise Rejected("invalid authority signature") from exc
        commitment = next_commitment(change)
        self.anchor.advance(state, commitment, change.next_policy)
        state.epoch = change.to_epoch
        state.policy = change.next_policy
        state.commitment = commitment
