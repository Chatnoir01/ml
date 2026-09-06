"""Frozen scientific contract for Phase 2A-S depth attenuation diagnostic."""

from __future__ import annotations

DEPTHS = (3, 4, 5)
DIFFERENCES = (0x00000001, 0x00000100)
ARCHITECTURE = "byte_tanh_mlp"
PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

DATASET_SEEDS = (72001, 72019, 72031, 72043, 72053, 72071, 72089, 72101)
MODEL_SEEDS = (82003, 82013, 82021, 82037, 82051, 82067, 82073, 82087)
PERMUTATION_SEEDS = {3: 92003, 4: 92009, 5: 92021}
PERMUTATION_REPETITIONS = 10_000

CANDIDATE_COUNT = 6
PAIRED_REPLICATES = 8
TRAININGS_PER_CELL = CANDIDATE_COUNT * PAIRED_REPLICATES
TRAININGS_PER_DEPTH = TRAININGS_PER_CELL * len(DIFFERENCES)
TOTAL_TRAININGS = len(DEPTHS) * TRAININGS_PER_DEPTH

MIN_CANDIDATE_ADVANTAGE = 0.04
MIN_NULL_MARGIN = 0.02
H5_H4_MAX_RATIO = 0.50
R5_R4_MAX_RATIO = 0.75
NEURAL_EVOLUTIONARY_PRESSURE = False


def classify_depth_attenuation(
    prerequisites_pass: bool,
    heterogeneity_by_depth: dict[int, float],
    range_by_depth: dict[int, float],
) -> str:
    """Apply the preregistered Phase-2A-S magnitude-based classification."""

    if not bool(prerequisites_pass):
        return "phase2as_inconclusive_prerequisites"

    h3, h4, h5 = (float(heterogeneity_by_depth[d]) for d in DEPTHS)
    r3, r4, r5 = (float(range_by_depth[d]) for d in DEPTHS)

    monotonic_h = h3 > h4 > h5
    monotonic_r = r3 >= r4 > r5
    if not (monotonic_h and monotonic_r):
        return "phase2as_depth_attenuation_not_supported"

    if h4 <= 0.0 or r4 <= 0.0:
        return "phase2as_depth_attenuation_not_supported"

    ratio_h = h5 / h4
    ratio_r = r5 / r4
    if ratio_h <= H5_H4_MAX_RATIO and ratio_r <= R5_R4_MAX_RATIO:
        return "phase2as_depth_attenuation_supported"
    return "phase2as_weak_attenuation"
