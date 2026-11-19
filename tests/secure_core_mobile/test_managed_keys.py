from __future__ import annotations
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from secure_core_mobile.key_lifecycle import KeyRegistry, LifecycleError, StoredKeyState
from secure_core_mobile.managed_keys import ManagedKeyService
from secure_core_mobile.opaque_provider import OpaqueEd25519Provider


def test_managed_create_binds_same_opaque_handle_to_registry():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    service = ManagedKeyService(registry=registry, provider=provider)
    managed = service.create()
    assert managed.record.handle.startswith("scm_ed25519_")
    assert managed.record.provider_id == provider.provider_id
    assert provider.has_key(managed.record.handle)
    service.assert_consistent(managed.record.handle)


def test_managed_key_can_sign_and_verify():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    managed = ManagedKeyService(registry=registry, provider=provider).create()
    signature = provider.operate(operation="sign", key_handle=managed.record.handle, payload=b"x")
    ed25519.Ed25519PublicKey.from_public_bytes(managed.public_key_raw).verify(signature, b"x")


def test_destroy_removes_provider_material_and_marks_registry_terminal():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    service = ManagedKeyService(registry=registry, provider=provider)
    managed = service.create()
    record = service.destroy(managed.record.handle)
    assert record.state is StoredKeyState.DESTROYED
    assert provider.has_key(managed.record.handle) is False
    service.assert_consistent(managed.record.handle)


def test_divergence_is_detected_fail_closed():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    service = ManagedKeyService(registry=registry, provider=provider)
    managed = service.create()
    provider.destroy(managed.record.handle)
    with pytest.raises(LifecycleError, match="divergence"):
        service.assert_consistent(managed.record.handle)
    with pytest.raises(LifecycleError, match="divergence"):
        service.destroy(managed.record.handle)
