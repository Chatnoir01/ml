from adversarial_sbox.neural100 import (
    _advantage,
    _auc_from_scores,
    _verify_candidate,
    aggregate_candidate_results,
)
from adversarial_sbox.neural100_candidates import CANDIDATES, DATASET_SEEDS, MODEL_SEEDS


def test_frozen_panel_and_seed_registry_shape():
    assert len(CANDIDATES) == 10
    fingerprints = [candidate["fingerprint"] for candidate in CANDIDATES]
    assert fingerprints == sorted(fingerprints)
    assert len(set(fingerprints)) == 10
    assert all(len(candidate["sbox"]) == 256 for candidate in CANDIDATES)
    assert len(DATASET_SEEDS) == len(set(DATASET_SEEDS)) == 10
    assert len(MODEL_SEEDS) == len(set(MODEL_SEEDS)) == 10
    assert set(DATASET_SEEDS).isdisjoint(MODEL_SEEDS)


def test_panel_endpoints_reproduce_frozen_classical_metrics():
    for candidate_index in (0, 9):
        _sbox, metrics = _verify_candidate(candidate_index)
        assert metrics["nonlinearity"] == 100
        assert metrics["differential_uniformity"] == 8
        assert metrics["max_linear_correlation"] == 56
        assert metrics["algebraic_degree"] == 7
        assert metrics["sac_score"] == 0.5
        assert metrics["fingerprint"] == CANDIDATES[candidate_index]["fingerprint"]


def test_auc_is_tie_aware_and_advantage_is_symmetric():
    labels = [0, 0, 1, 1]
    assert _auc_from_scores(labels, [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert _auc_from_scores(labels, [0.9, 0.8, 0.2, 0.1]) == 0.0
    assert _auc_from_scores(labels, [0.5, 0.5, 0.5, 0.5]) == 0.5
    assert _advantage(0.6) == _advantage(0.4)
    assert _advantage(0.5) == 0.0


def _synthetic_candidate(candidate_index: int, advantage: float, null_advantage: float):
    auc = 0.5 + advantage / 2.0
    null_auc = 0.5 + null_advantage / 2.0
    return {
        "candidate_index": candidate_index,
        "fingerprint": CANDIDATES[candidate_index]["fingerprint"],
        "runs": [
            {
                "replicate": replicate,
                "dataset_seed": DATASET_SEEDS[replicate],
                "model_seed": MODEL_SEEDS[replicate],
                "test_auc": auc,
                "neural_advantage": advantage,
                "null_auc": null_auc,
                "null_advantage": null_advantage,
            }
            for replicate in range(10)
        ],
    }


def test_aggregate_counts_exactly_100_trainings():
    results = [
        _synthetic_candidate(index, 0.01 + index * 0.001, 0.01)
        for index in range(10)
    ]
    aggregate = aggregate_candidate_results(results)
    assert aggregate["summary"]["total_trainings"] == 100
    assert aggregate["summary"]["candidate_count"] == 10
    assert aggregate["summary"]["replicates_per_candidate"] == 10
    assert aggregate["summary"]["global_gate1"] == "red"
    assert aggregate["summary"]["neural_oracle"] == "blocked"
