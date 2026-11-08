from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import (
    BoundaryEvidence, BoundaryKind, development_boundary,
)
from secure_core_mobile.hostile_protocol import HostileHostProtocol


def _self_declared_pvm(*, owns_monotonic_state: bool) -> BoundaryEvidence:
    """A Python dataclass supplied by a caller is never native attestation."""
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-test",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=owns_monotonic_state,
        evidence_sha256="a" * 64,
    )


def test_development_host_never_qualifies_as_isolated_boundary():
    boundary = development_boundary()
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="insufficient"):
        HostileHostProtocol(1, boundary).authorize_execution()


def test_partial_pvm_evidence_fails_closed():
    boundary = _self_declared_pvm(owns_monotonic_state=False)
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="insufficient"):
        HostileHostProtocol(1, boundary).authorize_execution()


def test_complete_self_declared_pvm_evidence_still_fails_closed():
    # Regression: all-True booleans and a SHA digest are not an Android proof.
    boundary = _self_declared_pvm(owns_monotonic_state=True)
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="insufficient"):
        HostileHostProtocol(1, boundary).authorize_execution()


def test_unfrozen_protocol_is_rejected_before_boundary_qualification():
    boundary = _self_declared_pvm(owns_monotonic_state=True)
    with pytest.raises(ValueError, match="frozen"):
        HostileHostProtocol(1, boundary, frozen=False).authorize_execution()
