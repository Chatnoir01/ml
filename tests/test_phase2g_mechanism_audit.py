"""RED contract for Phase 2G mechanism-activity audit receipts.

Synthetic only. No neural training, held-out H scoring, or scientific Phase-2G
execution occurs here. The GA adapter must expose enough information at every
B1 cutoff to compute the frozen mechanism-activity gate without reconstructing
selection decisions after the fact.
"""

from __future__ import annotations

from adversarial_sbox.evolution import ClassicalMetrics, primary_security_key
from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_ga_adapter import Phase2GGABlockAdapter
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
        # Historical order is descending by candidate when feasibility ties.
        # Lower score is preferred, so this deliberately flips membership at
        # the cutoff while staying entirely inside the synthetic B1 band.
        return float(tuple(candidate)[0])


def test_b1_event_receipts_are_sufficient_for_cross_key_mechanism_gate() -> None:
    seed = EVOLUTION_SEEDS[0]
    population = _population()
    adapter = Phase2GGABlockAdapter(
        arm="A",
        evolution_seed=seed,
        evaluator=_evaluator,
    )
    adapter._initialize_if_needed(population)

    ordered = adapter._order_at_cutoff(
        population,
        cutoff=8,
        generation=0,
        stage="shortlist",
        neural_selection_enabled=True,
        score_ledger=_ScoreLedger(),
        shuffle_stream=None,
    )
    assert len(ordered) == 20

    event = adapter.selection_events[-1]
    required = {
        "cutoff_reference_fingerprint",
        "cutoff_reference_metrics",
        "protected_key",
        "eligible_protected_keys",
        "assigned_scores",
        "selected_before",
        "selected_after",
        "entered",
        "exited",
        "score_caused_entered",
        "cross_protected_key_membership_change",
    }
    assert required <= set(event)

    assert event["boundary_opportunity"] is True
    assert event["membership_changed"] is True
    assert event["cross_protected_key_membership_change"] is True
    assert event["score_caused_entered"] == event["entered"]
    assert set(event["entered"]).isdisjoint(event["exited"])
    assert set(event["selected_after"]) - set(event["selected_before"]) == set(event["entered"])
    assert set(event["selected_before"]) - set(event["selected_after"]) == set(event["exited"])

    # Cross-key must be derivable from the receipted protected keys themselves.
    boundary_key = tuple(event["protected_key"])
    entered_keys = {
        tuple(event["eligible_protected_keys"][fingerprint])
        for fingerprint in event["entered"]
    }
    assert any(key != boundary_key for key in entered_keys)

    # The recorded boundary key must match the exact classical protected key.
    reference_fp = event["cutoff_reference_fingerprint"]
    reference = next(candidate for candidate in population if fingerprint_sbox(candidate) == reference_fp)
    assert tuple(event["protected_key"]) == primary_security_key(
        _evaluator(reference), adapter.constraints
    )
