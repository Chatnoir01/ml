import random

from adversarial_sbox.cryptoshield import is_bijective
from adversarial_sbox.evolution import (
    EvolutionConfig,
    HardConstraints,
    classical_rank,
    equivalent_random_budget,
    evaluate_classical,
    evolve_permutations,
    is_admissible,
    ordered_crossover,
    random_search,
    random_sbox,
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
    assert classical_rank(metrics, constraints)[0] == 1.0


def test_identity_fails_default_classical_constraints():
    identity = tuple(range(256))
    metrics = evaluate_classical(identity)
    assert not is_admissible(metrics, HardConstraints())
    assert classical_rank(metrics, HardConstraints())[0] == 0.0


def test_ga_is_deterministic_elitist_and_uses_exact_unique_budget():
    identity = tuple(range(256))
    config = EvolutionConfig(
        population_size=8,
        generations=4,
        elite_count=2,
        tournament_size=3,
        mutation_swaps=2,
        crossover_rate=0.8,
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
    assert first.evaluations == equivalent_random_budget(config)
    assert first.evaluations == 32
    assert all(
        later >= earlier
        for earlier, later in zip(first.best_rank_history, first.best_rank_history[1:])
    )


def test_random_search_matches_requested_unique_budget_and_is_deterministic():
    first = random_search(_fixed_points_rank, evaluations=25, seed=88)
    second = random_search(_fixed_points_rank, evaluations=25, seed=88)

    assert first == second
    assert first.evaluations == 25
    assert is_bijective(first.best_sbox)
    assert len(first.best_rank_history) == 25
