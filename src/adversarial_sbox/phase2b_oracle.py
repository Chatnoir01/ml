"""Frozen Phase-2B fitness Oracle scorer.

This module exposes only the U2-Block-A fitness scorer. Held-out Block V lives in
``phase2b_validation`` and is deliberately not imported here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from .cryptoshield import is_bijective, validate_sbox
from .datasets import generate_balanced_pairs, split_dataset
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2b import (
    ARCHITECTURE,
    DEPTH,
    DIFFERENCES,
    FITNESS_DATASET_SEEDS,
    FITNESS_MODEL_SEEDS,
    ORACLE_TRAININGS_PER_SCORE,
    PAIR_COUNT,
    SPLIT_SIZES,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

SBox = tuple[int, ...]


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def score_candidate_with_frozen_regime(
    sbox: Sequence[int],
    *,
    dataset_seeds: Sequence[int],
    model_seeds: Sequence[int],
    purpose: str,
) -> dict[str, Any]:
    """Score one bijective S-box with exactly the frozen 16-training regime."""

    frozen = validate_sbox(sbox)
    if not is_bijective(frozen):
        raise ValueError("Phase 2B Oracle requires a bijective 8x8 S-Box")
    if len(dataset_seeds) != 8 or len(model_seeds) != 8:
        raise ValueError("Phase 2B Oracle requires exactly eight paired neural seeds")
    if len(set(int(v) for v in dataset_seeds)) != 8 or len(set(int(v) for v in model_seeds)) != 8:
        raise ValueError("Phase 2B Oracle seed block contains duplicates")
    if purpose not in {"fitness", "validation"}:
        raise ValueError(f"unsupported Phase 2B Oracle purpose {purpose!r}")

    keys = ROUND_KEYS[: DEPTH + 1]
    cipher = ToySPN(frozen, keys)
    if cipher.rounds != DEPTH:
        raise RuntimeError("Phase 2B Oracle ToySPN depth drift")

    runs: list[dict[str, Any]] = []
    for difference in DIFFERENCES:
        for replicate, (dataset_seed, model_seed) in enumerate(zip(dataset_seeds, model_seeds)):
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=int(difference),
                seed=int(dataset_seed),
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            sizes = (len(train_samples), len(validation_samples), len(test_samples))
            if sizes != SPLIT_SIZES:
                raise RuntimeError(f"Phase 2B Oracle split-size drift: {sizes} != {SPLIT_SIZES}")
            endpoint = _train_byte_tanh_mlp(
                train_samples=train_samples,
                validation_samples=validation_samples,
                test_samples=test_samples,
                model_seed=int(model_seed),
            )
            runs.append(
                {
                    "difference": int(difference),
                    "replicate": int(replicate),
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": sizes[0],
                    "validation_size": sizes[1],
                    "test_size": sizes[2],
                    **endpoint,
                }
            )

    if len(runs) != ORACLE_TRAININGS_PER_SCORE:
        raise RuntimeError("Phase 2B Oracle training-count drift")

    neural_advantage = float(sum(float(run["neural_advantage"]) for run in runs) / len(runs))
    null_advantage = float(sum(float(run["null_advantage"]) for run in runs) / len(runs))
    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2b_candidate_oracle_score",
        "purpose": purpose,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "split_sizes": list(SPLIT_SIZES),
        "fingerprint": fingerprint_sbox(frozen),
        "training_count": len(runs),
        "neural_advantage": neural_advantage,
        "null_advantage": null_advantage,
        "runs": runs,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload


def score_fitness_candidate(sbox: Sequence[int]) -> dict[str, Any]:
    """Score one candidate using exactly the qualified U2 Block-A fitness seeds."""

    return score_candidate_with_frozen_regime(
        sbox,
        dataset_seeds=FITNESS_DATASET_SEEDS,
        model_seeds=FITNESS_MODEL_SEEDS,
        purpose="fitness",
    )
