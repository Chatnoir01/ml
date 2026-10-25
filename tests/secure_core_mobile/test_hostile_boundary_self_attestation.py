"""Security regression: claimed pVM state is not trusted hardware evidence.

Development-only synthetic inputs. Does not execute on Android hardware.
"""
from __future__ import annotations

import hashlib

from secure_core_mobile.hostile_boundary import BoundaryEvidence, BoundaryKind
from secure_core_mobile.security_gate import SecurityCapability, require_hostile_host_ready
from secure_core_mobile.hostile_campaign import HostileCampaign, REQUIRED_SCENARIOS, ScenarioResult
from secure_core_mobile.hostile_receipt import hostile_campaign_receipt


def _fabricated_boundary() -> BoundaryEvidence:
    return BoundaryEvidence(
        kind=BoundaryKind.ANDROID_PVM,
        boundary_id="attacker-claimed-pvm",
        isolated_from_host=True,
        owns_authorization_state=True,
        owns_monotonic_state=True,
        evidence_sha256=hashlib.sha256(b"attacker-controlled").hexdigest(),
    )


def test_forged_pvm_metadata_is_never_hardware_qualification() -> None:
    boundary = _fabricated_boundary()
    assert boundary.qualifies_for_hostile_host_experiment is False

    cap = SecurityCapability(
        boundary, monotonic_hardware_resistant=True,
        monotonic_boundary_owned=True,
        attestation_verified=True, secretkeeper_verified=True,
    )
    assert cap.hostile_host_ready is False


def test_synthetic_all_pass_campaign_never_reports_isolated_hardware_evidence() -> None:
    cap = SecurityCapability(_fabricated_boundary(), True, True, True, True)
    passing = tuple(ScenarioResult(s, True, False) for s in REQUIRED_SCENARIOS)
    receipt = hostile_campaign_receipt(
        campaign=HostileCampaign(),
        capability=cap,
        results=passing,
    )
    assert receipt["campaign_passed"] is True  # simulated behavior only
    assert receipt["scope"] == "development-host-only"
    assert receipt["hostile_host_ready"] is False
    assert receipt["qualifies_as_pkvm_evidence"] is False
    assert receipt["qualifies_as_hostile_host_evidence"] is False
    assert len(receipt["sha256"]) == 64
