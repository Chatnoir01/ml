"""Frozen scientific contract for Phase 2A-T depth-profile replication."""

from __future__ import annotations

DEPTHS = (3, 4, 5)
DIFFERENCES = (0x00000001, 0x00000100)
ARCHITECTURE = "byte_tanh_mlp"
PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

DATASET_SEEDS = (73003, 73019, 73031, 73043, 73061, 73079, 73091, 73103)
MODEL_SEEDS = (83003, 83017, 83029, 83047, 83059, 83071, 83089, 83101)
PERMUTATION_SEEDS = {3: 93001, 4: 93011, 5: 93023}
PERMUTATION_REPETITIONS = 10_000

CANDIDATE_COUNT = 6
PAIRED_REPLICATES = 8
TRAININGS_PER_CELL = CANDIDATE_COUNT * PAIRED_REPLICATES
TRAININGS_PER_DEPTH = TRAININGS_PER_CELL * len(DIFFERENCES)
TOTAL_TRAININGS = len(DEPTHS) * TRAININGS_PER_DEPTH

MIN_CANDIDATE_ADVANTAGE = 0.04
MIN_NULL_MARGIN = 0.02
DEPTH4_HETEROGENEITY_P_MAX = 0.05
NEURAL_EVOLUTIONARY_PRESSURE = False


def classify_depth_profile(
    prerequisites_pass: bool,
    heterogeneity_by_depth: dict[int, float],
    range_by_depth: dict[int, float],
    mean_advantage_by_depth: dict[int, float],
    depth4_heterogeneity_p: float,
) -> str:
    """Apply the preregistered Phase-2A-T fresh-seed profile classification."""

    if not bool(prerequisites_pass):
        return "phase2at_inconclusive_prerequisites"

    h3, h4, h5 = (float(heterogeneity_by_depth[d]) for d in DEPTHS)
    r3, r4, r5 = (float(range_by_depth[d]) for d in DEPTHS)
    m3, m4, m5 = (float(mean_advantage_by_depth[d]) for d in DEPTHS)

    directional_peak = (
        h4 > h3
        and h4 > h5
        and r4 > r3
        and r4 > r5
        and m3 > m4 > m5
    )
    if not directional_peak:
        return "phase2at_depth_profile_not_replicated"

    if float(depth4_heterogeneity_p) < DEPTH4_HETEROGENEITY_P_MAX:
        return "phase2at_depth4_peak_replicated"
    return "phase2at_peak_direction_only"
