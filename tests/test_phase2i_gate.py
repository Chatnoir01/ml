from __future__ import annotations

import pytest

from adversarial_sbox.phase2i_gate import select_intervention_family


@pytest.mark.parametrize(
    ("mechanism", "family"),
    [
        ("H1", "historical_replay_archive"),
        ("H2", "lagged_or_slow_target"),
        ("H3", "bounded_neural_influence"),
        ("H4", "partial_curriculum_retention"),
    ],
)
def test_phase2i_gate_maps_one_frozen_mechanism(mechanism: str, family: str) -> None:
    assert (
        select_intervention_family(
            {"phase": "2H-result", "frozen": True, "supported_mechanisms": [mechanism]}
        )
        == family
    )


def test_phase2i_gate_rejects_unfrozen_diagnostic() -> None:
    with pytest.raises(ValueError, match="not frozen"):
        select_intervention_family(
            {"phase": "2H-result", "frozen": False, "supported_mechanisms": ["H1"]}
        )


def test_phase2i_gate_forbids_rescue_sweep() -> None:
    with pytest.raises(RuntimeError, match="rescue sweep"):
        select_intervention_family(
            {"phase": "2H-result", "frozen": True, "supported_mechanisms": []}
        )


def test_phase2i_gate_forbids_unpreregistered_combination() -> None:
    with pytest.raises(RuntimeError, match="combination"):
        select_intervention_family(
            {"phase": "2H-result", "frozen": True, "supported_mechanisms": ["H1", "H4"]}
        )


def test_phase2i_gate_rejects_unknown_mechanism() -> None:
    with pytest.raises(ValueError, match="unknown"):
        select_intervention_family(
            {"phase": "2H-result", "frozen": True, "supported_mechanisms": ["H9"]}
        )
