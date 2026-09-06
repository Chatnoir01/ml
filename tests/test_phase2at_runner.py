from adversarial_sbox.phase2at_runner import expected_cell_keys, load_frozen_panel


def test_phase2at_runner_has_exact_six_cells_and_frozen_panel():
    assert expected_cell_keys() == (
        (3, 0x00000001),
        (3, 0x00000100),
        (4, 0x00000001),
        (4, 0x00000100),
        (5, 0x00000001),
        (5, 0x00000100),
    )
    assert len(load_frozen_panel()) == 6
