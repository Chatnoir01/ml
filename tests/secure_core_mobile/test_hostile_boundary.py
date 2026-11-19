from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import (
    BoundaryEvidence, BoundaryKind, development_boundary,
)
from secure_core_mobile.hostile_protocol import HostileHostProtocol


def test_development_host_never_qualifies_as_isolated_boundary():
    boundary = development_boundary()
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="insufficient"):
        HostileHostProtocol(1, boundary).authorize_execution()


def test_partial_pvm_evidence_fails_closed():
    boundary = BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-test",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=False,
        evidence_sha256="a" * 64,
    )
    assert boundary.qualifies_for_hostile_host_experiment is False


def test_complete_declared_pvm_evidence_passes_protocol_gate():
    boundary = BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-test",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256="a" * 64,
    )
    HostileHostProtocol(1, boundary).authorize_execution()


def test_unfrozen_protocol_is_rejected():
    boundary = BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-test",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="frozen"):
        HostileHostProtocol(1, boundary, frozen=False).authorize_execution()
