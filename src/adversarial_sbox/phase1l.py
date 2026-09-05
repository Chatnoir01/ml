"""Frozen Phase 1L comparison helpers.

This module implements only the pre-registered classification/reporting rules.
It does not alter either search algorithm or the frozen objective directions.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .pareto import ITOAwareMetrics, dominates

CLASSIFICATIONS = ("WIN", "LOSS", "MIXED", "INCOMPARABLE")


def classify_against_control(
    control: ITOAwareMetrics,
    treatment_front: Sequence[ITOAwareMetrics],
) -> str:
    """Classify one seed using the Phase 1L pre-registered dominance rule."""

    if not treatment_front:
        raise ValueError("treatment_front must not be empty")
    treatment_dominates = any(dominates(item, control) for item in treatment_front)
    control_dominates = any(dominates(control, item) for item in treatment_front)
    if treatment_dominates and control_dominates:
        return "MIXED"
    if treatment_dominates:
        return "WIN"
    if control_dominates:
        return "LOSS"
    return "INCOMPARABLE"


def summarize_classifications(labels: Iterable[str]) -> dict[str, int]:
    """Return complete deterministic counts for all frozen label classes."""

    counts = {label: 0 for label in CLASSIFICATIONS}
    for label in labels:
        if label not in counts:
            raise ValueError(f"unknown Phase 1L classification: {label}")
        counts[label] += 1
    return counts
