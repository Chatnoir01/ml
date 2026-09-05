"""Execution-gate tests for the Phase-2A neural runner."""

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


def test_neural_execution_loads_only_the_committed_frozen_panel():
    panel = load_committed_panel()
    assert len(panel) == 6
    assert tuple(candidate["source_seed"] for candidate in panel) == (
        2609,
        2657,
        2647,
        2633,
        2663,
        2621,
    )
    assert tuple(candidate["fingerprint"] for candidate in panel) == (
        "300769cec5fefe30060e5f04a2a976b728900ee2b121cbdb81e09ce5260b686b",
        "47db19cbaf316bdfbd6cccaa2c96934122edb259758b301ac8e812c9a84e4c3b",
        "72c4092c42e34efea6ee127355194ddfa254168759c67f9a4913a718c9830f9e",
        "c2316833af9f4c0f73a8f44a2132d39ce414a14c4fd45553279e7fd87ae3f1e3",
        "d6744195ad185ae528c68f6b40f658b94aee4682adf467a2d3154324140677c8",
        "dfb70187d44c755a4fa4fa650602ce92d17e5ad1ef232a223780f1c5268a3df4",
    )
