from adversarial_sbox.benchmark import CI_SEEDS
from adversarial_sbox.confirm import (
    ALPHA,
    CONFIRMATION_SEEDS,
    FROZEN_CONFIGURATION,
    MIN_REPEATED_ADMISSIBLE_RUNS,
    exact_one_sided_sign_test,
)
from adversarial_sbox.tuning import DEV_SEEDS


def test_confirmation_seeds_are_fresh_and_unique():
    assert len(CONFIRMATION_SEEDS) == 12
    assert len(set(CONFIRMATION_SEEDS)) == len(CONFIRMATION_SEEDS)
    assert set(CONFIRMATION_SEEDS).isdisjoint(DEV_SEEDS)
    assert set(CONFIRMATION_SEEDS).isdisjoint(CI_SEEDS)


def test_frozen_configuration_matches_selected_development_strategy():
    assert FROZEN_CONFIGURATION == {
        "population_size": 10,
        "generations": 12,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 3,
        "crossover_rate": 0.0,
        "immigrant_fraction": 0.25,
    }
    assert ALPHA == 0.05
    assert MIN_REPEATED_ADMISSIBLE_RUNS == 3


def test_exact_one_sided_sign_test_known_values():
    assert exact_one_sided_sign_test(wins=0, losses=0) == 1.0
    assert exact_one_sided_sign_test(wins=12, losses=0) == 1 / 4096
    assert exact_one_sided_sign_test(wins=10, losses=2) == 79 / 4096
    assert exact_one_sided_sign_test(wins=9, losses=3) == 299 / 4096
    assert exact_one_sided_sign_test(wins=10, losses=2) < ALPHA
    assert exact_one_sided_sign_test(wins=9, losses=3) > ALPHA
