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


def _model_state_receipts(checkpoint: Mapping[str, Any]) -> dict[tuple[int, int, int, int], str] | None:
    """Compare actual trained state hashes; never arm-tagged training-receipt hashes."""
    rows = checkpoint.get("model_receipts")
    if rows is None:
        return None
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)) or len(rows) != 16:
        raise ValueError("Phase 2H requires exactly 16 original model state receipts when present")
    states: dict[tuple[int, int, int, int], str] = {}
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError("malformed Phase 2G model state receipt")
        key = (
            int(item["difference"]),
            int(item["replicate"]),
            int(item["dataset_seed"]),
            int(item["model_seed"]),
        )
        value = str(item.get("state_sha256", ""))
        if key in states or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            raise ValueError("duplicate, missing or invalid Phase 2G actual model state receipt")
        states[key] = value.lower()
    return states


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
        a_states = _model_state_receipts(ac)
        f_states = _model_state_receipts(fc)
        if (a_states is None) != (f_states is None):
            raise ValueError("asymmetric actual Phase 2G model-state evidence")
        model_comparable = a_states is not None and f_states is not None
        if model_comparable and set(a_states) != set(f_states):
            raise ValueError("Phase 2G A/F model-state input seed identity mismatch")
        model_difference_count = (
            sum(a_states[key] != f_states[key] for key in a_states)
            if model_comparable else None
        )
        model_same = (model_difference_count == 0) if model_comparable else None

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
                "model_state_sha256_differing_count": model_difference_count,
                "arm_scoped_training_receipt_sha256_used_for_comparison": False,
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
    # No first-cause ordering when an earlier actual model state is unavailable.
    earlier_model_unknown = (
        earliest_generation is not None and any(
            row["generation"] <= earliest_generation and not row["model_identity_comparable"]
            for row in rows
        )
    )
    return {
        "checkpoints": rows,
        "first_curriculum_divergence_generation": first_curriculum,
        "first_population_divergence_generation": first_population,
        "first_model_divergence_generation": first_model,
        "earliest_divergence_generation": earliest_generation,
        "earliest_divergence_signals": earliest_signals,
        "ordering_claim_available": len(earliest_signals) == 1 and not earlier_model_unknown,
        "ordering_claim": (
            f"{earliest_signals[0]}_diverges_first"
            if len(earliest_signals) == 1 and not earlier_model_unknown
            else None
        ),
        "ordering_note": (
            "actual model states unavailable at/before earliest observed divergence"
            if earlier_model_unknown
            else "checkpoint resolution cannot order signals tied at the earliest observed generation"
            if len(earliest_signals) > 1
            else None
        ),
    }
