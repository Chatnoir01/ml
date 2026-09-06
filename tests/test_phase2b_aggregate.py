"""RED-first aggregate statistics for Phase 2B; synthetic inputs only."""

from adversarial_sbox.phase2b_aggregate import exact_one_sided_sign_p, summarize_support


def test_exact_sign_test_for_eight_of_nine_wins_is_preregistered_significant():
    assert abs(exact_one_sided_sign_p(8, 1) - (10 / 512)) < 1e-15
    assert exact_one_sided_sign_p(9, 0) == 1 / 512


def test_zero_differences_are_excluded_from_sign_test_not_counted_as_wins():
    # 8 positive, 0 negative, 1 exact tie -> denominator n=8.
    assert exact_one_sided_sign_p(8, 0) == 1 / 256


def test_synthetic_supported_summary_requires_all_six_gates():
    c = [0.40] * 9
    o = [0.35] * 9
    s = [0.39] * 9
    result = summarize_support(
        control=c,
        oracle=o,
        shuffled=s,
        classical_non_degradation=True,
    )
    assert result["checks"]["o_wins_c_8_of_9"] is True
    assert result["checks"]["paired_sign_p_lt_005"] is True
    assert result["checks"]["mean_reduction_ge_002"] is True
    assert result["checks"]["o_wins_s_6_of_9"] is True
    assert result["checks"]["o_reduction_gt_s_reduction"] is True
    assert result["verdict"] == "phase2b_oracle_pressure_supported"


def test_classical_degradation_is_valid_but_not_supported():
    result = summarize_support(
        control=[0.40] * 9,
        oracle=[0.30] * 9,
        shuffled=[0.39] * 9,
        classical_non_degradation=False,
    )
    assert result["verdict"] == "phase2b_oracle_pressure_not_supported"
