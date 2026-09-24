from __future__ import annotations
import hashlib
import json
import pytest

from secure_core_mobile.claim_gate import promote_from_experiment
from secure_core_mobile.claims import ClaimLevel, ClaimRegistry, EvidenceRef, baseline_claims


def _dev_receipt():
    body = {
        "scope": "development-host-only",
        "qualifies_as_pkvm_evidence": False,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "sha256": hashlib.sha256(canonical).hexdigest()}


def test_development_harness_cannot_promote_adversarial_claim():
    registry = ClaimRegistry(baseline_claims())
    registry.promote("SCM-I10", target=ClaimLevel.IMPLEMENTED,
                     evidence=(EvidenceRef("impl", "implementation", "a"*64),))
    registry.promote("SCM-I10", target=ClaimLevel.TESTED,
                     evidence=(EvidenceRef("test", "test", "a"*64),))
    with pytest.raises(ValueError, match="development-host"):
        promote_from_experiment(
            registry, "SCM-I10",
            target=ClaimLevel.ADVERSARIALLY_TESTED,
            experiment_receipt=_dev_receipt(),
        )


def test_development_receipt_can_only_support_ordinary_test_level():
    registry = ClaimRegistry(baseline_claims())
    registry.promote("SCM-I1", target=ClaimLevel.IMPLEMENTED,
                     evidence=(EvidenceRef("impl", "implementation", "a"*64),))
    promote_from_experiment(
        registry, "SCM-I1",
        target=ClaimLevel.TESTED,
        experiment_receipt=_dev_receipt(),
    )
    assert registry.get("SCM-I1").level is ClaimLevel.TESTED
