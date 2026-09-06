"""Locked neural runner and aggregate analysis for Phase 2A-U.

The runner uses only the committed fresh panel, fixed 4-round regime and frozen
seeds from the public preregistration. No neural score is exposed to evolution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import evaluate_classical
from .neural100 import PAIR_COUNT, _train_one as _train_bit_relu_mlp
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2au import (
    ARCHITECTURES,
    DATASET_SEEDS,
    MODEL_SEEDS,
    PANEL_SIZE,
    PERMUTATION_SEEDS,
    SPLIT_HALF_A,
    SPLIT_HALF_B,
    TOTAL_NEURAL_TRAININGS,
)
from .phase2au_neural import (
    CELL_SPECS,
    PERMUTATION_REPETITIONS,
    REPLICATES,
    TRAININGS_PER_CELL,
    blocked_heterogeneity_p,
    build_qualification_checks,
    consensus_scores,
    spearman_correlation,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN


def _cell_spec(architecture: str, input_difference: int) -> tuple[str, int, int]:
    target = (str(architecture), int(input_difference))
    for spec in CELL_SPECS:
        if (spec[0], spec[2]) == target:
            return spec
    raise ValueError(f"undeclared Phase 2A-U cell {target!r}")


def load_committed_panel() -> tuple[dict[str, Any], ...]:
    from .phase2au_candidates import CANDIDATES, PANEL_DIGEST_SHA256

    if len(CANDIDATES) != PANEL_SIZE:
        raise RuntimeError("Phase 2A-U committed panel size mismatch")
    if not isinstance(PANEL_DIGEST_SHA256, str) or len(PANEL_DIGEST_SHA256) != 64:
        raise RuntimeError("Phase 2A-U committed panel digest is invalid")
    return tuple(dict(candidate) for candidate in CANDIDATES)


def _verify_committed_candidate(candidate_index: int) -> tuple[tuple[int, ...], dict[str, Any]]:
    panel = load_committed_panel()
    if not 0 <= int(candidate_index) < len(panel):
        raise ValueError("Phase 2A-U candidate index out of range")
    candidate = panel[int(candidate_index)]
    sbox = tuple(int(value) for value in candidate["sbox"])
    metrics = evaluate_classical(sbox)
    checks = {
        "bijective": len(sbox) == 256 and sorted(sbox) == list(range(256)),
        "fingerprint": fingerprint_sbox(sbox) == str(candidate["fingerprint"]),
        "differential_uniformity": metrics.differential_uniformity == 8,
        "nonlinearity": metrics.nonlinearity == 100,
        "max_linear_correlation": metrics.max_linear_correlation == 56,
        "algebraic_degree": metrics.algebraic_degree == 7,
        "sac": abs(float(metrics.sac_score) - 0.5) <= 0.05,
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Phase 2A-U committed candidate {candidate_index} failed revalidation: {checks}"
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


def qualification_verdict(checks: dict[str, bool]) -> str:
    prereq_keys = (
        "training_count_exact",
        "panel_revalidated",
        "deterministic_receipts",
        "no_neural_evolutionary_pressure",
    )
    if not all(bool(checks.get(key, False)) for key in prereq_keys):
        return "phase2au_inconclusive_prerequisites"
    if all(bool(value) for value in checks.values()):
        return "phase2au_depth4_consensus_oracle_qualified"
    return "phase2au_oracle_not_qualified"


def run_cell(architecture: str, input_difference: int) -> dict[str, Any]:
    """Run one frozen 48-training Phase-2A-U cell."""

    architecture, rounds, input_difference = _cell_spec(architecture, input_difference)
    keys = ROUND_KEYS[: rounds + 1]
    runs: list[dict[str, Any]] = []

    for candidate_index in range(PANEL_SIZE):
        sbox, classical = _verify_committed_candidate(candidate_index)
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
            else:  # pragma: no cover
                raise RuntimeError(f"unsupported architecture {architecture!r}")

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
        raise RuntimeError("Phase 2A-U cell training count drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2au_depth4_oracle_qualification_cell",
        "architecture": architecture,
        "rounds": rounds,
        "input_difference": input_difference,
        "pair_count": PAIR_COUNT,
        "runs": runs,
        "neural_evolutionary_pressure": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["scientific_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def _canonical_cell_payload(item: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in item.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _candidate_means_from_blocks(blocks: Sequence[Sequence[float]]) -> list[float]:
    return [
        sum(float(block[index]) for block in blocks) / len(blocks)
        for index in range(PANEL_SIZE)
    ]


def aggregate_cells(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the four frozen cells and apply every preregistered criterion."""

    if len(results) != len(CELL_SPECS):
        raise ValueError("Phase 2A-U aggregation requires exactly four cell results")

    panel = load_committed_panel()
    fingerprints = tuple(str(candidate["fingerprint"]) for candidate in panel)
    expected_cells = set(CELL_SPECS)
    cells: dict[tuple[str, int, int], dict[str, Any]] = {}
    deterministic_receipts = True
    no_pressure = True

    for item in results:
        key = (
            str(item["architecture"]),
            int(item["rounds"]),
            int(item["input_difference"]),
        )
        if key in cells:
            raise ValueError(f"duplicate Phase 2A-U cell {key!r}")
        expected_receipt = hashlib.sha256(_canonical_cell_payload(item)).hexdigest()
        if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
            deterministic_receipts = False
        if bool(item.get("neural_evolutionary_pressure", True)):
            no_pressure = False
        cells[key] = item
    if set(cells) != expected_cells:
        raise ValueError("Phase 2A-U cell set does not match the frozen design")

    # block key = (architecture, input difference, paired replicate), width = six S-boxes.
    block_map: dict[tuple[str, int, int], list[float | None]] = {}
    null_map: dict[tuple[str, int, int], list[float | None]] = {}
    total_trainings = 0

    for key in CELL_SPECS:
        item = cells[key]
        runs = item["runs"]
        if len(runs) != TRAININGS_PER_CELL:
            raise ValueError("every Phase 2A-U cell must contain exactly 48 trainings")
        architecture, _rounds, input_difference = key
        seen: set[tuple[int, int]] = set()
        for run in runs:
            candidate_index = int(run["candidate_index"])
            replicate = int(run["replicate"])
            if not 0 <= candidate_index < PANEL_SIZE or not 0 <= replicate < REPLICATES:
                raise ValueError("Phase 2A-U candidate/replicate index out of range")
            pair = (candidate_index, replicate)
            if pair in seen:
                raise ValueError("duplicate Phase 2A-U candidate/replicate training")
            seen.add(pair)
            if str(run["fingerprint"]) != fingerprints[candidate_index]:
                raise ValueError("Phase 2A-U training fingerprint mismatch")
            if int(run["source_seed"]) != int(panel[candidate_index]["source_seed"]):
                raise ValueError("Phase 2A-U source-seed provenance mismatch")
            if int(run["dataset_seed"]) != DATASET_SEEDS[replicate]:
                raise ValueError("Phase 2A-U dataset seed mismatch")
            if int(run["model_seed"]) != MODEL_SEEDS[replicate]:
                raise ValueError("Phase 2A-U model seed mismatch")
            block_key = (architecture, input_difference, replicate)
            block = block_map.setdefault(block_key, [None] * PANEL_SIZE)
            null_block = null_map.setdefault(block_key, [None] * PANEL_SIZE)
            if block[candidate_index] is not None:
                raise ValueError("duplicate Phase 2A-U candidate inside blocked cell")
            block[candidate_index] = float(run["neural_advantage"])
            null_block[candidate_index] = float(run["null_advantage"])
            total_trainings += 1

    if total_trainings != TOTAL_NEURAL_TRAININGS:
        raise ValueError(f"expected {TOTAL_NEURAL_TRAININGS} trainings, got {total_trainings}")
    if any(any(value is None for value in block) for block in block_map.values()):
        raise ValueError("incomplete Phase 2A-U neural block")
    if any(any(value is None for value in block) for block in null_map.values()):
        raise ValueError("incomplete Phase 2A-U null block")

    architecture_summaries: dict[str, dict[str, Any]] = {}
    architecture_scores: dict[str, list[float]] = {}
    architecture_null_scores: dict[str, list[float]] = {}

    for architecture in ARCHITECTURES:
        keys = sorted(
            (key for key in block_map if key[0] == architecture),
            key=lambda key: (key[1], key[2]),
        )
        blocks = [[float(value) for value in block_map[key]] for key in keys]
        null_blocks = [[float(value) for value in null_map[key]] for key in keys]
        variance, p_value = blocked_heterogeneity_p(
            blocks,
            repetitions=PERMUTATION_REPETITIONS,
            seed=PERMUTATION_SEEDS[architecture],
        )
        scores = _candidate_means_from_blocks(blocks)
        null_scores = _candidate_means_from_blocks(null_blocks)
        score_range = max(scores) - min(scores)
        signal = any(
            score >= 0.04 and score - null_score >= 0.02
            for score, null_score in zip(scores, null_scores)
        )
        architecture_scores[architecture] = scores
        architecture_null_scores[architecture] = null_scores
        architecture_summaries[architecture] = {
            "heterogeneity_variance": variance,
            "heterogeneity_permutation_p": p_value,
            "candidate_score_range": score_range,
            "candidate_mean_advantages": scores,
            "candidate_mean_null_advantages": null_scores,
            "signal_condition": signal,
        }

    bit_scores = architecture_scores["bit_relu_mlp"]
    byte_scores = architecture_scores["byte_tanh_mlp"]
    cross_arch_spearman = spearman_correlation(bit_scores, byte_scores)
    consensus = consensus_scores(bit_scores, byte_scores)

    all_keys = sorted(block_map, key=lambda key: (key[0], key[1], key[2]))
    all_blocks = [[float(value) for value in block_map[key]] for key in all_keys]
    consensus_variance, consensus_p = blocked_heterogeneity_p(
        all_blocks,
        repetitions=PERMUTATION_REPETITIONS,
        seed=PERMUTATION_SEEDS["consensus"],
    )
    consensus_range = max(consensus) - min(consensus)

    def half_consensus(indices: tuple[int, ...]) -> list[float]:
        selected_keys = [key for key in all_keys if key[2] in indices]
        selected_blocks = [[float(value) for value in block_map[key]] for key in selected_keys]
        # Averaging all architecture/difference blocks is algebraically the same as
        # the frozen unweighted two-architecture consensus inside this fixed design.
        return _candidate_means_from_blocks(selected_blocks)

    half_a_scores = half_consensus(SPLIT_HALF_A)
    half_b_scores = half_consensus(SPLIT_HALF_B)
    split_half_spearman = spearman_correlation(half_a_scores, half_b_scores)

    panel_revalidated = True
    for candidate_index in range(PANEL_SIZE):
        _verify_committed_candidate(candidate_index)

    checks = build_qualification_checks(
        total_trainings=total_trainings,
        panel_revalidated=panel_revalidated,
        deterministic_receipts=deterministic_receipts,
        neural_evolutionary_pressure=not no_pressure,
        bit_p=architecture_summaries["bit_relu_mlp"]["heterogeneity_permutation_p"],
        byte_p=architecture_summaries["byte_tanh_mlp"]["heterogeneity_permutation_p"],
        bit_range=architecture_summaries["bit_relu_mlp"]["candidate_score_range"],
        byte_range=architecture_summaries["byte_tanh_mlp"]["candidate_score_range"],
        cross_arch_spearman=cross_arch_spearman,
        bit_signal=architecture_summaries["bit_relu_mlp"]["signal_condition"],
        byte_signal=architecture_summaries["byte_tanh_mlp"]["signal_condition"],
        consensus_p=consensus_p,
        consensus_range=consensus_range,
        split_half_spearman=split_half_spearman,
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2au_depth4_oracle_qualification_aggregate",
        "panel_digest_sha256": __import__(
            "adversarial_sbox.phase2au_candidates", fromlist=["PANEL_DIGEST_SHA256"]
        ).PANEL_DIGEST_SHA256,
        "total_trainings": total_trainings,
        "architecture_summaries": architecture_summaries,
        "cross_architecture_spearman": cross_arch_spearman,
        "consensus": {
            "candidate_scores": consensus,
            "heterogeneity_variance": consensus_variance,
            "heterogeneity_permutation_p": consensus_p,
            "candidate_score_range": consensus_range,
            "split_half_a_candidate_scores": half_a_scores,
            "split_half_b_candidate_scores": half_b_scores,
            "split_half_spearman": split_half_spearman,
        },
        "candidates": [
            {
                "candidate_index": index,
                "source_seed": int(panel[index]["source_seed"]),
                "fingerprint": fingerprints[index],
                "bit_relu_score": bit_scores[index],
                "bit_relu_null_score": architecture_null_scores["bit_relu_mlp"][index],
                "byte_tanh_score": byte_scores[index],
                "byte_tanh_null_score": architecture_null_scores["byte_tanh_mlp"][index],
                "consensus_score": consensus[index],
            }
            for index in range(PANEL_SIZE)
        ],
        "qualification_checks": checks,
        "deterministic_receipts": deterministic_receipts,
        "neural_evolutionary_pressure": False,
        "verdict": qualification_verdict(checks),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


__all__ = [
    "_cell_spec",
    "aggregate_cells",
    "load_committed_panel",
    "qualification_verdict",
    "run_cell",
]
