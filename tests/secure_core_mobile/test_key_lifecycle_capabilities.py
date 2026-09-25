from __future__ import annotations
import pytest

from secure_core_mobile.android_keystore import AndroidKeystoreBackend, AndroidKeystoreUnavailable
from secure_core_mobile.capabilities import ProtectionLevel, development_capability
from secure_core_mobile.key_lifecycle import KeyRegistry, LifecycleError, StoredKeyState


def test_registry_exposes_only_opaque_metadata():
    registry = KeyRegistry()
    record = registry.create(provider_id="development")
    assert record.handle.startswith("scm_")
    assert not hasattr(record, "private_key")
    assert record.state is StoredKeyState.ACTIVE


def test_rotate_increments_generation_without_changing_handle():
    registry = KeyRegistry()
    original = registry.create(provider_id="development")
    rotated = registry.rotate(original.handle)
    assert rotated.handle == original.handle
    assert rotated.generation == original.generation + 1


def test_revoked_key_cannot_rotate_or_revoke_again():
    registry = KeyRegistry()
    record = registry.create(provider_id="development")
    registry.revoke(record.handle)
    with pytest.raises(LifecycleError):
        registry.rotate(record.handle)
    with pytest.raises(LifecycleError):
        registry.revoke(record.handle)


def test_destroyed_key_is_terminal():
    registry = KeyRegistry()
    record = registry.create(provider_id="development")
    registry.destroy(record.handle)
    with pytest.raises(LifecycleError):
        registry.destroy(record.handle)


def test_development_capability_never_claims_hardware():
    evidence = development_capability()
    assert evidence.protection is ProtectionLevel.SOFTWARE
    assert evidence.hardware_backed is False
    assert evidence.strongbox is False


def test_android_unavailable_is_explicit_not_simulated():
    backend = AndroidKeystoreBackend(runtime_available=False)
    assert backend.hardware_backed is False
    with pytest.raises(AndroidKeystoreUnavailable):
        backend.capability_evidence()
    with pytest.raises(AndroidKeystoreUnavailable):
        backend.operate(operation="sign", key_handle="scm_x", payload=b"x")


def test_android_runtime_presence_does_not_equal_hardware_verification():
    evidence = AndroidKeystoreBackend(runtime_available=True).capability_evidence()
    assert evidence.verified is False
    assert evidence.hardware_backed is False
    assert evidence.strongbox is False
