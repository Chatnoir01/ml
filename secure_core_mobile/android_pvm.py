"""Android pVM adapter boundary.

This module defines runtime probing and evidence intake without pretending a
non-Android process has AVF/pKVM capabilities.
"""

from __future__ import annotations
from dataclasses import dataclass
from .compat import StrEnum
import hashlib
import sys

from .hostile_boundary import BoundaryEvidence, BoundaryKind


class PvmRuntimeState(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    PRESENT_UNVERIFIED = "PRESENT_UNVERIFIED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"


@dataclass(frozen=True)
class PvmProbe:
    state: PvmRuntimeState
    reason: str


def probe_runtime(*, platform: str | None = None, avf_present: bool = False) -> PvmProbe:
    target = sys.platform if platform is None else platform
    if target != "android":
        return PvmProbe(PvmRuntimeState.UNAVAILABLE, "non-android-runtime")
    if not avf_present:
        return PvmProbe(PvmRuntimeState.UNAVAILABLE, "android-avf-not-detected")
    return PvmProbe(PvmRuntimeState.PRESENT_UNVERIFIED, "avf-present-evidence-not-verified")


@dataclass(frozen=True)
class PvmEvidenceBundle:
    boundary_id: str
    measurement: str
    authorization_state_inside_boundary: bool
    monotonic_state_inside_boundary: bool
    raw_evidence: bytes


class AndroidPvmAdapter:
    def verify_evidence(self, bundle: PvmEvidenceBundle) -> BoundaryEvidence:
        if not bundle.boundary_id or not bundle.measurement or not bundle.raw_evidence:
            raise ValueError("incomplete pVM evidence")
        # Cryptographic/platform verification is deliberately not implemented yet.
        # Hashing preserves evidence identity but is NOT verification.
        digest = hashlib.sha256(bundle.raw_evidence).hexdigest()
        return BoundaryEvidence(
            kind=BoundaryKind.ANDROID_PVM,
            boundary_id=bundle.boundary_id,
            isolated_from_host=False,
            owns_authorization_state=bundle.authorization_state_inside_boundary,
            owns_monotonic_state=bundle.monotonic_state_inside_boundary,
            evidence_sha256=digest,
        )
