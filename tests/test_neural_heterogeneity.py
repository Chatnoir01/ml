import math

import pytest

from adversarial_sbox import neural_heterogeneity as nh
from adversarial_sbox.neural100 import _verify_candidate
from adversarial_sbox.neural100_candidates import CANDIDATES


def test_factorial_design_is_exactly_1200_trainings():
    assert nh.ROUND_COUNTS == (3, 4, 5)
    assert nh.INPUT_DIFFERENCES == (0x00000001, 0x00000100, 0x00010001, 0x01010101)
    assert nh.ARCHITECTURES == ("bit_relu_mlp", "byte_tanh_mlp")
    assert len(nh.REGIMES) == 12
    assert len(CANDIDATES) == 10
    assert nh.REPLICATES == 5
    assert len(CANDIDATES) * len(nh.REGIMES) * len(nh.ARCHITECTURES) * nh.REPLICATES == 1200


def test_fresh_seed_formula_is_deterministic_and_architecture_separated():
    assert nh.frozen_seeds(3, 0x00000001, "bit_relu_mlp", 0) == (510001, 610001)
    assert nh.frozen_seeds(3, 0x00000001, "byte_tanh_mlp", 0) == (510001, 710001)
    assert nh.frozen_seeds(5, 0x01010101, "bit_relu_mlp", 4) == (521059, 621051)
    assert nh.frozen_seeds(5, 0x01010101, "byte_tanh_mlp", 4) == (521059, 721051)
    with pytest.raises(ValueError):
        nh.frozen_seeds(2, 1, "bit_relu_mlp", 0)
    with pytest.raises(ValueError):
        nh.frozen_seeds(3, 1, "unknown", 0)


def test_all_ten_candidates_revalidate_to_frozen_classical_profile():
    for candidate_index in range(10):
        _, metrics = _verify_candidate(candidate_index)
        assert metrics["nonlinearity"] == 100
        assert metrics["differential_uniformity"] == 8
        assert metrics["max_linear_correlation"] == 56
        assert metrics["algebraic_degree"] == 7
        assert metrics["sac_score"] == 0.5


def test_spearman_handles_order_reversal_and_ties():
    assert nh.spearman_correlation([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert nh.spearman_correlation([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    tied = nh.spearman_correlation([1, 1, 2, 3], [4, 4, 5, 6])
    assert math.isfinite(tied)
    assert tied == pytest.approx(1.0)


def test_blocked_permutation_detects_large_stable_candidate_effect():
    blocks = []
    for replicate in range(12):
        blocks.append([0.01 * candidate + 0.0001 * replicate for candidate in range(10)])
    observed, p_value = nh.blocked_heterogeneity_p(blocks, repetitions=300, seed=1234)
    assert observed > 0.0
    assert p_value < 0.05


def _synthetic_cells():
    results = []
    for rounds, input_difference in nh.REGIMES:
        for architecture in nh.ARCHITECTURES:
            runs = []
            for candidate_index, candidate in enumerate(CANDIDATES):
                for replicate in range(nh.REPLICATES):
                    dataset_seed, model_seed = nh.frozen_seeds(
                        rounds, input_difference, architecture, replicate
                    )
                    # Stable candidate ordering under both architectures. The effect is
                    # deliberately strong so the small test-only permutation count is enough.
                    advantage = 0.045 + 0.004 * candidate_index + 0.0002 * replicate
                    null_advantage = 0.010 + 0.0001 * replicate
                    runs.append(
                        {
                            "candidate_index": candidate_index,
                            "fingerprint": candidate["fingerprint"],
                            "replicate": replicate,
                            "dataset_seed": dataset_seed,
                            "model_seed": model_seed,
                            "neural_advantage": advantage,
                            "null_advantage": null_advantage,
                        }
                    )
            results.append(
                {
                    "regime_index": nh.regime_index(rounds, input_difference),
                    "rounds": rounds,
                    "input_difference": input_difference,
                    "architecture": architecture,
                    "runs": runs,
                }
            )
    return results


def test_aggregate_requires_all_1200_and_can_emit_replicated_verdict(monkeypatch):
    monkeypatch.setattr(nh, "GLOBAL_PERMUTATIONS", 200)
    monkeypatch.setattr(nh, "ARCH_PERMUTATIONS", 200)
    aggregate = nh.aggregate_cell_results(_synthetic_cells())
    assert aggregate["summary"]["total_trainings"] == 1200
    assert aggregate["summary"]["diagnostic"] == "replicated_sbox_heterogeneity"
    assert aggregate["summary"]["global_gate1"] == "red"
    assert aggregate["summary"]["neural_oracle"] == "blocked"


def test_aggregate_rejects_missing_cell(monkeypatch):
    monkeypatch.setattr(nh, "GLOBAL_PERMUTATIONS", 10)
    monkeypatch.setattr(nh, "ARCH_PERMUTATIONS", 10)
    cells = _synthetic_cells()
    cells.pop()
    with pytest.raises(ValueError, match="24 cell"):
        nh.aggregate_cell_results(cells)
