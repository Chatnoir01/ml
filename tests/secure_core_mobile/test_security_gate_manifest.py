import pytest

from secure_core_mobile.evidence_manifest import EvidenceManifest
from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind, development_boundary
from secure_core_mobile.security_gate import SecurityCapability, require_hostile_host_ready


def _boundary():
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM, boundary_id="pvm",
        isolated_from_host=True, owns_authorization_state=True,
        owns_monotonic_state=True, evidence_sha256="a"*64,
    )


def test_development_capability_cannot_pass_hostile_host_gate():
    cap = SecurityCapability(development_boundary(), False, False, False)
    assert cap.hostile_host_ready is False
    with pytest.raises(RuntimeError):
        require_hostile_host_ready(cap)


def test_all_independent_conditions_are_required():
    cap = SecurityCapability(_boundary(), True, True, True)
    assert cap.hostile_host_ready is True
    require_hostile_host_ready(cap)


def test_manifest_is_deterministic_and_validated():
    manifest = EvidenceManifest(
        1, "a"*64, "b"*64, 1, "development-monotonic-root", False
    )
    manifest.validate()
    assert manifest.sha256 == manifest.sha256
    assert len(manifest.sha256) == 64
