"""Held-out Phase 2F terminal validation, isolated from evolutionary selection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .phase2_neural_seed_registry import complete_seed_registry_through_phase2d
from .phase2f import FITNESS_DATASET_SEEDS, FITNESS_MODEL_SEEDS
from .phase2f_oracle import _score_candidate
from .phase2f_validation_seeds import VALIDATION_DATASET_SEEDS, VALIDATION_MODEL_SEEDS


def validation_seed_gate() -> bool:
    prior = set(complete_seed_registry_through_phase2d())
    fitness = set(FITNESS_DATASET_SEEDS) | set(FITNESS_MODEL_SEEDS)
    heldout = set(VALIDATION_DATASET_SEEDS) | set(VALIDATION_MODEL_SEEDS)
    return bool(
        len(fitness) == 16
        and len(heldout) == 16
        and fitness.isdisjoint(prior)
        and heldout.isdisjoint(prior)
        and fitness.isdisjoint(heldout)
    )


def score_terminal_candidate(sbox: Sequence[int]) -> dict[str, Any]:
    """Evaluate one already-frozen terminal candidate on fresh held-out Block X."""

    if not validation_seed_gate():
        raise RuntimeError("Phase 2F held-out seed provenance gate failed")
    return _score_candidate(
        sbox,
        dataset_seeds=VALIDATION_DATASET_SEEDS,
        model_seeds=VALIDATION_MODEL_SEEDS,
        purpose="validation",
    )
