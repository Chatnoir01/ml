"""Held-out Phase-2B terminal validation.

This module is intentionally separate from the evolutionary runner. Block V is
fresh, terminal-only evidence and must never be imported by selection code.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .phase2_neural_seed_registry import registry_is_disjoint
from .phase2b import VALIDATION_DATASET_SEEDS, VALIDATION_MODEL_SEEDS
from .phase2b_oracle import score_candidate_with_frozen_regime


def validation_seed_gate() -> bool:
    return registry_is_disjoint(
        VALIDATION_DATASET_SEEDS,
        VALIDATION_MODEL_SEEDS,
        before="phase2b",
    )


def score_terminal_candidate(sbox: Sequence[int]) -> dict[str, Any]:
    """Evaluate a frozen terminal candidate on held-out Block V only."""

    if not validation_seed_gate():
        raise RuntimeError("Phase 2B Block-V seeds overlap prior frozen neural registries")
    return score_candidate_with_frozen_regime(
        sbox,
        dataset_seeds=VALIDATION_DATASET_SEEDS,
        model_seeds=VALIDATION_MODEL_SEEDS,
        purpose="validation",
    )
