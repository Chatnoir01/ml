"""Scientific runner for Phase 2A-P fresh R4 peak confirmation.

Phase 2A-P is diagnostic/confirmatory only. Neural scores never influence any
search or evolutionary component.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2a_neural import blocked_heterogeneity_p
from .phase2ap import (
    ALPHA_PER_SIDE,
    ARCHITECTURE,
    DATASET_SEEDS,
    DEPTHS,
    DIFFERENCES,
    EFFECT_RATIO_MAX,
    HETEROGENEITY_PERMUTATION_SEEDS,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PANEL_SIZE,
    PEAK_PERMUTATION_SEEDS,
    PERMUTATION_REPETITIONS,
    REPLICATES,
    TOTAL_TRAININGS,
    TRAININGS_PER_CELL,
    TRAININGS_PER_DEPTH,
    block_dispersion,
    candidate_means,
    classify_peak,
    paired_block_peak_test,
    peak_side_pass,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

_REQUIRED_KEYS = (
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
        raise RuntimeError("Phase 2A-P panel digest drift")
    if len(CANDIDATES) != PANEL_SIZE:
        raise RuntimeError("Phase 2A-P panel size drift")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_frozen_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-P candidate index out of range")
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
            f"Phase 2A-P candidate {candidate_index} failed classical revalidation: {checks}"
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
        raise ValueError(f"undeclared Phase 2A-P depth {depth!r}")
    if difference not in DIFFERENCES:
        raise ValueError(f"undeclared Phase 2A-P difference {input_difference!r}")
    return frozen_depth, ARCHITECTURE, difference


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_cell(depth: int, input_difference: int) -> dict[str, Any]:
    """Run one frozen 120-training Phase-2A-P depth/difference cell."""

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
        raise RuntimeError("Phase 2A-P cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ap_r4_peak_cell",
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


def _requirements_pass(checks: dict[str, bool]) -> bool:
    return all(bool(checks.get(key, False)) for key in _REQUIRED_KEYS)


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all six cells and apply the frozen R4 peak decision rule."""

    if len(results) != len(expected_cell_keys()):
        raise ValueError("Phase 2A-P aggregation requires exactly six cell results")

    panel = load_frozen_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    source_seeds = tuple(int(candidate["source_seed"]) for candidate in panel)

    cells: dict[tuple[int, str, int], dict[str, Any]] = {}
    deterministic_receipts = True
    total_trainings = 0
    seed_registry_exact = True
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
            raise ValueError(f"duplicate Phase 2A-P cell {key!r}")
        if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
            raise ValueError("Phase 2A-P cell panel digest mismatch")
        if bool(item.get("neural_evolutionary_pressure", True)):
            raise ValueError("Phase 2A-P forbids neural evolutionary pressure")
        expected_receipt = hashlib.sha256(_canonical_without_receipt(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        cells[key] = item

    if set(cells) != expected_cell_keys():
        raise ValueError("Phase 2A-P cell set does not match the frozen design")

    for key in sorted(cells):
        depth, _architecture, input_difference = key
        runs = cells[key]["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-P cell must contain exactly 120 trainings")
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < PANEL_SIZE or not 0 <= replicate < REPLICATES:
                raise ValueError("Phase 2A-P candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-P candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-P training fingerprint mismatch")
            if int(run["source_seed"]) != source_seeds[candidate_index]:
                raise ValueError("Phase 2A-P source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                seed_registry_exact = False
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                seed_registry_exact = False
            block_key = (depth, input_difference, replicate)
            block = blocks.setdefault(block_key, [None] * PANEL_SIZE)
            null_block = null_blocks.setdefault(block_key, [None] * PANEL_SIZE)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-P candidate inside a matched block")
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
    depth_summaries: dict[str, dict[str, Any]] = {}

    for depth in DEPTHS:
        frozen_blocks: list[list[float]] = []
        frozen_null_blocks: list[list[float]] = []
        for difference in DIFFERENCES:
            for replicate in range(REPLICATES):
                raw = blocks[(depth, int(difference), replicate)]
                raw_null = null_blocks[(depth, int(difference), replicate)]
                if any(value is None for value in raw) or any(value is None for value in raw_null):
                    raise ValueError("Phase 2A-P incomplete matched block")
                frozen_blocks.append([float(value) for value in raw if value is not None])
                frozen_null_blocks.append([float(value) for value in raw_null if value is not None])

        scores = candidate_means(frozen_blocks)
        null_scores = candidate_means(frozen_null_blocks)
        variance, p_value = blocked_heterogeneity_p(
            frozen_blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=HETEROGENEITY_PERMUTATION_SEEDS[depth],
        )
        score_variance = float(statistics.pvariance(scores))
        if abs(score_variance - variance) > 1e-15:
            raise RuntimeError("Phase 2A-P blocked heterogeneity statistic drift")
        score_range = float(max(scores) - min(scores))
        signal = any(
            score >= 0.04 and (score - null_score) >= 0.02
            for score, null_score in zip(scores, null_scores)
        )
        block_dispersions = [block_dispersion(block) for block in frozen_blocks]
        mean_block_dispersion = float(statistics.fmean(block_dispersions))
        depth_blocks[depth] = frozen_blocks
        depth_summaries[f"R{depth}"] = {
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "candidate_score_variance": score_variance,
            "candidate_score_range": score_range,
            "heterogeneity_permutation_p": p_value,
            "signal_condition": bool(signal),
            "mean_block_dispersion": mean_block_dispersion,
            "block_dispersions": block_dispersions,
            "training_count_exact": depth_training_counts[depth] == TRAININGS_PER_DEPTH,
        }

    c43, p43, mean4a, mean3, ratio3over4 = paired_block_peak_test(
        depth_blocks[4],
        depth_blocks[3],
        repetitions=PERMUTATION_REPETITIONS,
        seed=PEAK_PERMUTATION_SEEDS[(4, 3)],
    )
    c45, p45, mean4b, mean5, ratio5over4 = paired_block_peak_test(
        depth_blocks[4],
        depth_blocks[5],
        repetitions=PERMUTATION_REPETITIONS,
        seed=PEAK_PERMUTATION_SEEDS[(4, 5)],
    )
    if abs(mean4a - mean4b) > 1e-15:
        raise RuntimeError("Phase 2A-P R4 block-dispersion mismatch across paired tests")

    side43_pass = peak_side_pass(
        contrast=c43,
        p_value=p43,
        neighbor_over_r4=ratio3over4,
    )
    side45_pass = peak_side_pass(
        contrast=c45,
        p_value=p45,
        neighbor_over_r4=ratio5over4,
    )

    r4 = depth_summaries["R4"]
    checks = {
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "seed_registry_exact": seed_registry_exact,
        "neural_evolutionary_pressure_absent": True,
        "r4_heterogeneity": float(r4["heterogeneity_permutation_p"]) < 0.05,
        "r4_range": float(r4["candidate_score_range"]) >= 0.015,
        "r4_signal": bool(r4["signal_condition"]),
    }
    requirements_pass = _requirements_pass(checks)
    verdict = classify_peak(
        requirements_pass=requirements_pass,
        side43_pass=side43_pass,
        side45_pass=side45_pass,
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ap_r4_peak_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "total_trainings": total_trainings,
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "seed_registry_exact": seed_registry_exact,
        "neural_evolutionary_pressure": False,
        "alpha_per_side": ALPHA_PER_SIDE,
        "effect_ratio_max": EFFECT_RATIO_MAX,
        "depths": depth_summaries,
        "primary_peak": {
            "R4_gt_R3": {
                "contrast_mean_block_dispersion": c43,
                "permutation_p": p43,
                "mean_R4_block_dispersion": mean4a,
                "mean_R3_block_dispersion": mean3,
                "neighbor_over_R4_ratio": ratio3over4,
                "pass": side43_pass,
            },
            "R4_gt_R5": {
                "contrast_mean_block_dispersion": c45,
                "permutation_p": p45,
                "mean_R4_block_dispersion": mean4b,
                "mean_R5_block_dispersion": mean5,
                "neighbor_over_R4_ratio": ratio5over4,
                "pass": side45_pass,
            },
        },
        "prerequisite_checks": checks,
        "requirements_pass": requirements_pass,
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
