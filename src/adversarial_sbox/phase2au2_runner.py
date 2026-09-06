"""Scientific runner for Phase 2A-U2 fresh-seed Oracle requalification.

U2 is measurement-only. Neural scores are never fed into evolution here.
Aggregation validates the frozen pair count and deterministic split sizes in
addition to the seed/fingerprint/receipt checks inherited from Phase 2A-U.
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
from .phase2au2 import (
    ARCHITECTURE,
    BLOCK_A_DATASET_SEEDS,
    BLOCK_A_MODEL_SEEDS,
    BLOCK_B_DATASET_SEEDS,
    BLOCK_B_MODEL_SEEDS,
    CANDIDATE_COUNT,
    DEPTH,
    DIFFERENCES,
    MIN_CANDIDATE_ADVANTAGE,
    MIN_NULL_MARGIN,
    PANEL_DIGEST_SHA256,
    PAIRED_REPLICATES,
    PERMUTATION_REPETITIONS,
    PERMUTATION_SEEDS,
    TOTAL_TRAININGS,
    TRAININGS_PER_BLOCK,
    TRAININGS_PER_CELL,
    build_qualification_checks,
    fresh_seeds_disjoint_from_prior,
    qualification_verdict,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

BLOCKS = ("A", "B")
EXPECTED_TRAIN_SIZE = int(PAIR_COUNT * 0.70)
EXPECTED_VALIDATION_SIZE = int(PAIR_COUNT * 0.15)
EXPECTED_TEST_SIZE = PAIR_COUNT - EXPECTED_TRAIN_SIZE - EXPECTED_VALIDATION_SIZE


def _seeds_for_block(block: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    block = str(block)
    if block == "A":
        return BLOCK_A_DATASET_SEEDS, BLOCK_A_MODEL_SEEDS
    if block == "B":
        return BLOCK_B_DATASET_SEEDS, BLOCK_B_MODEL_SEEDS
    raise ValueError(f"undeclared Phase 2A-U2 block {block!r}")


def load_frozen_panel() -> tuple[dict[str, Any], ...]:
    from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256 as COMMITTED_DIGEST

    if COMMITTED_DIGEST != PANEL_DIGEST_SHA256:
        raise RuntimeError("Phase 2A-U2 panel digest drift")
    if len(CANDIDATES) != CANDIDATE_COUNT:
        raise RuntimeError("Phase 2A-U2 panel size drift")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_frozen_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-U2 candidate index out of range")
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
            f"Phase 2A-U2 candidate {candidate_index} failed classical revalidation: {checks}"
        )
    return sbox, {
        "source_seed": int(candidate["source_seed"]),
        "fingerprint": str(candidate["fingerprint"]),
    }


def expected_cell_keys() -> tuple[tuple[str, int], ...]:
    return tuple((block, int(difference)) for block in BLOCKS for difference in DIFFERENCES)


def _cell_spec(block: str, input_difference: int) -> tuple[str, int]:
    block = str(block)
    difference = int(input_difference)
    _seeds_for_block(block)
    if difference not in DIFFERENCES:
        raise ValueError(f"undeclared Phase 2A-U2 difference {difference:#x}")
    return block, difference


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_cell(block: str, input_difference: int) -> dict[str, Any]:
    """Run one frozen 48-training U2 block/difference cell."""

    block, input_difference = _cell_spec(block, input_difference)
    if not fresh_seeds_disjoint_from_prior():
        raise RuntimeError("Phase 2A-U2 neural seed registry overlaps prior frozen registries")
    dataset_seeds, model_seeds = _seeds_for_block(block)
    keys = ROUND_KEYS[: DEPTH + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(CANDIDATE_COUNT):
        sbox, classical = _verify_candidate(candidate_index)
        cipher = ToySPN(sbox, keys)
        if cipher.rounds != DEPTH:
            raise RuntimeError(f"expected {DEPTH} ToySPN rounds, got {cipher.rounds}")
        for replicate, (dataset_seed, model_seed) in enumerate(zip(dataset_seeds, model_seeds)):
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=input_difference,
                seed=int(dataset_seed),
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            if (
                len(train_samples) != EXPECTED_TRAIN_SIZE
                or len(validation_samples) != EXPECTED_VALIDATION_SIZE
                or len(test_samples) != EXPECTED_TEST_SIZE
            ):
                raise RuntimeError("Phase 2A-U2 dataset split-size drift")
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
        raise RuntimeError("Phase 2A-U2 cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2au2_oracle_cell",
        "block": block,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
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
    if not blocks or any(len(row) != CANDIDATE_COUNT for row in blocks):
        raise ValueError("Phase 2A-U2 blocks must be non-empty and panel-width")
    return [
        float(sum(float(row[index]) for row in blocks) / len(blocks))
        for index in range(CANDIDATE_COUNT)
    ]


def _top2(scores: Sequence[float]) -> tuple[int, int]:
    ranked = sorted(range(len(scores)), key=lambda index: (-float(scores[index]), index))
    return int(ranked[0]), int(ranked[1])


def _verify_run_shape(run: dict[str, Any]) -> None:
    train_size = int(run.get("train_size", -1))
    validation_size = int(run.get("validation_size", -1))
    test_size = int(run.get("test_size", -1))
    if train_size != EXPECTED_TRAIN_SIZE:
        raise ValueError("Phase 2A-U2 train-size provenance mismatch")
    if validation_size != EXPECTED_VALIDATION_SIZE:
        raise ValueError("Phase 2A-U2 validation-size provenance mismatch")
    if test_size != EXPECTED_TEST_SIZE:
        raise ValueError("Phase 2A-U2 test-size provenance mismatch")
    if train_size + validation_size + test_size != PAIR_COUNT:
        raise ValueError("Phase 2A-U2 split total does not match frozen pair count")


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate four U2 cells and apply the frozen qualification rule."""

    expected_keys = expected_cell_keys()
    if len(results) != len(expected_keys):
        raise ValueError("Phase 2A-U2 aggregation requires exactly four cell results")

    panel = load_frozen_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    source_seeds = tuple(int(candidate["source_seed"]) for candidate in panel)
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    deterministic_receipts = True

    for item in results:
        key = (str(item["block"]), int(item["input_difference"]))
        if key in cells or key not in expected_keys:
            raise ValueError(f"invalid or duplicate Phase 2A-U2 cell {key!r}")
        if int(item.get("schema_version", -1)) != 1:
            raise ValueError("Phase 2A-U2 schema-version drift")
        if str(item.get("experiment", "")) != "phase2au2_oracle_cell":
            raise ValueError("Phase 2A-U2 experiment identity mismatch")
        if str(item.get("architecture", "")) != ARCHITECTURE or int(item.get("depth", -1)) != DEPTH:
            raise ValueError("Phase 2A-U2 neural regime drift")
        if int(item.get("pair_count", -1)) != PAIR_COUNT:
            raise ValueError("Phase 2A-U2 pair-count provenance mismatch")
        if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
            raise ValueError("Phase 2A-U2 panel digest mismatch")
        expected_receipt = hashlib.sha256(_canonical_without_receipt(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        if bool(item.get("neural_evolutionary_pressure", True)):
            raise ValueError("Phase 2A-U2 forbids neural evolutionary pressure")
        cells[key] = item

    if tuple(sorted(cells)) != tuple(sorted(expected_keys)):
        raise ValueError("Phase 2A-U2 cell set does not match frozen design")

    total_trainings = 0
    block_training_counts = {block: 0 for block in BLOCKS}
    values: dict[tuple[str, int, int], list[float | None]] = {}
    null_values: dict[tuple[str, int, int], list[float | None]] = {}

    for (block, difference), item in cells.items():
        dataset_seeds, model_seeds = _seeds_for_block(block)
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-U2 cell must contain exactly 48 trainings")
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < CANDIDATE_COUNT or not 0 <= replicate < PAIRED_REPLICATES:
                raise ValueError("Phase 2A-U2 candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-U2 candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-U2 training fingerprint mismatch")
            if int(run["source_seed"]) != source_seeds[candidate_index]:
                raise ValueError("Phase 2A-U2 source-seed provenance mismatch")
            if int(run["dataset_seed"]) != dataset_seeds[replicate]:
                raise ValueError("Phase 2A-U2 dataset seed mismatch")
            if int(run["model_seed"]) != model_seeds[replicate]:
                raise ValueError("Phase 2A-U2 model seed mismatch")
            _verify_run_shape(run)
            block_key = (block, difference, replicate)
            row = values.setdefault(block_key, [None] * CANDIDATE_COUNT)
            null_row = null_values.setdefault(block_key, [None] * CANDIDATE_COUNT)
            if row[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-U2 candidate inside blocked row")
            row[candidate_index] = float(run["neural_advantage"])
            null_row[candidate_index] = float(run["null_advantage"])
            total_trainings += 1
            block_training_counts[block] += 1

    panel_revalidated = True
    try:
        for candidate_index in range(CANDIDATE_COUNT):
            _verify_candidate(candidate_index)
    except Exception:
        panel_revalidated = False

    summaries: dict[str, dict[str, Any]] = {}
    scores_by_block: dict[str, list[float]] = {}
    signals: dict[str, bool] = {}

    for block in BLOCKS:
        rows: list[list[float]] = []
        null_rows: list[list[float]] = []
        for difference in DIFFERENCES:
            for replicate in range(PAIRED_REPLICATES):
                raw = values[(block, int(difference), replicate)]
                raw_null = null_values[(block, int(difference), replicate)]
                if any(value is None for value in raw) or any(value is None for value in raw_null):
                    raise ValueError("Phase 2A-U2 incomplete blocked data")
                rows.append([float(value) for value in raw if value is not None])
                null_rows.append([float(value) for value in raw_null if value is not None])
        scores = _candidate_means(rows)
        null_scores = _candidate_means(null_rows)
        variance, p_value = blocked_heterogeneity_p(
            rows,
            repetitions=PERMUTATION_REPETITIONS,
            seed=PERMUTATION_SEEDS[block],
        )
        score_range = float(max(scores) - min(scores))
        mean_advantage = float(sum(scores) / len(scores))
        signal = any(
            score >= MIN_CANDIDATE_ADVANTAGE and (score - null_score) >= MIN_NULL_MARGIN
            for score, null_score in zip(scores, null_scores)
        )
        scores_by_block[block] = scores
        signals[block] = bool(signal)
        summaries[block] = {
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "mean_neural_advantage": mean_advantage,
            "heterogeneity_variance": float(variance),
            "heterogeneity_permutation_p": float(p_value),
            "candidate_score_range": score_range,
            "signal_condition": bool(signal),
            "rank_order": list(sorted(range(CANDIDATE_COUNT), key=lambda i: (-scores[i], i))),
            "training_count_exact": block_training_counts[block] == TRAININGS_PER_BLOCK,
        }

    spearman = spearman_correlation(scores_by_block["A"], scores_by_block["B"])
    top2_a = set(_top2(scores_by_block["A"]))
    top2_b = set(_top2(scores_by_block["B"]))
    top2_overlap = len(top2_a & top2_b)
    absolute_differences = [
        abs(float(a) - float(b)) for a, b in zip(scores_by_block["A"], scores_by_block["B"])
    ]
    mad = float(sum(absolute_differences) / len(absolute_differences))

    fresh_seed_disjoint = fresh_seeds_disjoint_from_prior()
    prerequisites = (
        total_trainings == TOTAL_TRAININGS
        and panel_revalidated
        and deterministic_receipts
        and signals["A"]
        and signals["B"]
        and fresh_seed_disjoint
    )
    checks = build_qualification_checks(
        block_a_p=summaries["A"]["heterogeneity_permutation_p"],
        block_b_p=summaries["B"]["heterogeneity_permutation_p"],
        block_a_range=summaries["A"]["candidate_score_range"],
        block_b_range=summaries["B"]["candidate_score_range"],
        spearman=spearman,
        top2_overlap=top2_overlap,
        cross_block_mad=mad,
    )
    verdict = qualification_verdict(prerequisites, checks)

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2au2_oracle_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "expected_split_sizes": {
            "train": EXPECTED_TRAIN_SIZE,
            "validation": EXPECTED_VALIDATION_SIZE,
            "test": EXPECTED_TEST_SIZE,
        },
        "total_trainings": total_trainings,
        "training_count_exact": total_trainings == TOTAL_TRAININGS,
        "panel_revalidated": panel_revalidated,
        "deterministic_receipts": deterministic_receipts,
        "fresh_seed_registry_exact_and_disjoint": fresh_seed_disjoint,
        "signal_both_blocks": bool(signals["A"] and signals["B"]),
        "prerequisites_pass": prerequisites,
        "neural_evolutionary_pressure": False,
        "block_summaries": summaries,
        "cross_block": {
            "spearman": float(spearman),
            "top2_overlap": int(top2_overlap),
            "absolute_candidate_score_differences": absolute_differences,
            "mean_absolute_candidate_score_difference": mad,
        },
        "qualification_checks": checks,
        "verdict": verdict,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
