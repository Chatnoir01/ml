"""Phase 2S is a retrospective audit: never executes or modifies neural training."""
from copy import deepcopy
import json
import math
from pathlib import Path

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
from adversarial_sbox.phase2s_retro import (
    DiagnosticRejected, EXPECTED_CLASSICAL, EXPECTED_PROFILE_MEANS,
    audit, load_score_arrays, local_difference_row, pearson,
    report_from_frozen_repository, row_statistics,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = (ROOT / "research" / "PHASE2AT_RESULT.md").read_text(encoding="utf-8")


def test_six_matched_classical_candidates_have_distinct_local_ddt_profiles():
    output = report_from_frozen_repository()
    assert output["candidate_count"] == 6
    assert tuple(output["matched_global_metrics"].values()) == EXPECTED_CLASSICAL
    assert output["new_training_count"] == 0
    assert output["frozen_verdict_changed"] is False
    assert output["delta1_row_count_distinct"] >= 2
    assert output["inference"] == "DESCRIPTIVE_ONLY_N6_NO_CAUSAL_OR_SECURITY_CLAIM"
    assert min(row["r4_advantage"] for row in output["candidate_results"]) > 0.2


def test_frozen_round_means_and_score_range_exact():
    rows = load_score_arrays(REPORT)
    assert set(rows) == {3, 4, 5}
    for depth, mean in EXPECTED_PROFILE_MEANS.items():
        assert sum(rows[depth]) / 6 == pytest.approx(mean, abs=1e-12)
    assert max(rows[4]) - min(rows[4]) == pytest.approx(
        0.10658153113805419, abs=1e-12
    )


def test_known_delta1_row_statistics_from_frozen_panel():
    row = local_difference_row(CANDIDATES[0]["sbox"], 1)
    stats = row_statistics(row)
    assert stats["support"] == 105
    assert stats["maximum"] == 6
    assert stats["collision"] == pytest.approx(0.010986328125)
    assert stats["entropy_bits"] == pytest.approx(6.622932324168044)


def test_delta1_row_varies_even_with_identical_headline_metrics():
    a, b = CANDIDATES[0], CANDIDATES[4]
    for attr in ("differential_uniformity", "nonlinearity",
                 "max_linear_correlation", "algebraic_degree"):
        assert a[attr] == b[attr]
    first = row_statistics(local_difference_row(a["sbox"]))
    second = row_statistics(local_difference_row(b["sbox"]))
    assert first["maximum"] == 6
    assert second["maximum"] == 8
    assert first["collision"] != second["collision"]


def test_small_sample_correlations_only_descriptive():
    result = report_from_frozen_repository()
    assert result["pearson_r4_vs_delta1_collision"] == pytest.approx(
        0.0855840708293115, abs=1e-12
    )
    assert abs(result["pearson_r4_vs_delta1_entropy"]) < 0.05


def test_repeat_audit_exact_identical_json():
    left = json.dumps(report_from_frozen_repository(), sort_keys=True)
    right = json.dumps(report_from_frozen_repository(), sort_keys=True)
    assert left == right


def test_tampered_score_breaks_frozen_mean_contract():
    corrupted = REPORT.replace("0.3870684507628008", "0.1870684507628008", 1)
    assert corrupted != REPORT
    with pytest.raises(DiagnosticRejected, match="mean"):
        load_score_arrays(corrupted)


def test_missing_depth_or_frozen_verdict_fails_closed():
    with pytest.raises(DiagnosticRejected):
        load_score_arrays(REPORT.replace("Depth 5:", "Depth x:", 1))
    with pytest.raises(DiagnosticRejected):
        load_score_arrays(REPORT.replace("phase2at_depth4_peak_replicated", "not-replicated"))


def test_tampered_candidate_fingerprint_rejected():
    candidates = deepcopy(CANDIDATES)
    candidates = list(candidates)
    candidates[0]["fingerprint"] = "0" * 64
    with pytest.raises(DiagnosticRejected, match="fingerprint"):
        audit(report=REPORT, candidates=candidates,
              claimed_panel_digest=PANEL_DIGEST_SHA256)


def test_changed_headline_metric_rejected():
    candidates = list(deepcopy(CANDIDATES))
    candidates[1]["nonlinearity"] = 98
    with pytest.raises(DiagnosticRejected, match="headline"):
        audit(report=REPORT, candidates=candidates,
              claimed_panel_digest=PANEL_DIGEST_SHA256)


@pytest.mark.parametrize("delta", [-1, 0, 256, 1.0, True])
def test_invalid_difference_rejected(delta):
    with pytest.raises(DiagnosticRejected):
        local_difference_row(CANDIDATES[0]["sbox"], delta)


def test_invalid_ddt_row_rejected():
    with pytest.raises(DiagnosticRejected):
        row_statistics((2,) * 256)


def test_bad_or_constant_correlation_rejected():
    with pytest.raises(DiagnosticRejected):
        pearson((0., 0., 0.), (1., 2., 3.))
    with pytest.raises(DiagnosticRejected):
        pearson((1., 2., 3.), (1., float("nan"), 3.))


def test_report_serializes_without_nan_or_training_outputs():
    output = report_from_frozen_repository()
    serialized = json.dumps(output, sort_keys=True, allow_nan=False)
    assert len(serialized) > 100
    assert "model_state" not in serialized and "private_weights" not in serialized
