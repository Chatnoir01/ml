"""Held-out-blind terminal freeze for preregistered Phase 2G.

This module performs no neural training, candidate scoring, evolution, or held-out
H evaluation. It accepts only already-completed arm-cell records, verifies the
frozen pre-heldout contract, and emits a deterministic 36-cell manifest. Held-out
H may be authorized only from an intact manifest produced here.

No held-out dataset/model seed constant is imported or consumed by this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any

from .cryptoshield import validate_sbox
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    CHECKPOINT_TRAININGS_PER_CELL,
    EVOLUTION_SEEDS,
    TRAININGS_PER_CHECKPOINT,
)
from .provenance import fingerprint_sbox

CLASSICAL_EVALUATIONS_PER_CELL = 340
TERMINAL_SELECTION_RULE = "historical_classical_only"
CELL_COUNT = len(ARMS) * len(EVOLUTION_SEEDS)


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _is_hex64(value: object) -> bool:
    text = str(value)
    if len(text) != 64:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def _expected_cells() -> set[tuple[int, str]]:
    return {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS}


def _freeze_checkpoints(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError("Phase-2G checkpoints must be a sequence")
    if len(raw) != len(CHECKPOINT_GENERATIONS):
        raise ValueError("Phase-2G requires exactly four checkpoint receipts per cell")

    indexed: dict[int, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("Phase-2G checkpoint receipt must be a mapping")
        generation = int(item.get("generation", -1))
        if generation not in CHECKPOINT_GENERATIONS or generation in indexed:
            raise ValueError("invalid or duplicate Phase-2G checkpoint generation")
        if int(item.get("training_count", -1)) != TRAININGS_PER_CHECKPOINT:
            raise ValueError("Phase-2G checkpoint training-count drift")
        receipt = str(item.get("training_receipt_sha256", ""))
        if not _is_hex64(receipt):
            raise ValueError("Phase-2G checkpoint training receipt is invalid")
        indexed[generation] = {
            "generation": generation,
            "training_count": TRAININGS_PER_CHECKPOINT,
            "training_receipt_sha256": receipt,
        }

    if set(indexed) != set(CHECKPOINT_GENERATIONS):
        raise ValueError("Phase-2G checkpoint set drift")
    return [indexed[generation] for generation in CHECKPOINT_GENERATIONS]


def _freeze_cell(raw: Mapping[str, Any]) -> dict[str, Any]:
    if str(raw.get("phase", "")) != "2G":
        raise ValueError("terminal cell is not a Phase-2G record")

    seed = int(raw.get("seed", -1))
    arm = str(raw.get("arm", ""))
    if seed not in EVOLUTION_SEEDS or arm not in ARMS:
        raise ValueError("terminal cell has an unfrozen Phase-2G seed/arm")
    if int(raw.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise ValueError("Phase-2G classical evaluation budget drift")
    if int(raw.get("checkpoint_trainings", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
        raise ValueError("Phase-2G checkpoint training budget drift")
    if str(raw.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
        raise ValueError("Phase-2G terminal selection must remain classical-only")

    checkpoints = _freeze_checkpoints(raw.get("checkpoints"))
    sbox = validate_sbox(raw.get("terminal_sbox", ()))
    fingerprint = fingerprint_sbox(sbox)
    if str(raw.get("terminal_fingerprint", "")) != fingerprint:
        raise ValueError("Phase-2G terminal fingerprint mismatch")

    classical = raw.get("terminal_classical")
    if not isinstance(classical, Mapping) or not classical:
        raise ValueError("Phase-2G terminal classical metrics are missing")
    classical_payload = json.loads(json.dumps(dict(classical), sort_keys=True))

    frozen: dict[str, Any] = {
        "seed": seed,
        "arm": arm,
        "classical_evaluations": CLASSICAL_EVALUATIONS_PER_CELL,
        "checkpoint_trainings": CHECKPOINT_TRAININGS_PER_CELL,
        "checkpoints": checkpoints,
        "terminal_selection_rule": TERMINAL_SELECTION_RULE,
        "terminal_fingerprint": fingerprint,
        "terminal_sbox": list(sbox),
        "terminal_classical": classical_payload,
    }
    frozen["cell_manifest_sha256"] = _sha256(frozen)
    return frozen


def freeze_phase2g_terminals(
    arm_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate and deterministically freeze all 9-seed × 4-arm terminals.

    The function is intentionally held-out blind: the resulting payload explicitly
    records zero held-out accesses/trainings and contains no held-out score.
    """

    if len(arm_results) != CELL_COUNT:
        raise ValueError("Phase-2G terminal freeze requires exact 9-seed × 4-arm records")

    expected = _expected_cells()
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for raw in arm_results:
        if not isinstance(raw, Mapping):
            raise ValueError("Phase-2G arm result must be a mapping")
        frozen = _freeze_cell(raw)
        key = (int(frozen["seed"]), str(frozen["arm"]))
        if key not in expected or key in indexed:
            raise ValueError(f"invalid or duplicate Phase-2G terminal cell {key!r}")
        indexed[key] = frozen

    if set(indexed) != expected:
        raise ValueError("Phase-2G terminal freeze is incomplete")

    terminals = [
        indexed[(int(seed), arm)]
        for seed in EVOLUTION_SEEDS
        for arm in ARMS
    ]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G-terminal-freeze",
        "cell_count": CELL_COUNT,
        "evolution_seeds": [int(seed) for seed in EVOLUTION_SEEDS],
        "arms": list(ARMS),
        "classical_evaluations_per_cell": CLASSICAL_EVALUATIONS_PER_CELL,
        "checkpoint_generations": list(CHECKPOINT_GENERATIONS),
        "checkpoint_trainings_per_cell": CHECKPOINT_TRAININGS_PER_CELL,
        "checkpoint_training_count": CELL_COUNT * CHECKPOINT_TRAININGS_PER_CELL,
        "heldout_accessed": False,
        "heldout_training_count": 0,
        "terminal_selection_rule": TERMINAL_SELECTION_RULE,
        "terminals": terminals,
    }
    payload["terminal_freeze_sha256"] = _sha256(payload)
    return payload


