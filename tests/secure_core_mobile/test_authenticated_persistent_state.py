from __future__ import annotations
from dataclasses import replace
import pytest

from secure_core_mobile.authenticated_state import StateAuthenticator
from secure_core_mobile.monotonic_root import DevelopmentMonotonicRoot, PersistentStateGate


def test_authenticated_state_roundtrip_at_current_root():
    root = DevelopmentMonotonicRoot()
    gate = PersistentStateGate(authenticator=StateAuthenticator(b"k"*32), root=root)
    state = gate.seal_next(b"journal")
    gate.open(state, b"journal")
    assert root.hardware_resistant is False
    assert root.boundary_owned is False


def test_payload_tampering_is_rejected():
    root = DevelopmentMonotonicRoot()
    gate = PersistentStateGate(authenticator=StateAuthenticator(b"k"*32), root=root)
    state = gate.seal_next(b"journal")
    with pytest.raises(ValueError, match="digest"):
        gate.open(state, b"tampered")


def test_mac_tampering_is_rejected():
    root = DevelopmentMonotonicRoot()
    gate = PersistentStateGate(authenticator=StateAuthenticator(b"k"*32), root=root)
    state = gate.seal_next(b"journal")
    bad = replace(state, tag_sha256="0"*64)
    with pytest.raises(ValueError, match="authentication"):
        gate.open(bad, b"journal")


def test_old_valid_state_is_rejected_after_root_advances():
    root = DevelopmentMonotonicRoot()
    gate = PersistentStateGate(authenticator=StateAuthenticator(b"k"*32), root=root)
    old = gate.seal_next(b"old")
    gate.seal_next(b"new")
    with pytest.raises(ValueError, match="rollback"):
        gate.open(old, b"old")
