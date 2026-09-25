from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from secure_core_mobile.authgraph_session import SecretkeeperIdentityVerifierUnavailable
from secure_core_mobile.secretkeeper_dt import (
    MAX_SECRETKEEPER_KEY_BYTES,
    TRUSTED_SECRETKEEPER_DT_PATH,
    read_pvmfw_secretkeeper_key,
)


def _valid_p256_cose_key() -> bytes:
    numbers = ec.generate_private_key(ec.SECP256R1()).public_key().public_numbers()

    def head(major: int, n: int) -> bytes:
        if n < 24:
            return bytes(((major << 5) | n,))
        return bytes(((major << 5) | 24, n))

    def integer(v: int) -> bytes:
        return head(0, v) if v >= 0 else head(1, -1 - v)

    def bstr(v: bytes) -> bytes:
        return head(2, len(v)) + v

    entries = [
        (integer(1), integer(2)),
        (integer(3), integer(-7)),
        (integer(-1), integer(1)),
        (integer(-2), bstr(numbers.x.to_bytes(32, "big"))),
        (integer(-3), bstr(numbers.y.to_bytes(32, "big"))),
    ]
    entries.sort(key=lambda pair: pair[0])
    return head(5, len(entries)) + b"".join(k + v for k, v in entries)


def test_secretkeeper_dt_reader_accepts_only_exact_trusted_path() -> None:
    called = False

    def reader(path: Path) -> bytes:
        nonlocal called
        called = True
        return _valid_p256_cose_key()

    with pytest.raises(ValueError, match="trusted /avf"):
        read_pvmfw_secretkeeper_key(
            path="/tmp/secretkeeper_public_key",
            reader=reader,
        )
    assert called is False


def test_secretkeeper_dt_reader_preserves_exact_provenance() -> None:
    encoded = _valid_p256_cose_key()
    key = read_pvmfw_secretkeeper_key(reader=lambda path: encoded)
    assert key.public_key_cbor == encoded
    assert key.source_path == str(TRUSTED_SECRETKEEPER_DT_PATH)


def test_secretkeeper_dt_reader_fails_closed_when_property_is_unavailable() -> None:
    def missing(path: Path) -> bytes:
        raise FileNotFoundError(path)

    with pytest.raises(RuntimeError, match="unavailable"):
        read_pvmfw_secretkeeper_key(reader=missing)


@pytest.mark.parametrize("payload", [b"", b"x" * (MAX_SECRETKEEPER_KEY_BYTES + 1)])
def test_secretkeeper_dt_reader_rejects_invalid_size(payload: bytes) -> None:
    with pytest.raises(ValueError):
        read_pvmfw_secretkeeper_key(reader=lambda path: payload)


def test_device_tree_read_does_not_self_promote_identity() -> None:
    key = read_pvmfw_secretkeeper_key(reader=lambda path: _valid_p256_cose_key())
    with pytest.raises(RuntimeError, match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(key)


def test_device_tree_reader_rejects_malformed_cose_key() -> None:
    with pytest.raises(ValueError):
        read_pvmfw_secretkeeper_key(reader=lambda path: b"not-a-cose-key")
