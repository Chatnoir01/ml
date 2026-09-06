"""Runner invariants for Phase 2A-U2; no neural training is executed."""

from adversarial_sbox.neural100 import PAIR_COUNT
from adversarial_sbox.phase2au2_runner import (
    EXPECTED_TEST_SIZE,
    EXPECTED_TRAIN_SIZE,
    EXPECTED_VALIDATION_SIZE,
    expected_cell_keys,
    load_frozen_panel,
)


def test_phase2au2_runner_frozen_cells_panel_and_dataset_shape():
    assert expected_cell_keys() == (
        ("A", 0x00000001),
        ("A", 0x00000100),
        ("B", 0x00000001),
        ("B", 0x00000100),
    )
    assert len(load_frozen_panel()) == 6
    assert PAIR_COUNT == 8192
    assert EXPECTED_TRAIN_SIZE == 5734
    assert EXPECTED_VALIDATION_SIZE == 1228
    assert EXPECTED_TEST_SIZE == 1230
    assert EXPECTED_TRAIN_SIZE + EXPECTED_VALIDATION_SIZE + EXPECTED_TEST_SIZE == PAIR_COUNT
