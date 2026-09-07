"""Frozen-score replay primitives for preregistered Phase 2C-B.

This module deliberately contains no neural scorer import and no Block-V path.
It can consume only scores already frozen inside original Phase 2B arm receipts.
Real 27-cell replay remains separately gated by research/PHASE2CB_EXECUTE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Sequence

from .cryptoshield import validate_sbox
from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    feasibility_rank,
    primary_security_key,
)
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]


class FrozenScoreReplayError(RuntimeError):
    """Base class for fail-closed Phase 2C-B frozen-score replay errors."""


class FrozenScoreCacheMiss(FrozenScoreReplayError):
    """A replay-required candidate was absent from the frozen Phase 2B receipts."""


class FrozenScoreSequenceMismatch(FrozenScoreReplayError):
    """Replay attempted first-use score consumption in a non-historical order."""


class FrozenScoreBudgetExhausted(FrozenScoreReplayError):
    """Replay attempted to consume a new score after the historical budget."""


@dataclass(frozen=True, slots=True)
class FrozenScoreReceipt:
    fingerprint: str
    neural_advantage: float
    role: str


class FrozenScoreReplayCache:
    """Read-only Phase 2B score cache with historical first-use semantics.

    The receipt payload may contain both selection and padding scores. Phase 2C-B
    may *read* every stored score, but first-use scoring during evolution must
    follow exactly the original receipt sequence restricted to selection roles.
    Padding scores are never eligible to rescue a divergent replay.
    """

    def __init__(
        self,
        receipts: Sequence[dict[str, Any] | FrozenScoreReceipt],
        *,
        budget: int,
        enforce_receipt_count: bool = True,
    ) -> None:
        if int(budget) < 1:
            raise ValueError("frozen replay score budget must be positive")
        self._budget = int(budget)
        parsed: list[FrozenScoreReceipt] = []
        for raw in receipts:
            if isinstance(raw, FrozenScoreReceipt):
                receipt = raw
            else:
                fingerprint = str(raw.get("fingerprint", ""))
                score = float(raw.get("neural_advantage", float("nan")))
                role = str(raw.get("role", ""))
                receipt = FrozenScoreReceipt(fingerprint, score, role)
            if not receipt.fingerprint:
                raise ValueError("frozen replay receipt missing fingerprint")
            if not math.isfinite(float(receipt.neural_advantage)):
                raise ValueError("frozen replay receipt contains non-finite score")
            if receipt.role not in {"selection", "padding"}:
                raise ValueError(f"unsupported frozen replay receipt role {receipt.role!r}")
            parsed.append(receipt)

        if enforce_receipt_count and len(parsed) != self._budget:
            raise ValueError(
                f"frozen replay requires exactly {self._budget} receipts; got {len(parsed)}"
            )
        fingerprints = [receipt.fingerprint for receipt in parsed]
        if len(set(fingerprints)) != len(fingerprints):
            raise ValueError("duplicate frozen replay receipt fingerprint")

        self._scores = {
            receipt.fingerprint: float(receipt.neural_advantage) for receipt in parsed
        }
        self._roles = {receipt.fingerprint: receipt.role for receipt in parsed}
        self._selection_sequence = tuple(
            receipt.fingerprint for receipt in parsed if receipt.role == "selection"
        )
        self._consumed: set[str] = set()
        self._consumed_sequence: list[str] = []
        self._selection_closed = False

    @property
    def budget(self) -> int:
        return self._budget

    @property
    def score_count(self) -> int:
        return len(self._consumed)

    @property
    def remaining(self) -> int:
        return self._budget - self.score_count

    @property
    def selection_closed(self) -> bool:
        return self._selection_closed

    @property
    def selection_consumed_fingerprints(self) -> tuple[str, ...]:
        return tuple(self._consumed_sequence)

    @property
    def expected_selection_fingerprints(self) -> tuple[str, ...]:
        return self._selection_sequence

    def close_selection(self) -> None:
        self._selection_closed = True

    def can_score_complete_group(self, candidates: Sequence[SBox]) -> bool:
        missing = 0
        seen_missing: set[str] = set()
        for candidate in candidates:
            fingerprint = fingerprint_sbox(validate_sbox(candidate))
            if fingerprint in self._consumed or fingerprint in seen_missing:
                continue
            seen_missing.add(fingerprint)
            missing += 1
        return (not self._selection_closed) and missing <= self.remaining

    def score(self, candidate: Sequence[int]) -> float:
        frozen = validate_sbox(candidate)
        fingerprint = fingerprint_sbox(frozen)
        if fingerprint in self._consumed:
            return self._scores[fingerprint]
        if self._selection_closed:
            raise FrozenScoreReplayError("selection scoring attempted after replay closure")
        if fingerprint not in self._scores:
            raise FrozenScoreCacheMiss(
                f"required frozen score missing for fingerprint {fingerprint}"
            )
        if self.score_count >= self._budget:
            raise FrozenScoreBudgetExhausted("frozen replay score budget exhausted")

        expected_index = len(self._consumed_sequence)
        if expected_index >= len(self._selection_sequence):
            raise FrozenScoreSequenceMismatch(
                "replay attempted a new first-use score after historical selection receipts ended"
            )
        expected = self._selection_sequence[expected_index]
        if fingerprint != expected:
            raise FrozenScoreSequenceMismatch(
                f"selection score sequence drift: expected {expected}, got {fingerprint}"
            )
        if self._roles[fingerprint] != "selection":
            raise FrozenScoreSequenceMismatch(
                f"padding-only fingerprint {fingerprint} cannot enter replay selection"
            )

        self._consumed.add(fingerprint)
        self._consumed_sequence.append(fingerprint)
        return self._scores[fingerprint]


def _base_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
) -> list[SBox]:
    """Exact historical Phase 2B base order before the boundary tie rule."""

    return sorted(
        candidates,
        key=lambda candidate: (
            feasibility_rank(metrics[candidate], constraints),
            candidate,
        ),
        reverse=True,
    )


def _fingerprints(candidates: Sequence[SBox]) -> list[str]:
    return [fingerprint_sbox(candidate) for candidate in candidates]


def _trace_record(
    *,
    generation: int,
    stage: str,
    cutoff: int,
    base: Sequence[SBox],
    boundary_key: tuple[float, ...],
    start: int,
    end: int,
    score_cache: FrozenScoreReplayCache,
) -> dict[str, Any]:
    selected_before = _fingerprints(base[:cutoff])
    group = base[start:end]
    return {
        "generation": int(generation),
        "stage": stage,
        "cutoff": int(cutoff),
        "boundary_opportunity": bool(start < cutoff < end),
        "protected_key": list(boundary_key),
        "group_start": int(start),
        "group_end": int(end),
        "group_fingerprints_base": _fingerprints(group),
        "group_fingerprints_after": _fingerprints(group),
        "score_budget_remaining_before": score_cache.remaining,
        "score_budget_remaining_after": score_cache.remaining,
        "selection_closed_before": score_cache.selection_closed,
        "selection_closed_after": score_cache.selection_closed,
        "score_eligible": False,
        "blocked_by_budget": False,
        "observational_only": False,
        "selected_before": selected_before,
        "selected_after": list(selected_before),
        "entered": [],
        "exited": [],
        "order_changed": False,
        "membership_changed": False,
    }


def instrumented_cutoff_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    cutoff: int,
    mode: str,
    score_cache: FrozenScoreReplayCache,
    shuffle_rng: random.Random | None,
    generation: int,
    stage: str,
    legacy_events: list[dict[str, Any]],
    trace_events: list[dict[str, Any]],
) -> list[SBox]:
    """Replay one historical Phase 2B cutoff while recording Phase 2C-B trace.

    `legacy_events` is intentionally kept Phase-2B compatible for later exact
    identity comparison. New Phase-2C-B fields live only in `trace_events`.
    """

    if mode not in {"control", "oracle", "shuffled"}:
        raise ValueError(f"unsupported Phase 2C-B arm mode {mode!r}")
    if mode == "shuffled" and shuffle_rng is None:
        raise ValueError("Phase 2C-B shuffled replay requires one persistent RNG stream")
    if stage not in {"shortlist", "survival", "terminal_shortlist"}:
        raise ValueError(f"unsupported Phase 2C-B stage {stage!r}")
    if not 1 <= int(cutoff) <= len(candidates):
        raise ValueError("Phase 2C-B cutoff outside candidate pool")

    base = _base_order(candidates, metrics=metrics, constraints=constraints)
    boundary_key = primary_security_key(metrics[base[cutoff - 1]], constraints)
    indices = [
        index
        for index, candidate in enumerate(base)
        if primary_security_key(metrics[candidate], constraints) == boundary_key
    ]
    start, end = min(indices), max(indices) + 1
    trace = _trace_record(
        generation=int(generation),
        stage=stage,
        cutoff=int(cutoff),
        base=base,
        boundary_key=boundary_key,
        start=start,
        end=end,
        score_cache=score_cache,
    )

    if not trace["boundary_opportunity"]:
        trace_events.append(trace)
        return base

    group = base[start:end]
    if score_cache.selection_closed:
        trace["observational_only"] = True
        trace_events.append(trace)
        return base

    trace["score_eligible"] = score_cache.can_score_complete_group(group)
    if not trace["score_eligible"]:
        score_cache.close_selection()
        legacy_events.append(
            {
                "event": "oracle_selection_budget_closed",
                "cutoff": int(cutoff),
                "group_size": len(group),
                "remaining": score_cache.remaining,
            }
        )
        trace["blocked_by_budget"] = True
        trace["selection_closed_after"] = True
        trace["score_budget_remaining_after"] = score_cache.remaining
        trace_events.append(trace)
        return base

    scored = [(candidate, score_cache.score(candidate)) for candidate in group]
    if mode == "oracle":
        reordered = [candidate for candidate, _score in sorted(scored, key=lambda item: item[1])]
        assigned = {
            fingerprint_sbox(candidate): score for candidate, score in scored
        }
    elif mode == "shuffled":
        scores = [score for _candidate, score in scored]
        assert shuffle_rng is not None
        shuffle_rng.shuffle(scores)
        assigned_pairs = list(zip([candidate for candidate, _score in scored], scores))
        assigned_pairs.sort(key=lambda item: item[1])
        reordered = [candidate for candidate, _score in assigned_pairs]
        assigned = {
            fingerprint_sbox(candidate): score for candidate, score in assigned_pairs
        }
    else:
        reordered = list(group)
        assigned = {
            fingerprint_sbox(candidate): score for candidate, score in scored
        }

    legacy_events.append(
        {
            "event": "oracle_cutoff_tie",
            "mode": mode,
            "cutoff": int(cutoff),
            "protected_key": list(boundary_key),
            "fingerprints": _fingerprints(group),
            "assigned_scores": assigned,
        }
    )

    ordered = [*base[:start], *reordered, *base[end:]]
    selected_before = trace["selected_before"]
    selected_after = _fingerprints(ordered[:cutoff])
    before_set = set(selected_before)
    after_set = set(selected_after)

    trace["group_fingerprints_after"] = _fingerprints(reordered)
    trace["score_budget_remaining_after"] = score_cache.remaining
    trace["selection_closed_after"] = score_cache.selection_closed
    trace["selected_after"] = selected_after
    trace["entered"] = [fp for fp in selected_after if fp not in before_set]
    trace["exited"] = [fp for fp in selected_before if fp not in after_set]
    trace["order_changed"] = reordered != list(group)
    trace["membership_changed"] = before_set != after_set
    trace_events.append(trace)
    return ordered
