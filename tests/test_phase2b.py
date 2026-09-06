"""RED-first scientific contract for Phase 2B first GA <- Oracle pressure."""

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase2b import (
    BLIND_DATASET_SEEDS,
    BLIND_MODEL_SEEDS,
    CLASSICAL_EVALUATIONS_PER_ARM,
    EVOLUTION_SEEDS,
    GA_CONFIG_KWARGS,
    NEURAL_TRAININGS_TOTAL,
    PANEL_DIGEST_SHA256,
    PRESSURE_DATASET_SEEDS,
    PRESSURE_MODEL_SEEDS,
    build_arm_rank,
    classify_phase2b,
    exact_paired_signflip_p,
    protected_classical_key,
)


def _metrics(*, nl: int, du: int, lat: int, degree: int, sac: float = 0.5) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=lat,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint="0" * 64,
    )


def test_phase2b_frozen_contract():
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert EVOLUTION_SEEDS == (290003, 290017, 290029, 290041, 290057)
    assert GA_CONFIG_KWARGS == {
        "population_size": 6,
        "generations": 5,
        "elite_count": 2,
        "tournament_size": 2,
        "mutation_swaps": 1,
        "crossover_rate": 0.0,
        "immigrant_fraction": 0.0,
        "offspring_multiplier": 1,
    }
    assert CLASSICAL_EVALUATIONS_PER_ARM == 26
    assert NEURAL_TRAININGS_TOTAL == 2320
    assert len(PRESSURE_DATASET_SEEDS) == len(PRESSURE_MODEL_SEEDS) == 8
    assert len(BLIND_DATASET_SEEDS) == len(BLIND_MODEL_SEEDS) == 8
    assert set(PRESSURE_DATASET_SEEDS + PRESSURE_MODEL_SEEDS).isdisjoint(
        BLIND_DATASET_SEEDS + BLIND_MODEL_SEEDS
    )


def test_neural_pressure_cannot_override_better_classical_key():
    constraints = HardConstraints()
    stronger = _metrics(nl=102, du=8, lat=56, degree=7)
    weaker = _metrics(nl=100, du=8, lat=56, degree=7)
    assert protected_classical_key(stronger, constraints) > protected_classical_key(
        weaker, constraints
    )
    assert build_arm_rank(stronger, constraints, arm="neural", pressure_value=-999.0) > build_arm_rank(
        weaker, constraints, arm="neural", pressure_value=999.0
    )


def test_lower_neural_advantage_wins_only_inside_exact_protected_tie():
    constraints = HardConstraints()
    left = _metrics(nl=100, du=8, lat=56, degree=7, sac=0.49)
    right = _metrics(nl=100, du=8, lat=56, degree=7, sac=0.51)
    assert protected_classical_key(left, constraints) == protected_classical_key(right, constraints)
    assert build_arm_rank(left, constraints, arm="neural", pressure_value=0.10) > build_arm_rank(
        right, constraints, arm="neural", pressure_value=0.30
    )


def test_exact_primary_classification_is_frozen():
    deltas = (0.04, 0.03, 0.02, 0.05, 0.01)
    p = exact_paired_signflip_p(deltas)
    assert p == 0.03125
    assert classify_phase2b(prerequisites_pass=True, paired_deltas=deltas) == "phase2b_neural_pressure_supported"
    weak = (0.01, 0.01, 0.01, 0.01, 0.01)
    assert classify_phase2b(prerequisites_pass=True, paired_deltas=weak) == "phase2b_neural_pressure_not_supported"
    assert classify_phase2b(prerequisites_pass=False, paired_deltas=deltas) == "phase2b_inconclusive_prerequisites"
