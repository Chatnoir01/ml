"""CryptoWall v1 envelope regression and tamper tests (real cryptography primitives)."""

from __future__ import annotations

import hashlib

import pytest

# CryptoWall is an explicitly optional research extra; the legacy Phase 0
# matrix has zero crypto dependencies. Only the dedicated CryptoWall workflow
# installs [crypto] and MUST execute these tests (not skip them).
pytest.importorskip("cryptography")

from cryptowall import (
    EnvelopeError,
    generate_recipient,
    key_fingerprint,
    open_envelope,
    public_key_bytes,
    seal,
)
from cryptowall.envelope import (
    HEADER_LEN,
    MAGIC,
    MAX_CONTEXT_BYTES,
    MAX_PLAINTEXT_BYTES,
    NONCE_LEN,
    PUBLIC_KEY_LEN,
    SALT_LEN,
    TAG_LEN,
)


@pytest.fixture
def recipient():
    return generate_recipient()


def _flip(data: bytes, index: int) -> bytes:
    damaged = bytearray(data)
    damaged[index] ^= 1
    return bytes(damaged)


@pytest.mark.parametrize("message", [b"", b"bonjour", b"\x00\xff" * 200, bytes(range(256))])
def test_binary_roundtrip_with_context(recipient, message):
    private, public = recipient
    wrapped = seal(public, message, context=b"stoparnaques/v1:test")
    assert wrapped.startswith(MAGIC)
    assert len(wrapped) == HEADER_LEN + len(message) + TAG_LEN
    assert open_envelope(private, wrapped, context=b"stoparnaques/v1:test") == message


def test_fingerprint_stable_and_recipient_private_not_serialized(recipient):
    private, public = recipient
    assert public_key_bytes(private) == public
    assert len(public) == PUBLIC_KEY_LEN
    expected = hashlib.sha256(b"CryptoWall-v1-recipient:" + public).hexdigest()
    assert key_fingerprint(public) == expected
    assert len(expected) == 64


def test_repeated_encryption_yields_distinct_envelopes(recipient):
    private, public = recipient
    values = [seal(public, b"same message") for _ in range(16)]
    assert len(set(values)) == 16
    assert all(open_envelope(private, value) == b"same message" for value in values)


def test_wrong_recipient_key_fails_authentication(recipient):
    _private, public = recipient
    other_private, _ = generate_recipient()
    wrapped = seal(public, b"secret")
    with pytest.raises(EnvelopeError, match="invalid CryptoWall envelope"):
        open_envelope(other_private, wrapped)


def test_wrong_or_missing_context_fails_authentication(recipient):
    private, public = recipient
    wrapped = seal(public, b"secret", context=b"tenant:A")
    with pytest.raises(EnvelopeError):
        open_envelope(private, wrapped, context=b"tenant:B")
    with pytest.raises(EnvelopeError):
        open_envelope(private, wrapped)


@pytest.mark.parametrize("index", [
    0, len(MAGIC) - 1, len(MAGIC), len(MAGIC) + 15,
    len(MAGIC) + 16, len(MAGIC) + 16 + 31,
    len(MAGIC) + 16 + 32, len(MAGIC) + 16 + 32 + SALT_LEN - 1,
    HEADER_LEN - NONCE_LEN, HEADER_LEN - 1, HEADER_LEN, -1,
])
def test_all_header_fields_ciphertext_and_tag_are_authenticated(recipient, index):
    private, public = recipient
    wrapped = seal(public, b"tamper detection")
    with pytest.raises(EnvelopeError):
        open_envelope(private, _flip(wrapped, index))


@pytest.mark.parametrize("length", [0, 1, len(MAGIC) - 1, HEADER_LEN - 1, HEADER_LEN, HEADER_LEN + 15])
def test_truncated_payload_fails_closed(recipient, length):
    private, public = recipient
    wrapped = seal(public, b"payload")
    with pytest.raises(EnvelopeError):
        open_envelope(private, wrapped[:length])


def test_wrong_version_or_suffix_fails(recipient):
    private, public = recipient
    wrapped = seal(public, b"content")
    with pytest.raises(EnvelopeError):
        open_envelope(private, b"CWALLv2\x00" + wrapped[len(MAGIC):])
    with pytest.raises(EnvelopeError):
        open_envelope(private, wrapped + b"extra")


def test_bad_public_key_and_low_order_x25519_rejected():
    with pytest.raises(ValueError):
        seal(b"", b"hi")
    with pytest.raises(ValueError):
        seal(bytes(32), b"hi")
    with pytest.raises(ValueError):
        key_fingerprint(b"not-public")


def test_maximum_context_length_and_type_guards(recipient):
    private, public = recipient
    with pytest.raises(ValueError):
        seal(public, b"x", context=b"c" * (MAX_CONTEXT_BYTES + 1))
    with pytest.raises(ValueError):
        open_envelope(private, seal(public, b"x"), context=b"c" * (MAX_CONTEXT_BYTES + 1))
    with pytest.raises(TypeError):
        seal(public, "not bytes")
    with pytest.raises(TypeError):
        open_envelope(private, bytearray(seal(public, b"x")))
    with pytest.raises(TypeError):
        seal(public, b"x", context=None)


def test_message_and_envelope_limits_enforced(recipient):
    private, public = recipient
    with pytest.raises(ValueError):
        seal(public, b"a" * (MAX_PLAINTEXT_BYTES + 1))
    with pytest.raises(ValueError):
        open_envelope(private, b"x" * (HEADER_LEN + MAX_PLAINTEXT_BYTES + TAG_LEN + 1))


def test_private_key_type_is_checked(recipient):
    _private, public = recipient
    wrapped = seal(public, b"private")
    with pytest.raises(TypeError):
        open_envelope(public, wrapped)
    with pytest.raises(TypeError):
        public_key_bytes(public)


def test_replay_not_solved_by_stateless_envelope(recipient):
    """Demonstrates intentionally missing replay protection, not a pass claim."""
    private, public = recipient
    wrapped = seal(public, b"valid repeated data")
    assert open_envelope(private, wrapped) == b"valid repeated data"
    assert open_envelope(private, wrapped) == b"valid repeated data"


def test_sender_is_not_authenticated_by_public_key_encryption(recipient):
    """Anybody with public key can encrypt; recipient cannot identify sender."""
    private, public = recipient
    sender_a = seal(public, b"sender claims A")
    sender_b = seal(public, b"sender claims B")
    assert open_envelope(private, sender_a) == b"sender claims A"
    assert open_envelope(private, sender_b) == b"sender claims B"
