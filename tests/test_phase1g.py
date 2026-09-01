import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.experiment_seeds import (
    PHASE1G_CONFIRM_RESERVED_SEEDS,
    PHASE1G_DEV_SEEDS,
)
from adversarial_sbox.phase1g import (
    annealed_escape_search,
    escape_score,
    excursion_eligible,
    run_development,
    structural_target,
)
from adversarial_sbox.references import AES_SBOX


def _metrics(*, nl=98, du=8, corr=60, degree=7, sac=0.5):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint="test",
    )


def test_phase1g_seed_sets_are_disjoint():
    assert set(PHASE1G_DEV_SEEDS).isdisjoint(PHASE1G_CONFIRM_RESERVED_SEEDS)


def test_escape_score_penalizes_temporary_structural_violations():
    baseline = _metrics(nl=98, du=8, corr=60)
    du_excursion = _metrics(nl=100, du=10, corr=60)
    corr_excursion = _metrics(nl=100, du=8, corr=72)
    assert escape_score(baseline) == 98.0
    assert escape_score(du_excursion) == 96.0
    assert escape_score(corr_excursion) == 98.0


def test_excursion_caps_and_degree_are_hard():
    constraints = HardConstraints()
    assert excursion_eligible(
        _metrics(du=12, corr=72, degree=6),
        du_cap=12,
        corr_cap=72,
        constraints=constraints,
    )
    assert not excursion_eligible(
        _metrics(du=14, corr=72, degree=6),
        du_cap=12,
        corr_cap=72,
        constraints=constraints,
    )
    assert not excursion_eligible(
        _metrics(du=12, corr=72, degree=5),
        du_cap=12,
        corr_cap=72,
        constraints=constraints,
    )


def test_structural_target_excludes_sac_but_requires_primary_gates():
    constraints = HardConstraints()
    assert structural_target(_metrics(nl=100, du=8, corr=64, degree=6, sac=0.9), constraints)
    assert not structural_target(_metrics(nl=98, du=8, corr=64, degree=6), constraints)


def test_annealed_search_charges_exact_full_evaluation_budget():
    result = annealed_escape_search(
        AES_SBOX,
        seed=17,
        evaluations=2,
        du_cap=12,
        corr_cap=72,
        t_start=1.5,
        t_end=0.05,
        reset_after=2,
    )
    assert result["evaluations"] == 2
    assert len(result["best_sbox"]) == 256


def test_confirmation_seed_is_rejected_before_warm_start_reproduction():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(
            du_cap=12,
            corr_cap=72,
            t_start=1.5,
            t_end=0.05,
            reset_after=32,
            seeds=(PHASE1G_CONFIRM_RESERVED_SEEDS[0],),
            evaluations=1,
        )
