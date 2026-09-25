"""Contract for a monotonic root owned by the isolated pVM boundary.

No production implementation is provided until Android/pVM storage semantics
are backed by platform evidence.
"""

from __future__ import annotations
from threading import Lock
from typing import Protocol

from .hostile_boundary import BoundaryEvidence
from .monotonic_root import MonotonicRootSnapshot


class MonotonicRoot(Protocol):
    hardware_resistant: bool
    boundary_owned: bool
    def advance(self) -> MonotonicRootSnapshot: ...
    def current(self) -> MonotonicRootSnapshot: ...


class PvmMonotonicRootUnavailable:
    """Fail-closed placeholder: never masquerades as protected persistence."""

    hardware_resistant = False
    boundary_owned = False

    def __init__(self, boundary: BoundaryEvidence) -> None:
        if not boundary.qualifies_for_hostile_host_experiment:
            raise ValueError("qualified pVM boundary required")
        self._boundary = boundary

    def advance(self) -> MonotonicRootSnapshot:
        raise RuntimeError("pVM monotonic storage backend not implemented")

    def current(self) -> MonotonicRootSnapshot:
        raise RuntimeError("pVM monotonic storage backend not implemented")


_RP_STATE_MAGIC = b"SCMRP001"
_RP_STATE_BYTES = 32
_U64_MAX = (1 << 64) - 1


class RollbackProtectedStorage(Protocol):
    def read(self) -> bytes | None: ...
    def write(self, value: bytes) -> None: ...


def encode_rollback_protected_snapshot(
    snapshot: MonotonicRootSnapshot,
) -> bytes:
    if snapshot.epoch <= 0 or snapshot.epoch > _U64_MAX:
        raise ValueError("rollback-protected epoch out of range")
    if snapshot.counter < 0 or snapshot.counter > _U64_MAX:
        raise ValueError("rollback-protected counter out of range")
    return (
        _RP_STATE_MAGIC
        + snapshot.epoch.to_bytes(8, "big")
        + snapshot.counter.to_bytes(8, "big")
        + b"\x00" * 8
    )


def decode_rollback_protected_snapshot(
    encoded: bytes,
) -> MonotonicRootSnapshot:
    if not isinstance(encoded, bytes) or len(encoded) != _RP_STATE_BYTES:
        raise ValueError("rollback-protected state must be exactly 32 bytes")
    if encoded[:8] != _RP_STATE_MAGIC:
        raise ValueError("rollback-protected state magic mismatch")
    if encoded[24:] != b"\x00" * 8:
        raise ValueError("rollback-protected state reserved bytes are nonzero")

    epoch = int.from_bytes(encoded[8:16], "big")
    counter = int.from_bytes(encoded[16:24], "big")
    if epoch <= 0:
        raise ValueError("rollback-protected state epoch invalid")
    return MonotonicRootSnapshot(epoch=epoch, counter=counter)


class PvmRollbackProtectedMonotonicRoot:
    """Executable single-writer root backed by VM Payload rollback storage.

    The Android API promises rollback-detectable storage on supported devices,
    but this Python object does not self-promote that platform contract into
    hardware evidence. Real-device AVF verification remains a separate gate.
    """

    hardware_resistant = False
    boundary_owned = False
    rollback_detectable_storage = True
    single_writer = True

    def __init__(
        self,
        storage: RollbackProtectedStorage,
        *,
        epoch: int = 1,
    ) -> None:
        if epoch <= 0 or epoch > _U64_MAX:
            raise ValueError("invalid rollback-protected root epoch")
        self._storage = storage
        self._epoch = epoch
        self._lock = Lock()

    def _persist_and_verify(self, snapshot: MonotonicRootSnapshot) -> None:
        encoded = encode_rollback_protected_snapshot(snapshot)
        self._storage.write(encoded)
        persisted = self._storage.read()
        if persisted is None:
            raise RuntimeError(
                "rollback-protected state disappeared after write"
            )
        observed = decode_rollback_protected_snapshot(persisted)
        if observed != snapshot:
            raise RuntimeError(
                "rollback-protected state read-after-write mismatch"
            )

    def _current_locked(self) -> MonotonicRootSnapshot:
        encoded = self._storage.read()
        if encoded is None:
            initial = MonotonicRootSnapshot(
                epoch=self._epoch,
                counter=0,
            )
            self._persist_and_verify(initial)
            return initial

        snapshot = decode_rollback_protected_snapshot(encoded)
        if snapshot.epoch != self._epoch:
            raise ValueError("rollback-protected root epoch mismatch")
        return snapshot

    def current(self) -> MonotonicRootSnapshot:
        with self._lock:
            return self._current_locked()

    def advance(self) -> MonotonicRootSnapshot:
        with self._lock:
            current = self._current_locked()
            if current.counter == _U64_MAX:
                raise OverflowError("rollback-protected counter exhausted")
            next_snapshot = MonotonicRootSnapshot(
                epoch=current.epoch,
                counter=current.counter + 1,
            )
            self._persist_and_verify(next_snapshot)
            return next_snapshot
