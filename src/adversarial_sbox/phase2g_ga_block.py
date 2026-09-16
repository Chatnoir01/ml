"""Held-out-blind Phase 2G GA/B1 selection adapter.

This small adapter is intentionally geometry-agnostic: the real GA supplies its
historical classical order and exact B1 boundary finder. The adapter only controls
whether checkpoint scores may act and, for S, shuffles score assignment inside
that same complete boundary. It performs no training and imports no held-out H.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import random
from typing import Any

from .phase2g import ARMS


def apply_phase2g_selection_boundary(
    *,
    candidates: Sequence[Any],
    arm: str,
    selection_enabled: bool,
    classical_order: Callable[[Sequence[Any]], Sequence[Any]],
    b1_group: Callable[[Sequence[Any], int], tuple[int, int]],
    score_candidate: Callable[[Any], float],
    cutoff: int,
    shuffle_rng: random.Random | None,
) -> list[Any]:
    """Order one shortlist/survival boundary using checkpoint scores only in B1."""

    frozen_arm = str(arm)
    if frozen_arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
    if not callable(classical_order) or not callable(b1_group) or not callable(score_candidate):
        raise TypeError("Phase-2G GA block callbacks must be callable")

    ordered = list(classical_order(tuple(candidates)))
    if len(ordered) != len(candidates) or len(set(map(repr, ordered))) != len(ordered):
        raise RuntimeError("Phase-2G classical ordering must preserve the complete unique pool")
    if not 1 <= int(cutoff) <= len(ordered):
        raise ValueError("Phase-2G selection cutoff outside candidate pool")

    if frozen_arm == "C":
        if bool(selection_enabled):
            raise RuntimeError("Phase-2G control arm must remain audit-only")
        return ordered

    if not bool(selection_enabled):
        raise RuntimeError("Phase-2G neural arm cannot run with selection disabled")
    if frozen_arm == "S" and shuffle_rng is None:
        raise ValueError("Phase-2G S arm requires the persistent checkpoint shuffle RNG")

    start, end = b1_group(tuple(ordered), int(cutoff))
    start = int(start)
    end = int(end)
    if not 0 <= start < end <= len(ordered):
        raise RuntimeError("Phase-2G B1 boundary is invalid")
    if not start < int(cutoff) < end:
        # No complete B1 group crosses the selection boundary, so neural scores
        # cannot affect membership and must not be evaluated observationally.
        return ordered

    group = list(ordered[start:end])
    scored = [(candidate, float(score_candidate(candidate))) for candidate in group]

    if frozen_arm == "S":
        assert shuffle_rng is not None
        assigned = [score for _candidate, score in scored]
        shuffle_rng.shuffle(assigned)
        decorated = list(zip((candidate for candidate, _score in scored), assigned))
        decorated.sort(key=lambda pair: float(pair[1]))
        reordered = [candidate for candidate, _score in decorated]
    else:
        scored.sort(key=lambda pair: float(pair[1]))
        reordered = [candidate for candidate, _score in scored]

    return [*ordered[:start], *reordered, *ordered[end:]]
