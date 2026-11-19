"""Strict parser for the AOSP Secretkeeper identity COSE_Key profiles.

AOSP allows exactly three public-key profiles for Secretkeeper identity:
Ed25519, ECDSA P-256 and ECDSA P-384. Structural/key validity is necessary
input hygiene only; successful parsing is not identity or platform verification.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Literal

from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from .cose_sign1_payload import decode_one


COSE_KTY = 1
COSE_ALG = 3
COSE_CRV = -1
COSE_X = -2
COSE_Y = -3

KTY_OKP = 1
KTY_EC2 = 2

ALG_ES256 = -7
ALG_EDDSA = -8
ALG_ES384 = -35

CRV_P256 = 1
CRV_P384 = 2
CRV_ED25519 = 6


@dataclass(frozen=True)
class ParsedSecretkeeperCoseKey:
    profile: Literal["Ed25519", "ECDSA_P256", "ECDSA_P384"]
    encoded_sha256: str
    x: bytes
    y: bytes | None = None

    def __post_init__(self) -> None:
        if len(self.encoded_sha256) != 64:
            raise ValueError("invalid Secretkeeper COSE_Key digest")


def _digest(encoded: bytes) -> str:
    return hashlib.sha256(encoded).hexdigest()


def parse_secretkeeper_cose_key(encoded: bytes) -> ParsedSecretkeeperCoseKey:
    """Parse and validate one permitted Secretkeeper identity COSE_Key."""

    if not isinstance(encoded, bytes):
        raise TypeError("Secretkeeper COSE_Key must be bytes")

    value = decode_one(encoded)
    if not isinstance(value, dict):
        raise ValueError("Secretkeeper identity is not a COSE_Key map")

    kty = value.get(COSE_KTY)
    alg = value.get(COSE_ALG)
    crv = value.get(COSE_CRV)
    x = value.get(COSE_X)
    y = value.get(COSE_Y)

    if (kty, alg, crv) == (KTY_OKP, ALG_EDDSA, CRV_ED25519):
        if set(value) != {COSE_KTY, COSE_ALG, COSE_CRV, COSE_X}:
            raise ValueError("unexpected labels in Ed25519 Secretkeeper COSE_Key")
        if not isinstance(x, bytes) or len(x) != 32:
            raise ValueError("invalid Ed25519 Secretkeeper public key")
        try:
            ed25519.Ed25519PublicKey.from_public_bytes(x)
        except ValueError as exc:
            raise ValueError("invalid Ed25519 Secretkeeper public key") from exc
        return ParsedSecretkeeperCoseKey("Ed25519", _digest(encoded), x)

    if (kty, alg, crv) == (KTY_EC2, ALG_ES256, CRV_P256):
        profile = "ECDSA_P256"
        curve: ec.EllipticCurve = ec.SECP256R1()
        width = 32
    elif (kty, alg, crv) == (KTY_EC2, ALG_ES384, CRV_P384):
        profile = "ECDSA_P384"
        curve = ec.SECP384R1()
        width = 48
    else:
        raise ValueError("unsupported Secretkeeper COSE_Key profile")

    if set(value) != {COSE_KTY, COSE_ALG, COSE_CRV, COSE_X, COSE_Y}:
        raise ValueError("unexpected labels in ECDSA Secretkeeper COSE_Key")
    if (
        not isinstance(x, bytes)
        or not isinstance(y, bytes)
        or len(x) != width
        or len(y) != width
    ):
        raise ValueError("invalid ECDSA Secretkeeper coordinates")

    try:
        ec.EllipticCurvePublicNumbers(
            int.from_bytes(x, "big"),
            int.from_bytes(y, "big"),
            curve,
        ).public_key()
    except ValueError as exc:
        raise ValueError("invalid ECDSA Secretkeeper public point") from exc

    return ParsedSecretkeeperCoseKey(profile, _digest(encoded), x, y)
