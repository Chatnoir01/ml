from __future__ import annotations
import pytest
from secure_core_mobile.avf_extension import AvfAttestationExtension, VmComponent
from secure_core_mobile.avf_policy import AvfComponentPolicy, ExpectedVmComponent


def _claims(version=5, code=b"c"*32, authority=b"a"*32):
    return AvfAttestationExtension(
        b"challenge", True,
        (VmComponent("payload.apk", version, code, authority),),
    )


def _policy():
    return AvfComponentPolicy((
        ExpectedVmComponent("payload.apk", 5, b"c"*32, b"a"*32),
    ))


def test_exact_component_policy_passes():
    _policy().verify(_claims())


def test_component_security_version_rollback_fails():
    with pytest.raises(ValueError, match="rollback"):
        _policy().verify(_claims(version=4))


@pytest.mark.parametrize("field", ["code", "authority"])
def test_component_measurement_substitution_fails(field):
    kwargs = {field: b"x"*32}
    with pytest.raises(ValueError, match="hash mismatch"):
        _policy().verify(_claims(**kwargs))


def test_unexpected_component_fails_closed():
    claims = AvfAttestationExtension(
        b"challenge", True,
        _claims().vm_components + (VmComponent("extra.apex", 1, b"x"*32, b"y"*32),),
    )
    with pytest.raises(ValueError, match="unexpected"):
        _policy().verify(claims)
