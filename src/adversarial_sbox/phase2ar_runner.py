"""Scientific runner for Phase 2A-R neural rank-instability decomposition.

Phase 2A-R is diagnostic only. This module never feeds a neural score back into
any evolutionary component.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT, _train_one as _train_bit_relu_mlp
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2a_neural import blocked_heterogeneity_p, spearman_correlation
from .phase2ar import (
    DATASET_SEEDS,
    MODEL_SEEDS,
    PANEL_DIGEST_SHA256,
    PANEL_SIZE,
    PERMUTATION_REPETITIONS,
    PERMUTATION_SEEDS,
    REGIMES,
    REPLICATES,
    TOTAL_TRAININGS,
    TRAININGS_PER_CELL,
    TRAININGS_PER_REGIME,
    classify_diagnostic,
    regime_spec,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN


_REQUIRED_PREREQUISITE_KEYS = (
    "training_count_exact",
    "panel_revalidated",
    "heterogeneity",
    "range",
    "signal",
    "deterministic_receipts",
)


def load_frozen_panel() -> tuple[dict[str, Any], ...]:
    from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256 as COMMITTED_DIGEST

    if COMMITTED_DIGEST != PANEL_DIGEST_SHA256:
        raise RuntimeError("Phase 2A-R panel digest drift")
    if len(CANDIDATES) != PANEL_SIZE:
        raise RuntimeError("Phase 2A-R panel size drift")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_frozen_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-R candidate index out of range")
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
            f"Phase 2A-R candidate {candidate_index} failed classical revalidation: {checks}"
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


def expected_cell_keys() -> set[tuple[str, str, int, int]]:
    keys: set[tuple[str, str, int, int]] = set()
    for regime, architecture, rounds, differences in REGIMES:
        for difference in differences:
            keys.add((regime, architecture, rounds, int(difference)))
    return keys


def _cell_spec(regime: str, input_difference: int) -> tuple[str, str, int, int]:
    name, architecture, rounds, differences = regime_spec(regime)
    difference = int(input_difference)
    if difference not in differences:
        raise ValueError(f"undeclared Phase 2A-R cell {(name, difference)!r}")
    return name, architecture, rounds, difference


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_cell(regime: str, input_difference: int) -> dict[str, Any]:
    """Run one frozen 30-training Phase-2A-R cell."""

    regime, architecture, rounds, input_difference = _cell_spec(regime, input_difference)
    keys = ROUND_KEYS[: rounds + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(PANEL_SIZE):
        sbox, classical = _verify_candidate(candidate_index)
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != rounds:
            raise RuntimeError(f"expected {rounds} ToySPN rounds, got {cipher.rounds}")
        for replicate, (dataset_seed, model_seed) in enumerate(zip(DATASET_SEEDS, MODEL_SEEDS)):
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=input_difference,
                seed=int(dataset_seed),
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            if architecture == "bit_relu_mlp":
                endpoint = _train_bit_relu_mlp(
                    train_samples=train_samples,
                    validation_samples=validation_samples,
                    test_samples=test_samples,
                    model_seed=int(model_seed),
                )
            elif architecture == "byte_tanh_mlp":
                endpoint = _train_byte_tanh_mlp(
                    train_samples=train_samples,
                    validation_samples=validation_samples,
                    test_samples=test_samples,
                    model_seed=int(model_seed),
                )
            else:  # pragma: no cover - impossible under frozen REGIMES
                raise RuntimeError(f"unsupported Phase 2A-R architecture {architecture!r}")
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
        raise RuntimeError("Phase 2A-R cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ar_rank_instability_cell",
        "regime": regime,
        "architecture": architecture,
        "rounds": rounds,
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


def summarize_regime_prerequisites(checks: dict[str, bool]) -> bool:
    return all(bool(checks.get(key, False)) for key in _REQUIRED_PREREQUISITE_KEYS)


def _candidate_means(blocks: Sequence[Sequence[float]]) -> list[float]:
    if not blocks or any(len(block) != PANEL_SIZE for block in blocks):
        raise ValueError("Phase 2A-R blocks must be non-empty and panel-width")
    return [
        float(sum(float(block[index]) for block in blocks) / len(blocks))
        for index in range(PANEL_SIZE)
    ]


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all eight frozen cells and classify the diagnostic transition."""

    if len(results) != len(expected_cell_keys()):
        raise ValueError("Phase 2A-R aggregation requires exactly eight cell results")

    panel = load_frozen_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    source_seeds = tuple(int(candidate["source_seed"]) for candidate in panel)

    cells: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    deterministic_receipts = True
    total_trainings = 0
    regime_training_counts = {regime: 0 for regime, *_ in REGIMES}
    blocks: dict[tuple[str, int, int], list[float | None]] = {}
    null_blocks: dict[tuple[str, int, int], list[float | None]] = {}

    for item in results:
        key = (
            str(item["regime"]),
            str(item["architecture"]),
            int(item["rounds"]),
            int(item["input_difference"]),
        )
        if key in cells:
            raise ValueError(f"duplicate Phase 2A-R cell {key!r}")
        if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
            raise ValueError("Phase 2A-R cell panel digest mismatch")
        expected_receipt = hashlib.sha256(_canonical_without_receipt(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        if bool(item.get("neural_evolutionary_pressure", True)):
            raise ValueError("Phase 2A-R forbids neural evolutionary pressure")
        cells[key] = item

    if set(cells) != expected_cell_keys():
        raise ValueError("Phase 2A-R cell set does not match the frozen design")

    for key, item in cells.items():
        regime, _architecture, _rounds, input_difference = key
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-R cell must contain exactly 30 trainings")
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < PANEL_SIZE or not 0 <= replicate < REPLICATES:
                raise ValueError("Phase 2A-R candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-R candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-R training fingerprint mismatch")
            if int(run["source_seed"]) != source_seeds[candidate_index]:
                raise ValueError("Phase 2A-R source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                raise ValueError("Phase 2A-R dataset seed mismatch")
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                raise ValueError("Phase 2A-R model seed mismatch")
            block_key = (regime, input_difference, replicate)
            block = blocks.setdefault(block_key, [None] * PANEL_SIZE)
            null_block = null_blocks.setdefault(block_key, [None] * PANEL_SIZE)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-R candidate inside a blocked cell")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1
            regime_training_counts[regime] += 1

    panel_revalidated = True
    try:
        for candidate_index in range(PANEL_SIZE):
            _verify_candidate(candidate_index)
    except Exception:
        panel_revalidated = False

    regime_summaries: dict[str, dict[str, Any]] = {}
    regime_scores: dict[str, list[float]] = {}
    all_prerequisites = True

    for regime, _architecture, _rounds, differences in REGIMES:
        regime_blocks: list[list[float]] = []
        regime_null_blocks: list[list[float]] = []
        for difference in differences:
            for replicate in range(REPLICATES):
                raw = blocks[(regime, int(difference), replicate)]
                raw_null = null_blocks[(regime, int(difference), replicate)]
                if any(value is None for value in raw) or any(value is None for value in raw_null):
                    raise ValueError("Phase 2A-R incomplete blocked data")
                regime_blocks.append([float(value) for value in raw if value is not None])
                regime_null_blocks.append(
                    [float(value) for value in raw_null if value is not None]
                )

        scores = _candidate_means(regime_blocks)
        null_scores = _candidate_means(regime_null_blocks)
        variance, p_value = blocked_heterogeneity_p(
            regime_blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=PERMUTATION_SEEDS[regime],
        )
        score_range = float(max(scores) - min(scores))
        signal = any(
            score >= 0.04 and (score - null_score) >= 0.02
            for score, null_score in zip(scores, null_scores)
        )
        checks = {
            "training_count_exact": regime_training_counts[regime] == TRAININGS_PER_REGIME,
            "panel_revalidated": panel_revalidated,
            "heterogeneity": p_value < 0.05,
            "range": score_range >= 0.015,
            "signal": bool(signal),
            "deterministic_receipts": deterministic_receipts,
        }
        prerequisite_pass = summarize_regime_prerequisites(checks)
        all_prerequisites = all_prerequisites and prerequisite_pass
        regime_scores[regime] = scores
        regime_summaries[regime] = {
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "heterogeneity_variance": variance,
            "heterogeneity_permutation_p": p_value,
            "candidate_score_range": score_range,
            "signal_condition": signal,
            "checks": checks,
            "prerequisites_pass": prerequisite_pass,
        }

    rho_ab = spearman_correlation(regime_scores["A"], regime_scores["B"])
    rho_bc = spearman_correlation(regime_scores["B"], regime_scores["C"])
    rho_cd = spearman_correlation(regime_scores["C"], regime_scores["D"])
    verdict = classify_diagnostic(all_prerequisites, rho_ab, rho_bc, rho_cd)

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2ar_rank_instability_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "total_trainings": total_trainings,
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "neural_evolutionary_pressure": False,
        "regimes": regime_summaries,
        "adjacent_spearman": {
            "rho_AB": rho_ab,
            "rho_BC": rho_bc,
            "rho_CD": rho_cd,
        },
        "all_signal_prerequisites_pass": all_prerequisites,
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
