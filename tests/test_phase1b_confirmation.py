from adversarial_sbox.phase1b_confirmation import (
    evaluate_preregistered_gates,
    exact_one_sided_sign_test,
)


def _evidence(**summary_overrides):
    summary = {
        "primary_ga_wins": 8,
        "primary_random_wins": 1,
        "primary_ties": 0,
        "median_constraint_violation_ga": 0.20,
        "median_constraint_violation_random": 0.29,
        "median_nonlinearity_ga": 100.0,
        "median_nonlinearity_random": 96.0,
        "median_differential_uniformity_ga": 8.0,
        "median_differential_uniformity_random": 10.0,
        "median_max_linear_correlation_ga": 60.0,
        "median_max_linear_correlation_random": 64.0,
        "admissible_ga": 2,
        "admissible_random": 0,
    }
    summary.update(summary_overrides)
    return {"summary": summary}


def test_sign_test_exact_values():
    assert exact_one_sided_sign_test(wins=0, losses=0) == 1.0
    assert exact_one_sided_sign_test(wins=8, losses=1) == 10 / 512
    assert exact_one_sided_sign_test(wins=9, losses=0) == 1 / 512


def test_full_gate_pass_requires_search_superiority_and_repeated_admissibility():
    gates = evaluate_preregistered_gates(_evidence())
    assert gates["gate1a_primary_search_superiority"]
    assert gates["gate1b_repeated_admissibility"]
    assert gates["gate1_full_pass"]


def test_significance_without_admissibility_keeps_full_gate_red():
    gates = evaluate_preregistered_gates(_evidence(admissible_ga=0))
    assert gates["gate1a_primary_search_superiority"]
    assert not gates["gate1b_repeated_admissibility"]
    assert not gates["gate1_full_pass"]


def test_admissibility_without_structural_superiority_keeps_full_gate_red():
    gates = evaluate_preregistered_gates(
        _evidence(
            median_constraint_violation_ga=0.29,
            median_nonlinearity_ga=96.0,
            median_differential_uniformity_ga=10.0,
            median_max_linear_correlation_ga=64.0,
        )
    )
    assert not gates["gate1a_primary_search_superiority"]
    assert gates["gate1b_repeated_admissibility"]
    assert not gates["gate1_full_pass"]
