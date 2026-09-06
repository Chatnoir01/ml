"""Frozen contract and provenance tests for Phase 2A-U2."""

from adversarial_sbox.phase2_neural_seed_registry import (
    overlap_with_prior,
    prior_seed_registry_before_phase2au,
    prior_seed_registry_before_phase2au2,
)
from adversarial_sbox.phase2au import fresh_seed_registry as historical_u_seed_registry
from adversarial_sbox.phase2au2 import (
    ARCHITECTURE,
    BLOCK_A_DATASET_SEEDS,
    BLOCK_A_MODEL_SEEDS,
    BLOCK_B_DATASET_SEEDS,
    BLOCK_B_MODEL_SEEDS,
    DEPTH,
    DIFFERENCES,
    HETEROGENEITY_P_MAX,
    MAD_MAX,
    MIN_SCORE_RANGE,
    PANEL_DIGEST_SHA256,
    PAIRED_REPLICATES,
    PERMUTATION_REPETITIONS,
    SPEARMAN_MIN,
    TOP2_OVERLAP_MIN,
    TOTAL_TRAININGS,
    fresh_seed_registry,
    fresh_seeds_disjoint_from_prior,
    qualification_verdict,
)


def test_historical_phase2au_overlap_is_visible_in_complete_registry():
    overlap = set(historical_u_seed_registry()) & set(prior_seed_registry_before_phase2au())
    assert overlap == {
        74003,
        74017,
        74027,
        74047,
        74071,
        74093,
        74101,
        84011,
        84017,
        84029,
        84061,
        84067,
        84089,
    }


def test_phase2au2_frozen_contract_and_freshness():
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTH == 4
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert PAIRED_REPLICATES == 8
    assert PERMUTATION_REPETITIONS == 10_000
    assert TOTAL_TRAININGS == 192
    assert HETEROGENEITY_P_MAX == 0.05
    assert MIN_SCORE_RANGE == 0.05
    assert SPEARMAN_MIN == 0.80
    assert TOP2_OVERLAP_MIN == 1
    assert MAD_MAX == 0.05

    assert len(fresh_seed_registry()) == 32
    assert fresh_seeds_disjoint_from_prior() is True
    assert set(fresh_seed_registry()).isdisjoint(prior_seed_registry_before_phase2au2())

    all_dataset = (*BLOCK_A_DATASET_SEEDS, *BLOCK_B_DATASET_SEEDS)
    all_model = (*BLOCK_A_MODEL_SEEDS, *BLOCK_B_MODEL_SEEDS)
    assert overlap_with_prior(all_dataset, all_model, before="phase2au2") == ()


def test_phase2au2_qualification_rule_is_frozen():
    passed = {
        "block_a_heterogeneity": True,
        "block_b_heterogeneity": True,
        "block_a_range": True,
        "block_b_range": True,
        "rank_replication": True,
        "top2_overlap": True,
        "cross_block_mad": True,
    }
    assert qualification_verdict(True, passed) == "phase2au2_oracle_qualified"
    failed = dict(passed)
    failed["rank_replication"] = False
    assert qualification_verdict(True, failed) == "phase2au2_oracle_not_qualified"
    assert qualification_verdict(False, passed) == "phase2au2_inconclusive_prerequisites"
