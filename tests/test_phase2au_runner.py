from __future__ import annotations

from adversarial_sbox.phase2au import TOTAL_NEURAL_TRAININGS
from adversarial_sbox.phase2au_runner import (
    _cell_spec,
    load_committed_panel,
    qualification_verdict,
)


def test_phase2au_runner_loads_only_the_committed_fresh_panel() -> None:
    panel = load_committed_panel()
    assert len(panel) == 6
    assert tuple(item["source_seed"] for item in panel) == (
        90601,
        90631,
        90703,
        90709,
        90671,
        90641,
    )


def test_phase2au_runner_cell_specs_are_frozen() -> None:
    assert _cell_spec("bit_relu_mlp", 0x00000001) == ("bit_relu_mlp", 4, 0x00000001)
    assert _cell_spec("bit_relu_mlp", 0x00000100) == ("bit_relu_mlp", 4, 0x00000100)
    assert _cell_spec("byte_tanh_mlp", 0x00000001) == ("byte_tanh_mlp", 4, 0x00000001)
    assert _cell_spec("byte_tanh_mlp", 0x00000100) == ("byte_tanh_mlp", 4, 0x00000100)


def test_phase2au_verdict_is_fail_closed() -> None:
    all_green = {
        "training_count_exact": True,
        "panel_revalidated": True,
        "deterministic_receipts": True,
        "no_neural_evolutionary_pressure": True,
        "bit_heterogeneity": True,
        "byte_heterogeneity": True,
        "bit_range": True,
        "byte_range": True,
        "cross_architecture_rank": True,
        "bit_signal": True,
        "byte_signal": True,
        "consensus_heterogeneity": True,
        "consensus_range": True,
        "split_half_consensus_rank": True,
    }
    assert TOTAL_NEURAL_TRAININGS == 192
    assert qualification_verdict(all_green) == "phase2au_depth4_consensus_oracle_qualified"
    bad = dict(all_green, cross_architecture_rank=False)
    assert qualification_verdict(bad) == "phase2au_oracle_not_qualified"
    inconclusive = dict(all_green, panel_revalidated=False)
    assert qualification_verdict(inconclusive) == "phase2au_inconclusive_prerequisites"
