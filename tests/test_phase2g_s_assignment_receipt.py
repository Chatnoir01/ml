"""RED contract for Phase 2G shuffled-control assignment receipts.

Synthetic only. No neural training, held-out H scoring, or scientific Phase-2G
execution occurs here. Every real S-arm B1 opportunity must consume exactly one
persistent shuffle draw and receipt the exact candidate/score assignment used by
selection; audit must never replay or advance the scientific RNG a second time.
"""

from __future__ import annotations

from adversarial_sbox.evolution import ClassicalMetrics
from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_ga_adapter import Phase2GGABlockAdapter
from adversarial_sbox.phase2g_preconditions import make_s_shuffle_stream
from adversarial_sbox.provenance import fingerprint_sbox


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _population() -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox(index) for index in range(20))


def _evaluator(candidate: tuple[int, ...]) -> ClassicalMetrics:
    value = int(candidate[0])
    return ClassicalMetrics(
        nonlinearity=104 + (value % 3),
        differential_uniformity=4,
        max_linear_correlation=32,
        sac_score=0.5,
        algebraic_degree=6,
        fingerprint=fingerprint_sbox(candidate),
    )


class _ScoreLedger:
    def score(self, candidate) -> float:
        return float(tuple(candidate)[0])


def _run_once():
    seed = EVOLUTION_SEEDS[0]
    population = _population()
    adapter = Phase2GGABlockAdapter(
        arm="S",
        evolution_seed=seed,
        evaluator=_evaluator,
    )
    adapter._initialize_if_needed(population)
    stream = make_s_shuffle_stream(seed, 0)
    assert stream.draw_count == 0

    ordered = adapter._order_at_cutoff(
        population,
        cutoff=8,
        generation=0,
        stage="shortlist",
        neural_selection_enabled=True,
        score_ledger=_ScoreLedger(),
        shuffle_stream=stream,
    )
    return adapter, stream, ordered


def test_s_b1_opportunity_consumes_exactly_one_draw_and_receipts_used_assignment() -> None:
    adapter, stream, ordered = _run_once()
    assert len(ordered) == 20
    assert stream.draw_count == 1

    event = adapter.selection_events[-1]
    assert event["boundary_opportunity"] is True
    receipt = event["s_shuffle_assignment_receipt"]
    assert receipt is not None
    assert receipt["evolution_seed"] == EVOLUTION_SEEDS[0]
    assert receipt["checkpoint_generation"] == 0
    assert receipt["rng_seed"] == stream.rng_seed
    assert receipt["draw_index"] == 0
    assert len(receipt["receipt_sha256"]) == 64

    before = dict(receipt["before"])
    after = dict(receipt["after"])
    assert set(before) == set(event["b1_group"])
    assert set(after) == set(event["b1_group"])
    assert event["assigned_scores"] == after


def test_s_assignment_receipt_and_order_are_deterministic_without_double_draw() -> None:
    first_adapter, first_stream, first_order = _run_once()
    second_adapter, second_stream, second_order = _run_once()

    first_receipt = first_adapter.selection_events[-1]["s_shuffle_assignment_receipt"]
    second_receipt = second_adapter.selection_events[-1]["s_shuffle_assignment_receipt"]
    assert first_receipt == second_receipt
    assert [fingerprint_sbox(candidate) for candidate in first_order] == [
        fingerprint_sbox(candidate) for candidate in second_order
    ]
    assert first_stream.draw_count == second_stream.draw_count == 1
