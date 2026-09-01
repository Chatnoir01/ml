import pytest

from adversarial_sbox.cryptoshield import (
    differential_distribution_table,
    linear_approximation_table,
)
from adversarial_sbox.phase1h import (
    build_plateau_diagnostics,
    projected_ddt_count,
    projected_lat_correlation,
    run_development,
    score_proposal,
)
from adversarial_sbox.references import AES_SBOX


def _cycle4(sbox, indices=(0, 1, 2, 3)):
    out = list(sbox)
    values = [out[index] for index in indices]
    rotated = [values[-1], *values[:-1]]
    for index, value in zip(indices, rotated):
        out[index] = value
    return tuple(out)


def test_aes_plateau_diagnostics_match_known_maxima():
    diagnostics = build_plateau_diagnostics(AES_SBOX, panel_mode="ties")
    assert diagnostics.lat_max == 32
    assert diagnostics.ddt_max == 4
    assert diagnostics.lat_cells
    assert diagnostics.ddt_cells
    assert diagnostics.hotspot_indices


def test_local_lat_projection_is_exact_for_cycle4():
    parent = tuple(AES_SBOX)
    child = _cycle4(parent)
    changed = (0, 1, 2, 3)
    diagnostics = build_plateau_diagnostics(parent, panel_mode="band")
    child_lat = linear_approximation_table(child)

    for cell in diagnostics.lat_cells[:32]:
        projected = projected_lat_correlation(parent, child, changed, cell)
        assert projected == child_lat[cell.input_mask][cell.output_mask]


def test_local_ddt_projection_is_exact_for_cycle4():
    parent = tuple(AES_SBOX)
    child = _cycle4(parent)
    changed = (0, 1, 2, 3)
    diagnostics = build_plateau_diagnostics(parent, panel_mode="band")
    child_ddt = differential_distribution_table(child)

    for cell in diagnostics.ddt_cells[:32]:
        projected = projected_ddt_count(parent, child, changed, cell)
        assert projected == child_ddt[cell.input_difference][cell.output_difference]


def test_proposal_score_is_deterministic_and_preserves_cycle4_contract():
    parent = tuple(AES_SBOX)
    child = _cycle4(parent)
    diagnostics = build_plateau_diagnostics(parent, panel_mode="ties")
    first = score_proposal(parent, child, diagnostics, order=7)
    second = score_proposal(parent, child, diagnostics, order=7)
    assert first == second
    assert first.projected_lat_max >= 0
    assert first.projected_ddt_max >= 0


def test_phase1h_confirmation_seed_is_rejected_before_reproduction():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(
            proposal_pool=32,
            panel_mode="ties",
            seeds=(1601,),
            evaluations=1,
        )
