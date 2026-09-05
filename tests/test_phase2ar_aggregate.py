"""Pure synthetic aggregation tests for Phase 2A-R; no neural training."""

import hashlib

import adversarial_sbox.phase2ar_runner as runner
from adversarial_sbox.phase2ar import DATASET_SEEDS, MODEL_SEEDS, REGIMES


def _cell(regime, architecture, rounds, difference, scores):
    panel = runner.load_frozen_panel()
    runs = []
    for candidate_index, candidate in enumerate(panel):
        for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "source_seed": candidate["source_seed"],
                    "fingerprint": candidate["fingerprint"],
                    "replicate": replicate,
                    "dataset_seed": dataset_seed,
                    "model_seed": model_seed,
                    "neural_advantage": float(scores[candidate_index]),
                    "null_advantage": 0.01,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2ar_rank_instability_cell",
        "regime": regime,
        "architecture": architecture,
        "rounds": rounds,
        "input_difference": difference,
        "pair_count": 1,
        "panel_digest_sha256": runner.PANEL_DIGEST_SHA256,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        runner._canonical_without_receipt(payload)
    ).hexdigest()
    return payload


def _results(score_map):
    items = []
    for regime, architecture, rounds, differences in REGIMES:
        for difference in differences:
            items.append(_cell(regime, architecture, rounds, difference, score_map[regime]))
    return items


def test_phase2ar_aggregate_reports_stable_adjacent_ranks(monkeypatch):
    monkeypatch.setattr(runner, "PERMUTATION_REPETITIONS", 200)
    stable = [0.05, 0.08, 0.11, 0.14, 0.17, 0.20]
    result = runner.aggregate_cells(_results({name: stable for name in "ABCD"}))
    assert result["total_trainings"] == 240
    assert result["training_count_exact"] is True
    assert result["all_signal_prerequisites_pass"] is True
    assert result["adjacent_spearman"] == {"rho_AB": 1.0, "rho_BC": 1.0, "rho_CD": 1.0}
    assert result["verdict"] == "phase2ar_no_adjacent_instability"
    assert result["neural_evolutionary_pressure"] is False


def test_phase2ar_aggregate_localizes_difference_transition(monkeypatch):
    monkeypatch.setattr(runner, "PERMUTATION_REPETITIONS", 200)
    stable = [0.05, 0.08, 0.11, 0.14, 0.17, 0.20]
    reversed_scores = list(reversed(stable))
    result = runner.aggregate_cells(
        _results({"A": stable, "B": stable, "C": stable, "D": reversed_scores})
    )
    assert result["all_signal_prerequisites_pass"] is True
    assert result["adjacent_spearman"]["rho_AB"] == 1.0
    assert result["adjacent_spearman"]["rho_BC"] == 1.0
    assert result["adjacent_spearman"]["rho_CD"] == -1.0
    assert result["verdict"] == "phase2ar_difference_transition_localized"
