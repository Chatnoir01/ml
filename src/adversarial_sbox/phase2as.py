"""Frozen scientific contract for Phase 2A-S depth attenuation diagnostic."""

DEPTHS = (3, 4, 5)
DIFFERENCES = (0x00000001, 0x00000100)
PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
PERMUTATION_REPETITIONS = 10_000
CANDIDATE_COUNT = 6
PAIRED_REPLICATES = 5
TOTAL_TRAININGS = len(DEPTHS) * CANDIDATE_COUNT * len(DIFFERENCES) * PAIRED_REPLICATES
RANK_STABILITY_THRESHOLD = 0.60
HETEROGENEITY_ALPHA = 0.05
MIN_CANDIDATE_RANGE = 0.015
MIN_CANDIDATE_ADVANTAGE = 0.04
MIN_NULL_MARGIN = 0.02
NEURAL_EVOLUTIONARY_PRESSURE = False


def classify_depth_signal(reliable_by_depth: dict[int, bool]) -> str:
    """Apply the preregistered primary Phase 2A-S classification only."""
    pattern = tuple(bool(reliable_by_depth[d]) for d in DEPTHS)
    if pattern == (True, True, False):
        return "phase2as_depth_attenuation_supported"
    if pattern == (True, False, False):
        return "phase2as_early_attenuation_supported"
    if pattern == (True, True, True):
        return "phase2as_no_reliability_loss"
    if pattern in {(False, True, False), (False, False, True), (False, True, True), (True, False, True)}:
        return "phase2as_nonmonotone_signal"
    return "phase2as_inconclusive"
