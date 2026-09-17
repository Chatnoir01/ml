"""Concrete held-out-blind Phase 2G scientific-cell composition.

This module joins the already-frozen checkpoint bundle, historical GA/B1 adapter,
and complete arm runner into one production cell.  It cannot access held-out H,
does not perform terminal neural reranking, and does not authorize execution; the
separate execution marker/workflow remains the only scientific launch gate.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from .cryptoshield import improved_transparency_order, validate_sbox
from .evolution import feasibility_rank, is_admissible
from .pareto import ITOAwareMetrics, non_dominated_sort
from .phase1m import _initial_population
from .phase2_evolution_seed_registry import phase2g_evolution_seeds_are_fresh
from .phase2g import ARMS, EVOLUTION_SEEDS
from .phase2g_arm_runner import CLASSICAL_EVALUATIONS_PER_CELL, run_phase2g_arm
from .phase2g_checkpoint_adapter import (
    build_phase2g_checkpoint_bundle,
    make_phase2g_checkpoint_score_ledger,
)
from .phase2g_ga_adapter import Phase2GGABlockAdapter
from .phase2g_shared_model import score_candidate_checkpoint, train_shared_checkpoint_model

InitialPopulationFactory = Callable[[int], Sequence[Sequence[int]]]
ModelTrainer = Callable[..., Any]
CandidateScorer = Callable[..., dict[str, Any]]
GAAdapterFactory = Callable[..., Any]

POPULATION_SIZE = 20
SHORTLIST_SIZE = 8


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


def run_phase2g_scientific_cell(
    *,
    seed: int,
    arm: str,
    initial_population_factory: InitialPopulationFactory = _initial_population,
    train_model: ModelTrainer = train_shared_checkpoint_model,
    score_candidate: CandidateScorer = score_candidate_checkpoint,
    ga_adapter_factory: GAAdapterFactory = Phase2GGABlockAdapter,
) -> dict[str, Any]:
    """Run one frozen 20-generation C/F/A/S Phase-2G cell, held-out blind.

    This function is a composition boundary only.  Defaults are the real frozen
    checkpoint trainer/scorer and historical GA adapter; tests inject deterministic
    doubles.  Held-out H is deliberately absent from this module.
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

    def score_ledger_factory(bundle: Any) -> Any:
        return make_phase2g_checkpoint_score_ledger(
            bundle,
            score_candidate=score_candidate,
        )

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
        return build_phase2g_checkpoint_bundle(
            arm=str(kwargs["arm"]),
            evolution_seed=int(kwargs["evolution_seed"]),
            checkpoint_generation=int(kwargs["checkpoint_generation"]),
            curriculum=kwargs["curriculum"],
            train_model=train_model,
        )

    def evolve_block(**kwargs: Any) -> dict[str, Any]:
        before_evaluations = int(adapter.classical_evaluations)
        before_events = len(adapter.selection_events)
        population = adapter.evolve_block(
            population=kwargs["population"],
            start_generation=int(kwargs["start_generation"]),
            end_generation=int(kwargs["end_generation"]),
            selection_enabled=bool(kwargs["selection_enabled"]),
            model=kwargs["model"],
            shuffle_stream=kwargs["shuffle_stream"],
        )
        after_evaluations = int(adapter.classical_evaluations)
        events = [dict(event) for event in adapter.selection_events[before_events:]]
        return {
            "population": tuple(population),
            "generation_count": int(kwargs["end_generation"])
            - int(kwargs["start_generation"]),
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
    return result
