"""Deterministic post-H aggregate for preregistered Phase 2G.

This module performs no evolution, neural training, candidate scoring, or held-out
access. It consumes only already-receipted 36-cell arm results, an intact terminal
freeze, and an intact held-out-H validation payload, then applies the exact frozen
support rule and emits a canonical aggregate receipt.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    CHECKPOINT_TRAININGS_PER_CELL,
    EVOLUTION_SEEDS,
    SUPPORT_CHECKS,
    TOTAL_CHECKPOINT_TRAININGS,
    TOTAL_HELDOUT_TRAININGS,
    TOTAL_SCIENTIFIC_TRAININGS,
    phase2g_verdict,
)
from .phase2g_terminal_freeze import heldout_h_authorized
from .phase2g_validation import HELDOUT_TRAININGS_PER_TERMINAL

CELL_COUNT = len(ARMS) * len(EVOLUTION_SEEDS)
CLASSICAL_EVALUATIONS_PER_CELL = 340
TERMINAL_SELECTION_RULE = "historical_classical_only"


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


def _verify_payload_sha(raw: Mapping[str, Any], field: str) -> str:
    stored = str(raw.get(field, ""))
    if not _is_hex64(stored):
        raise ValueError(f"Phase-2G {field} is missing or invalid")
    clean = {key: value for key, value in raw.items() if key != field}
    if _sha256(clean) != stored:
        raise ValueError(f"Phase-2G {field} integrity failure")
    return stored


def _expected_keys() -> tuple[tuple[int, str], ...]:
    return tuple((int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ARMS)


def _checkpoint_curriculum_digests(raw: Mapping[str, Any]) -> dict[int, str]:
    checkpoints = raw.get("checkpoints")
    if not isinstance(checkpoints, Sequence) or isinstance(
        checkpoints, (str, bytes, bytearray)
    ):
        raise ValueError("Phase-2G arm checkpoints must be a sequence")
    if len(checkpoints) != len(CHECKPOINT_GENERATIONS):
        raise ValueError("Phase-2G arm result must contain four checkpoint receipts")

    indexed: dict[int, str] = {}
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, Mapping):
            raise ValueError("Phase-2G checkpoint receipt must be a mapping")
        generation = int(checkpoint.get("generation", -1))
        if generation not in CHECKPOINT_GENERATIONS or generation in indexed:
            raise ValueError("Phase-2G checkpoint generation drift")
        if int(checkpoint.get("training_count", -1)) != 16:
            raise ValueError("Phase-2G checkpoint training-count drift")
        training_receipt = str(checkpoint.get("training_receipt_sha256", ""))
        if not _is_hex64(training_receipt):
            raise ValueError("Phase-2G checkpoint training receipt is invalid")
        curriculum_digest = str(checkpoint.get("curriculum_digest_sha256", ""))
        if not _is_hex64(curriculum_digest):
            raise ValueError("Phase-2G checkpoint curriculum digest is invalid")
        indexed[generation] = curriculum_digest

    if tuple(sorted(indexed)) != tuple(sorted(CHECKPOINT_GENERATIONS)):
        raise ValueError("Phase-2G checkpoint set drift")
    return indexed


def _index_arm_results(
    arm_results: Sequence[Mapping[str, Any]],
    terminal_freeze: Mapping[str, Any],
) -> dict[tuple[int, str], Mapping[str, Any]]:
    if len(arm_results) != CELL_COUNT:
        raise ValueError("Phase-2G aggregate requires exactly 36 arm results")
    if not heldout_h_authorized(terminal_freeze):
        raise ValueError("Phase-2G aggregate requires an intact terminal freeze")

    frozen_terminals = terminal_freeze.get("terminals")
    if not isinstance(frozen_terminals, Sequence) or isinstance(
        frozen_terminals, (str, bytes, bytearray)
    ):
        raise ValueError("Phase-2G terminal freeze is malformed")
    frozen_by_key = {
        (int(item["seed"]), str(item["arm"])): item
        for item in frozen_terminals
        if isinstance(item, Mapping)
    }
    if set(frozen_by_key) != set(_expected_keys()):
        raise ValueError("Phase-2G terminal freeze cell set drift")

    indexed: dict[tuple[int, str], Mapping[str, Any]] = {}
    for raw in arm_results:
        if not isinstance(raw, Mapping):
            raise ValueError("Phase-2G arm result must be a mapping")
        if str(raw.get("phase", "")) != "2G":
            raise ValueError("Phase-2G aggregate received a non-2G arm result")
        key = (int(raw.get("seed", -1)), str(raw.get("arm", "")))
        if key not in set(_expected_keys()) or key in indexed:
            raise ValueError("Phase-2G aggregate arm identity drift")
        if int(raw.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
            raise ValueError("Phase-2G arm classical budget drift")
        if int(raw.get("checkpoint_trainings", -1)) != CHECKPOINT_TRAININGS_PER_CELL:
            raise ValueError("Phase-2G arm checkpoint-training budget drift")
        if bool(raw.get("heldout_accessed", True)):
            raise ValueError("Phase-2G pre-H arm result accessed held-out data")
        if str(raw.get("terminal_selection_rule", "")) != TERMINAL_SELECTION_RULE:
            raise ValueError("Phase-2G terminal selection-rule drift")
        scientific_receipt = _verify_payload_sha(raw, "scientific_payload_sha256")
        _checkpoint_curriculum_digests(raw)

        frozen = frozen_by_key[key]
        if str(frozen.get("scientific_payload_sha256", "")) != scientific_receipt:
            raise ValueError("Phase-2G arm result is not bound to terminal freeze")
        if str(frozen.get("terminal_fingerprint", "")) != str(
            raw.get("terminal_fingerprint", "")
        ):
            raise ValueError("Phase-2G terminal fingerprint linkage failure")
        indexed[key] = raw

    if set(indexed) != set(_expected_keys()):
        raise ValueError("Phase-2G aggregate arm set is incomplete")

    # The exact initial canonical curriculum must match across all four arms.
    for seed in EVOLUTION_SEEDS:
        checkpoint_zero = {
            _checkpoint_curriculum_digests(indexed[(int(seed), arm)])[0]
            for arm in ARMS
        }
        if len(checkpoint_zero) != 1:
            raise ValueError("Phase-2G matched arms checkpoint-0 curriculum drift")
        fixed_digests = _checkpoint_curriculum_digests(indexed[(int(seed), "F")])
        if any(value != fixed_digests[0] for value in fixed_digests.values()):
            raise ValueError("Phase-2G F curriculum must remain the exact initial curriculum")

    return indexed


def _index_validation(
    terminal_freeze: Mapping[str, Any],
    heldout_validation: Mapping[str, Any],
) -> dict[tuple[int, str], Mapping[str, Any]]:
    if not isinstance(heldout_validation, Mapping):
        raise ValueError("Phase-2G held-out validation must be a mapping")
    if int(heldout_validation.get("schema_version", -1)) != 1:
        raise ValueError("Phase-2G held-out validation schema drift")
    if str(heldout_validation.get("phase", "")) != "2G-heldout-H-validation":
        raise ValueError("Phase-2G held-out validation phase drift")
    if str(heldout_validation.get("terminal_freeze_sha256", "")) != str(
        terminal_freeze.get("terminal_freeze_sha256", "")
    ):
        raise ValueError("Phase-2G validation is not bound to terminal freeze")
    if int(heldout_validation.get("cell_count", -1)) != CELL_COUNT:
        raise ValueError("Phase-2G held-out validation cell-count drift")
    if int(heldout_validation.get("heldout_training_count", -1)) != TOTAL_HELDOUT_TRAININGS:
        raise ValueError("Phase-2G held-out training budget drift")
    if not bool(heldout_validation.get("heldout_accessed", False)):
        raise ValueError("Phase-2G held-out validation access receipt is missing")
    _verify_payload_sha(heldout_validation, "validation_sha256")

    terminals = terminal_freeze.get("terminals")
    frozen_by_key = {
        (int(item["seed"]), str(item["arm"])): item
        for item in terminals
        if isinstance(item, Mapping)
    }
    records = heldout_validation.get("records")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes, bytearray)):
        raise ValueError("Phase-2G held-out validation records are malformed")
    if len(records) != CELL_COUNT:
        raise ValueError("Phase-2G held-out validation requires 36 records")

    indexed: dict[tuple[int, str], Mapping[str, Any]] = {}
    expected = _expected_keys()
    for expected_key, record in zip(expected, records):
        if not isinstance(record, Mapping):
            raise ValueError("Phase-2G held-out record must be a mapping")
        key = (int(record.get("seed", -1)), str(record.get("arm", "")))
        if key != expected_key or key in indexed:
            raise ValueError("Phase-2G held-out record order/identity drift")
        if int(record.get("training_count", -1)) != HELDOUT_TRAININGS_PER_TERMINAL:
            raise ValueError("Phase-2G held-out record training-count drift")
        advantage = float(record.get("neural_advantage", float("nan")))
        if not math.isfinite(advantage) or advantage < 0.0:
            raise ValueError("Phase-2G held-out neural advantage is invalid")
        if not _is_hex64(record.get("scientific_payload_sha256", "")):
            raise ValueError("Phase-2G held-out score receipt is invalid")
        if str(record.get("terminal_fingerprint", "")) != str(
            frozen_by_key[key].get("terminal_fingerprint", "")
        ):
            raise ValueError("Phase-2G held-out terminal linkage failure")
        indexed[key] = record

    if set(indexed) != set(expected):
        raise ValueError("Phase-2G held-out validation set is incomplete")
    return indexed


def _fully_scored_b1_events(raw: Mapping[str, Any]) -> dict[tuple[int, str, tuple[str, ...]], tuple[str, ...]]:
    events = raw.get("selection_events", ())
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
        raise ValueError("Phase-2G selection events must be a sequence")
    out: dict[tuple[int, str, tuple[str, ...]], tuple[str, ...]] = {}
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("Phase-2G selection event must be a mapping")
        if not bool(event.get("neural_selection_enabled", False)):
            continue
        if not bool(event.get("boundary_opportunity", False)):
            continue
        group_raw = event.get("b1_group", ())
        if not isinstance(group_raw, Sequence) or isinstance(
            group_raw, (str, bytes, bytearray)
        ):
            continue
        group = tuple(str(value) for value in group_raw)
        if not group or len(set(group)) != len(group):
            continue
        if int(event.get("scored_candidate_count", -1)) != len(group):
            continue
        scores_raw = event.get("assigned_scores")
        if not isinstance(scores_raw, Mapping) or set(str(key) for key in scores_raw) != set(group):
            continue
        scores: dict[str, float] = {}
        valid = True
        for fingerprint in group:
            try:
                score = float(scores_raw[fingerprint])
            except (TypeError, ValueError, KeyError):
                valid = False
                break
            if not math.isfinite(score):
                valid = False
                break
            scores[fingerprint] = score
        if not valid:
            continue
        ordering = tuple(sorted(group, key=lambda fp: (scores[fp], fp)))
        key = (
            int(event.get("generation", -1)),
            str(event.get("stage", "")),
            tuple(sorted(group)),
        )
        out[key] = ordering
    return out


def _adaptation_activity(
    indexed: Mapping[tuple[int, str], Mapping[str, Any]],
) -> dict[str, Any]:
    curriculum_changed_seeds: list[int] = []
    ordering_changed_seeds: list[int] = []

    for seed in EVOLUTION_SEEDS:
        frozen_seed = int(seed)
        adaptive_checkpoints = _checkpoint_curriculum_digests(indexed[(frozen_seed, "A")])
        initial_curriculum = adaptive_checkpoints[0]
        if any(
            adaptive_checkpoints[generation] != initial_curriculum
            for generation in CHECKPOINT_GENERATIONS
            if generation != 0
        ):
            curriculum_changed_seeds.append(frozen_seed)

        adaptive_events = _fully_scored_b1_events(indexed[(frozen_seed, "A")])
        fixed_events = _fully_scored_b1_events(indexed[(frozen_seed, "F")])
        shared = set(adaptive_events) & set(fixed_events)
        if any(adaptive_events[key] != fixed_events[key] for key in shared):
            ordering_changed_seeds.append(frozen_seed)

    curriculum_count = len(curriculum_changed_seeds)
    ordering_count = len(ordering_changed_seeds)
    passes = curriculum_count >= 6 and ordering_count >= 6
    return {
        "curriculum_changed_seed_count": curriculum_count,
        "curriculum_changed_seeds": curriculum_changed_seeds,
        "score_ordering_changed_seed_count": ordering_count,
        "score_ordering_changed_seeds": ordering_changed_seeds,
        "passes": bool(passes),
    }


def _mechanism_activity(
    indexed: Mapping[tuple[int, str], Mapping[str, Any]],
) -> dict[str, Any]:
    active: list[int] = []
    for seed in EVOLUTION_SEEDS:
        frozen_seed = int(seed)
        events = indexed[(frozen_seed, "A")].get("selection_events", ())
        if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
            raise ValueError("Phase-2G A selection events are malformed")
        seed_active = False
        for event in events:
            if not isinstance(event, Mapping):
                raise ValueError("Phase-2G A selection event must be a mapping")
            entered = event.get("score_caused_entered", ())
            if (
                bool(event.get("neural_selection_enabled", False))
                and bool(event.get("boundary_opportunity", False))
                and bool(event.get("cross_protected_key_membership_change", False))
                and isinstance(entered, Sequence)
                and not isinstance(entered, (str, bytes, bytearray))
                and len(entered) > 0
            ):
                seed_active = True
                break
        if seed_active:
            active.append(frozen_seed)
    return {
        "cross_key_seed_count": len(active),
        "cross_key_seeds": active,
        "passes": bool(len(active) >= 6),
    }


def _exact_one_sided_sign_p(adaptive: Sequence[float], fixed: Sequence[float]) -> float:
    wins = sum(a < f for a, f in zip(adaptive, fixed))
    losses = sum(a > f for a, f in zip(adaptive, fixed))
    n = int(wins + losses)
    if n == 0:
        return 1.0
    numerator = sum(math.comb(n, k) for k in range(int(wins), n + 1))
    return float(numerator / (2**n))


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("Phase-2G aggregate mean requires non-empty values")
    return float(sum(float(value) for value in values) / len(values))


def _heldout_comparisons(
    validation: Mapping[tuple[int, str], Mapping[str, Any]],
) -> dict[str, Any]:
    adaptive = [float(validation[(int(seed), "A")]["neural_advantage"]) for seed in EVOLUTION_SEEDS]
    fixed = [float(validation[(int(seed), "F")]["neural_advantage"]) for seed in EVOLUTION_SEEDS]
    shuffled = [float(validation[(int(seed), "S")]["neural_advantage"]) for seed in EVOLUTION_SEEDS]
    control = [float(validation[(int(seed), "C")]["neural_advantage"]) for seed in EVOLUTION_SEEDS]

    wins_fixed = sum(a < f for a, f in zip(adaptive, fixed))
    wins_shuffled = sum(a < s for a, s in zip(adaptive, shuffled))
    wins_control = sum(a < c for a, c in zip(adaptive, control))
    mean_adaptive = _mean(adaptive)
    mean_fixed = _mean(fixed)
    mean_shuffled = _mean(shuffled)
    mean_control = _mean(control)
    mean_fixed_minus_adaptive = _mean([f - a for a, f in zip(adaptive, fixed)])

    return {
        "wins_vs_fixed": int(wins_fixed),
        "sign_test_vs_fixed_p": _exact_one_sided_sign_p(adaptive, fixed),
        "mean_fixed_minus_adaptive": mean_fixed_minus_adaptive,
        "wins_vs_shuffled": int(wins_shuffled),
        "wins_vs_control": int(wins_control),
        "mean_adaptive": mean_adaptive,
        "mean_fixed": mean_fixed,
        "mean_shuffled": mean_shuffled,
        "mean_control": mean_control,
    }


def _classical_non_degradation(terminal_freeze: Mapping[str, Any]) -> dict[str, Any]:
    terminals = terminal_freeze.get("terminals")
    if not isinstance(terminals, Sequence) or isinstance(
        terminals, (str, bytes, bytearray)
    ):
        raise ValueError("Phase-2G terminal freeze is malformed")
    indexed = {
        (int(item["seed"]), str(item["arm"])): item
        for item in terminals
        if isinstance(item, Mapping)
    }
    passing: list[int] = []
    per_seed: dict[str, bool] = {}
    for seed in EVOLUTION_SEEDS:
        frozen_seed = int(seed)
        adaptive = indexed[(frozen_seed, "A")]["terminal_classical"]
        control = indexed[(frozen_seed, "C")]["terminal_classical"]
        passes = bool(
            int(bool(adaptive["admissible"])) >= int(bool(control["admissible"]))
            and int(adaptive["nonlinearity"]) >= int(control["nonlinearity"])
            and int(adaptive["differential_uniformity"])
            <= int(control["differential_uniformity"])
            and int(adaptive["max_abs_lat"]) <= int(control["max_abs_lat"])
            and int(adaptive["algebraic_degree"]) >= int(control["algebraic_degree"])
        )
        per_seed[str(frozen_seed)] = passes
        if passes:
            passing.append(frozen_seed)
    return {
        "passing_seed_count": len(passing),
        "passing_seeds": passing,
        "per_seed": per_seed,
        "passes": bool(len(passing) == len(EVOLUTION_SEEDS)),
    }


def aggregate_phase2g_results(
    *,
    arm_results: Sequence[Mapping[str, Any]],
    terminal_freeze: Mapping[str, Any],
    heldout_validation: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the exact preregistered Phase-2G aggregate support rule.

    Input order of ``arm_results`` is intentionally irrelevant. All output lists
    are emitted in the frozen seed/arm order, making repeated aggregation byte
    deterministic for identical scientific receipts.
    """

    indexed = _index_arm_results(arm_results, terminal_freeze)
    validation = _index_validation(terminal_freeze, heldout_validation)
    adaptation = _adaptation_activity(indexed)
    mechanism = _mechanism_activity(indexed)
    heldout = _heldout_comparisons(validation)
    classical = _classical_non_degradation(terminal_freeze)

    checks = {
        "adaptation_activity": bool(adaptation["passes"]),
        "mechanism_activity": bool(mechanism["passes"]),
        "wins_vs_fixed": bool(heldout["wins_vs_fixed"] >= 8),
        "sign_test_vs_fixed": bool(heldout["sign_test_vs_fixed_p"] < 0.05),
        "effect_size_vs_fixed": bool(heldout["mean_fixed_minus_adaptive"] >= 0.02),
        "classical_non_degradation": bool(classical["passes"]),
        "wins_vs_shuffled": bool(heldout["wins_vs_shuffled"] >= 6),
        "mean_vs_shuffled": bool(heldout["mean_adaptive"] < heldout["mean_shuffled"]),
        "wins_vs_control": bool(heldout["wins_vs_control"] >= 6),
        "mean_vs_control": bool(heldout["mean_adaptive"] < heldout["mean_control"]),
    }
    if tuple(checks.keys()) != SUPPORT_CHECKS:
        raise RuntimeError("Phase-2G aggregate support-check ordering drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2G-aggregate",
        "terminal_freeze_sha256": str(terminal_freeze["terminal_freeze_sha256"]),
        "validation_sha256": str(heldout_validation["validation_sha256"]),
        "cell_count": CELL_COUNT,
        "evolution_seeds": [int(seed) for seed in EVOLUTION_SEEDS],
        "arms": list(ARMS),
        "checkpoint_training_count": TOTAL_CHECKPOINT_TRAININGS,
        "heldout_training_count": TOTAL_HELDOUT_TRAININGS,
        "total_training_count": TOTAL_SCIENTIFIC_TRAININGS,
        "adaptation_activity": adaptation,
        "mechanism_activity": mechanism,
        "heldout_comparisons": heldout,
        "classical_non_degradation": classical,
        "support_checks": checks,
        "verdict": phase2g_verdict(True, checks),
    }
    payload["aggregate_sha256"] = _sha256(payload)
    return payload
