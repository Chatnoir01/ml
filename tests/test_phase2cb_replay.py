from __future__ import annotations

import random

import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase2cb_replay import (
    FrozenScoreCacheMiss,
    FrozenScoreReplayCache,
    FrozenScoreSequenceMismatch,
    instrumented_cutoff_order,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _candidate(left: int, right: int) -> tuple[int, ...]:
    values = list(range(256))
    values[left], values[right] = values[right], values[left]
    return tuple(values)


def _metrics(tag: str) -> ClassicalMetrics:
    return ClassicalMetrics(
        nonlinearity=100,
        differential_uniformity=8,
        max_linear_correlation=64,
        sac_score=0.5,
        algebraic_degree=7,
        fingerprint=tag,
    )


def _receipt(candidate: tuple[int, ...], score: float, role: str = "selection") -> dict:
    return {
        "fingerprint": fingerprint_sbox(candidate),
        "neural_advantage": score,
        "role": role,
    }


def test_frozen_cache_rejects_unknown_required_fingerprint() -> None:
    first = _candidate(0, 1)
    unknown = _candidate(0, 2)
    cache = FrozenScoreReplayCache([_receipt(first, 0.4)], budget=1)

    with pytest.raises(FrozenScoreCacheMiss):
        cache.score(unknown)


def test_frozen_cache_rejects_selection_sequence_drift() -> None:
    first = _candidate(0, 1)
    second = _candidate(0, 2)
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.4), _receipt(second, 0.3)],
        budget=2,
    )

    with pytest.raises(FrozenScoreSequenceMismatch):
        cache.score(second)


def test_frozen_cache_reuse_costs_no_extra_budget() -> None:
    first = _candidate(0, 1)
    second = _candidate(0, 2)
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.4), _receipt(second, 0.3)],
        budget=2,
    )

    assert cache.score(first) == pytest.approx(0.4)
    assert cache.remaining == 1
    assert cache.score(first) == pytest.approx(0.4)
    assert cache.remaining == 1
    assert cache.score(second) == pytest.approx(0.3)
    assert cache.remaining == 0


def test_oracle_instrumentation_records_exact_membership_flip() -> None:
    classical_first = _candidate(0, 1)
    oracle_first = tuple(range(256))
    # With equal metrics, the historical base order uses candidate tuple as the
    # final deterministic reverse-sort key, so classical_first comes first.
    metrics = {
        classical_first: _metrics("a"),
        oracle_first: _metrics("b"),
    }
    cache = FrozenScoreReplayCache(
        [
            _receipt(classical_first, 0.9),
            _receipt(oracle_first, 0.1),
        ],
        budget=2,
    )
    legacy: list[dict] = []
    trace: list[dict] = []

    ordered = instrumented_cutoff_order(
        [classical_first, oracle_first],
        metrics=metrics,
        constraints=HardConstraints(),
        cutoff=1,
        mode="oracle",
        score_cache=cache,
        shuffle_rng=None,
        generation=3,
        stage="shortlist",
        legacy_events=legacy,
        trace_events=trace,
    )

    assert ordered[0] == oracle_first
    assert len(legacy) == 1
    assert legacy[0]["event"] == "oracle_cutoff_tie"
    assert len(trace) == 1
    event = trace[0]
    assert event["generation"] == 3
    assert event["stage"] == "shortlist"
    assert event["group_start"] == 0
    assert event["group_end"] == 2
    assert event["membership_changed"] is True
    assert event["entered"] == [fingerprint_sbox(oracle_first)]
    assert event["exited"] == [fingerprint_sbox(classical_first)]


def test_post_closure_opportunity_is_observed_but_cannot_change_order() -> None:
    first = _candidate(0, 1)
    second = tuple(range(256))
    metrics = {first: _metrics("a"), second: _metrics("b")}
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.9), _receipt(second, 0.1)],
        budget=2,
    )
    cache.close_selection()
    trace: list[dict] = []
    legacy: list[dict] = []

    ordered = instrumented_cutoff_order(
        [first, second],
        metrics=metrics,
        constraints=HardConstraints(),
        cutoff=1,
        mode="oracle",
        score_cache=cache,
        shuffle_rng=None,
        generation=9,
        stage="survival",
        legacy_events=legacy,
        trace_events=trace,
    )

    assert ordered[0] == first
    assert legacy == []
    assert trace[0]["boundary_opportunity"] is True
    assert trace[0]["observational_only"] is True
    assert trace[0]["membership_changed"] is False


def test_budget_block_closes_without_partial_group_scoring() -> None:
    first = _candidate(0, 1)
    second = tuple(range(256))
    metrics = {first: _metrics("a"), second: _metrics("b")}
    # Only one slot remains but the complete boundary group needs two new scores.
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.9), _receipt(second, 0.1)],
        budget=1,
        enforce_receipt_count=False,
    )
    legacy: list[dict] = []
    trace: list[dict] = []

    ordered = instrumented_cutoff_order(
        [first, second],
        metrics=metrics,
        constraints=HardConstraints(),
        cutoff=1,
        mode="oracle",
        score_cache=cache,
        shuffle_rng=None,
        generation=0,
        stage="shortlist",
        legacy_events=legacy,
        trace_events=trace,
    )

    assert ordered[0] == first
    assert cache.selection_closed is True
    assert legacy == [
        {
            "event": "oracle_selection_budget_closed",
            "cutoff": 1,
            "group_size": 2,
            "remaining": 1,
        }
    ]
    assert trace[0]["blocked_by_budget"] is True
    assert trace[0]["membership_changed"] is False


def test_shuffled_arm_requires_persistent_rng() -> None:
    first = _candidate(0, 1)
    second = tuple(range(256))
    metrics = {first: _metrics("a"), second: _metrics("b")}
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.9), _receipt(second, 0.1)],
        budget=2,
    )

    with pytest.raises(ValueError):
        instrumented_cutoff_order(
            [first, second],
            metrics=metrics,
            constraints=HardConstraints(),
            cutoff=1,
            mode="shuffled",
            score_cache=cache,
            shuffle_rng=None,
            generation=0,
            stage="shortlist",
            legacy_events=[],
            trace_events=[],
        )

    # Sanity: supplying one persistent RNG stream is accepted.
    cache = FrozenScoreReplayCache(
        [_receipt(first, 0.9), _receipt(second, 0.1)],
        budget=2,
    )
    instrumented_cutoff_order(
        [first, second],
        metrics=metrics,
        constraints=HardConstraints(),
        cutoff=1,
        mode="shuffled",
        score_cache=cache,
        shuffle_rng=random.Random(123),
        generation=0,
        stage="shortlist",
        legacy_events=[],
        trace_events=[],
    )
