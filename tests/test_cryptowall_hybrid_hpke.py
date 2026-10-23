"""Hybrid HPKE smoke and adversarial regression — never a PQ certification."""

from __future__ import annotations

import pytest

# Explicitly optional in Phase 0: the dedicated hybrid CI installs [pq],
# verifies backend availability, and MUST run every test rather than skip.
pytest.importorskip("cryptography.hazmat.primitives.hpke")

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from cryptowall import EnvelopeError
from cryptowall.hybrid_hpke import (
    generate_hybrid_recipient,
    hybrid_capability,
    open_hybrid,
    seal_hybrid,
)


@pytest.fixture(scope="module")
def recipient():
    assert hybrid_capability(), "ML-KEM backend required in dedicated hybrid CI"
    return generate_hybrid_recipient()


@pytest.mark.parametrize("message", [b"", b"secret", b"\x00\xff" * 100])
def test_actual_hybrid_hpke_roundtrip_and_context(recipient, message):
    private, public = recipient
    packet = seal_hybrid(public, message, context=b"cryptowall:tenant-a:v0")
    assert packet.startswith(b"CWALLPQ1\x00")
    assert message == open_hybrid(private, packet, context=b"cryptowall:tenant-a:v0")


def test_random_encapsulation_changes_ciphertext(recipient):
    private, public = recipient
    envelopes = [seal_hybrid(public, b"same") for _ in range(8)]
    assert len(set(envelopes)) == 8
    assert all(open_hybrid(private, p) == b"same" for p in envelopes)


def test_wrong_recipient_fails(recipient):
    _private, public = recipient
    other_private, _ = generate_hybrid_recipient()
    encrypted = seal_hybrid(public, b"secret")
    with pytest.raises(EnvelopeError):
        open_hybrid(other_private, encrypted)


def test_wrong_context_fails(recipient):
    private, public = recipient
    packet = seal_hybrid(public, b"secret", context=b"alice")
    with pytest.raises(EnvelopeError):
        open_hybrid(private, packet, context=b"bob")
    with pytest.raises(EnvelopeError):
        open_hybrid(private, packet)


@pytest.mark.parametrize("index", [0, 8, 9, 10, 100, 512, -17, -1])
def test_mutated_any_envelope_component_fails(recipient, index):
    private, public = recipient
    packet = bytearray(seal_hybrid(public, b"test-data"))
    packet[index] ^= 1
    with pytest.raises(EnvelopeError):
        open_hybrid(private, bytes(packet))


def test_truncation_and_suffix_injection_fail(recipient):
    private, public = recipient
    packet = seal_hybrid(public, b"short")
    for short in (packet[:1], packet[:10], packet[:-1]):
        with pytest.raises(EnvelopeError):
            open_hybrid(private, short)
    with pytest.raises(EnvelopeError):
        open_hybrid(private, packet + b"unauthenticated garbage")


def test_no_classical_downgrade_or_old_version_accepted(recipient):
    private, public = recipient
    with pytest.raises(TypeError, match="no downgrade"):
        seal_hybrid(X25519PrivateKey.generate().public_key(), b"weak")
    with pytest.raises(TypeError):
        open_hybrid(X25519PrivateKey.generate(), b"unknown")
    packet = seal_hybrid(public, b"secret")
    with pytest.raises(EnvelopeError):
        open_hybrid(private, b"CWALLv1\x00" + packet[9:])


def test_context_type_and_size_and_plaintext_caps(recipient):
    private, public = recipient
    with pytest.raises(TypeError):
        seal_hybrid(public, "not bytes")
    with pytest.raises(TypeError):
        seal_hybrid(public, b"x", context="not bytes")
    with pytest.raises(ValueError):
        seal_hybrid(public, b"x", context=b"x" * 4097)
    with pytest.raises(ValueError):
        seal_hybrid(public, b"x" * (8 * 1024 * 1024 + 1))
    with pytest.raises(TypeError):
        open_hybrid(private, bytearray(seal_hybrid(public, b"x")))


def test_hybrid_remains_stateless_no_replay_protection(recipient):
    private, public = recipient
    packet = seal_hybrid(public, b"replay-me")
    assert open_hybrid(private, packet) == b"replay-me"
    assert open_hybrid(private, packet) == b"replay-me"
