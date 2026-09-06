"""Red-first contract for Phase 2A-U 4-round Neural Oracle qualification."""

from adversarial_sbox.phase2au import (
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
    PERMUTATION_SEEDS,
    SPEARMAN_MIN,
    TOP2_OVERLAP_MIN,
    TOTAL_TRAININGS,
    qualification_verdict,
)


def test_phase2au_frozen_contract():
    assert ARCHITECTURE == "byte_tanh_mlp"
    assert DEPTH == 4
    assert DIFFERENCES == (0x00000001, 0x00000100)
    assert PANEL_DIGEST_SHA256 == "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
    assert BLOCK_A_DATASET_SEEDS == (74003, 74017, 74027, 74047, 74059, 74071, 74093, 74101)
    assert BLOCK_A_MODEL_SEEDS == (84011, 84017, 84029, 84043, 84061, 84067, 84089, 84103)
    assert BLOCK_B_DATASET_SEEDS == (75011, 75017, 75029, 75041, 75061, 75083, 75109, 75121)
    assert BLOCK_B_MODEL_SEEDS == (85009, 85021, 85027, 85049, 85061, 85081, 85093, 85109)
    assert PERMUTATION_SEEDS == {"A": 94007, "B": 94009}
    assert PAIRED_REPLICATES == 8
    assert PERMUTATION_REPETITIONS == 10_000
    assert TOTAL_TRAININGS == 192
    assert HETEROGENEITY_P_MAX == 0.05
    assert MIN_SCORE_RANGE == 0.05
    assert SPEARMAN_MIN == 0.80
    assert TOP2_OVERLAP_MIN == 1
    assert MAD_MAX == 0.05


def test_phase2au_qualification_rule_is_frozen():
    passed = {
        "block_a_heterogeneity": True,
        "block_b_heterogeneity": True,
        "block_a_range": True,
        "block_b_range": True,
        "rank_replication": True,
        "top2_overlap": True,
        "cross_block_mad": True,
    }
    assert qualification_verdict(True, passed) == "phase2au_oracle_qualified"
    failed = dict(passed)
    failed["rank_replication"] = False
    assert qualification_verdict(True, failed) == "phase2au_oracle_not_qualified"
    assert qualification_verdict(False, passed) == "phase2au_inconclusive_prerequisites"
