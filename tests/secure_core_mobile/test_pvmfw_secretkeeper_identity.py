import pytest
from secure_core_mobile.authgraph_session import PvmfwValidatedSecretkeeperKey, SecretkeeperIdentityVerifierUnavailable

def test_secretkeeper_key_requires_exact_trusted_avf_path():
    with pytest.raises(ValueError,match="trusted /avf"):
        PvmfwValidatedSecretkeeperKey(b"key",source_path="/proc/device-tree/avf/untrusted/secretkeeper_public_key")

def test_empty_pvmfw_validated_key_is_rejected():
    with pytest.raises(ValueError,match="empty"):
        PvmfwValidatedSecretkeeperKey(b"")

def test_validated_dt_type_still_cannot_self_promote_to_verified_identity():
    key=PvmfwValidatedSecretkeeperKey(b"cbor-cose-key")
    with pytest.raises(RuntimeError,match="not implemented"):
        SecretkeeperIdentityVerifierUnavailable().verify(key)
