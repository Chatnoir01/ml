"""Phase 2R preflight: synthetic input bytes only, no model training."""
from __future__ import annotations

import hashlib
import json

import pytest

from adversarial_sbox.phase2r_input_preflight import preflight_phase2r_input_cell


def test_pinned_input_generation_is_repeatable_and_order_invariant() -> None:
    result = preflight_phase2r_input_cell(difference=1, replicate=0)
    assert result["status"] == "SAME_PROCESS_INPUT_PRECHECK_PASS"
    assert result["split_sizes"] == {"train": 5600, "validation": 1200, "test": 1200}
    assert len(set(result["split_sha256"].values())) == 3
    assert all(len(s) == 64 for s in result["split_sha256"].values())
    assert result["same_process_reproducible"]
    assert result["order_invariant"]
    assert result["neural_training_performed"] is False
    assert result["cross_process_reproducibility_established"] is False
    assert result["historical_discrepancy_explained"] is False
    assert result["cryptographic_security_established"] is False
    copy = dict(result)
    digest = copy.pop("report_sha256")
    blob = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert digest == hashlib.sha256(blob).hexdigest()


@pytest.mark.parametrize("difference,replicate", [
    (0, 0), (2, 0), (1, -1), (1, 8), (True, 0), (1, False),
    ("1", 0), (1, "0"),
])
def test_unregistered_or_non_integral_parameters_rejected(difference: object, replicate: object) -> None:
    with pytest.raises(ValueError, match="unregistered"):
        preflight_phase2r_input_cell(difference=difference, replicate=replicate)
