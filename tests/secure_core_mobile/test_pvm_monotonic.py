import pytest

from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind, development_boundary
from secure_core_mobile.pvm_monotonic import PvmMonotonicRootUnavailable


def _self_declared_pvm():
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM, boundary_id="pvm",
        isolated_from_host=True, owns_authorization_state=True,
        owns_monotonic_state=True, evidence_sha256="a"*64,
    )


def test_development_boundary_cannot_construct_pvm_root():
    with pytest.raises(ValueError, match="qualified"):
        PvmMonotonicRootUnavailable(development_boundary())


def test_self_declared_pvm_cannot_construct_monotonic_root():
    # Do not revive the old positive construction test: there is no
    # independently verified native Android issuer for this dataclass.
    boundary = _self_declared_pvm()
    assert boundary.qualifies_for_hostile_host_experiment is False
    assert PvmMonotonicRootUnavailable.hardware_resistant is False
    assert PvmMonotonicRootUnavailable.boundary_owned is False
    with pytest.raises(ValueError, match="qualified"):
        PvmMonotonicRootUnavailable(boundary)
