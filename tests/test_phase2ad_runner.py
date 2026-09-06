"""Red-first execution/aggregation contract for Phase 2A-D."""

from adversarial_sbox.phase2ad import TOTAL_TRAININGS, TRAININGS_PER_CELL
from adversarial_sbox.phase2ad_runner import (
    baseline_r4_requirements_pass,
    expected_cell_keys,
    load_frozen_panel,
)


def test_phase2ad_expected_cells_and_budget_are_exact():
    assert expected_cell_keys() == {
        (3, "byte_tanh_mlp", 0x00000001),
        (3, "byte_tanh_mlp", 0x00000100),
        (4, "byte_tanh_mlp", 0x00000001),
        (4, "byte_tanh_mlp", 0x00000100),
        (5, "byte_tanh_mlp", 0x00000001),
        (5, "byte_tanh_mlp", 0x00000100),
    }
    assert TRAININGS_PER_CELL == 60
    assert TOTAL_TRAININGS == 360


def test_phase2ad_uses_exact_frozen_phase2a_panel():
    panel = load_frozen_panel()
    assert len(panel) == 6
    assert tuple(item["source_seed"] for item in panel) == (2609, 2657, 2647, 2633, 2663, 2621)


def test_phase2ad_r4_baseline_requires_every_frozen_check():
    good = {
        "training_count_exact": True,
        "panel_revalidated": True,
        "deterministic_receipts": True,
        "seed_registry_exact": True,
        "neural_evolutionary_pressure_absent": True,
        "r4_heterogeneity": True,
        "r4_range": True,
        "r4_signal": True,
    }
    assert baseline_r4_requirements_pass(good) is True
    for key in tuple(good):
        bad = dict(good)
        bad[key] = False
        assert baseline_r4_requirements_pass(bad) is False
