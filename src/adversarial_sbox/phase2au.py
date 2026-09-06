"""Phase 2A-U fresh-panel fixed-depth Neural Oracle qualification contracts.

Scientific protocol: ``research/PHASE2AU_PROTOCOL.md``.
Public preregistration: issue #79. Execution lock: issue #80.

This module contains no neural evolutionary feedback path.
"""

from __future__ import annotations

import random
from typing import Sequence

from .cryptoshield import improved_transparency_order
from .evolution import HardConstraints, evaluate_classical
from .pareto import ITOAwareMetrics, non_dominated_sort, select_nsga2
from .phase1m import (
    CLASSICAL_BUDGET,
    GENERATIONS,
    PARENT_COUNT,
    POPULATION_SIZE,
    SHORTLIST_SIZE,
    ClassicalEvaluationLedger,
    _initial_population,
    _ranked_population,
)
from .phase1o import _collect_unique_batch
from .phase2a import CandidateRecord, is_phase2a_eligible, panel_digest
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]

PANEL_SIZE = 6

CLASSICAL_SOURCE_SEEDS = (
    90601,
    90617,
    90631,
    90641,
    90647,
    90659,
    90671,
    90677,
    90679,
    90697,
    90703,
    90709,
)

ARCHITECTURES = ("bit_relu_mlp", "byte_tanh_mlp")
ROUNDS = 4
DIFFERENCES = (0x00000001, 0x00000100)

DATASET_SEEDS = (
    100003,
    100019,
    100043,
    100049,
    100057,
    100069,
    100103,
    100109,
)
MODEL_SEEDS = (
    110003,
    110017,
    110023,
    110039,
    110051,
    110071,
    110083,
    110107,
)

PERMUTATION_SEEDS = {
    "bit_relu_mlp": 120011,
    "byte_tanh_mlp": 120017,
    "consensus": 120041,
}
PERMUTATIONS = 10_000
SPLIT_HALF_A = (0, 1, 2, 3)
SPLIT_HALF_B = (4, 5, 6, 7)

TRAININGS_PER_ARCHITECTURE = PANEL_SIZE * len(DIFFERENCES) * len(DATASET_SEEDS)
TOTAL_NEURAL_TRAININGS = len(ARCHITECTURES) * TRAININGS_PER_ARCHITECTURE


def is_phase2au_eligible(candidate: CandidateRecord) -> bool:
    """Return the frozen classical eligibility predicate for Phase 2A-U."""

    return is_phase2a_eligible(candidate)


def select_phase2au_panel(records: Sequence[CandidateRecord]) -> tuple[CandidateRecord, ...]:
    """Select six candidates using only the preregistered classical rule."""

    eligible = [record for record in records if is_phase2au_eligible(record)]
    per_seed: dict[int, CandidateRecord] = {}
    for record in sorted(eligible, key=lambda item: (item.source_seed, item.fingerprint)):
        if record.source_seed not in CLASSICAL_SOURCE_SEEDS:
            continue
        current = per_seed.get(record.source_seed)
        if current is None or record.fingerprint < current.fingerprint:
            per_seed[record.source_seed] = record

    if len(per_seed) < PANEL_SIZE:
        raise ValueError(
            "Phase 2A-U requires at least six eligible source seeds before neural training"
        )

    return tuple(sorted(per_seed.values(), key=lambda item: item.fingerprint)[:PANEL_SIZE])


def replay_phase1o_arm_a(seed: int) -> tuple[CandidateRecord, ...]:
    """Replay frozen Phase-1O Arm A on one preregistered fresh source seed.

    The algorithm and exact classical budget are intentionally copied from the
    already-frozen Phase-2A replay path, except that these new source seeds do not
    have pre-existing terminal fingerprints. Determinism is therefore proven by
    two independent replays in the panel builder/workflow before panel selection.
    """

    seed = int(seed)
    if seed not in CLASSICAL_SOURCE_SEEDS:
        raise ValueError(f"seed {seed} is not a frozen Phase 2A-U source seed")

    constraints = HardConstraints()
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    rng = random.Random(seed)
    population = list(_initial_population(seed))
    seen_ever = set(population)
    ito_cache: dict[SBox, ITOAwareMetrics] = {}

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

    for _generation in range(GENERATIONS):
        ranked = _ranked_population(population, ledger, constraints)
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_metrics = tuple(with_ito(candidate) for candidate in shortlist)
        parent_indices = select_nsga2(shortlist_metrics, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in parent_indices)
        proposals, _audit = _collect_unique_batch(parents, rng, seen_ever=seen_ever)
        for proposal in proposals:
            ledger.evaluate(proposal)
        population = _ranked_population(
            [*population, *proposals], ledger, constraints
        )[:POPULATION_SIZE]

    if ledger.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError(
            f"Phase 2A-U replay budget drift: {ledger.evaluations} != {CLASSICAL_BUDGET}"
        )

    ranked = _ranked_population(population, ledger, constraints)
    final_shortlist = tuple(ranked[:SHORTLIST_SIZE])
    final_metrics = tuple(with_ito(candidate) for candidate in final_shortlist)
    front_indices = non_dominated_sort(final_metrics)[0]

    records: list[CandidateRecord] = []
    for index in front_indices:
        candidate = final_shortlist[index]
        metrics = final_metrics[index]
        fingerprint = fingerprint_sbox(candidate)
        if fingerprint != metrics.fingerprint:
            raise RuntimeError("Phase 2A-U replay fingerprint/metrics mismatch")
        records.append(
            CandidateRecord(
                source_seed=seed,
                fingerprint=fingerprint,
                sbox=tuple(candidate),
                differential_uniformity=metrics.differential_uniformity,
                nonlinearity=metrics.nonlinearity,
                max_linear_correlation=metrics.max_linear_correlation,
                algebraic_degree=metrics.algebraic_degree,
                sac_score=metrics.sac_score,
            )
        )

    return tuple(records)


__all__ = [
    "ARCHITECTURES",
    "CLASSICAL_BUDGET",
    "CLASSICAL_SOURCE_SEEDS",
    "DATASET_SEEDS",
    "DIFFERENCES",
    "MODEL_SEEDS",
    "PANEL_SIZE",
    "PERMUTATIONS",
    "PERMUTATION_SEEDS",
    "ROUNDS",
    "SPLIT_HALF_A",
    "SPLIT_HALF_B",
    "TOTAL_NEURAL_TRAININGS",
    "TRAININGS_PER_ARCHITECTURE",
    "CandidateRecord",
    "is_phase2au_eligible",
    "panel_digest",
    "replay_phase1o_arm_a",
    "select_phase2au_panel",
]
