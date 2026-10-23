"""CryptoWall v1: experimental, one-way public-key envelope.

Only audited, standard building blocks are used. This module is NOT a secure
messenger: it has no sender authentication, replay protection, ratchet,
forward secrecy after compromise of the recipient's static key, or PQ safety.

Do not place private keys, secrets or user messages in this repository.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"CWALLv1\x00"
KEY_ID_LEN = 16
PUBLIC_KEY_LEN = 32
SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16
HEADER_LEN = len(MAGIC) + KEY_ID_LEN + PUBLIC_KEY_LEN + SALT_LEN + NONCE_LEN
MAX_PLAINTEXT_BYTES = 8 * 1024 * 1024
MAX_CONTEXT_BYTES = 4096
_KDF_DOMAIN = b"CryptoWall/v1/X25519/HKDF-SHA256/AES-256-GCM/"

# Compatibility rule: these offsets, field lengths, and KDF context are frozen
# for this experimental version. Protocol changes require a new magic/version.


class EnvelopeError(ValueError):
    """Malformed, unsupported or unauthenticated CryptoWall envelope."""


def _bytes(value: object, name: str, maximum: int) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if len(value) > maximum:
        raise ValueError(f"{name} exceeds configured maximum")
    return value


def public_key_bytes(private_key: X25519PrivateKey) -> bytes:
    """Return public identity bytes, not the private key."""
    if not isinstance(private_key, X25519PrivateKey):
        raise TypeError("recipient private key must be X25519PrivateKey")
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def generate_recipient() -> tuple[X25519PrivateKey, bytes]:
    """Generate an in-memory recipient keypair; no keys are written to disk."""
    private_key = X25519PrivateKey.generate()
    return private_key, public_key_bytes(private_key)


def key_fingerprint(public_key: bytes) -> str:
    """Display-only fingerprint; compare over an authenticated channel."""
    if not isinstance(public_key, bytes) or len(public_key) != PUBLIC_KEY_LEN:
        raise ValueError("recipient public key must be 32 bytes")
    return hashlib.sha256(b"CryptoWall-v1-recipient:" + public_key).hexdigest()


def _recipient_id(public_key: bytes) -> bytes:
    return bytes.fromhex(key_fingerprint(public_key))[:KEY_ID_LEN]


def _derive_key(
    shared_secret: bytes, *, salt: bytes,
    recipient_public: bytes, ephemeral_public: bytes,
) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=_KDF_DOMAIN + recipient_public + ephemeral_public,
    ).derive(shared_secret)


def _aad(header: bytes, context: bytes) -> bytes:
    # This length prefix prevents ambiguous external context representation.
    return header + struct.pack(">I", len(context)) + context


def seal(
    recipient_public: bytes, plaintext: bytes, *, context: bytes = b"",
) -> bytes:
    """Encrypt for a pinned X25519 recipient public key, with AEAD integrity.

    Caller MUST authenticate/pin the recipient key separately. An attacker
    who substitutes that key can decrypt the resulting envelope.
    """
    if not isinstance(recipient_public, bytes) or len(recipient_public) != PUBLIC_KEY_LEN:
        raise ValueError("recipient public key must be 32 bytes")
    plaintext = _bytes(plaintext, "plaintext", MAX_PLAINTEXT_BYTES)
    context = _bytes(context, "context", MAX_CONTEXT_BYTES)
    try:
        recipient = X25519PublicKey.from_public_bytes(recipient_public)
        ephemeral_private = X25519PrivateKey.generate()
        ephemeral_public = public_key_bytes(ephemeral_private)
        shared = ephemeral_private.exchange(recipient)
    except ValueError as exc:
        raise ValueError("invalid recipient X25519 public key") from exc

    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    header = (
        MAGIC + _recipient_id(recipient_public) + ephemeral_public + salt + nonce
    )
    key = _derive_key(
        shared, salt=salt, recipient_public=recipient_public,
        ephemeral_public=ephemeral_public,
    )
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, _aad(header, context))
    return header + ciphertext


def open_envelope(
    recipient_private: X25519PrivateKey, envelope: bytes, *,
    context: bytes = b"",
) -> bytes:
    """Decrypt only after authenticating the complete header and context.

    Errors reveal no decrypted bytes. A replay of a valid envelope remains
    valid: freshness is a higher-layer responsibility.
    """
    if not isinstance(recipient_private, X25519PrivateKey):
        raise TypeError("recipient private key must be X25519PrivateKey")
    context = _bytes(context, "context", MAX_CONTEXT_BYTES)
    envelope = _bytes(
        envelope, "envelope", HEADER_LEN + MAX_PLAINTEXT_BYTES + TAG_LEN,
    )
    if len(envelope) < HEADER_LEN + TAG_LEN or envelope[:len(MAGIC)] != MAGIC:
        raise EnvelopeError("invalid CryptoWall envelope")

    header, ciphertext = envelope[:HEADER_LEN], envelope[HEADER_LEN:]
    index = len(MAGIC)
    recipient_id = header[index:index + KEY_ID_LEN]
    index += KEY_ID_LEN
    ephemeral_public = header[index:index + PUBLIC_KEY_LEN]
    index += PUBLIC_KEY_LEN
    salt = header[index:index + SALT_LEN]
    index += SALT_LEN
    nonce = header[index:index + NONCE_LEN]

    recipient_public = public_key_bytes(recipient_private)
    if not hmac.compare_digest(recipient_id, _recipient_id(recipient_public)):
        raise EnvelopeError("invalid CryptoWall envelope")
    try:
        shared = recipient_private.exchange(
            X25519PublicKey.from_public_bytes(ephemeral_public)
        )
        key = _derive_key(
            shared, salt=salt, recipient_public=recipient_public,
            ephemeral_public=ephemeral_public,
        )
        return AESGCM(key).decrypt(nonce, ciphertext, _aad(header, context))
    except (InvalidTag, ValueError) as exc:
        raise EnvelopeError("invalid CryptoWall envelope") from exc
