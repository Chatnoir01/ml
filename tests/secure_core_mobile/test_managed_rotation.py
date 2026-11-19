from secure_core_mobile.key_lifecycle import KeyRegistry, StoredKeyState
from secure_core_mobile.managed_keys import ManagedKeyService
from secure_core_mobile.opaque_provider import OpaqueEd25519Provider


def test_rotation_creates_new_handle_and_revokes_old():
    registry = KeyRegistry()
    provider = OpaqueEd25519Provider()
    service = ManagedKeyService(registry=registry, provider=provider)
    old = service.create()
    new = service.rotate(old.record.handle)
    assert new.record.handle != old.record.handle
    assert registry.get(old.record.handle).state is StoredKeyState.REVOKED
    assert registry.get(new.record.handle).state is StoredKeyState.ACTIVE
    assert provider.has_key(new.record.handle)
    # Revoked material remains until explicit destruction/recovery policy.
    assert provider.has_key(old.record.handle)
