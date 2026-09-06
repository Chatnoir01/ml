"""Evolution plumbing for frozen Phase 2B GA <- fitness-Oracle pressure.

The held-out terminal validator is intentionally absent from this module. This
runner can only access the frozen U2-Block-A fitness scorer.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Any

from .cryptoshield import improved_transparency_order, validate_sbox
from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    evaluate_classical,
    feasibility_rank,
    primary_security_key,
)
from .pareto import ITOAwareMetrics, non_dominated_sort, select_nsga2
from .phase1m import ClassicalEvaluationLedger, _initial_population, _population_digest
from .phase1o import _collect_unique_batch, _proposal_audit_digest
from .phase2_evolution_seed_registry import phase2b_evolution_seeds_are_fresh
from .phase2b import (
    CLASSICAL_BUDGET_PER_ARM_SEED,
    EVOLUTION_GENERATIONS,
    EVOLUTION_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PARENT_COUNT,
    POPULATION_SIZE,
    SHORTLIST_SIZE,
    SHUFFLE_SEED_OFFSET,
)
from .phase2b_oracle import score_fitness_candidate
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
OracleScorer = Callable[[Sequence[int]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class OracleReceipt:
    fingerprint: str
    neural_advantage: float
    payload_sha256: str
    training_count: int
    role: str


class OracleScoreLedger:
    """Cache frozen candidate scores and enforce the ex-ante 32-score cap."""

    def __init__(
        self,
        scorer: OracleScorer = score_fitness_candidate,
        *,
        budget: int = ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ) -> None:
        if budget < 1:
            raise ValueError("Oracle score budget must be positive")
        self._scorer = scorer
        self._budget = int(budget)
        self._cache: dict[SBox, OracleReceipt] = {}
        self._selection_closed = False

    @property
    def score_count(self) -> int:
        return len(self._cache)

    @property
    def training_count(self) -> int:
        return self.score_count * ORACLE_TRAININGS_PER_SCORE

    @property
    def remaining(self) -> int:
        return self._budget - self.score_count

    @property
    def selection_closed(self) -> bool:
        return self._selection_closed

    @property
    def receipts(self) -> tuple[OracleReceipt, ...]:
        return tuple(self._cache.values())

    def close_selection(self) -> None:
        self._selection_closed = True

    def can_score_complete_group(self, candidates: Sequence[SBox]) -> bool:
        if self._selection_closed:
            return False
        missing = sum(validate_sbox(candidate) not in self._cache for candidate in candidates)
        return missing <= self.remaining

    def score(self, sbox: Sequence[int], *, role: str = "selection") -> float:
        frozen = validate_sbox(sbox)
        cached = self._cache.get(frozen)
        if cached is not None:
            return cached.neural_advantage
        if self.score_count >= self._budget:
            raise RuntimeError("Phase 2B Oracle candidate-score budget exhausted")
        if role not in {"selection", "padding"}:
            raise ValueError(f"unsupported Phase 2B Oracle receipt role {role!r}")

        payload = self._scorer(frozen)
        expected_fingerprint = fingerprint_sbox(frozen)
        if str(payload.get("purpose", "")) != "fitness":
            raise RuntimeError("Phase 2B fitness scorer purpose drift")
        if str(payload.get("fingerprint", "")) != expected_fingerprint:
            raise RuntimeError("Phase 2B fitness scorer fingerprint mismatch")
        if int(payload.get("training_count", -1)) != ORACLE_TRAININGS_PER_SCORE:
            raise RuntimeError("Phase 2B fitness scorer training-count drift")
        score = float(payload.get("neural_advantage", float("nan")))
        if not math.isfinite(score):
            raise RuntimeError("Phase 2B fitness scorer returned non-finite score")
        payload_sha = str(payload.get("scientific_payload_sha256", ""))
        if not payload_sha:
            raise RuntimeError("Phase 2B fitness scorer receipt missing")

        self._cache[frozen] = OracleReceipt(
            fingerprint=expected_fingerprint,
            neural_advantage=score,
            payload_sha256=payload_sha,
            training_count=ORACLE_TRAININGS_PER_SCORE,
            role=role,
        )
        return score

    def pad_to_exact_budget(
        self,
        candidates: Iterable[SBox],
        *,
        terminal: SBox,
    ) -> None:
        """Consume unused score slots after terminal freeze without affecting evolution."""

        terminal = validate_sbox(terminal)
        frozen_candidates = {validate_sbox(candidate) for candidate in candidates}
        frozen_candidates.discard(terminal)
        ordered = sorted(frozen_candidates, key=fingerprint_sbox)
        for candidate in ordered:
            if self.score_count >= self._budget:
                break
            if candidate in self._cache:
                continue
            self.score(candidate, role="padding")
        if self.score_count != self._budget:
            raise RuntimeError("insufficient distinct audit-padding candidates for exact Oracle budget")
        if self.training_count != FITNESS_TRAININGS_PER_ARM_SEED:
            raise RuntimeError("Phase 2B exact fitness training budget drift")


def make_shuffled_control_rng(seed: int) -> random.Random:
    """Return the single preregistered shuffled-control RNG stream for one seed."""

    return random.Random(int(seed) + SHUFFLE_SEED_OFFSET)


def _base_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
) -> list[SBox]:
    """Exact Phase-1O historical order before any neural tie-break intervention."""

    return sorted(
        candidates,
        key=lambda candidate: (
            feasibility_rank(metrics[candidate], constraints),
            candidate,
        ),
        reverse=True,
    )


def cutoff_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    cutoff: int,
    mode: str,
    oracle: OracleScoreLedger,
    shuffle_rng: random.Random | None,
    audit_events: list[dict[str, Any]] | None = None,
) -> list[SBox]:
    """Order one selection pool, allowing neural pressure only at the cutoff tie.

    The underlying order is byte-for-byte equivalent in semantics to Phase 1O's
    historical feasibility ranking. Neural information may replace only the final
    within-group ordering for one exact protected-key group that straddles the
    requested cutoff; it can never move a candidate across protected keys.
    """

    if mode not in {"control", "oracle", "shuffled"}:
        raise ValueError(f"unsupported Phase 2B arm mode {mode!r}")
    if mode == "shuffled" and shuffle_rng is None:
        raise ValueError("Phase 2B shuffled arm requires one persistent RNG stream")
    if not 1 <= int(cutoff) <= len(candidates):
        raise ValueError("Phase 2B cutoff outside candidate pool")
    base = _base_order(candidates, metrics=metrics, constraints=constraints)
    if oracle.selection_closed:
        return base

    boundary_key = primary_security_key(metrics[base[cutoff - 1]], constraints)
    indices = [
        index
        for index, candidate in enumerate(base)
        if primary_security_key(metrics[candidate], constraints) == boundary_key
    ]
    start, end = min(indices), max(indices) + 1
    if not (start < cutoff < end):
        return base

    group = base[start:end]
    if not oracle.can_score_complete_group(group):
        oracle.close_selection()
        if audit_events is not None:
            audit_events.append(
                {
                    "event": "oracle_selection_budget_closed",
                    "cutoff": int(cutoff),
                    "group_size": len(group),
                    "remaining": oracle.remaining,
                }
            )
        return base

    scored = [(candidate, oracle.score(candidate, role="selection")) for candidate in group]
    if mode == "oracle":
        reordered = [candidate for candidate, _score in sorted(scored, key=lambda item: item[1])]
        assigned = {fingerprint_sbox(candidate): score for candidate, score in scored}
    elif mode == "shuffled":
        scores = [score for _candidate, score in scored]
        assert shuffle_rng is not None
        shuffle_rng.shuffle(scores)
        assigned_pairs = list(zip([candidate for candidate, _score in scored], scores))
        assigned_pairs.sort(key=lambda item: item[1])
        reordered = [candidate for candidate, _score in assigned_pairs]
        assigned = {fingerprint_sbox(candidate): score for candidate, score in assigned_pairs}
    else:
        # Control still pays the exact same kind of score receipt at an eligible
        # boundary, but preserves historical Phase-1O ordering exactly.
        reordered = list(group)
        assigned = {fingerprint_sbox(candidate): score for candidate, score in scored}

    if audit_events is not None:
        audit_events.append(
            {
                "event": "oracle_cutoff_tie",
                "mode": mode,
                "cutoff": int(cutoff),
                "protected_key": list(boundary_key),
                "fingerprints": [fingerprint_sbox(candidate) for candidate in group],
                "assigned_scores": assigned,
            }
        )
    return [*base[:start], *reordered, *base[end:]]


def _metrics_payload(metrics: ClassicalMetrics) -> dict[str, Any]:
    return {
        "nonlinearity": int(metrics.nonlinearity),
        "differential_uniformity": int(metrics.differential_uniformity),
        "max_linear_correlation": int(metrics.max_linear_correlation),
        "sac_score": float(metrics.sac_score),
        "algebraic_degree": int(metrics.algebraic_degree),
        "fingerprint": str(metrics.fingerprint),
    }


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_arm(
    *,
    seed: int,
    mode: str,
    scorer: OracleScorer = score_fitness_candidate,
) -> dict[str, Any]:
    """Run one frozen C/O/S arm. Calling this with the real scorer performs neural work."""

    if int(seed) not in EVOLUTION_SEEDS:
        raise ValueError(f"seed {seed} is not a frozen Phase 2B evolution seed")
    if not phase2b_evolution_seeds_are_fresh(EVOLUTION_SEEDS):
        raise RuntimeError("Phase 2B evolution seed provenance gate failed")
    if mode not in {"control", "oracle", "shuffled"}:
        raise ValueError(f"unsupported Phase 2B arm mode {mode!r}")

    constraints = HardConstraints()
    initial = _initial_population(int(seed))
    initial_digest = _population_digest(initial)
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET_PER_ARM_SEED)
    oracle = OracleScoreLedger(scorer)
    shuffle_rng = make_shuffled_control_rng(int(seed)) if mode == "shuffled" else None
    rng = random.Random(int(seed))
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    proposal_audit = []
    oracle_events: list[dict[str, Any]] = []

    for candidate in population:
        ledger.evaluate(candidate)

    def with_ito(candidate: SBox) -> ITOAwareMetrics:
        cached = ito_cache.get(candidate)
        if cached is None:
            cached = ITOAwareMetrics.from_classical(
                ledger.evaluate(candidate),
                improved_transparency_order_value=improved_transparency_order(candidate),
            )
            ito_cache[candidate] = cached
        return cached

    for _generation in range(EVOLUTION_GENERATIONS):
        ranked = cutoff_order(
            population,
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=SHORTLIST_SIZE,
            mode=mode,
            oracle=oracle,
            shuffle_rng=shuffle_rng,
            audit_events=oracle_events,
        )
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_metrics = tuple(with_ito(candidate) for candidate in shortlist)
        parent_indices = select_nsga2(shortlist_metrics, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in parent_indices)
        proposals, audit = _collect_unique_batch(parents, rng, seen_ever=seen_ever)
        proposal_audit.extend(audit)
        for proposal in proposals:
            ledger.evaluate(proposal)
        population = cutoff_order(
            [*population, *proposals],
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=POPULATION_SIZE,
            mode=mode,
            oracle=oracle,
            shuffle_rng=shuffle_rng,
            audit_events=oracle_events,
        )[:POPULATION_SIZE]

    if ledger.evaluations != CLASSICAL_BUDGET_PER_ARM_SEED:
        raise RuntimeError("Phase 2B classical budget drift")

    # Preserve the confirmed Phase-1O terminal rule: shortlist -> ITO-aware
    # non-dominated front -> best feasibility-ranked member. Oracle pressure may
    # affect shortlist membership only through an eligible exact-key boundary.
    final_ranked = cutoff_order(
        population,
        metrics=ledger.cache,
        constraints=constraints,
        cutoff=SHORTLIST_SIZE,
        mode=mode,
        oracle=oracle,
        shuffle_rng=shuffle_rng,
        audit_events=oracle_events,
    )
    final_shortlist = tuple(final_ranked[:SHORTLIST_SIZE])
    final_ito = tuple(with_ito(candidate) for candidate in final_shortlist)
    front_indices = non_dominated_sort(final_ito)[0]
    terminal_front = tuple(final_shortlist[index] for index in front_indices)
    terminal = max(
        terminal_front,
        key=lambda candidate: (
            feasibility_rank(ledger.cache[candidate], constraints),
            candidate,
        ),
    )
    terminal_metrics = ledger.cache[terminal]

    # Terminal is frozen before audit-only compute padding.
    oracle.pad_to_exact_budget(ledger.cache.keys(), terminal=terminal)

    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2B",
        "seed": int(seed),
        "arm": mode,
        "initial_population_digest_sha256": initial_digest,
        "terminal_sbox": list(terminal),
        "terminal_fingerprint": fingerprint_sbox(terminal),
        "terminal_classical": _metrics_payload(terminal_metrics),
        "classical_evaluations": ledger.evaluations,
        "oracle_candidate_scores": oracle.score_count,
        "oracle_fitness_trainings": oracle.training_count,
        "oracle_selection_closed": oracle.selection_closed,
        "oracle_receipts": [
            {
                "fingerprint": receipt.fingerprint,
                "neural_advantage": receipt.neural_advantage,
                "payload_sha256": receipt.payload_sha256,
                "training_count": receipt.training_count,
                "role": receipt.role,
            }
            for receipt in oracle.receipts
        ],
        "oracle_events": oracle_events,
        "proposal_audit_sha256": _proposal_audit_digest(proposal_audit),
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload
