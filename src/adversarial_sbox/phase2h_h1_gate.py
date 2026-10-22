"""Receipt-only H1 feasibility audit; never retrains or substitutes frozen models.

This module can establish why the Phase-2H forgetting matrix is unavailable.
SHA-256 model receipts identify past model states but cannot reconstruct weights.
Likewise checkpoint-specific score receipts are NOT a frozen cross-checkpoint
probe design. H1 remains unavailable until independently provenance-checked
model snapshots and a prospectively frozen immutable probe exist.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import string
from typing import Any

from .phase2g import CHECKPOINT_GENERATIONS

# Frozen Phase-2G checkpoint geometry: two differential inputs, eight replicates.
_EXPECTED_MODELS = {(difference, replicate) for difference in (1, 256) for replicate in range(8)}
_HEX = frozenset(string.hexdigits)
_MODEL_PAYLOAD_FIELDS = ("state_bytes", "state_bytes_b64", "serialized_model", "model_state")
_IMMUTABLE_PROBE_FIELDS = ("immutable_probe_results", "cross_checkpoint_probe_matrix")


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in _HEX for c in value)


def assess_h1_receipt_feasibility(arm: Mapping[str, Any]) -> dict[str, Any]:
    """Inventory evidence without claiming that an H1 matrix can be computed.

    The inputs are the 2G arm.json receipts only. Never use checkpoint training
    seeds to replay models, and never treat raw candidate-score receipts as
    a shared, leakage-free historical probe.
    """
    checkpoints = arm.get("checkpoints")
    if not isinstance(checkpoints, Sequence) or isinstance(checkpoints, (str, bytes, bytearray)):
        raise ValueError("H1 feasibility requires checkpoint receipts")

    indexed: dict[int, Mapping[str, Any]] = {}
    for row in checkpoints:
        if not isinstance(row, Mapping):
            raise ValueError("malformed H1 checkpoint receipt")
        try:
            generation = int(row["generation"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("invalid H1 checkpoint generation") from exc
        if generation not in CHECKPOINT_GENERATIONS or generation in indexed:
            raise ValueError("duplicate or unexpected H1 checkpoint generation")
        indexed[generation] = row
    if set(indexed) != set(CHECKPOINT_GENERATIONS):
        raise ValueError("incomplete H1 checkpoint set")

    rows = []
    for generation in CHECKPOINT_GENERATIONS:
        checkpoint = indexed[generation]
        raw_models = checkpoint.get("model_receipts")
        models_present = isinstance(raw_models, Sequence) and not isinstance(
            raw_models, (str, bytes, bytearray)
        )
        observed: set[tuple[int, int]] = set()
        valid_grid = models_present and len(raw_models) == len(_EXPECTED_MODELS)
        serialized_model_available = False
        if models_present:
            for model in raw_models:
                if not isinstance(model, Mapping):
                    valid_grid = False
                    continue
                try:
                    key = (int(model["difference"]), int(model["replicate"]))
                except (KeyError, TypeError, ValueError, OverflowError):
                    valid_grid = False
                    continue
                if key in observed or key not in _EXPECTED_MODELS:
                    valid_grid = False
                observed.add(key)
                if not _valid_sha256(model.get("state_sha256")):
                    valid_grid = False
                if any(model.get(field) not in (None, "") for field in _MODEL_PAYLOAD_FIELDS):
                    serialized_model_available = True

        valid_grid = bool(valid_grid and observed == _EXPECTED_MODELS)
        probe_results_present = any(
            checkpoint.get(field) not in (None, "", [], {}) for field in _IMMUTABLE_PROBE_FIELDS
        )
        rows.append(
            {
                "generation": int(generation),
                "model_hash_receipts": len(raw_models) if models_present else 0,
                "complete_16_model_hash_grid": valid_grid,
                "serialized_checkpoint_model_present_in_arm_receipt": serialized_model_available,
                "probe_result_field_present_in_arm_receipt": probe_results_present,
                "model_snapshot_independently_verified": False,
                "immutable_probe_independently_verified": False,
            }
        )

    all_grids = all(row["complete_16_model_hash_grid"] for row in rows)
    all_snapshots = all(
        row["serialized_checkpoint_model_present_in_arm_receipt"] for row in rows
    )
    has_probe_fields = all(row["probe_result_field_present_in_arm_receipt"] for row in rows)
    return {
        "schema_version": 1,
        "scope": "frozen_phase2g_arm_json_only",
        "checkpoint_count": len(rows),
        "hash_receipt_grid_complete": all_grids,
        "serialized_checkpoint_states_present": all_snapshots,
        "checkpoint_probe_fields_present": has_probe_fields,
        "forgetting_matrix_go": False,
        "status": "NO_GO_UNVERIFIED_MODEL_SNAPSHOTS_AND_IMMUTABLE_PROBES",
        "checkpoint_evidence": rows,
        "reason": (
            "Hash receipts and reproducible training seeds do not contain model "
            "weights or validate cross-checkpoint probe scores. An independently "
            "pinned state/probe manifest and an anti-leakage review are required; "
            "do not retrain historic checkpoints to reconstruct a frozen H1 matrix."
        ),
    }
