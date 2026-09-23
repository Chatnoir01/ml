import pytest
from secure_core_mobile.avf_platform_verifier import AndroidAvfAuthoritativeVerifierUnavailable
from secure_core_mobile.secretkeeper import SecretkeeperCapability
from secure_core_mobile.secretkeeper_monotonic import SecretkeeperMonotonicRoot

def test_all_true_secretkeeper_metadata_cannot_claim_hardware_monotonic_root():
    capability=SecretkeeperCapability(identity_verified=True,authgraph_channel_established=True,policy_gated_storage=True,rollback_protected_storage=True)
    root=SecretkeeperMonotonicRoot(capability=capability)
    assert root.hardware_resistant is False
    assert root.boundary_owned is False
    with pytest.raises(RuntimeError,match="not implemented"): root.current()

def test_authoritative_avf_verifier_is_explicitly_unavailable():
    with pytest.raises(RuntimeError,match="not implemented"):
        AndroidAvfAuthoritativeVerifierUnavailable().verify()
