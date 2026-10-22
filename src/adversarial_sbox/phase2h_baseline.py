"""Conservative checkpoint-0 A/F comparability audit over frozen Phase-2G receipts.

Only declared training inputs and model-state SHA-256 hashes are compared. No
training is executed; neither matching metadata nor a digest proves identical
runtime/hardware execution. Arm-tagged aggregate training receipts are NOT
model-state identities.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from typing import Any

from .phase2g import (
    TRAINING_DATASET_BASE_SEEDS,
    TRAINING_MODEL_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from .phase2h_timeline import _model_identity

EXPECTED_MODELS = {(difference, replicate) for difference in (1, 256) for replicate in range(8)}
EXPECTED_DATASET_SEEDS = expanded_checkpoint_seed_block(TRAINING_DATASET_BASE_SEEDS, 0)
EXPECTED_MODEL_SEEDS = expanded_checkpoint_seed_block(TRAINING_MODEL_BASE_SEEDS, 0)


def _initial_checkpoint(arm: Mapping[str, Any]) -> Mapping[str, Any]:
    checkpoints = arm.get("checkpoints")
    if not isinstance(checkpoints, Sequence) or isinstance(checkpoints, (str, bytes, bytearray)):
        raise ValueError("checkpoint-0 audit requires checkpoint receipts")
    matches = [
        row for row in checkpoints
        if isinstance(row, Mapping) and row.get("generation") == 0
    ]
    if len(matches) != 1:
        raise ValueError("checkpoint-0 audit requires exactly one generation-zero receipt")
    return matches[0]


def _curriculum(checkpoint: Mapping[str, Any]) -> tuple[str, ...] | None:
    fingerprints = checkpoint.get("curriculum_fingerprints")
    digest = checkpoint.get("curriculum_digest_sha256")
    if fingerprints is None or digest is None:
        return None
    if (
        not isinstance(fingerprints, Sequence)
        or isinstance(fingerprints, (str, bytes, bytearray))
        or len(fingerprints) != 20
        or any(not isinstance(fp, str) or not fp for fp in fingerprints)
    ):
        raise ValueError("invalid checkpoint-0 curriculum fingerprints")
    items = tuple(sorted(fingerprints))
    if len(set(items)) != 20:
        raise ValueError("duplicate checkpoint-0 curriculum fingerprints")
    calculated = hashlib.sha256("\n".join(items).encode("ascii")).hexdigest()
    if not isinstance(digest, str) or calculated != digest.lower():
        raise ValueError("checkpoint-0 curriculum digest mismatch")
    return items


def _model_seed_registry(checkpoint: Mapping[str, Any]) -> dict[tuple[int, int], tuple[int, int]] | None:
    receipts = checkpoint.get("model_receipts")
    if receipts is None:
        return None
    # Validate the complete 16-model hash grid first (also rejects duplicates).
    if _model_identity(checkpoint) is None:
        return None
    registry: dict[tuple[int, int], tuple[int, int]] = {}
    for row in receipts:
        if not isinstance(row, Mapping):
            raise ValueError("invalid model receipt")
        try:
            difference = int(row["difference"])
            replicate = int(row["replicate"])
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise ValueError("invalid model identity") from exc
        if "dataset_seed" not in row or "model_seed" not in row:
            return None
        try:
            seeds = (int(row["dataset_seed"]), int(row["model_seed"]))
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("invalid model training seeds") from exc
        registry[(difference, replicate)] = seeds
    if set(registry) != EXPECTED_MODELS:
        raise ValueError("invalid checkpoint-0 model seed grid")
    return registry


def audit_checkpoint0_baseline(
    adaptive: Mapping[str, Any], fixed: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit same *declared* A/F inputs; never declare a causal explanation."""
    ac = _initial_checkpoint(adaptive)
    fc = _initial_checkpoint(fixed)
    a_curr = _curriculum(ac)
    f_curr = _curriculum(fc)
    curriculum_equal = (a_curr == f_curr) if a_curr is not None and f_curr is not None else None

    a_model = _model_identity(ac)
    f_model = _model_identity(fc)
    model_comparable = a_model is not None and f_model is not None
    mismatches = None
    by_difference: dict[str, Any] = {}
    if model_comparable:
        a = {(d, r): digest for d, r, digest in a_model}
        f = {(d, r): digest for d, r, digest in f_model}
        mismatches = sum(a[key] != f[key] for key in EXPECTED_MODELS)
        for difference in (1, 256):
            bad = [replicate for replicate in range(8)
                   if a[difference, replicate] != f[difference, replicate]]
            by_difference[str(difference)] = {
                "different_model_state_sha256_count": len(bad),
                "different_replicates": bad,
            }

    a_seeds = _model_seed_registry(ac)
    f_seeds = _model_seed_registry(fc)
    seeds_comparable = a_seeds is not None and f_seeds is not None
    seeds_equal = (a_seeds == f_seeds) if seeds_comparable else None
    seeds_match_frozen = (
        all(
            a_seeds[difference, replicate] == (
                EXPECTED_DATASET_SEEDS[replicate], EXPECTED_MODEL_SEEDS[replicate]
            ) and f_seeds[difference, replicate] == (
                EXPECTED_DATASET_SEEDS[replicate], EXPECTED_MODEL_SEEDS[replicate]
            )
            for difference, replicate in EXPECTED_MODELS
        )
        if seeds_comparable else None
    )

    # The frozen checkpoint records also carry declared aggregate seed arrays.
    # Missing arrays must not be silently treated as matching the trained models.
    def arrays_match(checkpoint: Mapping[str, Any]) -> bool | None:
        dataset = checkpoint.get("training_dataset_seeds")
        model = checkpoint.get("training_model_seeds")
        if dataset is None or model is None:
            return None
        if not isinstance(dataset, list) or not isinstance(model, list):
            raise ValueError("malformed checkpoint-0 training seed arrays")
        if len(dataset) != 8 or len(model) != 8:
            raise ValueError("incomplete checkpoint-0 training seed arrays")
        return tuple(dataset) == EXPECTED_DATASET_SEEDS and tuple(model) == EXPECTED_MODEL_SEEDS

    arrays_a, arrays_f = arrays_match(ac), arrays_match(fc)
    registry_arrays_ok = (
        arrays_a is True and arrays_f is True
        if arrays_a is not None and arrays_f is not None else None
    )
    same_declared_inputs = (
        curriculum_equal is True
        and seeds_equal is True
        and seeds_match_frozen is True
        and registry_arrays_ok is True
    )
    if curriculum_equal is False or seeds_equal is False or seeds_match_frozen is False or registry_arrays_ok is False:
        status = "DECLARED_INPUT_MISMATCH"
    elif not same_declared_inputs or not model_comparable:
        status = "INSUFFICIENT_DECLARED_INPUT_EVIDENCE"
    elif mismatches:
        status = "MATCHED_DECLARED_INPUTS_DIFFERENT_MODEL_HASHES"
    else:
        status = "MATCHED_DECLARED_INPUTS_MATCHED_MODEL_HASHES"

    return {
        "schema_version": 1,
        "scope": "checkpoint_0_frozen_receipts_only",
        "curriculum_equal_and_hash_verified": curriculum_equal,
        "model_grid_comparable": model_comparable,
        "model_state_sha256_mismatches": mismatches,
        "mismatches_by_difference": by_difference,
        "model_seed_receipts_complete": seeds_comparable,
        "declared_model_seeds_equal": seeds_equal,
        "declared_model_seeds_match_frozen": seeds_match_frozen,
        "checkpoint_seed_arrays_match_frozen": registry_arrays_ok,
        "same_declared_training_inputs": same_declared_inputs,
        "status": status,
        "causal_explanation_established": False,
        "note": (
            "The four-field input check is based on frozen declared seed and "
            "curriculum receipts. It cannot establish identical runtime/BLAS, "
            "data bytes or scientific causality. Do not retroactively rerun "
            "or reinterpret the frozen Phase-2G outcome."
        ),
    }
