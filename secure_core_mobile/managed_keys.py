"""Atomic lifecycle coordinator for registry metadata and opaque provider keys.

The coordinator prevents normal API paths from creating registry/provider
divergence. It does not claim crash-atomic durable transactions.
"""

from __future__ import annotations
from dataclasses import dataclass

from .key_lifecycle import KeyRecord, KeyRegistry, LifecycleError, StoredKeyState
from .opaque_provider import OpaqueEd25519Provider, PublicKeyRecord


@dataclass(frozen=True)
class ManagedKey:
    record: KeyRecord
    public_key_raw: bytes


class ManagedKeyService:
    def __init__(self, *, registry: KeyRegistry, provider: OpaqueEd25519Provider) -> None:
        self._registry = registry
        self._provider = provider

    def create(self) -> ManagedKey:
        material = self._provider.create_key()
        try:
            record = self._registry.register(
                handle=material.handle, provider_id=self._provider.provider_id
            )
        except Exception:
            self._provider.destroy(material.handle)
            raise
        return ManagedKey(record, material.public_key_raw)

    def destroy(self, handle: str) -> KeyRecord:
        record = self._registry.get(handle)
        if record is None or record.state is not StoredKeyState.ACTIVE:
            raise LifecycleError("only active managed keys may destroy")
        if not self._provider.has_key(handle):
            raise LifecycleError("provider/registry divergence detected")
        self._provider.destroy(handle)
        return self._registry.destroy(handle)

    def assert_consistent(self, handle: str) -> None:
        record = self._registry.get(handle)
        provider_has = self._provider.has_key(handle)
        if record is None:
            if provider_has:
                raise LifecycleError("orphan provider key detected")
            raise LifecycleError("unknown managed key")
        should_exist = record.state is not StoredKeyState.DESTROYED
        if provider_has != should_exist:
            raise LifecycleError("provider/registry divergence detected")
