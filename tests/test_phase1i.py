import random

import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints, equivalent_random_budget
from adversarial_sbox.phase1e import cycle_mutation
from adversarial_sbox.phase1f import ga_config
from adversarial_sbox.phase1h import build_plateau_diagnostics
from adversarial_sbox.phase1i import (
    BRIDGE_CORR_CAP,
    BRIDGE_DU_CAP,
    CONFIGURATIONS,
    DISCOVERY_GENERATIONS,
    FULL_GA_GENERATIONS,
    LocalProposalScore,
    TOTAL_BUDGET,
    bridge_region,
    run_development,
    score_local_proposal,
)
from adversarial_sbox.references import AES_SBOX


def metrics(*, nl=98, du=10, corr=60, degree=7, sac=0.5):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=corr,
        sac_score=sac,
        algebraic_degree=degree,
        fingerprint="test",
    )


def test_frozen_batch_contains_exactly_ten_declared_configurations():
    assert list(CONFIGURATIONS) == [
        "c2_p96",
        "c3_p96",
        "c4_p32",
        "c4_p96",
        "c5_p96",
        "c6_p96",
        "c8_p96",
        "mix234_p96",
        "mix456_p96",
        "mix2468_p96",
    ]
    assert len(CONFIGURATIONS) == 10


def test_exact_matched_budget_formula():
    discovery = equivalent_random_budget(
        ga_config(seed=0, generations=DISCOVERY_GENERATIONS)
    )
    comparator = equivalent_random_budget(
        ga_config(seed=0, generations=FULL_GA_GENERATIONS)
    )
    assert discovery == 436
    assert TOTAL_BUDGET - discovery == 544
    assert comparator == TOTAL_BUDGET == 980


def test_bridge_region_is_broad_but_frozen():
    assert bridge_region(metrics(du=BRIDGE_DU_CAP, corr=BRIDGE_CORR_CAP, degree=6))
    assert not bridge_region(metrics(du=BRIDGE_DU_CAP + 2))
    assert not bridge_region(metrics(corr=BRIDGE_CORR_CAP + 4))
    assert not bridge_region(metrics(degree=5))


def test_dynamic_proposal_ranking_switches_priority_at_du_frontier():
    low_ddt = LocalProposalScore(58, 8, 1, 0, 100, 100, 0)
    low_lat = LocalProposalScore(56, 10, 1, 1, 100, 100, 1)
    # Above the DU frontier, DDT takes priority.
    assert low_ddt.ranking_key(parent_ddt_max=10) < low_lat.ranking_key(parent_ddt_max=10)
    # On the DU frontier, LAT takes priority.
    assert low_lat.ranking_key(parent_ddt_max=8) < low_ddt.ranking_key(parent_ddt_max=8)


def test_generalized_local_projection_accepts_cycle2_and_cycle8():
    parent = tuple(AES_SBOX)
    diagnostics = build_plateau_diagnostics(parent, panel_mode="ties")
    for cycle_length in (2, 8):
        child, _ = cycle_mutation(
            parent,
            random.Random(100 + cycle_length),
            cycle_length=cycle_length,
            anchor_indices=diagnostics.hotspot_indices,
        )
        score = score_local_proposal(parent, child, diagnostics, order=0)
        assert score.projected_lat_max >= 0
        assert score.projected_ddt_max >= 0


def test_confirmation_seed_is_rejected_before_any_run():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(configuration="c4_p96", seeds=(1801,))
