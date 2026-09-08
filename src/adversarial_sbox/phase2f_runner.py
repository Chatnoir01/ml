"""Evolution runner for preregistered Phase 2F minimal-band neural pressure.

This module can access only fresh fitness Block G. Held-out Block X scoring is
physically separated and must never be imported by the evolutionary runner.
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
from .phase1o import MultiHotspotProposal, _proposal_audit_digest, multihotspot_walsh_swap_proposals
from .phase2_evolution_seed_registry import phase2f_evolution_seeds_are_fresh
from .phase2f import (
    ARMS,
    CLASSICAL_BUDGET_PER_ARM_SEED,
    EVOLUTION_GENERATIONS,
    EVOLUTION_SEEDS,
    FITNESS_TRAININGS_PER_ARM_SEED,
    ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ORACLE_TRAININGS_PER_SCORE,
    PARENT_COUNT,
    POPULATION_SIZE,
    PROPOSALS_PER_GENERATION,
    PROPOSALS_PER_PARENT,
    SHORTLIST_SIZE,
    SHUFFLE_SEED_OFFSET,
    in_b1_band,
)
from .phase2f_oracle import score_fitness_candidate
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
FitnessScorer = Callable[[Sequence[int]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class Phase2FScoreReceipt:
    fingerprint: str
    neural_advantage: float
    payload_sha256: str
    training_count: int
    role: str
    score_payload: dict[str, Any]


class Phase2FScoreLedger:
    """Cache fitness scores and enforce the exact preregistered 32-score cap."""

    def __init__(
        self,
        scorer: FitnessScorer = score_fitness_candidate,
        *,
        budget: int = ORACLE_SCORE_BUDGET_PER_ARM_SEED,
    ) -> None:
        if int(budget) < 1:
            raise ValueError("Phase 2F score budget must be positive")
        self._scorer = scorer
        self._budget = int(budget)
        self._cache: dict[SBox, Phase2FScoreReceipt] = {}
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
    def receipts(self) -> tuple[Phase2FScoreReceipt, ...]:
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
            raise RuntimeError("Phase 2F candidate-score budget exhausted")
        if role not in {"selection", "padding"}:
            raise ValueError(f"unsupported Phase 2F score receipt role {role!r}")
        payload = self._scorer(frozen)
        expected_fingerprint = fingerprint_sbox(frozen)
        if str(payload.get("purpose", "")) != "fitness":
            raise RuntimeError("Phase 2F fitness scorer purpose drift")
        if str(payload.get("fingerprint", "")) != expected_fingerprint:
            raise RuntimeError("Phase 2F fitness scorer fingerprint mismatch")
        if int(payload.get("training_count", -1)) != ORACLE_TRAININGS_PER_SCORE:
            raise RuntimeError("Phase 2F fitness training-count drift")
        score = float(payload.get("neural_advantage", float("nan")))
        if not math.isfinite(score):
            raise RuntimeError("Phase 2F fitness scorer returned non-finite score")
        payload_sha = str(payload.get("scientific_payload_sha256", ""))
        if not payload_sha:
            raise RuntimeError("Phase 2F fitness score receipt missing")
        frozen_payload = json.loads(json.dumps(payload, sort_keys=True))
        self._cache[frozen] = Phase2FScoreReceipt(
            fingerprint=expected_fingerprint,
            neural_advantage=score,
            payload_sha256=payload_sha,
            training_count=ORACLE_TRAININGS_PER_SCORE,
            role=role,
            score_payload=frozen_payload,
        )
        return score

    def pad_to_exact_budget(self, candidates: Iterable[SBox], *, terminal: SBox) -> None:
        terminal = validate_sbox(terminal)
        frozen_candidates = {validate_sbox(candidate) for candidate in candidates}
        frozen_candidates.discard(terminal)
        for candidate in sorted(frozen_candidates, key=fingerprint_sbox):
            if self.score_count >= self._budget:
                break
            if candidate in self._cache:
                continue
            self.score(candidate, role="padding")
        if self.score_count != self._budget:
            raise RuntimeError("insufficient audit-padding candidates for exact Phase 2F budget")
        if self.training_count != FITNESS_TRAININGS_PER_ARM_SEED:
            raise RuntimeError("Phase 2F exact fitness training budget drift")


def make_shuffled_control_rng(seed: int) -> random.Random:
    return random.Random(int(seed) + SHUFFLE_SEED_OFFSET)


def _base_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
) -> list[SBox]:
    return sorted(
        candidates,
        key=lambda candidate: (feasibility_rank(metrics[candidate], constraints), candidate),
        reverse=True,
    )


def _fp(candidate: SBox) -> str:
    return fingerprint_sbox(candidate)


def _exact_key_boundary(
    base: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    cutoff: int,
) -> tuple[int, int, list[SBox]]:
    boundary_key = primary_security_key(metrics[base[cutoff - 1]], constraints)
    indices = [
        index
        for index, candidate in enumerate(base)
        if primary_security_key(metrics[candidate], constraints) == boundary_key
    ]
    start, end = min(indices), max(indices) + 1
    return start, end, list(base[start:end])


def _b1_contiguous_boundary(
    base: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    cutoff: int,
) -> tuple[int, int, list[SBox]]:
    center = int(cutoff) - 1
    reference = metrics[base[center]]
    left = center
    while left - 1 >= 0 and in_b1_band(metrics[base[left - 1]], reference, constraints):
        left -= 1
    right = center + 1
    while right < len(base) and in_b1_band(metrics[base[right]], reference, constraints):
        right += 1
    return left, right, list(base[left:right])


def cutoff_order(
    candidates: Sequence[SBox],
    *,
    metrics: dict[SBox, ClassicalMetrics],
    constraints: HardConstraints,
    cutoff: int,
    arm: str,
    oracle: Phase2FScoreLedger,
    shuffle_rng: random.Random | None,
    generation: int,
    stage: str,
    audit_events: list[dict[str, Any]] | None = None,
) -> list[SBox]:
    """Apply one frozen Phase-2F cutoff ordering using Block-G scores only."""

    if arm not in ARMS:
        raise ValueError(f"unsupported Phase 2F arm {arm!r}")
    if arm == "SB1" and shuffle_rng is None:
        raise ValueError("SB1 requires one persistent shuffled-score RNG")
    if stage not in {"shortlist", "survival"}:
        raise ValueError(f"unsupported Phase 2F stage {stage!r}")
    if not 1 <= int(cutoff) <= len(candidates):
        raise ValueError("Phase 2F cutoff outside candidate pool")

    base = _base_order(candidates, metrics=metrics, constraints=constraints)
    reference = base[cutoff - 1]
    reference_metrics = metrics[reference]
    boundary_key = primary_security_key(reference_metrics, constraints)

    if arm == "O0":
        start, end, group = _exact_key_boundary(
            base, metrics=metrics, constraints=constraints, cutoff=cutoff
        )
        group_kind = "exact_key"
    else:
        start, end, group = _b1_contiguous_boundary(
            base, metrics=metrics, constraints=constraints, cutoff=cutoff
        )
        group_kind = "b1_contiguous_band"

    boundary_opportunity = start < cutoff < end
    display_candidates = [_fp(candidate) for candidate in group]
    event: dict[str, Any] = {
        "event": "selection_boundary",
        "generation": int(generation),
        "stage": str(stage),
        "cutoff": int(cutoff),
        "group_kind": group_kind,
        "boundary_opportunity": bool(boundary_opportunity),
        "selection_closed_before": bool(oracle.selection_closed),
        "cutoff_reference_fingerprint": _fp(reference),
        "cutoff_reference_metrics": _metrics_payload(reference_metrics),
        "protected_key": list(boundary_key),
        "group_start": int(start),
        "group_end": int(end),
        "base_group": display_candidates,
        "eligible_protected_keys": {
            _fp(candidate): list(primary_security_key(metrics[candidate], constraints))
            for candidate in group
        },
    }

    if not boundary_opportunity:
        event.update(
            {
                "scored": False,
                "observational_only": False,
                "blocked_by_budget": False,
                "score_ordered_group": display_candidates,
                "final_group": display_candidates,
                "membership_changed": False,
                "ordering_changed": False,
                "cross_protected_key_membership_change": False,
                "score_caused_entered": [],
                "entered": [],
                "exited": [],
                "selection_closed_after": bool(oracle.selection_closed),
            }
        )
        if audit_events is not None:
            audit_events.append(event)
        return base

    before_selected = set(base[:cutoff])
    if oracle.selection_closed:
        event.update(
            {
                "scored": False,
                "observational_only": True,
                "blocked_by_budget": False,
                "score_ordered_group": display_candidates,
                "final_group": display_candidates,
                "membership_changed": False,
                "ordering_changed": False,
                "cross_protected_key_membership_change": False,
                "score_caused_entered": [],
                "entered": [],
                "exited": [],
                "selection_closed_after": True,
            }
        )
        if audit_events is not None:
            audit_events.append(event)
        return base

    if not oracle.can_score_complete_group(group):
        oracle.close_selection()
        event.update(
            {
                "event": "score_budget_closed",
                "scored": False,
                "observational_only": True,
                "blocked_by_budget": True,
                "remaining": int(oracle.remaining),
                "score_ordered_group": display_candidates,
                "final_group": display_candidates,
                "membership_changed": False,
                "ordering_changed": False,
                "cross_protected_key_membership_change": False,
                "score_caused_entered": [],
                "entered": [],
                "exited": [],
                "selection_closed_after": True,
            }
        )
        if audit_events is not None:
            audit_events.append(event)
        return base

    scored = [(candidate, oracle.score(candidate, role="selection")) for candidate in group]
    assigned: dict[SBox, float]
    if arm == "SB1":
        scores = [float(score) for _candidate, score in scored]
        assert shuffle_rng is not None
        shuffle_rng.shuffle(scores)
        assigned = {candidate: float(score) for (candidate, _real), score in zip(scored, scores)}
    else:
        assigned = {candidate: float(score) for candidate, score in scored}

    if arm == "C":
        reordered = list(group)
    else:
        reordered = sorted(group, key=lambda candidate: assigned[candidate])

    final_global = [*base[:start], *reordered, *base[end:]]
    final_selected = set(final_global[:cutoff])
    entered_candidates = final_selected - before_selected
    exited_candidates = before_selected - final_selected
    entered_fps = sorted(_fp(candidate) for candidate in entered_candidates)
    cross_key = any(
        primary_security_key(metrics[candidate], constraints) != boundary_key
        for candidate in entered_candidates
    )

    event.update(
        {
            "scored": True,
            "observational_only": False,
            "blocked_by_budget": False,
            "score_budget_remaining_after": int(oracle.remaining),
            "assigned_scores": {_fp(candidate): assigned[candidate] for candidate in group},
            "score_ordered_group": [_fp(candidate) for candidate in reordered],
            "final_group": [_fp(candidate) for candidate in reordered],
            "selected_before": sorted(_fp(candidate) for candidate in before_selected),
            "selected_after": sorted(_fp(candidate) for candidate in final_selected),
            "membership_changed": bool(final_selected != before_selected),
            "ordering_changed": bool(reordered != group),
            "cross_protected_key_membership_change": bool(cross_key),
            "score_caused_entered": entered_fps if arm != "C" else [],
            "entered": entered_fps,
            "exited": sorted(_fp(candidate) for candidate in exited_candidates),
            "selection_closed_after": bool(oracle.selection_closed),
        }
    )
    if audit_events is not None:
        audit_events.append(event)
    return final_global


def _metrics_payload(metrics: ClassicalMetrics) -> dict[str, Any]:
    return {
        "nonlinearity": int(metrics.nonlinearity),
        "differential_uniformity": int(metrics.differential_uniformity),
        "max_linear_correlation": int(metrics.max_linear_correlation),
        "sac_score": float(metrics.sac_score),
        "algebraic_degree": int(metrics.algebraic_degree),
        "fingerprint": str(metrics.fingerprint),
    }


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _collect_unique_batch_with_parents(
    parents: Sequence[SBox],
    rng: random.Random,
    *,
    seen_ever: set[SBox],
) -> tuple[list[SBox], list[MultiHotspotProposal], list[dict[str, str]]]:
    batch: list[SBox] = []
    audit: list[MultiHotspotProposal] = []
    links: list[dict[str, str]] = []
    parent_index = 0
    stalled = 0
    while len(batch) < PROPOSALS_PER_GENERATION:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(batch))
        generated = multihotspot_walsh_swap_proposals(parent, rng, count=needed)
        added = 0
        for record in generated:
            if record.sbox in seen_ever:
                continue
            seen_ever.add(record.sbox)
            batch.append(record.sbox)
            audit.append(record)
            links.append({"proposal_fingerprint": _fp(record.sbox), "parent_fingerprint": _fp(parent)})
            added += 1
            if len(batch) == PROPOSALS_PER_GENERATION:
                break
        stalled = stalled + 1 if added == 0 else 0
        if stalled > 512:
            raise RuntimeError("unable to generate globally unique Phase 2F proposals")
    return batch, audit, links


def _has_ancestor(candidate: str, ancestor: str, parent_map: dict[str, str]) -> bool:
    current = candidate
    seen: set[str] = set()
    while current in parent_map:
        if current in seen:
            raise RuntimeError("cycle in Phase 2F realized parent map")
        seen.add(current)
        current = parent_map[current]
        if current == ancestor:
            return True
    return False


def _lineage_diagnostics(
    *,
    events: Sequence[dict[str, Any]],
    generations: Sequence[dict[str, Any]],
    parent_map: dict[str, str],
    terminal_fingerprint: str,
) -> list[dict[str, Any]]:
    populations: dict[int, set[str]] = {
        int(record["generation"]): set(record["population_before"])
        for record in generations
    }
    if generations:
        populations[EVOLUTION_GENERATIONS] = set(generations[-1]["next_population"])
    results: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        entered = list(event.get("score_caused_entered", []))
        if not entered:
            continue
        generation = int(event["generation"])
        records: list[dict[str, Any]] = []
        for fingerprint in entered:
            item: dict[str, Any] = {"fingerprint": fingerprint}
            for offset in (1, 2, 5):
                target = generation + offset
                population = populations.get(target)
                if population is None:
                    item[f"direct_plus_{offset}"] = None
                    item[f"descendant_plus_{offset}"] = None
                    continue
                item[f"direct_plus_{offset}"] = fingerprint in population
                item[f"descendant_plus_{offset}"] = any(
                    candidate != fingerprint and _has_ancestor(candidate, fingerprint, parent_map)
                    for candidate in population
                )
            item["terminal_self"] = terminal_fingerprint == fingerprint
            item["terminal_descendant"] = _has_ancestor(terminal_fingerprint, fingerprint, parent_map)
            records.append(item)
        results.append(
            {
                "event_index": int(event_index),
                "generation": generation,
                "stage": str(event["stage"]),
                "entered": records,
            }
        )
    return results


def run_arm(
    *,
    seed: int,
    arm: str,
    scorer: FitnessScorer = score_fitness_candidate,
) -> dict[str, Any]:
    """Run one C/O0/B1/SB1 arm using fitness Block G only."""

    if int(seed) not in EVOLUTION_SEEDS:
        raise ValueError(f"seed {seed} is not a frozen Phase 2F evolution seed")
    if not phase2f_evolution_seeds_are_fresh(EVOLUTION_SEEDS):
        raise RuntimeError("Phase 2F evolution seed provenance gate failed")
    if arm not in ARMS:
        raise ValueError(f"unsupported Phase 2F arm {arm!r}")

    constraints = HardConstraints()
    initial = _initial_population(int(seed))
    initial_digest = _population_digest(initial)
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET_PER_ARM_SEED)
    oracle = Phase2FScoreLedger(scorer)
    shuffle_rng = make_shuffled_control_rng(int(seed)) if arm == "SB1" else None
    rng = random.Random(int(seed))
    population = list(initial)
    seen_ever = set(initial)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}
    proposal_audit: list[MultiHotspotProposal] = []
    selection_events: list[dict[str, Any]] = []
    generation_trace: list[dict[str, Any]] = []
    parent_map: dict[str, str] = {}

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

    for generation in range(EVOLUTION_GENERATIONS):
        population_before = list(population)
        ranked = cutoff_order(
            population,
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=SHORTLIST_SIZE,
            arm=arm,
            oracle=oracle,
            shuffle_rng=shuffle_rng,
            generation=generation,
            stage="shortlist",
            audit_events=selection_events,
        )
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_metrics = tuple(with_ito(candidate) for candidate in shortlist)
        parent_indices = select_nsga2(shortlist_metrics, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in parent_indices)
        proposals, audit, links = _collect_unique_batch_with_parents(parents, rng, seen_ever=seen_ever)
        proposal_audit.extend(audit)
        for link in links:
            child = link["proposal_fingerprint"]
            if child in parent_map:
                raise RuntimeError("duplicate Phase 2F proposal parent")
            parent_map[child] = link["parent_fingerprint"]
        for proposal in proposals:
            ledger.evaluate(proposal)
        next_population = cutoff_order(
            [*population, *proposals],
            metrics=ledger.cache,
            constraints=constraints,
            cutoff=POPULATION_SIZE,
            arm=arm,
            oracle=oracle,
            shuffle_rng=shuffle_rng,
            generation=generation,
            stage="survival",
            audit_events=selection_events,
        )[:POPULATION_SIZE]
        generation_trace.append(
            {
                "generation": int(generation),
                "population_before": [_fp(candidate) for candidate in population_before],
                "shortlist": [_fp(candidate) for candidate in shortlist],
                "parents": [_fp(candidate) for candidate in parents],
                "proposals": links,
                "next_population": [_fp(candidate) for candidate in next_population],
            }
        )
        population = list(next_population)

    if ledger.evaluations != CLASSICAL_BUDGET_PER_ARM_SEED:
        raise RuntimeError("Phase 2F classical budget drift")

    # Terminal selection is deliberately historical classical-only. No Block-G
    # score is consulted here, isolating trajectory pressure as preregistered.
    final_ranked = _base_order(population, metrics=ledger.cache, constraints=constraints)
    final_shortlist = tuple(final_ranked[:SHORTLIST_SIZE])
    final_ito = tuple(with_ito(candidate) for candidate in final_shortlist)
    front_indices = non_dominated_sort(final_ito)[0]
    terminal_front = tuple(final_shortlist[index] for index in front_indices)
    terminal = max(
        terminal_front,
        key=lambda candidate: feasibility_rank(ledger.cache[candidate], constraints),
    )
    terminal_metrics = ledger.cache[terminal]

    oracle.close_selection()
    oracle.pad_to_exact_budget(ledger.cache.keys(), terminal=terminal)
    terminal_fp = _fp(terminal)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2F",
        "seed": int(seed),
        "arm": arm,
        "initial_population_digest_sha256": initial_digest,
        "terminal_sbox": list(terminal),
        "terminal_fingerprint": terminal_fp,
        "terminal_classical": _metrics_payload(terminal_metrics),
        "classical_evaluations": int(ledger.evaluations),
        "oracle_candidate_scores": int(oracle.score_count),
        "oracle_fitness_trainings": int(oracle.training_count),
        "oracle_selection_closed": bool(oracle.selection_closed),
        "oracle_receipts": [
            {
                "fingerprint": receipt.fingerprint,
                "neural_advantage": receipt.neural_advantage,
                "payload_sha256": receipt.payload_sha256,
                "training_count": receipt.training_count,
                "role": receipt.role,
                "score_payload": receipt.score_payload,
            }
            for receipt in oracle.receipts
        ],
        "selection_events": selection_events,
        "generation_trace": generation_trace,
        "parent_map": dict(sorted(parent_map.items())),
        "proposal_audit_sha256": _proposal_audit_digest(proposal_audit),
        "terminal_selection_rule": "historical_classical_only",
    }
    payload["lineage_diagnostics"] = _lineage_diagnostics(
        events=selection_events,
        generations=generation_trace,
        parent_map=parent_map,
        terminal_fingerprint=terminal_fp,
    )
    payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload
