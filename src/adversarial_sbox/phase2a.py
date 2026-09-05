"""Phase 2A fresh-panel Neural Oracle qualification contracts.

Scientific protocol: ``research/PHASE2A_PROTOCOL.md``.

This module deliberately contains no evolutionary feedback path. Phase 2A may
qualify a neural scoring procedure for a later, separately preregistered Phase 2B,
but cannot inject a neural score into GA selection itself.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
from typing import Mapping, Sequence

from .cryptoshield import improved_transparency_order, is_bijective, validate_sbox
from .evolution import HardConstraints, evaluate_classical
from .experiment_seeds import PHASE1O_CONFIRM_RESERVED_SEEDS
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
from .provenance import fingerprint_sbox

SBox = tuple[int, ...]

PANEL_SIZE = 6

ORACLE_ARCHITECTURE = "bit_relu_mlp"
ORACLE_ROUNDS = 4
ORACLE_DIFFERENCES = (0x00000001, 0x00000100)

CHALLENGER_ARCHITECTURE = "byte_tanh_mlp"
CHALLENGER_ROUNDS = 5
CHALLENGER_DIFFERENCES = (0x00010000, 0x01000000)

DATASET_SEEDS = (51001, 51007, 51011, 51031, 51047)
MODEL_SEEDS = (61001, 61007, 61027, 61031, 61043)

TRAININGS_PER_SIDE = PANEL_SIZE * 2 * len(DATASET_SEEDS)
TOTAL_TRAININGS = 2 * TRAININGS_PER_SIDE

PHASE1O_CONFIRM_ARTIFACT_SHA256 = (
    "8ea2b8f01a19095882aa56e9c335e6abefc0f2100225b6779d40e19381a2cf99"
)

# Frozen Arm-A terminal fingerprints from the preregistered Phase-1O blind
# confirmation artifact. These are classical receipts known before any Phase-2A
# neural training and are used only to prove replay identity.
FROZEN_CONFIRM_ARM_A_TERMINAL_FINGERPRINTS: dict[int, tuple[str, ...]] = {
    2609: ("300769cec5fefe30060e5f04a2a976b728900ee2b121cbdb81e09ce5260b686b",),
    2617: ("a06c615dceaadd395bc1dfd14d1e58d2b6eb5744267c3c5db4797f22406c1163",),
    2621: ("dfb70187d44c755a4fa4fa650602ce92d17e5ad1ef232a223780f1c5268a3df4",),
    2633: ("c2316833af9f4c0f73a8f44a2132d39ce414a14c4fd45553279e7fd87ae3f1e3",),
    2647: ("72c4092c42e34efea6ee127355194ddfa254168759c67f9a4913a718c9830f9e",),
    2657: (
        "f2e791f89b779697869ec67d89213cac65b3c329f60b7f8c7c39531e5886a3ee",
        "47db19cbaf316bdfbd6cccaa2c96934122edb259758b301ac8e812c9a84e4c3b",
    ),
    2663: ("d6744195ad185ae528c68f6b40f658b94aee4682adf467a2d3154324140677c8",),
    2671: ("d4ad8f1dbab5e099ae492af73adfdc1979ba7bb4e6766021924c2b5cb05d602c",),
    2683: ("9034f299d97e8ddb741da52acd24c3416ed96d52acb730f77577cd19f730dff5",),
}

REQUIRED_CHECKS = (
    "training_count_exact",
    "panel_revalidated",
    "oracle_heterogeneity",
    "challenger_heterogeneity",
    "oracle_range",
    "challenger_range",
    "rank_replication",
    "oracle_signal",
    "challenger_signal",
    "deterministic_receipts",
)


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    """Classical-only Phase-2A panel candidate receipt."""

    source_seed: int
    fingerprint: str
    sbox: SBox
    differential_uniformity: int
    nonlinearity: int
    max_linear_correlation: int
    algebraic_degree: int
    sac_score: float

    def canonical_payload(self) -> dict[str, object]:
        return {
            "source_seed": int(self.source_seed),
            "fingerprint": str(self.fingerprint),
            "sbox": [int(value) for value in self.sbox],
            "differential_uniformity": int(self.differential_uniformity),
            "nonlinearity": int(self.nonlinearity),
            "max_linear_correlation": int(self.max_linear_correlation),
            "algebraic_degree": int(self.algebraic_degree),
            "sac_score": float(self.sac_score),
        }


def is_phase2a_eligible(candidate: CandidateRecord) -> bool:
    """Return whether a record satisfies the preregistered classical panel gate.

    Fingerprint/permutation identity is deliberately validated at reconstruction
    and committed-panel revalidation boundaries, rather than inside this pure
    classical selection predicate.
    """

    try:
        frozen = validate_sbox(candidate.sbox)
    except (TypeError, ValueError):
        return False

    return (
        is_bijective(frozen)
        and candidate.differential_uniformity == 8
        and candidate.nonlinearity == 100
        and candidate.max_linear_correlation == 56
        and candidate.algebraic_degree == 7
        and abs(float(candidate.sac_score) - 0.5) <= 0.05
        and len(candidate.fingerprint) == 64
    )


def select_fresh_panel(records: Sequence[CandidateRecord]) -> tuple[CandidateRecord, ...]:
    """Select the frozen six-candidate panel using classical information only."""

    eligible = [record for record in records if is_phase2a_eligible(record)]
    per_seed: dict[int, CandidateRecord] = {}
    for record in sorted(eligible, key=lambda item: (item.source_seed, item.fingerprint)):
        current = per_seed.get(record.source_seed)
        if current is None or record.fingerprint < current.fingerprint:
            per_seed[record.source_seed] = record

    if len(per_seed) < PANEL_SIZE:
        raise ValueError(
            "Phase 2A requires at least six eligible source seeds before neural training"
        )

    return tuple(sorted(per_seed.values(), key=lambda item: item.fingerprint)[:PANEL_SIZE])


def panel_digest(panel: Sequence[CandidateRecord]) -> str:
    """SHA-256 receipt for the ordered, committed classical panel."""

    if len(panel) != PANEL_SIZE:
        raise ValueError(f"Phase 2A panel must contain exactly {PANEL_SIZE} candidates")
    payload = [record.canonical_payload() for record in panel]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _replay_phase1o_arm_a(seed: int) -> tuple[CandidateRecord, ...]:
    """Replay frozen Phase-1O Arm A and return its terminal front with permutations."""

    if seed not in PHASE1O_CONFIRM_RESERVED_SEEDS:
        raise ValueError(f"seed {seed} is not a frozen Phase-1O confirmation seed")

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
            f"Phase 2A replay budget drift: {ledger.evaluations} != {CLASSICAL_BUDGET}"
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
            raise RuntimeError("Phase 2A replay fingerprint/metrics mismatch")
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

    expected = FROZEN_CONFIRM_ARM_A_TERMINAL_FINGERPRINTS[seed]
    actual = tuple(record.fingerprint for record in records)
    if actual != expected:
        raise RuntimeError(
            f"Phase 2A replay diverged from frozen Phase-1O confirmation for seed {seed}: "
            f"{actual!r} != {expected!r}"
        )
    return tuple(records)


def reconstruct_fresh_panel() -> tuple[CandidateRecord, ...]:
    """Replay all nine frozen confirmation seeds and select the six-candidate panel."""

    all_records: list[CandidateRecord] = []
    for seed in PHASE1O_CONFIRM_RESERVED_SEEDS:
        all_records.extend(_replay_phase1o_arm_a(seed))
    return select_fresh_panel(all_records)


def qualification_verdict(checks: Mapping[str, bool]) -> str:
    """Return the frozen Phase-2A verdict from the complete check set."""

    missing = [name for name in REQUIRED_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2A qualification checks: {', '.join(missing)}")
    passed = all(bool(checks[name]) for name in REQUIRED_CHECKS)
    return "phase2a_oracle_qualified" if passed else "phase2a_oracle_not_qualified"
