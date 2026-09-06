"""Red-first runner contract for Phase 2A-P."""

from adversarial_sbox.phase2ap import TOTAL_TRAININGS
from adversarial_sbox.phase2ap_runner import expected_cell_keys, load_frozen_panel


def test_phase2ap_runner_frozen_shape():
    assert len(load_frozen_panel()) == 6
    assert expected_cell_keys() == {
        (3, "byte_tanh_mlp", 0x00000001),
        (3, "byte_tanh_mlp", 0x00000100),
        (4, "byte_tanh_mlp", 0x00000001),
        (4, "byte_tanh_mlp", 0x00000100),
        (5, "byte_tanh_mlp", 0x00000001),
        (5, "byte_tanh_mlp", 0x00000100),
    }
    assert TOTAL_TRAININGS == 720
