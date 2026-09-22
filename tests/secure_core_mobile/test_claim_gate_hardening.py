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
