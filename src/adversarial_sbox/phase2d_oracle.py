"""Phase 2D fitness-Block-F scorer only.

Held-out Block W is deliberately absent. The evolutionary runner may import this
module, but it must never import the separate Phase-2D validation module.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from .cryptoshield import is_bijective, validate_sbox
from .datasets import generate_balanced_pairs, split_dataset
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2d import (
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


def _canonical_without_receipt(payload: dict[str, Any]) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _score_candidate(
    sbox: Sequence[int],
    *,
    dataset_seeds: Sequence[int],
    model_seeds: Sequence[int],
    purpose: str,
) -> dict[str, Any]:
    frozen = validate_sbox(sbox)
    if not is_bijective(frozen):
        raise ValueError("Phase 2D neural scorer requires a bijective 8x8 S-Box")
    if len(dataset_seeds) != 8 or len(model_seeds) != 8:
        raise ValueError("Phase 2D neural scorer requires exactly eight paired seeds")
    if len(set(int(v) for v in dataset_seeds)) != 8 or len(set(int(v) for v in model_seeds)) != 8:
        raise ValueError("Phase 2D neural seed block contains duplicates")
    if purpose not in {"fitness", "validation"}:
        raise ValueError(f"unsupported Phase 2D neural purpose {purpose!r}")

    cipher = ToySPN(frozen, ROUND_KEYS[: DEPTH + 1])
    if cipher.rounds != DEPTH:
        raise RuntimeError("Phase 2D ToySPN depth drift")

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
                raise RuntimeError(f"Phase 2D split-size drift: {sizes} != {SPLIT_SIZES}")
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
        raise RuntimeError("Phase 2D neural training-count drift")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2d_candidate_neural_score",
        "purpose": purpose,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "split_sizes": list(SPLIT_SIZES),
        "fingerprint": fingerprint_sbox(frozen),
        "training_count": len(runs),
        "neural_advantage": float(sum(float(run["neural_advantage"]) for run in runs) / len(runs)),
        "null_advantage": float(sum(float(run["null_advantage"]) for run in runs) / len(runs)),
        "runs": runs,
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(
        _canonical_without_receipt(payload)
    ).hexdigest()
    return payload


def score_fitness_candidate(sbox: Sequence[int]) -> dict[str, Any]:
    """Score one candidate using only fresh preregistered Phase-2D Block F."""

    return _score_candidate(
        sbox,
        dataset_seeds=FITNESS_DATASET_SEEDS,
        model_seeds=FITNESS_MODEL_SEEDS,
        purpose="fitness",
    )
