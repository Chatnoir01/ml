"""Red-first runner contract for Phase 2A-U."""

from adversarial_sbox.phase2au_runner import expected_cell_keys, load_frozen_panel


def test_phase2au_runner_has_exact_four_cells_and_frozen_panel():
    assert expected_cell_keys() == (
        ("A", 0x00000001),
        ("A", 0x00000100),
        ("B", 0x00000001),
        ("B", 0x00000100),
    )
    assert len(load_frozen_panel()) == 6