def heldout_h_authorized(freeze_payload: Mapping[str, Any]) -> bool:
    """Return True only for an intact, complete pre-H terminal freeze manifest."""

    try:
        if int(freeze_payload.get("schema_version", -1)) != 1:
            return False
        if str(freeze_payload.get("phase", "")) != "2G-terminal-freeze":
            return False
        if int(freeze_payload.get("cell_count", -1)) != CELL_COUNT:
            return False
        if tuple(int(v) for v in freeze_payload.get("evolution_seeds", ())) != tuple(
            int(seed) for seed in EVOLUTION_SEEDS
        ):
            return False
        if tuple(str(v) for v in freeze_payload.get("arms", ())) != ARMS:
            return False
        if int(freeze_payload.get("classical_evaluations_per_cell", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
            return False
        if tuple(int(v) for v in freeze_payload.get("checkpoint_generations", ())) != CHECKPOINT_GENERATIONS:
            return False
        if int(freeze_payload.get("checkpoint_trainings_per_cell", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
            return False
        if int(freeze_payload.get("checkpoint_training_count", -1)) != CELL_COUNT * CHECKPOINT_TRAININGS_PER_CELL:
            return False
        if bool(freeze_payload.get("heldout_accessed", True)):
            return False
        if int(freeze_payload.get("heldout_training_count", -1)) != 0:
            return False
        if str(freeze_payload.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
            return False

        terminals = freeze_payload.get("terminals")
        if not isinstance(terminals, Sequence) or isinstance(terminals, (str, bytes, bytearray)):
            return False
        if len(terminals) != CELL_COUNT:
            return False

        seen: set[tuple[int, str]] = set()
        for item in terminals:
            if not isinstance(item, Mapping):
                return False
            key = (int(item.get("seed", -1)), str(item.get("arm", "")))
            if key not in _expected_cells() or key in seen:
                return False
            seen.add(key)
            if int(item.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
                return False
            if int(item.get("checkpoint_trainings", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
                return False
            if str(item.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
                return False
            checkpoints = _freeze_checkpoints(item.get("checkpoints"))
            if checkpoints != list(item.get("checkpoints", [])):
                return False
            sbox = validate_sbox(item.get("terminal_sbox", ()))
            if str(item.get("terminal_fingerprint", "")) != fingerprint_sbox(sbox):
                return False
            stored_cell_sha = str(item.get("cell_manifest_sha256", ""))
            if not _is_hex64(stored_cell_sha):
                return False
            clean_cell = {key_: value for key_, value in item.items() if key_ != "cell_manifest_sha256"}
            if _sha256(clean_cell) != stored_cell_sha:
                return False

        if seen != _expected_cells():
            return False
        stored = str(freeze_payload.get("terminal_freeze_sha256", ""))
        if not _is_hex64(stored):
            return False
        clean = {key: value for key, value in freeze_payload.items() if key != "terminal_freeze_sha256"}
        return _sha256(clean) == stored
    except (TypeError, ValueError, KeyError):
        return False
