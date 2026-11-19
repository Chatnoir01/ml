from __future__ import annotations

from dataclasses import replace

import pytest

from secure_core_mobile.monotonic_root import MonotonicRootSnapshot
from secure_core_mobile.pvm_monotonic import (
    PvmRollbackProtectedMonotonicRoot,
    decode_rollback_protected_snapshot,
    encode_rollback_protected_snapshot,
)


class _MemoryStorage:
    def __init__(self, value: bytes | None = None) -> None:
        self.value = value
        self.writes: list[bytes] = []

    def read(self) -> bytes | None:
        return self.value

    def write(self, value: bytes) -> None:
        self.value = bytes(value)
        self.writes.append(bytes(value))


class _CorruptingStorage(_MemoryStorage):
    def write(self, value: bytes) -> None:
        corrupted = bytearray(value)
        corrupted[16] ^= 0x01
        self.value = bytes(corrupted)
        self.writes.append(bytes(value))


def test_rollback_snapshot_codec_is_exactly_32_bytes() -> None:
    snapshot = MonotonicRootSnapshot(epoch=7, counter=42)
    encoded = encode_rollback_protected_snapshot(snapshot)

    assert len(encoded) == 32
    assert decode_rollback_protected_snapshot(encoded) == snapshot


@pytest.mark.parametrize(
    "mutation",
    [
        lambda data: b"BADMAGIC" + data[8:],
        lambda data: data[:24] + b"\x00" * 7 + b"\x01",
        lambda data: data[:-1],
    ],
)
def test_malformed_rollback_snapshot_is_rejected(mutation) -> None:
    encoded = encode_rollback_protected_snapshot(
        MonotonicRootSnapshot(epoch=1, counter=0)
    )
    with pytest.raises(ValueError):
        decode_rollback_protected_snapshot(mutation(encoded))


def test_current_initializes_absent_state_and_verifies_persistence() -> None:
    storage = _MemoryStorage()
    root = PvmRollbackProtectedMonotonicRoot(storage, epoch=3)

    current = root.current()

    assert current == MonotonicRootSnapshot(epoch=3, counter=0)
    assert len(storage.writes) == 1
    assert decode_rollback_protected_snapshot(storage.writes[0]) == current


def test_advance_is_single_writer_monotonic_semantics() -> None:
    storage = _MemoryStorage()
    root = PvmRollbackProtectedMonotonicRoot(storage, epoch=1)

    first = root.advance()
    second = root.advance()

    assert first == MonotonicRootSnapshot(epoch=1, counter=1)
    assert second == MonotonicRootSnapshot(epoch=1, counter=2)
    assert root.current() == second
    assert root.single_writer is True


def test_stored_epoch_mismatch_is_rejected() -> None:
    storage = _MemoryStorage(
        encode_rollback_protected_snapshot(
            MonotonicRootSnapshot(epoch=2, counter=9)
        )
    )
    root = PvmRollbackProtectedMonotonicRoot(storage, epoch=1)

    with pytest.raises(ValueError, match="epoch mismatch"):
        root.current()


def test_read_after_write_mismatch_fails_closed() -> None:
    root = PvmRollbackProtectedMonotonicRoot(_CorruptingStorage())

    with pytest.raises(RuntimeError, match="read-after-write mismatch"):
        root.current()


def test_storage_semantics_do_not_self_claim_hardware_evidence() -> None:
    root = PvmRollbackProtectedMonotonicRoot(_MemoryStorage())

    assert root.rollback_detectable_storage is True
    assert root.hardware_resistant is False
    assert root.boundary_owned is False


def test_counter_overflow_fails_closed() -> None:
    max_snapshot = MonotonicRootSnapshot(
        epoch=1,
        counter=(1 << 64) - 1,
    )
    storage = _MemoryStorage(
        encode_rollback_protected_snapshot(max_snapshot)
    )
    root = PvmRollbackProtectedMonotonicRoot(storage)

    with pytest.raises(OverflowError, match="exhausted"):
        root.advance()
