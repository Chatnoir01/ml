from __future__ import annotations

import pytest

from adversarial_sbox.phase2au import (
    CLASSICAL_SOURCE_SEEDS,
    DATASET_SEEDS,
    MODEL_SEEDS,
    PANEL_SIZE,
    TOTAL_NEURAL_TRAININGS,
    CandidateRecord,
    is_phase2au_eligible,
    select_phase2au_panel,
)


EXPECTED_CLASSICAL_SEEDS = (
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
EXPECTED_DATASET_SEEDS = (
    100003,
    100019,
    100043,
    100049,
    100057,
    100069,
    100103,
    100109,
)
EXPECTED_MODEL_SEEDS = (
    110003,
    110017,
    110023,
    110039,
    110051,
    110071,
    110083,
    110107,
)


def _record(seed: int, fingerprint: str, *, eligible: bool = True) -> CandidateRecord:
    # Identity is bijective; the scalar metrics below are contract fixtures only.
    return CandidateRecord(
        source_seed=seed,
        fingerprint=fingerprint,
        sbox=tuple(range(256)),
        differential_uniformity=8 if eligible else 10,
        nonlinearity=100,
        max_linear_correlation=56,
        algebraic_degree=7,
        sac_score=0.5,
    )


def test_frozen_phase2au_constants() -> None:
    assert CLASSICAL_SOURCE_SEEDS == EXPECTED_CLASSICAL_SEEDS
    assert DATASET_SEEDS == EXPECTED_DATASET_SEEDS
    assert MODEL_SEEDS == EXPECTED_MODEL_SEEDS
    assert PANEL_SIZE == 6
    assert TOTAL_NEURAL_TRAININGS == 192


def test_phase2au_eligibility_reuses_exact_classical_tuple() -> None:
    good = _record(90601, "a" * 64)
    bad = _record(90601, "b" * 64, eligible=False)
    assert is_phase2au_eligible(good)
    assert not is_phase2au_eligible(bad)


def test_panel_selection_is_one_per_seed_then_global_lexicographic_six() -> None:
    records = [
        _record(90601, "f" * 64),
        _record(90601, "0" * 64),  # same seed: must win locally
        _record(90617, "1" * 64),
        _record(90631, "2" * 64),
        _record(90641, "3" * 64),
        _record(90647, "4" * 64),
        _record(90659, "5" * 64),
        _record(90671, "6" * 64),
        _record(90677, "7" * 64, eligible=False),
    ]
    panel = select_phase2au_panel(records)
    assert tuple(item.source_seed for item in panel) == (
        90601,
        90617,
        90631,
        90641,
        90647,
        90659,
    )
    assert tuple(item.fingerprint for item in panel) == tuple(
        f"{digit}" * 64 for digit in "012345"
    )


def test_panel_selection_blocks_with_fewer_than_six_eligible_source_seeds() -> None:
    records = [_record(seed, f"{index}" * 64) for index, seed in enumerate(EXPECTED_CLASSICAL_SEEDS[:5])]
    with pytest.raises(ValueError, match="six eligible source seeds"):
        select_phase2au_panel(records)
