from __future__ import annotations
import pytest

from secure_core_mobile.claims import ClaimLevel, ClaimRegistry, EvidenceRef, baseline_claims


def _evidence(kind: str) -> tuple[EvidenceRef, ...]:
    return (EvidenceRef("e-1", kind, "a" * 64),)


def test_baseline_has_all_ten_frozen_invariants():
    registry = ClaimRegistry(baseline_claims())
    assert all(registry.get(f"SCM-I{i}").level is ClaimLevel.CLAIMED for i in range(1, 11))


def test_claim_cannot_skip_maturity_level():
    registry = ClaimRegistry(baseline_claims())
    with pytest.raises(ValueError, match="exactly one"):
        registry.promote("SCM-I1", target=ClaimLevel.TESTED, evidence=_evidence("test"))


def test_implemented_requires_implementation_evidence():
    registry = ClaimRegistry(baseline_claims())
    with pytest.raises(ValueError, match="implementation"):
        registry.promote("SCM-I1", target=ClaimLevel.IMPLEMENTED, evidence=_evidence("test"))


def test_adversarial_level_requires_hostile_host_evidence():
    registry = ClaimRegistry(baseline_claims())
    registry.promote("SCM-I1", target=ClaimLevel.IMPLEMENTED, evidence=_evidence("implementation"))
    registry.promote("SCM-I1", target=ClaimLevel.TESTED, evidence=_evidence("test"))
    with pytest.raises(ValueError, match="hostile-host-test"):
        registry.promote(
            "SCM-I1",
            target=ClaimLevel.ADVERSARIALLY_TESTED,
            evidence=_evidence("test"),
        )


def test_external_validation_requires_distinct_evidence_kind():
    registry = ClaimRegistry(baseline_claims())
    registry.promote("SCM-I1", target=ClaimLevel.IMPLEMENTED, evidence=_evidence("implementation"))
    registry.promote("SCM-I1", target=ClaimLevel.TESTED, evidence=_evidence("test"))
    registry.promote("SCM-I1", target=ClaimLevel.ADVERSARIALLY_TESTED, evidence=_evidence("hostile-host-test"))
    with pytest.raises(ValueError, match="external-validation"):
        registry.promote(
            "SCM-I1",
            target=ClaimLevel.EXTERNALLY_VALIDATED,
            evidence=_evidence("hostile-host-test"),
        )
