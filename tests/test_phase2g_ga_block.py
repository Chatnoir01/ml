"""RED contract for held-out-blind Phase 2G GA/B1 block integration.

Synthetic only. Locks that checkpoint scores can affect shortlist/survival only
through the already-qualified Phase-2G B1 ordering, while C stays audit-only.
"""

from __future__ import annotations

import random

from adversarial_sbox.phase2g_ga_block import apply_phase2g_selection_boundary


def test_control_arm_is_classical_and_never_scores() -> None:
    calls: list[tuple[int, ...]] = []

    def score(candidate):
        calls.append(tuple(candidate))
        return 0.0

    ordered = apply_phase2g_selection_boundary(
        candidates=("c0", "c1", "c2"),
        arm="C",
        selection_enabled=False,
        classical_order=lambda items: list(items),
        b1_group=lambda items, cutoff: (1, 3),
        score_candidate=score,
        cutoff=2,
        shuffle_rng=None,
    )
    assert ordered == ["c0", "c1", "c2"]
    assert calls == []


def test_adaptive_arm_scores_only_complete_b1_boundary_and_reorders_lower_first() -> None:
    scores = {"c1": 0.30, "c2": 0.10}
    calls: list[str] = []

    def score(candidate):
        calls.append(candidate)
        return scores[candidate]

    ordered = apply_phase2g_selection_boundary(
        candidates=("c0", "c1", "c2", "c3"),
        arm="A",
        selection_enabled=True,
        classical_order=lambda items: list(items),
        b1_group=lambda items, cutoff: (1, 3),
        score_candidate=score,
        cutoff=2,
        shuffle_rng=None,
    )
    assert ordered == ["c0", "c2", "c1", "c3"]
    assert calls == ["c1", "c2"]


def test_shuffled_arm_uses_persistent_rng_only_inside_same_b1_group() -> None:
    scores = {"c1": 0.10, "c2": 0.20, "c3": 0.30}
    rng = random.Random(12345)
    ordered = apply_phase2g_selection_boundary(
        candidates=("c0", "c1", "c2", "c3", "c4"),
        arm="S",
        selection_enabled=True,
        classical_order=lambda items: list(items),
        b1_group=lambda items, cutoff: (1, 4),
        score_candidate=lambda candidate: scores[candidate],
        cutoff=3,
        shuffle_rng=rng,
    )
    assert ordered[0] == "c0"
    assert ordered[-1] == "c4"
    assert set(ordered[1:4]) == {"c1", "c2", "c3"}


def test_neural_selection_fails_closed_if_disabled_for_non_control_arm() -> None:
    try:
        apply_phase2g_selection_boundary(
            candidates=("c0", "c1"),
            arm="A",
            selection_enabled=False,
            classical_order=lambda items: list(items),
            b1_group=lambda items, cutoff: (0, 2),
            score_candidate=lambda candidate: 0.0,
            cutoff=1,
            shuffle_rng=None,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("A must fail closed when neural selection is disabled")
