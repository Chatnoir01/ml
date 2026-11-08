from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import (
    BoundaryEvidence, BoundaryKind, development_boundary,
)
from secure_core_mobile.session import establish_boundary_session, establish_development_session


def _self_declared_pvm() -> BoundaryEvidence:
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-1",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256="a" * 64,
    )


def test_development_session_is_explicitly_untrusted():
    context, key = establish_development_session()
    assert context.trusted_boundary is False
    assert context.provenance == "development-process-random"
    assert len(key) == 32


def test_development_boundary_cannot_create_trusted_session():
    with pytest.raises(ValueError, match="does not qualify"):
        establish_boundary_session(
            boundary=development_boundary(),
            derived_key=b"x" * 32,
        )


@pytest.mark.parametrize("derived_key", [b"short", b"x" * 32])
def test_self_declared_pvm_cannot_create_trusted_session_at_any_key_length(derived_key):
    # Provenance is checked first. A 32-byte key alone cannot confer trust;
    # a too-short key must not bypass the boundary gate either.
    boundary = _self_declared_pvm()
    assert boundary.qualifies_for_hostile_host_experiment is False
    with pytest.raises(ValueError, match="does not qualify"):
        establish_boundary_session(boundary=boundary, derived_key=derived_key)


def test_self_declared_pvm_cannot_claim_qualified_session_provenance():
    with pytest.raises(ValueError, match="does not qualify"):
        establish_boundary_session(boundary=_self_declared_pvm(), derived_key=b"x" * 32)
