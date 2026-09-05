"""Frozen scientific contract for Phase 2A-R neural rank decomposition."""

from __future__ import annotations

PANEL_DIGEST_SHA256 = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"

DATASET_SEEDS = (71001, 71009, 71023, 71039, 71059)
MODEL_SEEDS = (81001, 81013, 81031, 81041, 81047)

REGIMES = (
    ("A", "bit_relu_mlp", 4, (0x00000001, 0x00000100)),
    ("B", "byte_tanh_mlp", 4, (0x00000001, 0x00000100)),
    ("C", "byte_tanh_mlp", 5, (0x00000001, 0x00000100)),
    ("D", "byte_tanh_mlp", 5, (0x00010000, 0x01000000)),
)

PERMUTATION_REPETITIONS = 10_000
PERMUTATION_SEEDS = {
    "A": 91001,
    "B": 91009,
    "C": 91023,
    "D": 91039,
}

PANEL_SIZE = 6
REPLICATES = 5
TRAININGS_PER_CELL = PANEL_SIZE * REPLICATES
TRAININGS_PER_REGIME = TRAININGS_PER_CELL * 2
TOTAL_TRAININGS = TRAININGS_PER_REGIME * len(REGIMES)
RANK_STABILITY_THRESHOLD = 0.60


def regime_spec(regime: str) -> tuple[str, str, int, tuple[int, int]]:
    for spec in REGIMES:
        if spec[0] == str(regime):
            return spec
    raise ValueError(f"undeclared Phase 2A-R regime {regime!r}")


def classify_diagnostic(
    signal_prerequisites_pass: bool,
    rho_ab: float,
    rho_bc: float,
    rho_cd: float,
) -> str:
    """Apply the preregistered Phase-2A-R diagnostic classification."""

    if not bool(signal_prerequisites_pass):
        return "phase2ar_inconclusive_signal"

    stable = (
        float(rho_ab) >= RANK_STABILITY_THRESHOLD,
        float(rho_bc) >= RANK_STABILITY_THRESHOLD,
        float(rho_cd) >= RANK_STABILITY_THRESHOLD,
    )
    unstable = tuple(not item for item in stable)
    count = sum(unstable)
    if count == 0:
        return "phase2ar_no_adjacent_instability"
    if count >= 2:
        return "phase2ar_multiple_instabilities"
    if unstable[0]:
        return "phase2ar_architecture_transition_localized"
    if unstable[1]:
        return "phase2ar_round_transition_localized"
    return "phase2ar_difference_transition_localized"
