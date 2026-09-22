"""Stronger-boundary monotonic-root contract."""

from __future__ import annotations
from dataclasses import dataclass
from threading import Lock

from .authenticated_state import AuthenticatedState, StateAuthenticator


@dataclass(frozen=True)
class MonotonicRootSnapshot:
    epoch: int
    counter: int


class DevelopmentMonotonicRoot:
    """Executable semantics only; not rollback resistant against host restore."""

    hardware_resistant = False
    boundary_owned = False

    def __init__(self, *, epoch: int = 1) -> None:
        self._epoch = epoch
        self._counter = 0
        self._lock = Lock()

    def advance(self) -> MonotonicRootSnapshot:
        with self._lock:
            self._counter += 1
            return MonotonicRootSnapshot(self._epoch, self._counter)

    def current(self) -> MonotonicRootSnapshot:
        with self._lock:
            return MonotonicRootSnapshot(self._epoch, self._counter)


class PersistentStateGate:
    def __init__(self, *, authenticator: StateAuthenticator, root: DevelopmentMonotonicRoot) -> None:
        self._authenticator = authenticator
        self._root = root

    def seal_next(self, payload: bytes) -> AuthenticatedState:
        snap = self._root.advance()
        return self._authenticator.seal(
            epoch=snap.epoch, counter=snap.counter, payload=payload
        )

    def open(self, state: AuthenticatedState, payload: bytes) -> None:
        self._authenticator.verify(state, payload=payload)
        root = self._root.current()
        if state.epoch != root.epoch:
            raise ValueError("persistent state epoch rollback/mismatch")
        if state.counter < root.counter:
            raise ValueError("persistent state rollback detected")
        if state.counter > root.counter:
            raise ValueError("persistent state is ahead of monotonic root")
