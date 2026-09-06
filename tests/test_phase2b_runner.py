"""Synthetic runner contracts for Phase 2B; no neural model training is executed."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

from adversarial_sbox.phase2b import (
    ARM_NAMES,
    BLIND_DATASET_SEEDS,
    BLIND_MODEL_SEEDS,
    CLASSICAL_EVALUATIONS_PER_ARM,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    EXPECTED_TEST_SIZE,
    EXPECTED_TRAIN_SIZE,
    EXPECTED_VALIDATION_SIZE,
    GA_CONFIG_KWARGS,
    PAIR_COUNT,
    PRESSURE_DATASET_SEEDS,
    PRESSURE_MODEL_SEEDS,
    TRAININGS_PER_ORACLE_SCORE,
    neural_seed_blocks_disjoint,
)
from adversarial_sbox.phase2b_runner import (
    aggregate_seed_results,
    initial_population_digest,
    load_frozen_initial_panel,
    run_seed,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _receipt(payload: dict, field: str) -> str:
    stripped = {key: value for key, value in payload.items() if key != field}
    blob = json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _synthetic_scorer(sbox: tuple[int, ...], block: str) -> dict:
    if block == "pressure":
        dataset_seeds, model_seeds = PRESSURE_DATASET_SEEDS, PRESSURE_MODEL_SEEDS
        block_offset = 0.0
    elif block == "blind":
        dataset_seeds, model_seeds = BLIND_DATASET_SEEDS, BLIND_MODEL_SEEDS
        block_offset = 0.01
    else:
        raise ValueError(block)

    fingerprint = fingerprint_sbox(sbox)
    base = (int(fingerprint[:8], 16) % 1000) / 10000.0 + block_offset
    runs = []
    for difference in DIFFERENCES:
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(dataset_seeds, model_seeds, strict=True)
        ):
            runs.append(
                {
                    "input_difference": int(difference),
                    "replicate": replicate,
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": EXPECTED_TRAIN_SIZE,
                    "validation_size": EXPECTED_VALIDATION_SIZE,
                    "test_size": EXPECTED_TEST_SIZE,
                    "neural_advantage": base,
                    "null_advantage": 0.0,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2b_oracle_score",
        "block": block,
        "architecture": "byte_tanh_mlp",
        "depth": 4,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "fingerprint": fingerprint,
        "runs": runs,
        "training_count": len(runs),
        "mean_neural_advantage": base,
        "mean_null_advantage": 0.0,
    }
    payload["oracle_payload_sha256"] = _receipt(payload, "oracle_payload_sha256")
    return payload


def test_phase2b_initial_panel_and_seed_provenance_are_frozen():
    panel = load_frozen_initial_panel()
    assert len(panel) == 6
    assert len(set(panel)) == 6
    assert len(initial_population_digest()) == 64
    assert neural_seed_blocks_disjoint() is True


def test_phase2b_three_arm_runner_keeps_exact_matched_budget_with_synthetic_oracle():
    payload = run_seed(EVOLUTION_SEEDS[0], oracle_scorer=_synthetic_scorer)
    assert payload["ga_config"] == GA_CONFIG_KWARGS
    assert payload["same_initial_population_all_arms"] is True
    assert payload["same_ga_seed_all_arms"] is True
    assert payload["blind_scoring_after_all_evolution"] is True
    assert payload["oracle_adapts_from_ga_outcomes"] is False
    assert tuple(payload["arms"]) == ARM_NAMES
    for arm in ARM_NAMES:
        assert payload["arms"][arm]["classical_evaluations"] == CLASSICAL_EVALUATIONS_PER_ARM
        assert payload["arms"][arm]["classical_safety_invariant"] is True
        assert payload["arms"][arm]["blind_final_score"]["training_count"] == TRAININGS_PER_ORACLE_SCORE
    assert payload["arms"]["neural"]["pressure_oracle_candidate_count"] == 26
    assert payload["arms"]["control"]["pressure_oracle_candidate_count"] == 0
    assert payload["arms"]["sham"]["pressure_oracle_candidate_count"] == 0
    assert payload["pressure_neural_trainings"] == 416
    assert payload["blind_neural_trainings"] == 48
    assert payload["neural_trainings"] == 464


def test_phase2b_aggregate_requires_exact_five_declared_seed_receipts():
    first = run_seed(EVOLUTION_SEEDS[0], oracle_scorer=_synthetic_scorer)
    results = []
    for seed in EVOLUTION_SEEDS:
        item = deepcopy(first)
        item["seed"] = seed
        item["scientific_payload_sha256"] = _receipt(item, "scientific_payload_sha256")
        results.append(item)
    aggregate = aggregate_seed_results(results)
    assert aggregate["total_classical_evaluations"] == 390
    assert aggregate["pressure_neural_trainings"] == 2080
    assert aggregate["blind_neural_trainings"] == 240
    assert aggregate["total_neural_trainings"] == 2320
    assert aggregate["prerequisites_pass"] is True
    assert aggregate["verdict"] in {
        "phase2b_neural_pressure_supported",
        "phase2b_neural_pressure_not_supported",
    }
