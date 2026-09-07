"""Terminal-freeze isolation and compatibility tests for Phase 2D."""

import hashlib
import json

from adversarial_sbox.phase2d import (
    ARCHITECTURE,
    ARMS,
    CLASSICAL_BUDGET_PER_ARM_SEED,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
)
from adversarial_sbox.phase2d_aggregate import freeze_terminals as aggregate_freeze_terminals
from adversarial_sbox.phase2d_terminal_freeze import freeze_terminals as isolated_freeze_terminals


def _sha(payload, field):
    clean = {key: value for key, value in payload.items() if key != field}
    blob = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _fitness_score(fingerprint: str):
    runs = []
    for difference in DIFFERENCES:
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(FITNESS_DATASET_SEEDS, FITNESS_MODEL_SEEDS)
        ):
            runs.append(
                {
                    "difference": int(difference),
                    "replicate": int(replicate),
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": SPLIT_SIZES[0],
                    "validation_size": SPLIT_SIZES[1],
                    "test_size": SPLIT_SIZES[2],
                    "neural_advantage": 0.125,
                    "null_advantage": 0.0,
                }
            )
    payload = {
        "schema_version": 1,
        "experiment": "phase2d_candidate_neural_score",
        "purpose": "fitness",
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "split_sizes": list(SPLIT_SIZES),
        "fingerprint": fingerprint,
        "training_count": ORACLE_TRAININGS_PER_SCORE,
        "neural_advantage": 0.125,
        "null_advantage": 0.0,
        "runs": runs,
    }
    payload["scientific_payload_sha256"] = _sha(payload, "scientific_payload_sha256")
    return payload


def _arm_results():
    score_payloads = {
        f"candidate-{index}": _fitness_score(f"candidate-{index}")
        for index in range(ORACLE_SCORE_BUDGET_PER_ARM_SEED)
    }
    receipts = [
        {
            "fingerprint": fingerprint,
            "neural_advantage": 0.125,
            "payload_sha256": payload["scientific_payload_sha256"],
            "training_count": ORACLE_TRAININGS_PER_SCORE,
            "role": "selection" if index < 8 else "padding",
            "score_payload": payload,
        }
        for index, (fingerprint, payload) in enumerate(score_payloads.items())
    ]
    results = []
    for seed in EVOLUTION_SEEDS:
        digest = f"initial-{seed}"
        for arm in ARMS:
            terminal_fp = f"terminal-{seed}-{arm}"
            run = {
                "schema_version": 1,
                "phase": "2D",
                "seed": int(seed),
                "arm": arm,
                "initial_population_digest_sha256": digest,
                "terminal_sbox": list(range(256)),
                "terminal_fingerprint": terminal_fp,
                "terminal_classical": {
                    "nonlinearity": 100,
                    "differential_uniformity": 8,
                    "max_linear_correlation": 56,
                    "sac_score": 0.5,
                    "algebraic_degree": 7,
                    "fingerprint": terminal_fp,
                },
                "classical_evaluations": CLASSICAL_BUDGET_PER_ARM_SEED,
                "oracle_candidate_scores": ORACLE_SCORE_BUDGET_PER_ARM_SEED,
                "oracle_fitness_trainings": FITNESS_TRAININGS_PER_ARM_SEED,
                "oracle_receipts": receipts,
            }
            run["scientific_payload_sha256"] = _sha(run, "scientific_payload_sha256")
            results.append(run)
    return results


def test_isolated_terminal_freeze_is_exactly_compatible_with_post_w_aggregate_freeze():
    arm_results = _arm_results()
    isolated = isolated_freeze_terminals(arm_results)
    aggregate = aggregate_freeze_terminals(arm_results)
    assert isolated == aggregate
    assert isolated["prerequisites"]["pass"] is True
    assert isolated["cell_count"] == 36
    assert len(isolated["terminals"]) == 36
    assert len(isolated["terminal_freeze_sha256"]) == 64
