from __future__ import annotations
import pytest

from secure_core_mobile.key_lifecycle import KeyRegistry, LifecycleError
from secure_core_mobile.lifecycle_journal import InMemoryLifecycleJournal
from secure_core_mobile.managed_keys import ManagedKeyService
from secure_core_mobile.opaque_provider import OpaqueEd25519Provider


def test_destroy_is_journaled_and_committed():
    journal = InMemoryLifecycleJournal()
    service = ManagedKeyService(
        registry=KeyRegistry(), provider=OpaqueEd25519Provider(), journal=journal
    )
    key = service.create()
    service.destroy(key.record.handle)
    assert journal.incomplete() == ()
    journal.verify_chain()


def test_interrupted_transition_is_reported_not_silently_recovered():
    journal = InMemoryLifecycleJournal()
    journal.begin(operation="destroy", handle="h1")
    service = ManagedKeyService(
        registry=KeyRegistry(), provider=OpaqueEd25519Provider(), journal=journal
    )
    pending = service.recover()
    assert len(pending) == 1
    assert pending[0].startswith("destroy:h1:")
