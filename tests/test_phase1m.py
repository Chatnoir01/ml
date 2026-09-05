import random

import pytest

from adversarial_sbox.cryptoshield import is_bijective
from adversarial_sbox.evolution import ClassicalMetrics
from adversarial_sbox.experiment_seeds import (
    PHASE1M_CONFIRM_RESERVED_SEEDS,
    PHASE1M_DEV_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1l import CLASSICAL_BUDGET as PHASE1L_CLASSICAL_BUDGET
from adversarial_sbox.phase1l import POPULATION_SIZE as PHASE1L_POPULATION_SIZE
from adversarial_sbox.phase1m import (
    CLASSICAL_BUDGET,
    ITO_NONINFERIORITY_TOLERANCE,
    ClassicalEvaluationLedger,
    aggregate_development,
    du_hotspot_swap_proposals,
    run_seed,
)


def test_phase1m_seed_registry_is_frozen_and_disjoint():
    validate_seed_registry()
    assert PHASE1M_DEV_SEEDS == (2111, 2113, 2129, 2131, 2137)
    assert PHASE1M_CONFIRM_RESERVED_SEEDS == (
        2203,
        2207,
        2213,
        2221,
        2237,
        2239,
        2243,
        2251,
        2267,
    )


def test_phase1m_budget_and_ito_guard_are_frozen_without_mutating_phase1l_defaults():
    assert CLASSICAL_BUDGET == 340
    assert ITO_NONINFERIORITY_TOLERANCE == pytest.approx(0.02)
    assert PHASE1L_CLASSICAL_BUDGET == 340
    assert PHASE1L_POPULATION_SIZE == 20


def test_classical_ledger_counts_unique_full_evaluations_only_and_enforces_cap():
    calls = []

    def evaluator(sbox):
        frozen = tuple(sbox)
        calls.append(frozen)
        return ClassicalMetrics(
            nonlinearity=100,
            differential_uniformity=10,
            max_linear_correlation=60,
            sac_score=0.5,
            algebraic_degree=7,
            fingerprint=str(frozen[0]),
        )

    ledger = ClassicalEvaluationLedger(evaluator, budget=2)
    a = tuple(range(256))
    b = tuple(reversed(range(256)))
    c = a[1:] + a[:1]

    first = ledger.evaluate(a)
    again = ledger.evaluate(a)
    assert first is again
    assert ledger.evaluations == 1
    assert len(calls) == 1

    ledger.evaluate(b)
    assert ledger.evaluations == 2
    assert ledger.remaining == 0

    with pytest.raises(RuntimeError, match="budget exhausted"):
        ledger.evaluate(c)


def test_du_hotspot_proposals_are_bijective_deterministic_unique_and_auditable():
    sbox = tuple(range(256))

    left = du_hotspot_swap_proposals(sbox, random.Random(12345), count=6)
    right = du_hotspot_swap_proposals(sbox, random.Random(12345), count=6)

    assert left == right
    assert len(left) == 6
    assert len({proposal.sbox for proposal in left}) == 6

    for proposal in left:
        assert is_bijective(proposal.sbox)
        assert proposal.sbox != sbox
        assert 1 <= proposal.input_difference <= 255
        assert 0 <= proposal.output_difference <= 255
        assert proposal.hotspot_count >= 2
        assert proposal.anchor_a != proposal.anchor_b
        assert proposal.anchor_a in proposal.hotspot_positions
        assert proposal.anchor_b in range(256)


def test_du_hotspot_operator_rejects_non_bijective_input():
    with pytest.raises(ValueError, match="bijective"):
        du_hotspot_swap_proposals(tuple(0 for _ in range(256)), random.Random(1), count=2)


def _seed_payload(
    *,
    seed: int,
    best_du_a: int = 8,
    best_du_b: int = 10,
    du8_a: int = 1,
    du8_b: int = 0,
    protected_a: int = 2,
    protected_b: int = 1,
    min_ito_a: float = 6.84,
    min_ito_b: float = 6.85,
    digest: str = "same",
):
    return {
        "phase": "1M",
        "seed": seed,
        "initial_population_digest_sha256": digest,
        "arm_a": {
            "best_du": best_du_a,
            "du8_count": du8_a,
            "protected_classical_count": protected_a,
            "min_ito": min_ito_a,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_b": {
            "best_du": best_du_b,
            "du8_count": du8_b,
            "protected_classical_count": protected_b,
            "min_ito": min_ito_b,
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "arm_c": {
            "classical_evaluations": 340,
            "initial_population_digest_sha256": digest,
        },
        "deterministic_payload_match": True,
        "neural_oracle_executed": False,
    }


def test_phase1m_aggregate_requires_every_frozen_gate():
    passing = [_seed_payload(seed=seed) for seed in PHASE1M_DEV_SEEDS]
    result = aggregate_development(passing)
    assert result["verdict"] == "phase1m_dev_pass"
    assert all(result["development_checks"].values())

    ito_regression = [
        _seed_payload(seed=seed, min_ito_a=6.88, min_ito_b=6.85)
        for seed in PHASE1M_DEV_SEEDS
    ]
    result = aggregate_development(ito_regression)
    assert result["development_checks"]["ito_noninferiority"] is False
    assert result["verdict"] == "phase1m_dev_fail"

    hidden_budget = passing.copy()
    hidden_budget[0] = {
        **hidden_budget[0],
        "arm_a": {**hidden_budget[0]["arm_a"], "classical_evaluations": 341},
    }
    assert aggregate_development(hidden_budget)["verdict"] == "phase1m_dev_fail"


def test_phase1m_run_rejects_unregistered_seed_before_work():
    with pytest.raises(ValueError, match="Phase 1M development seed"):
        run_seed(99991)
