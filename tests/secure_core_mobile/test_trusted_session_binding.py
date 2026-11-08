from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind, development_boundary
from secure_core_mobile.session_binding import (
    derive_session_key_for_test_only, establish_verified_session_for_test_only,
)


def _self_declared_pvm():
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


def test_self_declared_pvm_cannot_derive_or_establish_trusted_session():
    boundary = _self_declared_pvm()
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="unqualified"):
        derive_session_key_for_test_only(
            boundary=boundary, secret=b"s"*32, challenge=b"challenge"
        )
    with pytest.raises(ValueError, match="unqualified"):
        establish_verified_session_for_test_only(
            boundary=boundary, secret=b"s"*32, challenge=b"challenge"
        )
