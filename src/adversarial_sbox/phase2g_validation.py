"""Post-freeze held-out H validation for preregistered Phase 2G.

This module is deliberately dormant until a complete 36-cell terminal freeze has
passed ``heldout_h_authorized``. It performs no evolution and cannot change any
terminal. Real H seeds and the candidate-specific scorer are imported lazily only
after authorization; CI injects synthetic scorers and performs zero H training.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from .phase2g import ARMS, EVOLUTION_SEEDS
from .phase2g_terminal_freeze import heldout_h_authorized
from .provenance import fingerprint_sbox

HeldoutScorer = Callable[[Sequence[int]], Mapping[str, Any]]
HELDOUT_TRAININGS_PER_TERMINAL = 16
CELL_COUNT = len(ARMS) * len(EVOLUTION_SEEDS)
TOTAL_HELDOUT_TRAININGS = CELL_COUNT * HELDOUT_TRAININGS_PER_TERMINAL


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


def _verify_score_receipt(raw: Mapping[str, Any]) -> str:
    stored = str(raw.get("scientific_payload_sha256", ""))
    if not _is_hex64(stored):
        raise ValueError("Phase-2G held-out score receipt is missing or invalid")
    clean = {key: value for key, value in raw.items() if key != "scientific_payload_sha256"}
    if _sha256(clean) != stored:
        raise ValueError("Phase-2G held-out score receipt mismatch")
    return stored


def _default_score_terminal(candidate: Sequence[int]) -> Mapping[str, Any]:
    """Run the exact frozen candidate-specific H procedure after freeze authorization.

    Imports are local by design so merely importing this validation module does not
    expose H seed values to any pre-freeze code path.
    """

    from .phase2_neural_seed_registry import (
        complete_seed_registry_through_phase2f,
        phase2g_checkpoint_seed_values,
    )
    from .phase2f import DEPTH, DIFFERENCES, PAIR_COUNT, SPLIT_SIZES
    from .phase2f_oracle import _score_candidate
    from .phase2g_validation_seeds import HELDOUT_DATASET_SEEDS, HELDOUT_MODEL_SEEDS

    if DEPTH != 4:
        raise RuntimeError("Phase-2G held-out depth drift")
    if tuple(DIFFERENCES) != (0x00000001, 0x00000100):
        raise RuntimeError("Phase-2G held-out difference drift")
    if int(PAIR_COUNT) != 8192 or tuple(SPLIT_SIZES) != (5734, 1228, 1230):
        raise RuntimeError("Phase-2G held-out dataset geometry drift")

    h_dataset = tuple(int(v) for v in HELDOUT_DATASET_SEEDS)
    h_model = tuple(int(v) for v in HELDOUT_MODEL_SEEDS)
    if len(h_dataset) != 8 or len(set(h_dataset)) != 8:
        raise RuntimeError("Phase-2G held-out dataset seed registry drift")
    if len(h_model) != 8 or len(set(h_model)) != 8:
        raise RuntimeError("Phase-2G held-out model seed registry drift")

    heldout = set(h_dataset) | set(h_model)
    if len(heldout) != 16:
        raise RuntimeError("Phase-2G held-out dataset/model seeds overlap")
    if heldout & set(phase2g_checkpoint_seed_values()):
        raise RuntimeError("Phase-2G H overlaps checkpoint T/M/Q registry")
    if heldout & set(complete_seed_registry_through_phase2f()):
        raise RuntimeError("Phase-2G H overlaps prior Phase-2 neural registry")

    return _score_candidate(
        candidate,
        dataset_seeds=h_dataset,
        model_seeds=h_model,
        purpose="validation",
    )


def validate_frozen_terminals(
    freeze_payload: Mapping[str, Any],
    *,
    score_terminal: HeldoutScorer | None = None,
) -> dict[str, Any]:
    """Score each frozen terminal exactly once after an intact pre-H freeze.

    ``score_terminal`` is dependency-injected for synthetic qualification. When it
    is omitted, the exact preregistered H scorer is loaded lazily only after the
    freeze authorization gate succeeds.
    """

    if not isinstance(freeze_payload, Mapping) or not heldout_h_authorized(freeze_payload):
        raise ValueError("Phase-2G terminal freeze is not authorized for held-out H")

    scorer: HeldoutScorer = _default_score_terminal if score_terminal is None else score_terminal
    if not callable(scorer):
        raise TypeError("Phase-2G held-out scorer must be callable")

    terminals = freeze_payload.get("terminals")
    if not isinstance(terminals, Sequence) or isinstance(terminals, (str, bytes, bytearray)):
        raise ValueError("Phase-2G terminal freeze manifest is malformed")
    if len(terminals) != CELL_COUNT:
        raise ValueError("Phase-2G held-out validation requires exactly 36 terminals")

    expected_keys = [(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS]
    records: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    for expected_key, terminal in zip(expected_keys, terminals):
        if not isinstance(terminal, Mapping):
            raise ValueError("Phase-2G frozen terminal record must be a mapping")
        key = (int(terminal.get("seed", -1)), str(terminal.get("arm", "")))
        if key != expected_key or key in seen:
            raise ValueError("Phase-2G held-out terminal order/identity drift")
        seen.add(key)

        sbox = terminal.get("terminal_sbox", ())
        fingerprint = str(terminal.get("terminal_fingerprint", ""))
        if fingerprint_sbox(sbox) != fingerprint:
            raise ValueError("Phase-2G frozen terminal fingerprint mismatch")

        raw = scorer(sbox)
        if not isinstance(raw, Mapping):
            raise ValueError("Phase-2G held-out scorer must return a mapping")
        if str(raw.get("purpose", "")) != "validation":
            raise ValueError("Phase-2G held-out scorer purpose drift")
        if str(raw.get("fingerprint", "")) != fingerprint:
            raise ValueError("Phase-2G held-out score fingerprint mismatch")
        if int(raw.get("training_count", -1)) != HELDOUT_TRAININGS_PER_TERMINAL:
            raise ValueError("Phase-2G held-out training-count drift")
        advantage = float(raw.get("neural_advantage", float("nan")))
        if not math.isfinite(advantage) or advantage < 0.0:
            raise ValueError("Phase-2G held-out neural advantage is invalid")
        score_receipt = _verify_score_receipt(raw)

        records.append(
            {
                "seed": key[0],
                "arm": key[1],
                "terminal_fingerprint": fingerprint,
                "training_count": HELDOUT_TRAININGS_PER_TERMINAL,
                "neural_advantage": advantage,
                "scientific_payload_sha256": score_receipt,
            }
        )

    if seen != set(expected_keys) or len(records) != CELL_COUNT:
        raise ValueError("Phase-2G held-out validation cell set is incomplete")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G-heldout-H-validation",
        "terminal_freeze_sha256": str(freeze_payload["terminal_freeze_sha256"]),
        "cell_count": CELL_COUNT,
        "heldout_training_count": TOTAL_HELDOUT_TRAININGS,
        "heldout_accessed": True,
        "records": records,
    }
    payload["validation_sha256"] = _sha256(payload)
    return payload
