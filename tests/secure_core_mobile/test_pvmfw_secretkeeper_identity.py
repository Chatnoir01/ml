import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from secure_core_mobile.authgraph_session import (
    PvmfwValidatedSecretkeeperKey,
    SecretkeeperIdentityVerifierUnavailable,
)
from secure_core_mobile.secretkeeper_dt import read_pvmfw_secretkeeper_key


def _valid_ed25519_cose_key() -> bytes:
    public_key = ed25519.Ed25519PrivateKey.generate().public_key()
    x = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return b"\xa4\x01\x01\x03\x27\x20\x06\x21\x58\x20" + x


def test_secretkeeper_key_requires_reader_issued_provenance():
    with pytest.raises(TypeError, match="reader-issued"):
        PvmfwValidatedSecretkeeperKey(
            _valid_ed25519_cose_key(),
            source_path="/proc/device-tree/avf/secretkeeper_public_key",
            _key=object(),
        )


def test_empty_pvmfw_device_tree_key_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        read_pvmfw_secretkeeper_key(reader=lambda path: b"")


def test_validated_dt_token_still_cannot_self_promote_to_verified_identity():
    key = read_pvmfw_secretkeeper_key(
        reader=lambda path: _valid_ed25519_cose_key()
    )
    with pytest.raises(RuntimeError, match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(key)
