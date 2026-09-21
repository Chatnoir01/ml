"""Concrete held-out-blind Phase 2G scientific-cell composition.

This module joins the already-frozen checkpoint bundle, historical GA/B1 adapter,
and complete arm runner into one production cell. It cannot access held-out H,
does not perform terminal neural reranking, and does not authorize execution; the
separate execution marker/workflow remains the only scientific launch gate.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import hashlib
import json
from typing import Any

from .cryptoshield import improved_transparency_order, validate_sbox
from .evolution import feasibility_rank, is_admissible
from .pareto import ITOAwareMetrics, non_dominated_sort
from .phase1m import _initial_population
from .phase2_evolution_seed_registry import phase2g_evolution_seeds_are_fresh
from .phase2f_runner import _collect_unique_batch_with_parents
from .phase2g import (
    ARMS,
    CHECKPOINT_GENERATIONS,
    EVOLUTION_SEEDS,
    SCORING_DATASET_BASE_SEEDS,
    expanded_checkpoint_seed_block,
)
from .phase2g_arm_runner import CLASSICAL_EVALUATIONS_PER_CELL, run_phase2g_arm
from .phase2g_checkpoint_adapter import (
    build_phase2g_checkpoint_bundle,
    make_phase2g_checkpoint_score_ledger,
)
from .phase2g_ga_adapter import Phase2GGABlockAdapter
from .phase2g_shared_model import score_candidate_checkpoint, train_shared_checkpoint_model
from .provenance import fingerprint_sbox

InitialPopulationFactory = Callable[[int], Sequence[Sequence[int]]]
ModelTrainer = Callable[..., Any]
CandidateScorer = Callable[..., dict[str, Any]]
GAAdapterFactory = Callable[..., Any]

POPULATION_SIZE = 20
SHORTLIST_SIZE = 8
PROPOSALS_PER_GENERATION = 16


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _freeze_initial_population(
    factory: InitialPopulationFactory,
    seed: int,
) -> tuple[tuple[int, ...], ...]:
    if not callable(factory):
        raise TypeError("Phase-2G initial population factory must be callable")
    raw = factory(int(seed))
    if len(raw) != POPULATION_SIZE:
        raise ValueError("Phase-2G initial population must contain exactly 20 candidates")
    frozen = tuple(validate_sbox(candidate) for candidate in raw)
    if len(set(frozen)) != POPULATION_SIZE:
        raise ValueError("Phase-2G initial population must contain 20 unique candidates")
    return frozen


def _terminal_selector(adapter: Any, population: Sequence[Sequence[int]]) -> tuple[int, ...]:
    """Mirror the frozen Phase-2F historical classical-only terminal rule."""

    frozen = tuple(validate_sbox(candidate) for candidate in population)
    if len(frozen) != POPULATION_SIZE or len(set(frozen)) != POPULATION_SIZE:
        raise RuntimeError("Phase-2G final population geometry drift")

    ledger = getattr(adapter, "_ledger", None)
    constraints = getattr(adapter, "constraints", None)
    if ledger is None or constraints is None or not hasattr(ledger, "cache"):
        raise RuntimeError("Phase-2G GA adapter lacks terminal classical ledger")
    metrics = ledger.cache
    if any(candidate not in metrics for candidate in frozen):
        raise RuntimeError("Phase-2G terminal population contains an unevaluated candidate")

    ranked = sorted(
        frozen,
        key=lambda candidate: (feasibility_rank(metrics[candidate], constraints), candidate),
        reverse=True,
    )
    shortlist = tuple(ranked[:SHORTLIST_SIZE])
    ito_metrics = tuple(
        ITOAwareMetrics.from_classical(
            metrics[candidate],
            improved_transparency_order_value=improved_transparency_order(candidate),
        )
        for candidate in shortlist
    )
    fronts = non_dominated_sort(ito_metrics)
    if not fronts or not fronts[0]:
        raise RuntimeError("Phase-2G terminal classical Pareto front is empty")
    terminal_front = tuple(shortlist[index] for index in fronts[0])
    return max(
        terminal_front,
        key=lambda candidate: feasibility_rank(metrics[candidate], constraints),
    )


def _terminal_metrics(adapter: Any, candidate: Sequence[int]) -> dict[str, Any]:
    frozen = validate_sbox(candidate)
    ledger = getattr(adapter, "_ledger", None)
    constraints = getattr(adapter, "constraints", None)
    if ledger is None or constraints is None or frozen not in ledger.cache:
        raise RuntimeError("Phase-2G terminal classical metrics are not cached")
    metrics = ledger.cache[frozen]
    return {
        "admissible": bool(is_admissible(metrics, constraints)),
        "nonlinearity": int(metrics.nonlinearity),
        "differential_uniformity": int(metrics.differential_uniformity),
        "max_abs_lat": int(metrics.max_linear_correlation),
        "algebraic_degree": int(metrics.algebraic_degree),
    }


def _production_ga_adapter_factory(
    *, arm: str, evolution_seed: int, score_ledger_factory: Callable[[Any], Any]
) -> Phase2GGABlockAdapter:
    """Build the historical GA while receipting realized proposal parent links.

    The underlying proposal collector and RNG consumption are exactly the frozen
    Phase-2F path. This wrapper only preserves the parent links that the older
    adapter discarded so lineage persistence can be audited later.
    """

    parent_map: dict[str, str] = {}

    def proposal_factory(*, parents, rng, seen_ever, count):
        if int(count) != PROPOSALS_PER_GENERATION:
            raise ValueError("Phase-2G proposal count drift")
        batch, _audit, links = _collect_unique_batch_with_parents(
            parents,
            rng,
            seen_ever=seen_ever,
        )
        if len(batch) != PROPOSALS_PER_GENERATION or len(links) != PROPOSALS_PER_GENERATION:
            raise RuntimeError("Phase-2G historical proposal lineage geometry drift")
        for link in links:
            child = str(link["proposal_fingerprint"])
            parent = str(link["parent_fingerprint"])
            if child in parent_map:
                raise RuntimeError("duplicate Phase-2G realized proposal lineage")
            parent_map[child] = parent
        return tuple(batch)

    adapter = Phase2GGABlockAdapter(
        arm=arm,
        evolution_seed=evolution_seed,
        proposal_factory=proposal_factory,
        score_ledger_factory=score_ledger_factory,
    )
    adapter._phase2g_parent_map = parent_map
    return adapter


def _classical_evaluation_ledger(adapter: Any) -> list[dict[str, Any]]:
    ledger = getattr(adapter, "_ledger", None)
    if ledger is None or not hasattr(ledger, "cache"):
        raise RuntimeError("Phase-2G GA adapter lacks classical evaluation ledger")
    rows: list[dict[str, Any]] = []
    for candidate, metrics in ledger.cache.items():
        fingerprint = fingerprint_sbox(candidate)
        if str(metrics.fingerprint) != fingerprint:
            raise RuntimeError("Phase-2G classical evaluation fingerprint drift")
        rows.append(
            {
                "fingerprint": fingerprint,
                "nonlinearity": int(metrics.nonlinearity),
                "differential_uniformity": int(metrics.differential_uniformity),
                "max_abs_lat": int(metrics.max_linear_correlation),
                "sac_score": float(metrics.sac_score),
                "algebraic_degree": int(metrics.algebraic_degree),
            }
        )
    if len(rows) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise RuntimeError("Phase-2G classical evaluation ledger must contain exactly 340 rows")
    if len({row["fingerprint"] for row in rows}) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise RuntimeError("Phase-2G classical evaluation ledger contains duplicate candidates")
    return rows


def _has_ancestor(candidate: str, ancestor: str, parent_map: dict[str, str]) -> bool:
    current = str(candidate)
    target = str(ancestor)
    seen: set[str] = set()
    while current in parent_map:
        if current in seen:
            raise RuntimeError("cycle in Phase-2G realized parent map")
        seen.add(current)
        current = parent_map[current]
        if current == target:
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
        populations[20] = set(generations[-1]["next_population"])

    results: list[dict[str, Any]] = []
    for event_index, event in enumerate(events):
        entered = [str(value) for value in event.get("score_caused_entered", ())]
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
                else:
                    item[f"direct_plus_{offset}"] = fingerprint in population
                    item[f"descendant_plus_{offset}"] = any(
                        candidate != fingerprint
                        and _has_ancestor(candidate, fingerprint, parent_map)
                        for candidate in population
                    )
            item["terminal_self"] = terminal_fingerprint == fingerprint
            item["terminal_descendant"] = _has_ancestor(
                terminal_fingerprint, fingerprint, parent_map
            )
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


def _model_provenance(bundle: Any) -> tuple[list[int], list[int], list[dict[str, Any]]]:
    models = sorted(
        tuple(getattr(bundle, "models", ())),
        key=lambda model: (int(model.difference), int(model.replicate)),
    )
    if len(models) != 16:
        raise RuntimeError("Phase-2G checkpoint provenance requires exactly 16 models")
    t_by_rep: dict[int, int] = {}
    m_by_rep: dict[int, int] = {}
    receipts: list[dict[str, Any]] = []
    for model in models:
        replicate = int(model.replicate)
        dataset_seed = int(model.dataset_seed)
        model_seed = int(model.model_seed)
        if replicate in t_by_rep and t_by_rep[replicate] != dataset_seed:
            raise RuntimeError("Phase-2G T seed differs across checkpoint differences")
        if replicate in m_by_rep and m_by_rep[replicate] != model_seed:
            raise RuntimeError("Phase-2G M seed differs across checkpoint differences")
        t_by_rep[replicate] = dataset_seed
        m_by_rep[replicate] = model_seed
        state_sha = str(model.state_sha256)
        if len(state_sha) != 64:
            raise RuntimeError("Phase-2G checkpoint model state receipt is invalid")
        receipts.append(
            {
                "difference": int(model.difference),
                "replicate": replicate,
                "dataset_seed": dataset_seed,
                "model_seed": model_seed,
                "state_sha256": state_sha,
            }
        )
    if set(t_by_rep) != set(range(8)) or set(m_by_rep) != set(range(8)):
        raise RuntimeError("Phase-2G checkpoint replicate provenance drift")
    return (
        [t_by_rep[index] for index in range(8)],
        [m_by_rep[index] for index in range(8)],
        receipts,
    )


def _score_receipts(ledger: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for receipt in sorted(tuple(ledger.receipts), key=lambda item: item.cache_key):
        rows.append(
            {
                "cache_key": list(receipt.cache_key),
                "fingerprint": str(receipt.fingerprint),
                "neural_advantage": float(receipt.neural_advantage),
                "payload_sha256": str(receipt.payload_sha256),
                "training_count": int(receipt.training_count),
                "payload": receipt.payload,
            }
        )
    if int(ledger.cache_misses) != len(rows):
        raise RuntimeError("Phase-2G score cache miss count does not match unique receipts")
    return rows


def run_phase2g_scientific_cell(
    *,
    seed: int,
    arm: str,
    initial_population_factory: InitialPopulationFactory = _initial_population,
    train_model: ModelTrainer = train_shared_checkpoint_model,
    score_candidate: CandidateScorer = score_candidate_checkpoint,
    ga_adapter_factory: GAAdapterFactory = _production_ga_adapter_factory,
) -> dict[str, Any]:
    """Run one frozen 20-generation C/F/A/S Phase-2G cell, held-out blind.

    Defaults are the real frozen checkpoint trainer/scorer and historical GA.
    Tests may inject deterministic doubles. Held-out H is deliberately absent.
    """

    frozen_seed = int(seed)
    frozen_arm = str(arm)
    if frozen_seed not in EVOLUTION_SEEDS:
        raise ValueError(f"seed {frozen_seed!r} is not a frozen Phase-2G evolution seed")
    if frozen_arm not in ARMS:
        raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
    if not phase2g_evolution_seeds_are_fresh(EVOLUTION_SEEDS):
        raise RuntimeError("Phase-2G evolution seed provenance gate failed")
    for name, callback in (
        ("train_model", train_model),
        ("score_candidate", score_candidate),
        ("ga_adapter_factory", ga_adapter_factory),
    ):
        if not callable(callback):
            raise TypeError(f"Phase-2G {name} must be callable")

    initial = _freeze_initial_population(initial_population_factory, frozen_seed)
    score_ledgers: dict[int, Any] = {}
    checkpoint_bundles: dict[int, Any] = {}

    def score_ledger_factory(bundle: Any) -> Any:
        ledger = make_phase2g_checkpoint_score_ledger(
            bundle,
            score_candidate=score_candidate,
        )
        checkpoint = int(bundle.checkpoint_generation)
        if checkpoint in score_ledgers:
            raise RuntimeError("Phase-2G duplicate checkpoint score ledger")
        score_ledgers[checkpoint] = ledger
        return ledger

    adapter = ga_adapter_factory(
        arm=frozen_arm,
        evolution_seed=frozen_seed,
        score_ledger_factory=score_ledger_factory,
    )
    if str(getattr(adapter, "arm", "")) != frozen_arm:
        raise RuntimeError("Phase-2G GA adapter arm identity drift")
    if int(getattr(adapter, "evolution_seed", -1)) != frozen_seed:
        raise RuntimeError("Phase-2G GA adapter evolution-seed identity drift")
    initializer = getattr(adapter, "_initialize_if_needed", None)
    if not callable(initializer):
        raise RuntimeError("Phase-2G GA adapter lacks initial classical population gate")
    initializer(initial)
    if int(getattr(adapter, "classical_evaluations", -1)) != POPULATION_SIZE:
        raise RuntimeError("Phase-2G initial classical evaluation budget drift")

    def train_checkpoint(**kwargs: Any) -> Any:
        checkpoint = int(kwargs["checkpoint_generation"])
        if checkpoint in checkpoint_bundles:
            raise RuntimeError("Phase-2G duplicate checkpoint bundle")
        bundle = build_phase2g_checkpoint_bundle(
            arm=str(kwargs["arm"]),
            evolution_seed=int(kwargs["evolution_seed"]),
            checkpoint_generation=checkpoint,
            curriculum=kwargs["curriculum"],
            train_model=train_model,
        )
        checkpoint_bundles[checkpoint] = bundle
        return bundle

    def evolve_block(**kwargs: Any) -> dict[str, Any]:
        checkpoint = int(kwargs["start_generation"])
        before_evaluations = int(adapter.classical_evaluations)
        before_events = len(adapter.selection_events)
        population = adapter.evolve_block(
            population=kwargs["population"],
            start_generation=checkpoint,
            end_generation=int(kwargs["end_generation"]),
            selection_enabled=bool(kwargs["selection_enabled"]),
            model=kwargs["model"],
            shuffle_stream=kwargs["shuffle_stream"],
        )
        after_evaluations = int(adapter.classical_evaluations)
        events = [dict(event) for event in adapter.selection_events[before_events:]]

        # C is audit-only, not score-free. Scores are computed only after each
        # classical decision is frozen and are never fed back into ordering.
        if frozen_arm == "C":
            audit_ledger = score_ledgers.get(checkpoint)
            if audit_ledger is None:
                audit_ledger = score_ledger_factory(kwargs["model"])
            classical_cache = getattr(getattr(adapter, "_ledger", None), "cache", {})
            by_fingerprint = {
                fingerprint_sbox(candidate): candidate for candidate in classical_cache
            }
            for event in events:
                if not bool(event.get("boundary_opportunity", False)):
                    continue
                group = [str(value) for value in event.get("b1_group", ())]
                if not group:
                    continue
                scores: dict[str, float] = {}
                for fingerprint in group:
                    candidate = by_fingerprint.get(fingerprint)
                    if candidate is None:
                        raise RuntimeError(
                            "Phase-2G C audit B1 candidate is missing from classical ledger"
                        )
                    scores[fingerprint] = float(audit_ledger.score(candidate))
                event["scored_candidate_count"] = len(scores)
                event["assigned_scores"] = scores
                if event.get("selected_before") != event.get("selected_after"):
                    raise RuntimeError("Phase-2G C audit score altered classical selection")
                event["membership_changed"] = False
                event["ordering_changed"] = False
                event["score_caused_entered"] = []
                event["entered"] = []
                event["exited"] = []

        return {
            "population": tuple(population),
            "generation_count": int(kwargs["end_generation"]) - checkpoint,
            "classical_evaluations": after_evaluations - before_evaluations,
            "selection_events": events,
        }

    result = run_phase2g_arm(
        arm=frozen_arm,
        evolution_seed=frozen_seed,
        initial_population=initial,
        train_checkpoint=train_checkpoint,
        evolve_block=evolve_block,
        select_terminal_classical_only=lambda population: _terminal_selector(adapter, population),
        terminal_classical_metrics=lambda terminal: _terminal_metrics(adapter, terminal),
    )

    if int(getattr(adapter, "completed_generations", -1)) != 20:
        raise RuntimeError("Phase-2G GA adapter did not complete exactly 20 generations")
    if int(getattr(adapter, "classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_CELL:
        raise RuntimeError("Phase-2G concrete cell classical budget drift")
    if bool(result.get("heldout_accessed", True)):
        raise RuntimeError("Phase-2G concrete cell must remain held-out blind")
    if set(checkpoint_bundles) != set(CHECKPOINT_GENERATIONS):
        raise RuntimeError("Phase-2G checkpoint bundle provenance is incomplete")
    if set(score_ledgers) != set(CHECKPOINT_GENERATIONS):
        raise RuntimeError("Phase-2G checkpoint score provenance is incomplete")

    generation_trace = [dict(row) for row in adapter.generation_trace]
    if len(generation_trace) != 20:
        raise RuntimeError("Phase-2G generation trace must contain exactly 20 rows")
    result["generation_trace"] = generation_trace
    result["classical_evaluation_ledger"] = _classical_evaluation_ledger(adapter)

    parent_map = dict(sorted(getattr(adapter, "_phase2g_parent_map", {}).items()))
    result["parent_map"] = parent_map
    result["lineage_diagnostics"] = _lineage_diagnostics(
        events=result["selection_events"],
        generations=generation_trace,
        parent_map=parent_map,
        terminal_fingerprint=str(result["terminal_fingerprint"]),
    )

    for checkpoint_row in result["checkpoints"]:
        checkpoint = int(checkpoint_row["generation"])
        bundle = checkpoint_bundles[checkpoint]
        score_ledger = score_ledgers[checkpoint]
        t_seeds, m_seeds, model_receipts = _model_provenance(bundle)
        checkpoint_index = CHECKPOINT_GENERATIONS.index(checkpoint)
        q_seeds = list(
            expanded_checkpoint_seed_block(
                SCORING_DATASET_BASE_SEEDS,
                checkpoint_index,
            )
        )
        if len(q_seeds) != 8:
            raise RuntimeError("Phase-2G Q seed checkpoint geometry drift")
        checkpoint_row["training_dataset_seeds"] = t_seeds
        checkpoint_row["training_model_seeds"] = m_seeds
        checkpoint_row["scoring_dataset_seeds"] = [int(value) for value in q_seeds]
        checkpoint_row["model_receipts"] = model_receipts
        checkpoint_row["score_cache_hits"] = int(score_ledger.cache_hits)
        checkpoint_row["score_cache_misses"] = int(score_ledger.cache_misses)
        checkpoint_row["score_receipts"] = _score_receipts(score_ledger)

    result.pop("scientific_payload_sha256", None)
    result["scientific_payload_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result
