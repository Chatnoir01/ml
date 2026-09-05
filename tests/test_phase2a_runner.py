"""Red-first execution-gate tests for the Phase-2A neural runner."""

import pytest

from adversarial_sbox.phase2a_runner import _cell_spec, load_committed_panel


def test_phase2a_cell_routing_is_frozen():
    assert _cell_spec("oracle", 0x00000001) == (
        "oracle",
        4,
        0x00000001,
        "bit_relu_mlp",
    )
    assert _cell_spec("challenger", 0x01000000) == (
        "challenger",
        5,
        0x01000000,
        "byte_tanh_mlp",
    )
    with pytest.raises(ValueError):
        _cell_spec("oracle", 0xDEADBEEF)


def test_neural_execution_is_blocked_until_panel_is_committed():
    with pytest.raises(RuntimeError, match="blocked"):
        load_committed_panel()
