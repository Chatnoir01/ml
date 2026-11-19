import pytest

from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind, development_boundary
from secure_core_mobile.pvm_monotonic import PvmMonotonicRootUnavailable


def _qualified():
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM, boundary_id="pvm",
        isolated_from_host=True, owns_authorization_state=True,
        owns_monotonic_state=True, evidence_sha256="a"*64,
    )


def test_development_boundary_cannot_construct_pvm_root():
    with pytest.raises(ValueError, match="qualified"):
        PvmMonotonicRootUnavailable(development_boundary())


def test_placeholder_never_claims_hardware_resistance():
    root = PvmMonotonicRootUnavailable(_qualified())
    assert root.hardware_resistant is False
    assert root.boundary_owned is False
    with pytest.raises(RuntimeError, match="not implemented"):
        root.advance()
