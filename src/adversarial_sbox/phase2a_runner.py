"""Execution gate, neural cells, and aggregate analysis for Phase 2A.

The module loads the committed six-candidate classical panel lazily. Until
``phase2a_candidates.py`` exists, every neural execution path fails closed.
No function in this module feeds a neural score back into evolution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT, _train_one as _train_bit_relu_mlp
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2a import (
    DATASET_SEEDS,
    MODEL_SEEDS,
    PANEL_SIZE,
    TOTAL_TRAININGS,
    qualification_verdict,
)
from .phase2a_neural import (
    CELL_SPECS,
    CHALLENGER_PERMUTATION_SEED,
    ORACLE_PERMUTATION_SEED,
    PERMUTATION_REPETITIONS,
    REPLICATES,
    TRAININGS_PER_CELL,
    blocked_heterogeneity_p,
    build_qualification_checks,
    spearman_correlation,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN


def _cell_spec(side: str, input_difference: int) -> tuple[str, int, int, str]:
    target = (str(side), int(input_difference))
    for spec in CELL_SPECS:
        if (spec[0], spec[2]) == target:
            return spec
    raise ValueError(f"undeclared Phase 2A cell {target!r}")


def load_committed_panel() -> tuple[dict[str, Any], ...]:
    """Load the frozen six-candidate panel, or fail closed before it exists."""

    try:
        from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
    except ImportError as exc:
        raise RuntimeError(
            "Phase 2A neural execution is blocked until phase2a_candidates.py is committed"
        ) from exc

    if len(CANDIDATES) != PANEL_SIZE:
        raise RuntimeError("Phase 2A committed panel size mismatch")
    if not isinstance(PANEL_DIGEST_SHA256, str) or len(PANEL_DIGEST_SHA256) != 64:
        raise RuntimeError("Phase 2A committed panel digest is invalid")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_committed_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_committed_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A candidate index out of range")
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
            f"Phase 2A committed candidate {candidate_index} failed classical revalidation: {checks}"
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


def run_cell(side: str, input_difference: int) -> dict[str, Any]:
    """Run one frozen 30-training Phase-2A cell.

    Calling this before the classical panel is committed fails before any dataset
    generation or neural training occurs.
    """

    side, rounds, input_difference, architecture = _cell_spec(side, input_difference)
    keys = ROUND_KEYS[: rounds + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(PANEL_SIZE):
        sbox, classical = _verify_committed_candidate(candidate_index)
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != rounds:
            raise RuntimeError(f"expected {rounds} ToySPN rounds, got {cipher.rounds}")
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(DATASET_SEEDS, MODEL_SEEDS)
        ):
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
            else:  # pragma: no cover - impossible under frozen CELL_SPECS
                raise RuntimeError(f"unsupported Phase 2A architecture {architecture!r}")
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
        raise RuntimeError("Phase 2A cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2a_neural_oracle_qualification_cell",
        "side": side,
        "rounds": rounds,
        "input_difference": input_difference,
        "architecture": architecture,
        "pair_count": PAIR_COUNT,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["scientific_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def _expected_cell_keys() -> set[tuple[str, int, int, str]]:
    return set(CELL_SPECS)


def _canonical_cell_payload(item: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in item.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate all four frozen cells and apply every Phase-2A criterion."""

    if len(results) != len(CELL_SPECS):
        raise ValueError("Phase 2A aggregation requires exactly four cell results")

    panel = load_committed_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    cells: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    deterministic_receipts = True

    for item in results:
        key = (
            str(item["side"]),
            int(item["rounds"]),
            int(item["input_difference"]),
            str(item["architecture"]),
        )
        if key in cells:
            raise ValueError(f"duplicate Phase 2A cell {key!r}")
        expected_receipt = hashlib.sha256(_canonical_cell_payload(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        cells[key] = item

    if set(cells) != _expected_cell_keys():
        raise ValueError("Phase 2A cell set does not match the frozen design")

    block_map: dict[tuple[str, int, int], list[float | None]] = {}
    null_map: dict[tuple[str, int, int], list[float | None]] = {}
    total_trainings = 0

    for key in CELL_SPECS:
        item = cells[key]
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A cell must contain exactly 30 trainings")
        side, _rounds, input_difference, _architecture = key
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < PANEL_SIZE or not 0 <= replicate < REPLICATES:
                raise ValueError("Phase 2A candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A training fingerprint mismatch")
            if int(run["source_seed"]) != int(panel[candidate_index]["source_seed"]):
                raise ValueError("Phase 2A source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                raise ValueError("Phase 2A dataset seed mismatch")
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                raise ValueError("Phase 2A model seed mismatch")
            block_key = (side, input_difference, replicate)
            block = block_map.setdefault(block_key, [None] * PANEL_SIZE)
            null_block = null_map.setdefault(block_key, [None] * PANEL_SIZE)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A candidate inside a blocked cell")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1

    if total_trainings != TOTAL_TRAININGS:
        raise ValueError(f"expected {TOTAL_TRAININGS} trainings, got {total_trainings}")
    if any(any(value is None for value in block) for block in block_map.values()):
        raise ValueError("incomplete Phase 2A neural block")
    if any(any(value is None for value in block) for block in null_map.values()):
        raise ValueError("incomplete Phase 2A null block")

    side_summaries: dict[str, dict[str, Any]] = {}
    candidate_means: dict[str, list[float]] = {"oracle": [], "challenger": []}
    candidate_null_means: dict[str, list[float]] = {"oracle": [], "challenger": []}

    for side, permutation_seed in (
        ("oracle", ORACLE_PERMUTATION_SEED),
        ("challenger", CHALLENGER_PERMUTATION_SEED),
    ):
        keys = sorted(
            (key for key in block_map if key[0] == side),
            key=lambda key: (key[1], key[2]),
        )
        blocks = [[float(value) for value in block_map[key]] for key in keys]
        variance, p_value = blocked_heterogeneity_p(
            blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=permutation_seed,
        )
        for candidate_index in range(PANEL_SIZE):
            values = [float(block[candidate_index]) for block in blocks]
            null_values = [float(null_map[key][candidate_index]) for key in keys]
            candidate_means[side].append(sum(values) / len(values))
            candidate_null_means[side].append(sum(null_values) / len(null_values))
        means = candidate_means[side]
        null_means = candidate_null_means[side]
        score_range = max(means) - min(means)
        signal = any(
            mean >= 0.04 and mean - null_mean >= 0.02
            for mean, null_mean in zip(means, null_means)
        )
        side_summaries[side] = {
            "heterogeneity_variance": variance,
            "heterogeneity_permutation_p": p_value,
            "candidate_score_range": score_range,
            "candidate_mean_advantages": means,
            "candidate_mean_null_advantages": null_means,
            "signal_condition": signal,
        }

    spearman = spearman_correlation(candidate_means["oracle"], candidate_means["challenger"])

    for candidate_index in range(PANEL_SIZE):
        _verify_committed_candidate(candidate_index)

    checks = build_qualification_checks(
        total_trainings=total_trainings,
        panel_revalidated=True,
        oracle_p=side_summaries["oracle"]["heterogeneity_permutation_p"],
        challenger_p=side_summaries["challenger"]["heterogeneity_permutation_p"],
        oracle_range=side_summaries["oracle"]["candidate_score_range"],
        challenger_range=side_summaries["challenger"]["candidate_score_range"],
        spearman=spearman,
        oracle_signal=side_summaries["oracle"]["signal_condition"],
        challenger_signal=side_summaries["challenger"]["signal_condition"],
        deterministic_receipts=deterministic_receipts,
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2a_neural_oracle_qualification_aggregate",
        "summary": {
            "total_trainings": total_trainings,
            "oracle_heterogeneity_permutation_p": side_summaries["oracle"]["heterogeneity_permutation_p"],
            "challenger_heterogeneity_permutation_p": side_summaries["challenger"]["heterogeneity_permutation_p"],
            "oracle_score_range": side_summaries["oracle"]["candidate_score_range"],
            "challenger_score_range": side_summaries["challenger"]["candidate_score_range"],
            "oracle_challenger_spearman": spearman,
            "oracle_signal": side_summaries["oracle"]["signal_condition"],
            "challenger_signal": side_summaries["challenger"]["signal_condition"],
            "neural_evolutionary_pressure": False,
        },
        "side_summaries": side_summaries,
        "candidates": [
            {
                "candidate_index": index,
                "source_seed": int(panel[index]["source_seed"]),
                "fingerprint": fingerprints[index],
                "oracle_score": candidate_means["oracle"][index],
                "oracle_null_score": candidate_null_means["oracle"][index],
                "challenger_score": candidate_means["challenger"][index],
                "challenger_null_score": candidate_null_means["challenger"][index],
            }
            for index in range(PANEL_SIZE)
        ],
        "qualification_checks": checks,
        "verdict": qualification_verdict(checks),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
