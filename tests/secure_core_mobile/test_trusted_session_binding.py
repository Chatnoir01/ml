from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind, development_boundary
from secure_core_mobile.session_binding import establish_verified_session_for_test_only


def _qualified():
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM, boundary_id="pvm-1",
        isolated_from_host=True, owns_authorization_state=True,
        owns_monotonic_state=True, evidence_sha256="a"*64,
    )


def test_unqualified_boundary_cannot_establish_bound_session():
    with pytest.raises(ValueError, match="unqualified"):
        establish_verified_session_for_test_only(
            boundary=development_boundary(), secret=b"s"*32, challenge=b"c"
        )


def test_qualified_boundary_session_retains_trusted_provenance():
    context = establish_verified_session_for_test_only(
        boundary=_qualified(), secret=b"s"*32, challenge=b"challenge"
    )
    assert context.trusted_boundary is True
    assert context.provenance == "qualified-boundary:pvm-1"
