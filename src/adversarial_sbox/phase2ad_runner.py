"""Scientific runner for Phase 2A-D neural depth attenuation.

Phase 2A-D is diagnostic/confirmatory only. Neural scores never influence any
search or evolutionary component.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2a_neural import blocked_heterogeneity_p
from .phase2ad import (
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    HETEROGENEITY_PERMUTATION_SEEDS,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PANEL_SIZE,
    PERMUTATION_REPETITIONS,
    PRIMARY_PERMUTATION_SEED,
    REPLICATES,
    SECONDARY_PERMUTATION_SEED,
    TOTAL_TRAININGS,
    TRAININGS_PER_CELL,
    TRAININGS_PER_DEPTH,
    between_candidate_variance,
    classify_depth_attenuation,
    paired_dispersion_attenuation_p,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

_REQUIRED_BASELINE_KEYS = (
    "training_count_exact",
    "panel_revalidated",
    "deterministic_receipts",
    "seed_registry_exact",
    "neural_evolutionary_pressure_absent",
    "r4_heterogeneity",
    "r4_range",
    "r4_signal",
)


def load_frozen_panel() -> tuple[dict[str, Any], ...]:
    from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256 as COMMITTED_DIGEST

    if COMMITTED_DIGEST != PANEL_DIGEST_SHA256:
        raise RuntimeError("Phase 2A-D panel digest drift")
    if len(CANDIDATES) != PANEL_SIZE:
        raise RuntimeError("Phase 2A-D panel size drift")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_frozen_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-D candidate index out of range")
    candidate = panel[int(candidate_index)]
    sbox = tuple(int(value) for value in candidate["sbox"])
    metrics = evaluate_classical(sbox)
    checks = {
        "fingerprint": fingerprint_sbox(sbox) == str(candidate["fingerprint"]),
        "differential_uniformity": metrics.differential_uniformity == 8,
        "nonlinearity": metrics.nonlinearity == 100,
        "max_linear_correlation": metrics.max_linear_correlation == 56,
        "algebraic_degree": metrics.algebraic_degree == 7,
        "sac": abs(float(metrics.sac_score) - 0.5) <= 0.05,
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Phase 2A-D candidate {candidate_index} failed classical revalidation: {checks}"
        )
    return sbox, {
        "source_seed": int(candidate["source_seed"]),
        "fingerprint": str(candidate["fingerprint"]),
        "differential_uniformity": metrics.differential_uniformity,
        "nonlinearity": metrics.nonlinearity,
        "max_linear_correlation": metrics.max_linear_correlation,
        "algebraic_degree": metrics.algebraic_degree,
        "sac_score": metrics.sac_score,
    }


def expected_cell_keys() -> set[tuple[int, str, int]]:
    return {
        (int(depth), ARCHITECTURE, int(difference))
        for depth in DEPTHS
        for difference in DIFFERENCES
    }


def _cell_spec(depth: int, input_difference: int) -> tuple[int, str, int]:
    frozen_depth = int(depth)
    difference = int(input_difference)
    if frozen_depth not in DEPTHS:
        raise ValueError(f"undeclared Phase 2A-D depth {depth!r}")
    if difference not in DIFFERENCES:
        raise ValueError(f"undeclared Phase 2A-D difference {input_difference!r}")
    return frozen_depth, ARCHITECTURE, difference


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_cell(depth: int, input_difference: int) -> dict[str, Any]:
    """Run one frozen 60-training Phase-2A-D depth/difference cell."""

    depth, architecture, input_difference = _cell_spec(depth, input_difference)
    keys = ROUND_KEYS[: depth + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(PANEL_SIZE):
        sbox, classical = _verify_candidate(candidate_index)
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != depth:
            raise RuntimeError(f"expected {depth} ToySPN rounds, got {cipher.rounds}")
        for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=input_difference,
                seed=int(dataset_seed),
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            endpoint = _train_byte_tanh_mlp(
                train_samples=train_samples,
                validation_samples=validation_samples,
                test_samples=test_samples,
                model_seed=int(model_seed),
            )
            runs.append(
                {
                    "candidate_index": candidate_index,
                    "source_seed": classical["source_seed"],
                    "fingerprint": classical["fingerprint"],
                    "replicate": replicate,
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": len(train_samples),
                    "validation_size": len(validation_samples),
                    "test_size": len(test_samples),
                    **endpoint,
                }
            )

    if len(runs) != TRAININGS_PER_CELL:
        raise RuntimeError("Phase 2A-D cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ad_depth_attenuation_cell",
        "depth": depth,
        "architecture": architecture,
        "input_difference": input_difference,
        "pair_count": PAIR_COUNT,
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload


def baseline_r4_requirements_pass(checks: dict[str, bool]) -> bool:
    return all(bool(checks.get(key, False)) for key in _REQUIRED_BASELINE_KEYS)


def _candidate_means(blocks: Sequence[Sequence[float]]) -> list[float]:
    if not blocks or any(len(block) != PANEL_SIZE for block in blocks):
        raise ValueError("Phase 2A-D blocks must be non-empty and panel-width")
    return [
        float(sum(float(block[index]) for block in blocks) / len(blocks))
        for index in range(PANEL_SIZE)
    ]


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all six frozen cells and apply the preregistered attenuation test."""

    if len(results) != len(expected_cell_keys()):
        raise ValueError("Phase 2A-D aggregation requires exactly six cell results")

    panel = load_frozen_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    source_seeds = tuple(int(candidate["source_seed"]) for candidate in panel)

    cells: dict[tuple[int, str, int], dict[str, Any]] = {}
    deterministic_receipts = True
    total_trainings = 0
    depth_training_counts = {depth: 0 for depth in DEPTHS}
    blocks: dict[tuple[int, int, int], list[float | None]] = {}
    null_blocks: dict[tuple[int, int, int], list[float | None]] = {}

    for item in results:
        key = (
            int(item["depth"]),
            str(item["architecture"]),
            int(item["input_difference"]),
        )
        if key in cells:
            raise ValueError(f"duplicate Phase 2A-D cell {key!r}")
        if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
            raise ValueError("Phase 2A-D cell panel digest mismatch")
        expected_receipt = hashlib.sha256(_canonical_without_receipt(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        if bool(item.get("neural_evolutionary_pressure", True)):
            raise ValueError("Phase 2A-D forbids neural evolutionary pressure")
        cells[key] = item

    if set(cells) != expected_cell_keys():
        raise ValueError("Phase 2A-D cell set does not match the frozen design")

    seed_registry_exact = True
    for key in sorted(cells):
        depth, _architecture, input_difference = key
        item = cells[key]
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-D cell must contain exactly 60 trainings")
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < PANEL_SIZE or not 0 <= replicate < REPLICATES:
                raise ValueError("Phase 2A-D candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-D candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-D training fingerprint mismatch")
            if int(run["source_seed"]) != source_seeds[candidate_index]:
                raise ValueError("Phase 2A-D source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                seed_registry_exact = False
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                seed_registry_exact = False
            block_key = (depth, input_difference, replicate)
            block = blocks.setdefault(block_key, [None] * PANEL_SIZE)
            null_block = null_blocks.setdefault(block_key, [None] * PANEL_SIZE)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-D candidate inside a paired block")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1
            depth_training_counts[depth] += 1

    panel_revalidated = True
    try:
        for candidate_index in range(PANEL_SIZE):
            _verify_candidate(candidate_index)
    except Exception:
        panel_revalidated = False

    depth_blocks: dict[int, list[list[float]]] = {}
    depth_null_blocks: dict[int, list[list[float]]] = {}
    depth_summaries: dict[str, dict[str, Any]] = {}

    for depth in DEPTHS:
        frozen_blocks: list[list[float]] = []
        frozen_null_blocks: list[list[float]] = []
        for difference in DIFFERENCES:
            for replicate in range(REPLICATES):
                raw = blocks[(depth, int(difference), replicate)]
                raw_null = null_blocks[(depth, int(difference), replicate)]
                if any(value is None for value in raw) or any(value is None for value in raw_null):
                    raise ValueError("Phase 2A-D incomplete blocked data")
                frozen_blocks.append([float(value) for value in raw if value is not None])
                frozen_null_blocks.append(
                    [float(value) for value in raw_null if value is not None]
                )

        scores = _candidate_means(frozen_blocks)
        null_scores = _candidate_means(frozen_null_blocks)
        variance, p_value = blocked_heterogeneity_p(
            frozen_blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=HETEROGENEITY_PERMUTATION_SEEDS[depth],
        )
        score_range = float(max(scores) - min(scores))
        signal = any(
            score >= 0.04 and (score - null_score) >= 0.02
            for score, null_score in zip(scores, null_scores)
        )
        dispersion = between_candidate_variance(frozen_blocks)
        if abs(dispersion - variance) > 1e-15:
            raise RuntimeError("Phase 2A-D heterogeneity/dispersion statistic drift")
        depth_blocks[depth] = frozen_blocks
        depth_null_blocks[depth] = frozen_null_blocks
        depth_summaries[f"R{depth}"] = {
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "between_candidate_variance": dispersion,
            "heterogeneity_permutation_p": p_value,
            "candidate_score_range": score_range,
            "signal_condition": signal,
            "training_count_exact": depth_training_counts[depth] == TRAININGS_PER_DEPTH,
        }

    delta45, p45, variance4, variance5 = paired_dispersion_attenuation_p(
        depth_blocks[4],
        depth_blocks[5],
        repetitions=PERMUTATION_REPETITIONS,
        seed=PRIMARY_PERMUTATION_SEED,
    )
    delta34, p34, variance3, variance4_secondary = paired_dispersion_attenuation_p(
        depth_blocks[3],
        depth_blocks[4],
        repetitions=PERMUTATION_REPETITIONS,
        seed=SECONDARY_PERMUTATION_SEED,
    )
    if abs(variance4 - variance4_secondary) > 1e-15:
        raise RuntimeError("Phase 2A-D R4 variance mismatch across paired tests")

    r4 = depth_summaries["R4"]
    baseline_checks = {
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "seed_registry_exact": seed_registry_exact,
        "neural_evolutionary_pressure_absent": True,
        "r4_heterogeneity": float(r4["heterogeneity_permutation_p"]) < 0.05,
        "r4_range": float(r4["candidate_score_range"]) >= 0.015,
        "r4_signal": bool(r4["signal_condition"]),
    }
    requirements_pass = baseline_r4_requirements_pass(baseline_checks)
    variance_ratio45: float | None = (
        float(variance5 / variance4) if variance4 > 0.0 else None
    )
    verdict = classify_depth_attenuation(
        requirements_pass=requirements_pass,
        delta45=delta45,
        p45=p45,
        variance_ratio45=(variance_ratio45 if variance_ratio45 is not None else float("inf")),
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ad_depth_attenuation_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "total_trainings": total_trainings,
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "seed_registry_exact": seed_registry_exact,
        "neural_evolutionary_pressure": False,
        "depths": depth_summaries,
        "variance_trajectory": {
            "V3": variance3,
            "V4": variance4,
            "V5": variance5,
        },
        "primary_4_to_5": {
            "delta": delta45,
            "permutation_p": p45,
            "variance_ratio_V5_over_V4": variance_ratio45,
        },
        "secondary_3_to_4": {
            "delta": delta34,
            "permutation_p": p34,
            "variance_ratio_V4_over_V3": (
                float(variance4 / variance3) if variance3 > 0.0 else None
            ),
        },
        "baseline_checks": baseline_checks,
        "primary_requirements_pass": requirements_pass,
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
