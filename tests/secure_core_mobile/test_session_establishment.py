from __future__ import annotations
import pytest

from secure_core_mobile.hostile_boundary import (
    BoundaryEvidence, BoundaryKind, development_boundary,
)
from secure_core_mobile.session import establish_boundary_session, establish_development_session


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


def test_qualified_boundary_requires_strong_session_key():
    boundary = BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-1",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="too short"):
        establish_boundary_session(boundary=boundary, derived_key=b"short")


def test_qualified_boundary_records_provenance():
    boundary = BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="pvm-1",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256="a" * 64,
    )
    context = establish_boundary_session(boundary=boundary, derived_key=b"x" * 32)
    assert context.trusted_boundary is True
    assert context.provenance == "qualified-boundary:pvm-1"
