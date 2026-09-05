"""Phase 1L red-first contract for pre-registered comparison helpers."""

from adversarial_sbox.phase1l import classify_against_control, summarize_classifications
from adversarial_sbox.pareto import ITOAwareMetrics


def metric(*, nl=100, du=8, corr=64, ito=8.0, sac=0.5, degree=6, fp="x"):
    return ITOAwareMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        improved_transparency_order=ito,
        fingerprint=fp,
    )


def test_classification_contract_covers_win_loss_mixed_and_incomparable():
    control = metric(fp="control")
    better = metric(nl=102, fp="better")
    worse = metric(nl=98, fp="worse")
    tradeoff = metric(nl=102, du=10, fp="tradeoff")

    assert classify_against_control(control, [better]) == "WIN"
    assert classify_against_control(control, [worse]) == "LOSS"
    assert classify_against_control(control, [better, worse]) == "MIXED"
    assert classify_against_control(control, [tradeoff]) == "INCOMPARABLE"


def test_aggregate_summary_is_order_independent_and_complete():
    labels = ["WIN", "LOSS", "WIN", "MIXED", "INCOMPARABLE"]
    assert summarize_classifications(labels) == {
        "WIN": 2,
        "LOSS": 1,
        "MIXED": 1,
        "INCOMPARABLE": 1,
    }
