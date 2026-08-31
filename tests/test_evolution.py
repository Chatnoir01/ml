import random

import pytest

from adversarial_sbox.cryptoshield import is_bijective
from adversarial_sbox.evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    classical_rank,
    constraint_violation,
    equivalent_random_budget,
    evaluate_classical,
    evolve_permutations,
    feasibility_rank,
    is_admissible,
    make_classical_evaluator,
    ordered_crossover,
    primary_security_key,
    random_search,
    random_sbox,
    structural_gate_count,
    swap_mutation,
)
from adversarial_sbox.references import AES_SBOX


def _fixed_points_rank(sbox):
    return (float(sum(index == value for index, value in enumerate(sbox))),)


def test_random_mutation_and_crossover_preserve_bijection():
    rng = random.Random(1234)
    parent_a = random_sbox(rng)
    parent_b = random_sbox(rng)
    mutated = swap_mutation(parent_a, rng, swaps=7)
    child = ordered_crossover(parent_a, parent_b, rng)

    assert is_bijective(parent_a)
    assert is_bijective(parent_b)
    assert is_bijective(mutated)
    assert is_bijective(child)
    assert len(set(child)) == 256


def test_aes_passes_default_classical_constraints():
    metrics = evaluate_classical(AES_SBOX)
    constraints = HardConstraints()

    assert metrics.nonlinearity == 112
    assert metrics.differential_uniformity == 4
    assert metrics.max_linear_correlation == 32
    assert metrics.algebraic_degree == 7
    assert is_admissible(metrics, constraints)
    assert structural_gate_count(metrics, constraints) == 4
    assert constraint_violation(metrics, constraints) == 0.0
    assert classical_rank(metrics, constraints)[0] == 1.0
    assert feasibility_rank(metrics, constraints)[0] == 1.0


def test_identity_fails_default_classical_constraints():
    identity = tuple(range(256))
    metrics = evaluate_classical(identity)
    assert not is_admissible(metrics, HardConstraints())
    assert constraint_violation(metrics, HardConstraints()) > 0.0
    assert classical_rank(metrics, HardConstraints())[0] == 0.0


def test_historical_constraint_distance_rank_is_retained():
    constraints = HardConstraints()
    near = ClassicalMetrics(96, 8, 64, 0.5, 7, "near")
    misleading_high_nl = ClassicalMetrics(99, 16, 64, 0.5, 7, "far")

    assert constraint_violation(near, constraints) < constraint_violation(
        misleading_high_nl, constraints
    )
    assert classical_rank(near, constraints) > classical_rank(
        misleading_high_nl, constraints
    )


def test_feasibility_rank_rewards_more_structural_gates_before_nl():
    constraints = HardConstraints()
    high_nl_two_gates = ClassicalMetrics(98, 10, 60, 0.5, 7, "high-nl")
    lower_nl_three_gates = ClassicalMetrics(94, 8, 64, 0.5, 7, "three-gates")

    assert structural_gate_count(high_nl_two_gates, constraints) == 2
    assert structural_gate_count(lower_nl_three_gates, constraints) == 3
    assert feasibility_rank(lower_nl_three_gates, constraints) > feasibility_rank(
        high_nl_two_gates, constraints
    )


def test_primary_security_key_cannot_be_won_by_sac_only():
    constraints = HardConstraints()
    first = ClassicalMetrics(98, 10, 60, 0.5001, 7, "a")
    second = ClassicalMetrics(98, 10, 60, 0.5123, 7, "b")
    assert primary_security_key(first, constraints) == primary_security_key(
        second, constraints
    )


def test_make_evaluator_requires_known_versioned_ranking_mode():
    with pytest.raises(ValueError):
        make_classical_evaluator(HardConstraints(), ranking_mode="future-magic")


def test_historical_ga_budget_and_flow_remain_deterministic_with_defaults():
    identity = tuple(range(256))
    config = EvolutionConfig(
        population_size=8,
        generations=4,
        elite_count=2,
        tournament_size=3,
        mutation_swaps=2,
        crossover_rate=0.8,
        immigrant_fraction=0.25,
        seed=77,
    )

    first = evolve_permutations(
        _fixed_points_rank, config, initial_population=(identity,)
    )
    second = evolve_permutations(
        _fixed_points_rank, config, initial_population=(identity,)
    )

    assert first == second
    assert first.best_sbox == identity
    assert first.best_rank == (256.0,)
    assert first.evaluations == equivalent_random_budget(config) == 32


def test_oversampling_and_immigrants_are_fully_charged_to_budget():
    config = EvolutionConfig(
        population_size=8,
        generations=4,
        elite_count=2,
        tournament_size=3,
        mutation_swaps=3,
        crossover_rate=0.0,
        immigrant_fraction=0.25,
        offspring_multiplier=3,
        seed=91,
    )
    result = evolve_permutations(_fixed_points_rank, config)
    assert equivalent_random_budget(config) == 80
    assert result.evaluations == 80
    assert is_bijective(result.best_sbox)


def test_config_rejects_invalid_offspring_multiplier():
    with pytest.raises(ValueError):
        EvolutionConfig(offspring_multiplier=0)


def test_random_search_matches_requested_unique_budget_and_is_deterministic():
    first = random_search(_fixed_points_rank, evaluations=25, seed=88)
    second = random_search(_fixed_points_rank, evaluations=25, seed=88)

    assert first == second
    assert first.evaluations == 25
    assert is_bijective(first.best_sbox)
    assert len(first.best_rank_history) == 25
