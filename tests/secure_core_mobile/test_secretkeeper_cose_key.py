from __future__ import annotations

import hashlib

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from secure_core_mobile.secretkeeper_cose_key import parse_secretkeeper_cose_key


def _head(major: int, n: int) -> bytes:
    if n < 24:
        return bytes(((major << 5) | n,))
    if n <= 0xFF:
        return bytes(((major << 5) | 24, n))
    if n <= 0xFFFF:
        return bytes(((major << 5) | 25,)) + n.to_bytes(2, "big")
    raise ValueError("test CBOR value too large")


def _int(v: int) -> bytes:
    return _head(0, v) if v >= 0 else _head(1, -1 - v)


def _bstr(v: bytes) -> bytes:
    return _head(2, len(v)) + v


def _map(items: list[tuple[int, int | bytes]]) -> bytes:
    encoded = []
    for key, value in items:
        encoded_value = _int(value) if isinstance(value, int) else _bstr(value)
        encoded.append((_int(key), encoded_value))
    encoded.sort(key=lambda pair: pair[0])
    return _head(5, len(encoded)) + b"".join(k + v for k, v in encoded)


def _ed25519_key() -> bytes:
    pub = ed25519.Ed25519PrivateKey.generate().public_key()
    x = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _map([(1, 1), (3, -8), (-1, 6), (-2, x)])


def _ec_key(curve: ec.EllipticCurve, *, alg: int, crv: int, width: int) -> bytes:
    numbers = ec.generate_private_key(curve).public_key().public_numbers()
    return _map([
        (1, 2),
        (3, alg),
        (-1, crv),
        (-2, numbers.x.to_bytes(width, "big")),
        (-3, numbers.y.to_bytes(width, "big")),
    ])


@pytest.mark.parametrize(
    ("encoded", "profile"),
    [
        (_ed25519_key(), "Ed25519"),
        (_ec_key(ec.SECP256R1(), alg=-7, crv=1, width=32), "ECDSA_P256"),
        (_ec_key(ec.SECP384R1(), alg=-35, crv=2, width=48), "ECDSA_P384"),
    ],
)
def test_aosp_secretkeeper_key_profiles_are_accepted(encoded: bytes, profile: str) -> None:
    parsed = parse_secretkeeper_cose_key(encoded)
    assert parsed.profile == profile
    assert parsed.encoded_sha256 == hashlib.sha256(encoded).hexdigest()


def test_mismatched_secretkeeper_algorithm_curve_is_rejected() -> None:
    encoded = _ec_key(ec.SECP256R1(), alg=-35, crv=1, width=32)
    with pytest.raises(ValueError, match="unsupported"):
        parse_secretkeeper_cose_key(encoded)


def test_extra_cose_key_labels_are_rejected() -> None:
    pub = ed25519.Ed25519PrivateKey.generate().public_key()
    x = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    encoded = _map([(1, 1), (3, -8), (-1, 6), (-2, x), (4, 1)])
    with pytest.raises(ValueError, match="unexpected labels"):
        parse_secretkeeper_cose_key(encoded)


def test_invalid_p256_point_is_rejected() -> None:
    encoded = _map([
        (1, 2),
        (3, -7),
        (-1, 1),
        (-2, b"\x00" * 32),
        (-3, b"\x00" * 32),
    ])
    with pytest.raises(ValueError, match="public point"):
        parse_secretkeeper_cose_key(encoded)


@pytest.mark.parametrize("encoded", [b"", b"not-cbor", b"\xa0"])
def test_malformed_or_empty_secretkeeper_key_is_rejected(encoded: bytes) -> None:
    with pytest.raises(ValueError):
        parse_secretkeeper_cose_key(encoded)
