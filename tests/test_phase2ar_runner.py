"""Red-first execution/aggregation contract for Phase 2A-R."""

from adversarial_sbox.phase2ar import TOTAL_TRAININGS
from adversarial_sbox.phase2ar_runner import (
    expected_cell_keys,
    load_frozen_panel,
    summarize_regime_prerequisites,
)


def test_phase2ar_expected_cells_are_exact():
    assert expected_cell_keys() == {
        ("A", "bit_relu_mlp", 4, 0x00000001),
        ("A", "bit_relu_mlp", 4, 0x00000100),
        ("B", "byte_tanh_mlp", 4, 0x00000001),
        ("B", "byte_tanh_mlp", 4, 0x00000100),
        ("C", "byte_tanh_mlp", 5, 0x00000001),
        ("C", "byte_tanh_mlp", 5, 0x00000100),
        ("D", "byte_tanh_mlp", 5, 0x00010000),
        ("D", "byte_tanh_mlp", 5, 0x01000000),
    }
    assert TOTAL_TRAININGS == 240


def test_phase2ar_uses_exact_phase2a_frozen_panel():
    panel = load_frozen_panel()
    assert len(panel) == 6
    assert tuple(item["source_seed"] for item in panel) == (2609, 2657, 2647, 2633, 2663, 2621)


def test_phase2ar_regime_prerequisites_require_every_signal_check():
    good = {
        "training_count_exact": True,
        "panel_revalidated": True,
        "heterogeneity": True,
        "range": True,
        "signal": True,
        "deterministic_receipts": True,
    }
    assert summarize_regime_prerequisites(good) is True
    for key in tuple(good):
        bad = dict(good)
        bad[key] = False
        assert summarize_regime_prerequisites(bad) is False
