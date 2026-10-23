"""Opt-in hybrid HPKE experiment using cryptography's vetted suite API.

This is NOT CryptoWall v1 compatibility, E2EE, sender authentication,
post-compromise recovery, or a deployment-approved security upgrade.
No handwritten ML-KEM or key combiner: use the library HPKE implementation.

Do not silently downgrade to classical X25519 if hybrid support is absent.
"""

from __future__ import annotations

from cryptography.exceptions import InvalidTag, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import x25519, mlkem
from cryptography.hazmat.primitives.hpke import (
    AEAD, KDF, KEM, MLKEM768X25519PrivateKey, MLKEM768X25519PublicKey, Suite,
)

from .envelope import EnvelopeError

_MAGIC = b"CWALLPQ1\x00"
_DOMAIN = b"CryptoWall/research/v0/HPKE/MLKEM768-X25519/AES256GCM/"
_MAX_CONTEXT = 4096
_MAX_PLAINTEXT = 8 * 1024 * 1024
_SUITE = Suite(KEM.MLKEM768_X25519, KDF.HKDF_SHA256, AEAD.AES_256_GCM)


def hybrid_capability() -> bool:
    """Test actual ML-KEM backend. Capability is not cryptographic assurance."""
    try:
        _ = mlkem.MLKEM768PrivateKey.generate()
        return True
    except UnsupportedAlgorithm:
        return False


def _require_hybrid() -> None:
    if not hybrid_capability():
        raise RuntimeError("hybrid ML-KEM-768 backend unavailable; no classical fallback")


def generate_hybrid_recipient() -> tuple[MLKEM768X25519PrivateKey, MLKEM768X25519PublicKey]:
    """Independent in-memory key components; no private key serialization."""
    _require_hybrid()
    private = MLKEM768X25519PrivateKey(
        mlkem.MLKEM768PrivateKey.generate(),
        x25519.X25519PrivateKey.generate(),
    )
    return private, private.public_key()


def _context_info(context: bytes) -> bytes:
    if not isinstance(context, bytes):
        raise TypeError("hybrid HPKE context must be bytes")
    if len(context) > _MAX_CONTEXT:
        raise ValueError("hybrid HPKE context too large")
    return _DOMAIN + len(context).to_bytes(4, "big") + context


def seal_hybrid(
    recipient: MLKEM768X25519PublicKey,
    plaintext: bytes, *, context: bytes = b"",
) -> bytes:
    """Encrypt only to an independently authenticated hybrid recipient key."""
    if not isinstance(recipient, MLKEM768X25519PublicKey):
        raise TypeError("hybrid ML-KEM-768/X25519 public key required; no downgrade")
    if not isinstance(plaintext, bytes):
        raise TypeError("hybrid HPKE plaintext must be bytes")
    if len(plaintext) > _MAX_PLAINTEXT:
        raise ValueError("hybrid HPKE plaintext too large")
    info = _context_info(context)
    _require_hybrid()
    return _MAGIC + _SUITE.encrypt(plaintext, recipient, info=info)


def open_hybrid(
    recipient_private: MLKEM768X25519PrivateKey,
    envelope: bytes, *, context: bytes = b"",
) -> bytes:
    """Reject unsupported versions, modified envelopes and wrong context."""
    if not isinstance(recipient_private, MLKEM768X25519PrivateKey):
        raise TypeError("hybrid ML-KEM-768/X25519 private key required")
    if not isinstance(envelope, bytes):
        raise TypeError("hybrid HPKE envelope must be bytes")
    info = _context_info(context)
    _require_hybrid()
    min_length = len(_MAGIC) + KEM.MLKEM768_X25519.enc_length() + 16
    max_length = min_length + _MAX_PLAINTEXT
    if not (min_length <= len(envelope) <= max_length):
        raise EnvelopeError("invalid hybrid HPKE envelope")
    if not envelope.startswith(_MAGIC):
        raise EnvelopeError("invalid hybrid HPKE envelope")
    try:
        return _SUITE.decrypt(envelope[len(_MAGIC):], recipient_private, info=info)
    except (InvalidTag, ValueError) as exc:
        raise EnvelopeError("invalid hybrid HPKE envelope") from exc
