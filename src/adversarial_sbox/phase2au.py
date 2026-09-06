"""Frozen scientific contract for Phase 2A-U 4-round Neural Oracle qualification."""

from __future__ import annotations

from typing import Mapping

ARCHITECTURE = "byte_tanh_mlp"
DEPTH = 4
DIFFERENCES = (0x00000001, 0x00000100)
PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

BLOCK_A_DATASET_SEEDS = (74003, 74017, 74027, 74047, 74059, 74071, 74093, 74101)
BLOCK_A_MODEL_SEEDS = (84011, 84017, 84029, 84043, 84061, 84067, 84089, 84103)
BLOCK_B_DATASET_SEEDS = (75011, 75017, 75029, 75041, 75061, 75083, 75109, 75121)
BLOCK_B_MODEL_SEEDS = (85009, 85021, 85027, 85049, 85061, 85081, 85093, 85109)

PERMUTATION_SEEDS = {"A": 94007, "B": 94009}
PERMUTATION_REPETITIONS = 10_000

CANDIDATE_COUNT = 6
PAIRED_REPLICATES = 8
TRAININGS_PER_CELL = CANDIDATE_COUNT * PAIRED_REPLICATES
TRAININGS_PER_BLOCK = TRAININGS_PER_CELL * len(DIFFERENCES)
TOTAL_TRAININGS = 2 * TRAININGS_PER_BLOCK

MIN_CANDIDATE_ADVANTAGE = 0.04
MIN_NULL_MARGIN = 0.02
HETEROGENEITY_P_MAX = 0.05
MIN_SCORE_RANGE = 0.05
SPEARMAN_MIN = 0.80
TOP2_OVERLAP_MIN = 1
MAD_MAX = 0.05
NEURAL_EVOLUTIONARY_PRESSURE = False

REQUIRED_QUALIFICATION_CHECKS = (
    "block_a_heterogeneity",
    "block_b_heterogeneity",
    "block_a_range",
    "block_b_range",
    "rank_replication",
    "top2_overlap",
    "cross_block_mad",
)


def fresh_seed_registry() -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                *BLOCK_A_DATASET_SEEDS,
                *BLOCK_A_MODEL_SEEDS,
                *BLOCK_B_DATASET_SEEDS,
                *BLOCK_B_MODEL_SEEDS,
            }
        )
    )


def prior_frozen_neural_seed_registry() -> tuple[int, ...]:
    """Return prior Phase-2 frozen neural dataset/model seeds known before 2A-U."""

    from .phase2a import DATASET_SEEDS as P2A_DATASET, MODEL_SEEDS as P2A_MODEL
    from .phase2ar import DATASET_SEEDS as P2AR_DATASET, MODEL_SEEDS as P2AR_MODEL
    from .phase2as import DATASET_SEEDS as P2AS_DATASET, MODEL_SEEDS as P2AS_MODEL
    from .phase2at import DATASET_SEEDS as P2AT_DATASET, MODEL_SEEDS as P2AT_MODEL

    return tuple(
        sorted(
            {
                *P2A_DATASET,
                *P2A_MODEL,
                *P2AR_DATASET,
                *P2AR_MODEL,
                *P2AS_DATASET,
                *P2AS_MODEL,
                *P2AT_DATASET,
                *P2AT_MODEL,
            }
        )
    )


def fresh_seeds_disjoint_from_prior() -> bool:
    return set(fresh_seed_registry()).isdisjoint(prior_frozen_neural_seed_registry())


def build_qualification_checks(
    *,
    block_a_p: float,
    block_b_p: float,
    block_a_range: float,
    block_b_range: float,
    spearman: float,
    top2_overlap: int,
    cross_block_mad: float,
) -> dict[str, bool]:
    return {
        "block_a_heterogeneity": float(block_a_p) < HETEROGENEITY_P_MAX,
        "block_b_heterogeneity": float(block_b_p) < HETEROGENEITY_P_MAX,
        "block_a_range": float(block_a_range) >= MIN_SCORE_RANGE,
        "block_b_range": float(block_b_range) >= MIN_SCORE_RANGE,
        "rank_replication": float(spearman) >= SPEARMAN_MIN,
        "top2_overlap": int(top2_overlap) >= TOP2_OVERLAP_MIN,
        "cross_block_mad": float(cross_block_mad) <= MAD_MAX,
    }


def qualification_verdict(
    prerequisites_pass: bool,
    checks: Mapping[str, bool],
) -> str:
    if not bool(prerequisites_pass):
        return "phase2au_inconclusive_prerequisites"
    missing = [name for name in REQUIRED_QUALIFICATION_CHECKS if name not in checks]
    if missing:
        raise ValueError(f"missing Phase 2A-U qualification checks: {', '.join(missing)}")
    if all(bool(checks[name]) for name in REQUIRED_QUALIFICATION_CHECKS):
        return "phase2au_oracle_qualified"
    return "phase2au_oracle_not_qualified"
