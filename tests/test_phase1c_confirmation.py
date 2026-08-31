from adversarial_sbox.phase1c_confirmation import (
    evaluate_preregistered_gates,
    exact_one_sided_sign_test,
)


def _evidence(**overrides):
    summary = {
        "ga_wins": 8,
        "random_wins": 1,
        "ties": 0,
        "median_max_structural_violation_ga": 0.02,
        "median_max_structural_violation_random": 0.25,
        "median_total_structural_violation_ga": 0.02,
        "median_total_structural_violation_random": 0.27,
        "median_nonlinearity_ga": 100.0,
        "median_nonlinearity_random": 98.0,
        "median_differential_uniformity_ga": 8.0,
        "median_differential_uniformity_random": 10.0,
        "median_max_linear_correlation_ga": 60.0,
        "median_max_linear_correlation_random": 60.0,
        "admissible_ga": 2,
        "admissible_random": 0,
        "dual_nl_du_gate_ga": 3,
        "dual_nl_du_gate_random": 0,
    }
    summary.update(overrides)
    return {"summary": summary}


def test_sign_test_exact_values():
    assert exact_one_sided_sign_test(wins=0, losses=0) == 1.0
    assert exact_one_sided_sign_test(wins=8, losses=1) == 10 / 512
    assert exact_one_sided_sign_test(wins=9, losses=0) == 1 / 512


def test_full_gate_requires_balanced_superiority_and_repeated_admissibility():
    gates = evaluate_preregistered_gates(_evidence())
    assert gates["gate1a_balanced_search_superiority"]
    assert gates["gate1b_repeated_admissibility"]
    assert gates["gate1_full_pass"]


def test_significant_wins_without_violation_improvement_fail_gate1a():
    gates = evaluate_preregistered_gates(
        _evidence(
            median_max_structural_violation_ga=0.25,
            median_total_structural_violation_ga=0.27,
        )
    )
    assert not gates["gate1a_balanced_search_superiority"]
    assert not gates["gate1_full_pass"]


def test_search_superiority_without_admissibility_keeps_full_gate_red():
    gates = evaluate_preregistered_gates(_evidence(admissible_ga=0))
    assert gates["gate1a_balanced_search_superiority"]
    assert not gates["gate1b_repeated_admissibility"]
    assert not gates["gate1_full_pass"]
