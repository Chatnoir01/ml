"""Held-out-blind five-generation GA/B1 block adapter for Phase 2G.

The adapter is stateful across the four preregistered checkpoint blocks. It
reuses the historical classical geometry and proposal engine, while checkpoint
neural scores may influence only shortlist/survival ordering inside the frozen
Phase-2F B1 band. This module imports no held-out H validation and cannot
authorize or launch the scientific experiment.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import random
from typing import Any

from .cryptoshield import improved_transparency_order, validate_sbox
from .evolution import (
    ClassicalMetrics,
    HardConstraints,
    evaluate_classical,
    feasibility_rank,
)
from .pareto import ITOAwareMetrics, select_nsga2
from .phase1m import ClassicalEvaluationLedger
from .phase2f import (
    CLASSICAL_BUDGET_PER_ARM_SEED,
    PARENT_COUNT,
    POPULATION_SIZE,
    PROPOSALS_PER_GENERATION,
    SHORTLIST_SIZE,
    in_b1_band,
)
from .phase2f_runner import _collect_unique_batch_with_parents
from .phase2g import ARMS, CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from .phase2g_checkpoint_adapter import make_phase2g_checkpoint_score_ledger
from .phase2g_selection import apply_phase2g_cutoff_order
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]
Evaluator = Callable[[SBox], ClassicalMetrics]
ParentSelector = Callable[[Sequence[SBox], dict[SBox, ClassicalMetrics]], Sequence[SBox]]
ProposalFactory = Callable[..., Sequence[Sequence[int]]]
ScoreLedgerFactory = Callable[[Any], Any]


def _historical_parent_selector(
    shortlist: Sequence[SBox], metrics: dict[SBox, ClassicalMetrics]
) -> tuple[SBox, ...]:
    if len(shortlist) != SHORTLIST_SIZE:
        raise ValueError("Phase-2G parent selection requires the exact shortlist size")
    ito_metrics = tuple(
        ITOAwareMetrics.from_classical(
            metrics[candidate],
            improved_transparency_order_value=improved_transparency_order(candidate),
        )
        for candidate in shortlist
    )
    indices = select_nsga2(ito_metrics, PARENT_COUNT)
    parents = tuple(shortlist[index] for index in indices)
    if len(parents) != PARENT_COUNT or len(set(parents)) != PARENT_COUNT:
        raise RuntimeError("Phase-2G historical parent selection geometry drift")
    return parents


def _historical_proposal_factory(
    *,
    parents: Sequence[SBox],
    rng: random.Random,
    seen_ever: set[SBox],
    count: int,
) -> tuple[SBox, ...]:
    if int(count) != PROPOSALS_PER_GENERATION:
        raise ValueError("Phase-2G proposal count drift")
    batch, _audit, _links = _collect_unique_batch_with_parents(
        parents,
        rng,
        seen_ever=seen_ever,
    )
    if len(batch) != PROPOSALS_PER_GENERATION:
        raise RuntimeError("Phase-2G historical proposal engine returned wrong batch size")
    return tuple(batch)


class Phase2GGABlockAdapter:
    """Persistent classical GA state consumed by the four lifecycle blocks.

    The production defaults are the historical classical evaluator, NSGA-II
    parent selector and Phase-2F proposal engine. Tests may inject deterministic
    doubles, which keeps CI synthetic and prevents preregistered scientific GA
    execution before the marker exists.
    """

    def __init__(
        self,
        *,
        arm: str,
        evolution_seed: int,
        evaluator: Evaluator = evaluate_classical,
        parent_selector: ParentSelector = _historical_parent_selector,
        proposal_factory: ProposalFactory = _historical_proposal_factory,
        score_ledger_factory: ScoreLedgerFactory = make_phase2g_checkpoint_score_ledger,
    ) -> None:
        frozen_arm = str(arm)
        frozen_seed = int(evolution_seed)
        if frozen_arm not in ARMS:
            raise ValueError(f"unsupported Phase-2G arm {frozen_arm!r}")
        if frozen_seed not in EVOLUTION_SEEDS:
            raise ValueError(f"unregistered Phase-2G evolution seed {frozen_seed!r}")
        for name, callback in (
            ("evaluator", evaluator),
            ("parent_selector", parent_selector),
            ("proposal_factory", proposal_factory),
            ("score_ledger_factory", score_ledger_factory),
        ):
            if not callable(callback):
                raise TypeError(f"Phase-2G {name} must be callable")

        self.arm = frozen_arm
        self.evolution_seed = frozen_seed
        self.constraints = HardConstraints()
        self._ledger = ClassicalEvaluationLedger(
            evaluator,
            budget=CLASSICAL_BUDGET_PER_ARM_SEED,
        )
        self._parent_selector = parent_selector
        self._proposal_factory = proposal_factory
        self._score_ledger_factory = score_ledger_factory
        self._rng = random.Random(frozen_seed)
        self._seen_ever: set[SBox] = set()
        self._initialized = False
        self._completed_generations = 0
        self._selection_events: list[dict[str, Any]] = []
        self._generation_trace: list[dict[str, Any]] = []

    @property
    def classical_evaluations(self) -> int:
        return int(self._ledger.evaluations)

    @property
    def completed_generations(self) -> int:
        return int(self._completed_generations)

    @property
    def selection_events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._selection_events)

    @property
    def generation_trace(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._generation_trace)

    def _freeze_population(
        self, population: Sequence[Sequence[int]], *, role: str
    ) -> tuple[SBox, ...]:
        if len(population) != POPULATION_SIZE:
            raise ValueError(
                f"Phase-2G {role} population must contain exactly {POPULATION_SIZE} candidates"
            )
        frozen = tuple(validate_sbox(candidate) for candidate in population)
        if len(set(frozen)) != POPULATION_SIZE:
            raise ValueError(
                f"Phase-2G {role} population must contain {POPULATION_SIZE} unique candidates"
            )
        return frozen

    def _initialize_if_needed(self, population: tuple[SBox, ...]) -> None:
        if self._initialized:
            for candidate in population:
                if candidate not in self._ledger.cache:
                    raise RuntimeError(
                        "Phase-2G later checkpoint population contains an unevaluated candidate"
                    )
            return
        if self._completed_generations != 0:
            raise RuntimeError("Phase-2G GA adapter initialization state drift")
        self._seen_ever.update(population)
        for candidate in population:
            self._ledger.evaluate(candidate)
        self._initialized = True

    def _historical_order(self, candidates: Sequence[SBox]) -> list[SBox]:
        return sorted(
            candidates,
            key=lambda candidate: (
                feasibility_rank(self._ledger.cache[candidate], self.constraints),
                candidate,
            ),
            reverse=True,
        )

    def _order_at_cutoff(
        self,
        candidates: Sequence[SBox],
        *,
        cutoff: int,
        generation: int,
        stage: str,
        neural_selection_enabled: bool,
        score_ledger: Any | None,
        shuffle_stream: Any | None,
    ) -> list[SBox]:
        if stage not in {"shortlist", "survival"}:
            raise ValueError(f"unsupported Phase-2G selection stage {stage!r}")
        if not 1 <= int(cutoff) <= len(candidates):
            raise ValueError("Phase-2G cutoff outside candidate pool")

        base = self._historical_order(candidates)
        reference = base[int(cutoff) - 1]
        reference_metrics = self._ledger.cache[reference]

        left = int(cutoff) - 1
        while left - 1 >= 0 and in_b1_band(
            self._ledger.cache[base[left - 1]], reference_metrics, self.constraints
        ):
            left -= 1
        right = int(cutoff)
        while right < len(base) and in_b1_band(
            self._ledger.cache[base[right]], reference_metrics, self.constraints
        ):
            right += 1

        group = list(base[left:right])
        boundary_opportunity = left < int(cutoff) < right
        scored: dict[SBox, float] = {}
        if neural_selection_enabled and boundary_opportunity:
            if score_ledger is None:
                raise RuntimeError("Phase-2G neural selection requires a checkpoint score ledger")
            scored = {candidate: float(score_ledger.score(candidate)) for candidate in group}

        shuffle_rng = None
        shuffle_rng_seed = None
        if self.arm == "S":
            if shuffle_stream is None:
                raise ValueError("Phase-2G S arm requires its persistent checkpoint shuffle stream")
            shuffle_rng = shuffle_stream.rng
            shuffle_rng_seed = int(shuffle_stream.rng_seed)

        if neural_selection_enabled and boundary_opportunity:
            items = [
                (
                    candidate,
                    self._ledger.cache[candidate],
                    float(scored.get(candidate, 0.0)),
                )
                for candidate in base
            ]
            ordered_items = apply_phase2g_cutoff_order(
                items,
                constraints=self.constraints,
                arm=self.arm,
                cutoff_metrics=reference_metrics,
                shuffle_rng=shuffle_rng,
            )
            ordered = [validate_sbox(item[0]) for item in ordered_items]
        else:
            ordered = list(base)

        before_selected = set(base[: int(cutoff)])
        after_selected = set(ordered[: int(cutoff)])
        self._selection_events.append(
            {
                "generation": int(generation),
                "stage": stage,
                "cutoff": int(cutoff),
                "neural_selection_enabled": bool(neural_selection_enabled),
                "boundary_opportunity": bool(boundary_opportunity),
                "b1_group": [fingerprint_sbox(candidate) for candidate in group],
                "scored_candidate_count": int(len(scored)),
                "membership_changed": bool(before_selected != after_selected),
                "ordering_changed": bool(ordered != base),
                "shuffle_rng_seed": shuffle_rng_seed,
            }
        )
        return ordered

    def _validate_block_contract(
        self,
        *,
        start_generation: int,
        end_generation: int,
        selection_enabled: bool,
        model: Any,
        shuffle_stream: Any | None,
    ) -> tuple[int, int]:
        start = int(start_generation)
        end = int(end_generation)
        if start not in CHECKPOINT_GENERATIONS:
            raise ValueError("Phase-2G block must begin at a preregistered checkpoint")
        expected_end = start + 5
        if end != expected_end or end > 20:
            raise ValueError("Phase-2G checkpoint block must span exactly five generations")
        if start != self._completed_generations:
            raise ValueError("Phase-2G checkpoint blocks must execute sequentially")

        expected_selection = self.arm != "C"
        if bool(selection_enabled) != expected_selection:
            raise ValueError("Phase-2G lifecycle selection-enabled flag drift")

        required_model_identity = {
            "arm": self.arm,
            "evolution_seed": self.evolution_seed,
            "checkpoint_generation": start,
            "model_count": 16,
            "training_count": 16,
        }
        for field, expected in required_model_identity.items():
            if not hasattr(model, field):
                raise ValueError(f"Phase-2G checkpoint bundle missing {field}")
            actual = getattr(model, field)
            if field == "arm":
                matches = str(actual) == str(expected)
            else:
                matches = int(actual) == int(expected)
            if not matches:
                raise ValueError(f"Phase-2G checkpoint bundle {field} drift")

        if self.arm == "S":
            if shuffle_stream is None:
                raise ValueError("Phase-2G S arm requires a checkpoint shuffle stream")
            if int(getattr(shuffle_stream, "evolution_seed", -1)) != self.evolution_seed:
                raise ValueError("Phase-2G S shuffle evolution-seed drift")
            if int(getattr(shuffle_stream, "checkpoint_generation", -1)) != start:
                raise ValueError("Phase-2G S shuffle checkpoint drift")
        elif shuffle_stream is not None:
            raise ValueError("only Phase-2G S may receive a shuffle stream")

        return start, end

    def evolve_block(
        self,
        *,
        population: Sequence[Sequence[int]],
        start_generation: int,
        end_generation: int,
        selection_enabled: bool,
        model: Any,
        shuffle_stream: Any | None,
    ) -> tuple[SBox, ...]:
        """Run one exact five-generation Phase-2G classical block.

        Checkpoint training has already happened upstream. For F/A/S this method
        constructs one inference-only score ledger bound to that 16-model bundle
        and reuses it throughout the five-generation block. C never constructs
        a selection score ledger, keeping checkpoint models audit-only.
        """

        start, end = self._validate_block_contract(
            start_generation=start_generation,
            end_generation=end_generation,
            selection_enabled=selection_enabled,
            model=model,
            shuffle_stream=shuffle_stream,
        )
        current = self._freeze_population(population, role=f"block-{start}-input")
        self._initialize_if_needed(current)

        score_ledger = (
            self._score_ledger_factory(model) if bool(selection_enabled) else None
        )

        for generation in range(start, end):
            population_before = tuple(current)
            ranked = self._order_at_cutoff(
                current,
                cutoff=SHORTLIST_SIZE,
                generation=generation,
                stage="shortlist",
                neural_selection_enabled=bool(selection_enabled),
                score_ledger=score_ledger,
                shuffle_stream=shuffle_stream,
            )
            shortlist = tuple(ranked[:SHORTLIST_SIZE])
            parents = tuple(self._parent_selector(shortlist, self._ledger.cache))
            if len(parents) != PARENT_COUNT or len(set(parents)) != PARENT_COUNT:
                raise RuntimeError("Phase-2G parent selector must return exactly four unique parents")
            if any(parent not in shortlist for parent in parents):
                raise RuntimeError("Phase-2G parent selector returned a non-shortlisted candidate")

            seen_before = set(self._seen_ever)
            proposed = self._proposal_factory(
                parents=parents,
                rng=self._rng,
                seen_ever=self._seen_ever,
                count=PROPOSALS_PER_GENERATION,
            )
            proposals = tuple(validate_sbox(candidate) for candidate in proposed)
            if len(proposals) != PROPOSALS_PER_GENERATION or len(set(proposals)) != PROPOSALS_PER_GENERATION:
                raise RuntimeError("Phase-2G proposal factory must return 16 unique proposals")
            if any(candidate in seen_before for candidate in proposals):
                raise RuntimeError("Phase-2G proposal factory reused a previously evaluated candidate")
            self._seen_ever.update(proposals)
            for proposal in proposals:
                self._ledger.evaluate(proposal)

            survival = self._order_at_cutoff(
                [*current, *proposals],
                cutoff=POPULATION_SIZE,
                generation=generation,
                stage="survival",
                neural_selection_enabled=bool(selection_enabled),
                score_ledger=score_ledger,
                shuffle_stream=shuffle_stream,
            )
            next_population = tuple(survival[:POPULATION_SIZE])
            if len(next_population) != POPULATION_SIZE or len(set(next_population)) != POPULATION_SIZE:
                raise RuntimeError("Phase-2G survival selection population geometry drift")

            self._generation_trace.append(
                {
                    "generation": int(generation),
                    "population_before": [fingerprint_sbox(candidate) for candidate in population_before],
                    "shortlist": [fingerprint_sbox(candidate) for candidate in shortlist],
                    "parents": [fingerprint_sbox(candidate) for candidate in parents],
                    "proposals": [fingerprint_sbox(candidate) for candidate in proposals],
                    "next_population": [fingerprint_sbox(candidate) for candidate in next_population],
                }
            )
            current = next_population
            self._completed_generations = generation + 1

        expected_evaluations = POPULATION_SIZE + (
            self._completed_generations * PROPOSALS_PER_GENERATION
        )
        if self.classical_evaluations != expected_evaluations:
            raise RuntimeError("Phase-2G classical evaluation budget drift inside GA block")
        if self._completed_generations == 20 and self.classical_evaluations != CLASSICAL_BUDGET_PER_ARM_SEED:
            raise RuntimeError("Phase-2G terminal classical budget must equal 340")
        return tuple(current)
