"""Deterministic A/F checkpoint divergence timeline for Phase 2H."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .phase2g import CHECKPOINT_GENERATIONS


def _set(raw: object, *, label: str) -> set[str] | None:
    """Missing evidence is unknown, never equivalent to another missing set."""
    if raw is None:
        return None
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError(f"invalid {label} fingerprint evidence")
    if not raw:
        return None
    if any(not isinstance(value, str) or not value for value in raw):
        raise ValueError(f"invalid {label} fingerprint entry")
    if len(set(raw)) != len(raw):
        raise ValueError(f"duplicate {label} fingerprint")
    return set(raw)


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return float(len(left & right) / len(union)) if union else 1.0


def _model_identity(checkpoint: Mapping[str, Any]) -> str | None:
    value = checkpoint.get("model_sha256")
    if value is None:
        value = checkpoint.get("training_receipt_sha256")
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("invalid checkpoint model identity")
    return value


def build_divergence_timeline(
    adaptive: Mapping[str, Any], fixed: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare only frozen checkpoint identities shared by A and F."""

    def index(raw: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
        cps = raw.get("checkpoints", ())
        if not isinstance(cps, Sequence) or isinstance(cps, (str, bytes, bytearray)):
            raise ValueError("checkpoint evidence unavailable")
        out: dict[int, Mapping[str, Any]] = {}
        for row in cps:
            if not isinstance(row, Mapping):
                raise ValueError("malformed checkpoint evidence")
            try:
                generation = int(row.get("generation", -1))
            except (ValueError, TypeError) as exc:
                raise ValueError("invalid checkpoint generation") from exc
            if generation in out:
                raise ValueError("duplicate checkpoint generation")
            if generation not in CHECKPOINT_GENERATIONS:
                raise ValueError("unexpected checkpoint generation")
            out[generation] = row
        if set(out) != set(CHECKPOINT_GENERATIONS):
            raise ValueError("incomplete checkpoint evidence")
        return out

    a, f = index(adaptive), index(fixed)
    rows: list[dict[str, Any]] = []
    first_curriculum = first_population = first_model = None

    for generation in CHECKPOINT_GENERATIONS:
        ac, fc = a[generation], f[generation]
        a_curr = _set(ac.get("curriculum_fingerprints"), label="curriculum")
        f_curr = _set(fc.get("curriculum_fingerprints"), label="curriculum")
        a_pop = _set(ac.get("population_after_fingerprints"), label="population")
        f_pop = _set(fc.get("population_after_fingerprints"), label="population")
        curriculum_comparable = a_curr is not None and f_curr is not None
        population_comparable = a_pop is not None and f_pop is not None
        curriculum_same = (a_curr == f_curr) if curriculum_comparable else None
        population_same = (a_pop == f_pop) if population_comparable else None
        a_model = _model_identity(ac)
        f_model = _model_identity(fc)
        model_comparable = a_model is not None and f_model is not None
        model_same = (a_model == f_model) if model_comparable else None

        if curriculum_same is False and first_curriculum is None:
            first_curriculum = int(generation)
        if population_same is False and first_population is None:
            first_population = int(generation)
        if model_same is False and first_model is None:
            first_model = int(generation)

        rows.append(
            {
                "generation": int(generation),
                "curriculum_identity_comparable": curriculum_comparable,
                "curriculum_same": curriculum_same,
                "curriculum_jaccard": _jaccard(a_curr, f_curr) if curriculum_comparable else None,
                "population_identity_comparable": population_comparable,
                "population_after_same": population_same,
                "population_after_jaccard": _jaccard(a_pop, f_pop) if population_comparable else None,
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
    missing_before_first = (
        earliest_generation is not None
        and any(
            row["generation"] <= earliest_generation
            and not (
                row["curriculum_identity_comparable"]
                and row["population_identity_comparable"]
                and row["model_identity_comparable"]
            )
            for row in rows
        )
    )
    ordering_available = len(earliest_signals) == 1 and not missing_before_first
    return {
        "checkpoints": rows,
        "first_curriculum_divergence_generation": first_curriculum,
        "first_population_divergence_generation": first_population,
        "first_model_divergence_generation": first_model,
        "earliest_divergence_generation": earliest_generation,
        "earliest_divergence_signals": earliest_signals,
        "ordering_unresolved_due_to_missing_evidence": bool(missing_before_first),
        "ordering_claim_available": ordering_available,
        "ordering_claim": (
            f"{earliest_signals[0]}_diverges_first"
            if ordering_available
            else None
        ),
        "ordering_note": (
            "missing checkpoint identity evidence prevents a complete ordering claim"
            if missing_before_first
            else "checkpoint resolution cannot order signals tied at the earliest observed generation"
            if len(earliest_signals) > 1
            else None
        ),
    }
