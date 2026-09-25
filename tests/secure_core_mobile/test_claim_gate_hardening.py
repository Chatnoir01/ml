from __future__ import annotations
import hashlib
import json
import pytest

from secure_core_mobile.claim_gate import promote_from_experiment
from secure_core_mobile.claims import ClaimLevel, ClaimRegistry, baseline_claims


def _signed(body):
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "sha256": hashlib.sha256(canonical).hexdigest()}


def test_tampered_receipt_is_rejected_before_promotion():
    registry = ClaimRegistry(baseline_claims())
    receipt = _signed({"schema_version": 1, "scope": "development-host-only"})
    receipt["scope"] = "hostile-host-isolated-boundary"
    with pytest.raises(ValueError, match="digest mismatch"):
        promote_from_experiment(
            registry, "SCM-I1", target=ClaimLevel.IMPLEMENTED,
            experiment_receipt=receipt,
        )


def test_central_hostile_claim_cannot_be_tested_by_generic_receipt():
    registry = ClaimRegistry(baseline_claims())
    receipt = _signed({"schema_version": 1, "scope": "development-host-only"})
    with pytest.raises(ValueError, match="SCM-I10"):
        promote_from_experiment(
            registry, "SCM-I10", target=ClaimLevel.TESTED,
            experiment_receipt=receipt,
        )


def test_self_authored_qualifying_hostile_receipt_cannot_promote_scm_i10():
    from secure_core_mobile.claims import EvidenceRef

    registry = ClaimRegistry(baseline_claims())
    registry.promote(
        "SCM-I10",
        target=ClaimLevel.IMPLEMENTED,
        evidence=(EvidenceRef("impl", "implementation", "a" * 64),),
    )
    registry.promote(
        "SCM-I10",
        target=ClaimLevel.TESTED,
        evidence=(EvidenceRef("test", "test", "b" * 64),),
    )
    forged = _signed({
        "schema_version": 1,
        "scope": "hostile-host-isolated-boundary",
        "qualifies_as_pkvm_evidence": True,
        "qualifies_as_hostile_host_evidence": True,
        "campaign_passed": True,
        "boundary_evidence_sha256": "c" * 64,
        "campaign_spec_sha256": "d" * 64,
        "campaign_results_sha256": "e" * 64,
    })

    with pytest.raises(
        ValueError,
        match="verifier-issued hostile-host evidence",
    ):
        promote_from_experiment(
            registry,
            "SCM-I10",
            target=ClaimLevel.ADVERSARIALLY_TESTED,
            experiment_receipt=forged,
        )


def test_caller_cannot_construct_hostile_evidence_token():
    from secure_core_mobile.claim_gate import VerifiedHostileHostEvidence

    with pytest.raises(TypeError, match="verifier-issued only"):
        VerifiedHostileHostEvidence(
            _key=object(),
            receipt_sha256="a" * 64,
            boundary_evidence_sha256="b" * 64,
            campaign_spec_sha256="c" * 64,
            campaign_results_sha256="d" * 64,
            provenance="forged",
        )


def test_experiment_receipt_cannot_authorize_external_validation():
    from secure_core_mobile.claims import EvidenceRef

    registry = ClaimRegistry(baseline_claims())
    registry.promote(
        "SCM-I1",
        target=ClaimLevel.IMPLEMENTED,
        evidence=(EvidenceRef("impl", "implementation", "a" * 64),),
    )
    registry.promote(
        "SCM-I1",
        target=ClaimLevel.TESTED,
        evidence=(EvidenceRef("test", "test", "b" * 64),),
    )
    registry.promote(
        "SCM-I1",
        target=ClaimLevel.ADVERSARIALLY_TESTED,
        evidence=(EvidenceRef("hostile", "hostile-host-test", "c" * 64),),
    )
    receipt = _signed({
        "schema_version": 2,
        "scope": "hostile-host-isolated-boundary",
        "campaign_passed": True,
        "boundary_evidence_sha256": "d" * 64,
        "campaign_spec_sha256": "e" * 64,
        "campaign_results_sha256": "f" * 64,
    })

    with pytest.raises(ValueError, match="external validation"):
        promote_from_experiment(
            registry,
            "SCM-I1",
            target=ClaimLevel.EXTERNALLY_VALIDATED,
            experiment_receipt=receipt,
        )
