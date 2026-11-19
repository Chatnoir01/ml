from __future__ import annotations
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from secure_core_mobile.opaque_provider import OpaqueEd25519Provider
from secure_core_mobile.rollback_guard import InMemoryRollbackGuard, MonotonicSnapshot


def test_opaque_provider_signs_without_exporting_private_key():
    provider = OpaqueEd25519Provider()
    record = provider.create_key()
    signature = provider.operate(operation="sign", key_handle=record.handle, payload=b"message")
    ed25519.Ed25519PublicKey.from_public_bytes(record.public_key_raw).verify(signature, b"message")
    assert not hasattr(record, "private_key")
    assert len(signature) == 64


def test_destroyed_key_cannot_be_used():
    provider = OpaqueEd25519Provider()
    record = provider.create_key()
    provider.destroy(record.handle)
    with pytest.raises(KeyError, match="unknown"):
        provider.operate(operation="sign", key_handle=record.handle, payload=b"x")


def test_rollback_guard_rejects_old_and_future_state():
    guard = InMemoryRollbackGuard()
    first = guard.advance()
    second = guard.advance()
    with pytest.raises(ValueError, match="rollback"):
        guard.validate(first)
    guard.validate(second)
    with pytest.raises(ValueError, match="future"):
        guard.validate(MonotonicSnapshot(second.epoch, second.counter + 1))
    assert guard.hardware_resistant is False
