"""Red-first contract for Phase 2A fresh-panel Neural Oracle qualification."""

from adversarial_sbox.phase2a import (
    CHALLENGER_DIFFERENCES,
    CHALLENGER_ROUNDS,
    CHALLENGER_ARCHITECTURE,
    DATASET_SEEDS,
    MODEL_SEEDS,
    ORACLE_ARCHITECTURE,
    ORACLE_DIFFERENCES,
    ORACLE_ROUNDS,
    PANEL_SIZE,
    TOTAL_TRAININGS,
    CandidateRecord,
    qualification_verdict,
    select_fresh_panel,
)


def _candidate(seed: int, fingerprint: str, *, du: int = 8, nl: int = 100):
    return CandidateRecord(
        source_seed=seed,
        fingerprint=fingerprint,
        sbox=tuple(range(256)),
        differential_uniformity=du,
        nonlinearity=nl,
        max_linear_correlation=56,
        algebraic_degree=7,
        sac_score=0.5,
    )


def test_phase2a_frozen_contract():
    assert PANEL_SIZE == 6
    assert ORACLE_ARCHITECTURE == "bit_relu_mlp"
    assert ORACLE_ROUNDS == 4
    assert ORACLE_DIFFERENCES == (0x00000001, 0x00000100)
    assert CHALLENGER_ARCHITECTURE == "byte_tanh_mlp"
    assert CHALLENGER_ROUNDS == 5
    assert CHALLENGER_DIFFERENCES == (0x00010000, 0x01000000)
    assert DATASET_SEEDS == (51001, 51007, 51011, 51031, 51047)
    assert MODEL_SEEDS == (61001, 61007, 61027, 61031, 61043)
    assert TOTAL_TRAININGS == 120


def test_panel_selection_is_classical_only_one_per_seed_and_lexicographic():
    records = [
        _candidate(2609, "f" * 64),
        _candidate(2609, "0" * 64),
        _candidate(2617, "1" * 64),
        _candidate(2621, "2" * 64),
        _candidate(2633, "3" * 64),
        _candidate(2647, "4" * 64),
        _candidate(2657, "5" * 64),
        _candidate(2663, "6" * 64),
        _candidate(2671, "7" * 64),
        _candidate(2683, "8" * 64),
        _candidate(2671, "9" * 64, du=10),
    ]
    panel = select_fresh_panel(records)
    assert len(panel) == 6
    assert [item.fingerprint for item in panel] == [
        "0" * 64,
        "1" * 64,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
    ]
    assert len({item.source_seed for item in panel}) == PANEL_SIZE


def test_panel_selection_blocks_if_fewer_than_six_eligible_seeds():
    records = [_candidate(seed, f"{index:064x}") for index, seed in enumerate((2609, 2617, 2621, 2633, 2647))]
    try:
        select_fresh_panel(records)
    except ValueError as exc:
        assert "six" in str(exc).lower()
    else:
        raise AssertionError("Phase 2A must block with fewer than six eligible source seeds")


def test_qualification_requires_every_preregistered_check():
    checks = {
        "training_count_exact": True,
        "panel_revalidated": True,
        "oracle_heterogeneity": True,
        "challenger_heterogeneity": True,
        "oracle_range": True,
        "challenger_range": True,
        "rank_replication": True,
        "oracle_signal": True,
        "challenger_signal": True,
        "deterministic_receipts": True,
    }
    assert qualification_verdict(checks) == "phase2a_oracle_qualified"
    checks["rank_replication"] = False
    assert qualification_verdict(checks) == "phase2a_oracle_not_qualified"
