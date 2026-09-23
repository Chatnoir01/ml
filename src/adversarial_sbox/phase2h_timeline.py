"""Deterministic A/F checkpoint divergence timeline for Phase 2H."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .phase2g import CHECKPOINT_GENERATIONS


def _set(raw: object) -> set[str]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        return set()
    return {str(value) for value in raw}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return float(len(left & right) / len(union)) if union else 1.0


def build_divergence_timeline(
    adaptive: Mapping[str, Any], fixed: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare only frozen checkpoint identities shared by A and F."""

    def index(raw: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
        cps = raw.get("checkpoints", ())
        if not isinstance(cps, Sequence) or isinstance(cps, (str, bytes, bytearray)):
            raise ValueError("checkpoint evidence unavailable")
        out = {
            int(row.get("generation", -1)): row
            for row in cps
            if isinstance(row, Mapping)
        }
        if set(out) != set(CHECKPOINT_GENERATIONS):
            raise ValueError("incomplete checkpoint evidence")
        return out

    a, f = index(adaptive), index(fixed)
    rows: list[dict[str, Any]] = []
    first_curriculum = first_population = first_model = None

    for generation in CHECKPOINT_GENERATIONS:
        ac, fc = a[generation], f[generation]
        a_curr = _set(ac.get("curriculum_fingerprints", ()))
        f_curr = _set(fc.get("curriculum_fingerprints", ()))
        a_pop = _set(ac.get("population_after_fingerprints", ()))
        f_pop = _set(fc.get("population_after_fingerprints", ()))
        curriculum_same = a_curr == f_curr
        population_same = a_pop == f_pop
        a_model = str(ac.get("model_sha256", ac.get("training_receipt_sha256", "")))
        f_model = str(fc.get("model_sha256", fc.get("training_receipt_sha256", "")))
        model_comparable = bool(a_model and f_model)
        model_same = (a_model == f_model) if model_comparable else None

        if not curriculum_same and first_curriculum is None:
            first_curriculum = int(generation)
        if not population_same and first_population is None:
            first_population = int(generation)
        if model_same is False and first_model is None:
            first_model = int(generation)

        rows.append(
            {
                "generation": int(generation),
                "curriculum_same": curriculum_same,
                "curriculum_jaccard": _jaccard(a_curr, f_curr),
                "population_after_same": population_same,
                "population_after_jaccard": _jaccard(a_pop, f_pop),
                "model_identity_comparable": model_comparable,
                "model_same": model_same,
            }
        )

    ordered_signals = [
        ("curriculum", first_curriculum),
        ("population", first_population),
        ("model", first_model),
    ]
    observed = [(name, generation) for name, generation in ordered_signals if generation is not None]
    earliest_generation = min((generation for _, generation in observed), default=None)
    earliest_signals = [
        name for name, generation in observed if generation == earliest_generation
    ]
    return {
        "checkpoints": rows,
        "first_curriculum_divergence_generation": first_curriculum,
        "first_population_divergence_generation": first_population,
        "first_model_divergence_generation": first_model,
        "earliest_divergence_generation": earliest_generation,
        "earliest_divergence_signals": earliest_signals,
        "ordering_claim_available": len(earliest_signals) == 1,
        "ordering_claim": (
            f"{earliest_signals[0]}_diverges_first"
            if len(earliest_signals) == 1
            else None
        ),
        "ordering_note": (
            "checkpoint resolution cannot order signals tied at the earliest observed generation"
            if len(earliest_signals) > 1
            else None
        ),
    }
