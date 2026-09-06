"""Scientific runner for Phase 2A-T fresh-seed depth-profile replication.

This module is diagnostic only. Neural scores are never fed into evolution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2a_neural import blocked_heterogeneity_p, spearman_correlation
from .phase2at import (
    ARCHITECTURE,
    CANDIDATE_COUNT,
    DATASET_SEEDS,
    DEPTH4_HETEROGENEITY_P_MAX,
    DEPTHS,
    DIFFERENCES,
    MIN_CANDIDATE_ADVANTAGE,
    MIN_NULL_MARGIN,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PAIRED_REPLICATES,
    PERMUTATION_REPETITIONS,
    PERMUTATION_SEEDS,
    TOTAL_TRAININGS,
    TRAININGS_PER_CELL,
    TRAININGS_PER_DEPTH,
    classify_depth_profile,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN


def load_frozen_panel() -> tuple[dict[str, Any], ...]:
    from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256 as COMMITTED_DIGEST

    if COMMITTED_DIGEST != PANEL_DIGEST_SHA256:
        raise RuntimeError("Phase 2A-T panel digest drift")
    if len(CANDIDATES) != CANDIDATE_COUNT:
        raise RuntimeError("Phase 2A-T panel size drift")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_frozen_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-T candidate index out of range")
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
        "bijective": len(sbox) == 256 and len(set(sbox)) == 256,
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Phase 2A-T candidate {candidate_index} failed classical revalidation: {checks}"
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


def expected_cell_keys() -> tuple[tuple[int, int], ...]:
    return tuple((depth, int(difference)) for depth in DEPTHS for difference in DIFFERENCES)


def _cell_spec(depth: int, input_difference: int) -> tuple[int, int]:
    depth = int(depth)
    difference = int(input_difference)
    if depth not in DEPTHS:
        raise ValueError(f"undeclared Phase 2A-T depth {depth}")
    if difference not in DIFFERENCES:
        raise ValueError(f"undeclared Phase 2A-T difference {difference:#x}")
    return depth, difference


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_cell(depth: int, input_difference: int) -> dict[str, Any]:
    """Run one frozen 48-training Phase-2A-T depth/difference cell."""

    depth, input_difference = _cell_spec(depth, input_difference)
    keys = ROUND_KEYS[: depth + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(CANDIDATE_COUNT):
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
        raise RuntimeError("Phase 2A-T cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2at_depth_profile_cell",
        "architecture": ARCHITECTURE,
        "depth": depth,
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


def _candidate_means(blocks: Sequence[Sequence[float]]) -> list[float]:
    if not blocks or any(len(block) != CANDIDATE_COUNT for block in blocks):
        raise ValueError("Phase 2A-T blocks must be non-empty and panel-width")
    return [
        float(sum(float(block[index]) for block in blocks) / len(blocks))
        for index in range(CANDIDATE_COUNT)
    ]


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all six frozen cells and classify the fresh-seed profile replication."""

    expected_keys = expected_cell_keys()
    if len(results) != len(expected_keys):
        raise ValueError("Phase 2A-T aggregation requires exactly six cell results")

    panel = load_frozen_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    source_seeds = tuple(int(candidate["source_seed"]) for candidate in panel)

    cells: dict[tuple[int, int], dict[str, Any]] = {}
    deterministic_receipts = True
    total_trainings = 0
    depth_training_counts = {depth: 0 for depth in DEPTHS}
    blocks: dict[tuple[int, int, int], list[float | None]] = {}
    null_blocks: dict[tuple[int, int, int], list[float | None]] = {}

    for item in results:
        key = (int(item["depth"]), int(item["input_difference"]))
        if key in cells:
            raise ValueError(f"duplicate Phase 2A-T cell {key!r}")
        if key not in expected_keys:
            raise ValueError(f"undeclared Phase 2A-T cell {key!r}")
        if str(item.get("architecture", "")) != ARCHITECTURE:
            raise ValueError("Phase 2A-T architecture drift")
        if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
            raise ValueError("Phase 2A-T cell panel digest mismatch")
        expected_receipt = hashlib.sha256(_canonical_without_receipt(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        if bool(item.get("neural_evolutionary_pressure", True)):
            raise ValueError("Phase 2A-T forbids neural evolutionary pressure")
        cells[key] = item

    if tuple(sorted(cells)) != tuple(sorted(expected_keys)):
        raise ValueError("Phase 2A-T cell set does not match the frozen design")

    for (depth, input_difference), item in cells.items():
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-T cell must contain exactly 48 trainings")
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < CANDIDATE_COUNT:
                raise ValueError("Phase 2A-T candidate index out of range")
            if not 0 <= replicate < PAIRED_REPLICATES:
                raise ValueError("Phase 2A-T replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-T candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-T training fingerprint mismatch")
            if int(run["source_seed"]) != source_seeds[candidate_index]:
                raise ValueError("Phase 2A-T source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                raise ValueError("Phase 2A-T dataset seed mismatch")
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                raise ValueError("Phase 2A-T model seed mismatch")
            block_key = (depth, input_difference, replicate)
            block = blocks.setdefault(block_key, [None] * CANDIDATE_COUNT)
            null_block = null_blocks.setdefault(block_key, [None] * CANDIDATE_COUNT)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-T candidate inside a blocked cell")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1
            depth_training_counts[depth] += 1

    panel_revalidated = True
    try:
        for candidate_index in range(CANDIDATE_COUNT):
            _verify_candidate(candidate_index)
    except Exception:
        panel_revalidated = False

    depth_summaries: dict[int, dict[str, Any]] = {}
    depth_scores: dict[int, list[float]] = {}
    heterogeneity_by_depth: dict[int, float] = {}
    range_by_depth: dict[int, float] = {}
    mean_advantage_by_depth: dict[int, float] = {}
    p_by_depth: dict[int, float] = {}
    all_signals = True

    for depth in DEPTHS:
        depth_blocks: list[list[float]] = []
        depth_null_blocks: list[list[float]] = []
        for difference in DIFFERENCES:
            for replicate in range(PAIRED_REPLICATES):
                raw = blocks[(depth, int(difference), replicate)]
                raw_null = null_blocks[(depth, int(difference), replicate)]
                if any(value is None for value in raw) or any(value is None for value in raw_null):
                    raise ValueError("Phase 2A-T incomplete blocked data")
                depth_blocks.append([float(value) for value in raw if value is not None])
                depth_null_blocks.append([float(value) for value in raw_null if value is not None])

        scores = _candidate_means(depth_blocks)
        null_scores = _candidate_means(depth_null_blocks)
        variance, p_value = blocked_heterogeneity_p(
            depth_blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=PERMUTATION_SEEDS[depth],
        )
        score_range = float(max(scores) - min(scores))
        mean_advantage = float(sum(scores) / len(scores))
        signal = any(
            score >= MIN_CANDIDATE_ADVANTAGE and (score - null_score) >= MIN_NULL_MARGIN
            for score, null_score in zip(scores, null_scores)
        )
        all_signals = all_signals and bool(signal)
        depth_scores[depth] = scores
        heterogeneity_by_depth[depth] = float(variance)
        range_by_depth[depth] = score_range
        mean_advantage_by_depth[depth] = mean_advantage
        p_by_depth[depth] = float(p_value)
        depth_summaries[depth] = {
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "mean_neural_advantage": mean_advantage,
            "heterogeneity_variance": float(variance),
            "heterogeneity_permutation_p": float(p_value),
            "candidate_score_range": score_range,
            "signal_condition": bool(signal),
            "training_count_exact": depth_training_counts[depth] == TRAININGS_PER_DEPTH,
        }

    prerequisites = (
        total_trainings == TOTAL_TRAININGS
        and panel_revalidated
        and deterministic_receipts
        and all_signals
    )

    verdict = classify_depth_profile(
        prerequisites,
        heterogeneity_by_depth,
        range_by_depth,
        mean_advantage_by_depth,
        p_by_depth[4],
    )

    profile_criteria = {
        "H4_gt_H3": heterogeneity_by_depth[4] > heterogeneity_by_depth[3],
        "H4_gt_H5": heterogeneity_by_depth[4] > heterogeneity_by_depth[5],
        "R4_gt_R3": range_by_depth[4] > range_by_depth[3],
        "R4_gt_R5": range_by_depth[4] > range_by_depth[5],
        "M3_gt_M4_gt_M5": (
            mean_advantage_by_depth[3]
            > mean_advantage_by_depth[4]
            > mean_advantage_by_depth[5]
        ),
        "depth4_p_lt_0_05": p_by_depth[4] < DEPTH4_HETEROGENEITY_P_MAX,
    }

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2at_depth_profile_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "architecture": ARCHITECTURE,
        "depths": list(DEPTHS),
        "differences": list(DIFFERENCES),
        "total_trainings": total_trainings,
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "signal_all_depths": all_signals,
        "prerequisites_pass": prerequisites,
        "neural_evolutionary_pressure": False,
        "depth_summaries": {str(depth): summary for depth, summary in depth_summaries.items()},
        "heterogeneity_by_depth": {str(depth): value for depth, value in heterogeneity_by_depth.items()},
        "range_by_depth": {str(depth): value for depth, value in range_by_depth.items()},
        "mean_advantage_by_depth": {str(depth): value for depth, value in mean_advantage_by_depth.items()},
        "profile_criteria": profile_criteria,
        "adjacent_spearman": {
            "rho_34": spearman_correlation(depth_scores[3], depth_scores[4]),
            "rho_45": spearman_correlation(depth_scores[4], depth_scores[5]),
        },
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
