from __future__ import annotations

from pathlib import Path

import pytest

from secure_core_mobile.authgraph_session import SecretkeeperIdentityVerifierUnavailable
from secure_core_mobile.secretkeeper_dt import (
    MAX_SECRETKEEPER_KEY_BYTES,
    TRUSTED_SECRETKEEPER_DT_PATH,
    read_pvmfw_secretkeeper_key,
)


def test_secretkeeper_dt_reader_accepts_only_exact_trusted_path() -> None:
    called = False

    def reader(path: Path) -> bytes:
        nonlocal called
        called = True
        return b"cbor-cose-key"

    with pytest.raises(ValueError, match="trusted /avf"):
        read_pvmfw_secretkeeper_key(
            path="/tmp/secretkeeper_public_key",
            reader=reader,
        )
    assert called is False


def test_secretkeeper_dt_reader_preserves_exact_provenance() -> None:
    key = read_pvmfw_secretkeeper_key(reader=lambda path: b"cbor-cose-key")
    assert key.public_key_cbor == b"cbor-cose-key"
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
    key = read_pvmfw_secretkeeper_key(reader=lambda path: b"cbor-cose-key")
    with pytest.raises(RuntimeError, match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(key)
