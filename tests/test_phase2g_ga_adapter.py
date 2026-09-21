"""RED contract for the real Phase 2G five-generation GA/B1 block adapter.

Synthetic only: dependency injection prevents real neural training and avoids a
scientific Phase-2G run. The production adapter must nevertheless preserve the
historical GA geometry and let checkpoint scores act only through frozen B1
shortlist/survival ordering.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from adversarial_sbox.evolution import ClassicalMetrics
from adversarial_sbox.phase2g import EVOLUTION_SEEDS
from adversarial_sbox.phase2g_ga_adapter import Phase2GGABlockAdapter
from adversarial_sbox.phase2g_preconditions import make_s_shuffle_stream
from adversarial_sbox.provenance import fingerprint_sbox


def _sbox(offset: int) -> tuple[int, ...]:
    return tuple(list(range(offset, 256)) + list(range(offset)))


def _population(start: int = 0) -> tuple[tuple[int, ...], ...]:
    return tuple(_sbox((start + index) % 256) for index in range(20))


def _fake_evaluator(candidate: tuple[int, ...]) -> ClassicalMetrics:
    # Keep all candidates in a narrow classical neighborhood so B1 opportunities
    # exist, while retaining deterministic classical differences.
    value = int(candidate[0])
    return ClassicalMetrics(
        nonlinearity=104 + (value % 3),
        differential_uniformity=4,
        max_linear_correlation=32,
        sac_score=0.5,
        algebraic_degree=6,
        fingerprint=fingerprint_sbox(candidate),
    )


def _fake_parent_selector(shortlist, metrics):
    assert len(shortlist) == 8
    assert all(candidate in metrics for candidate in shortlist)
    return tuple(shortlist[:4])


class ProposalFactory:
    def __init__(self) -> None:
        self.calls: list[tuple[int, tuple[tuple[int, ...], ...]]] = []
        self.next_offset = 80

    def __call__(self, *, parents, rng, seen_ever, count):
        assert len(parents) == 4
        assert count == 16
        self.calls.append((count, tuple(parents)))
        batch = []
        while len(batch) < count:
            candidate = _sbox(self.next_offset % 256)
            self.next_offset += 1
            if candidate in seen_ever:
                continue
            seen_ever.add(candidate)
            batch.append(candidate)
        return tuple(batch)


class FakeScoreLedger:
    def __init__(self) -> None:
        self._cache: dict[tuple[int, ...], float] = {}
        self.score_calls: list[tuple[int, ...]] = []

    def score(self, candidate):
        frozen = tuple(candidate)
        if frozen not in self._cache:
            self.score_calls.append(frozen)
            self._cache[frozen] = float((frozen[0] % 17) / 100.0)
        return self._cache[frozen]

    @property
    def cache_size(self) -> int:
        return len(self._cache)


class LedgerFactory:
    def __init__(self) -> None:
        self.calls: list[object] = []
        self.ledgers: list[FakeScoreLedger] = []

    def __call__(self, bundle):
        self.calls.append(bundle)
        ledger = FakeScoreLedger()
        self.ledgers.append(ledger)
        return ledger


@dataclass(frozen=True)
class FakeBundle:
    arm: str
    evolution_seed: int
    checkpoint_generation: int
    model_count: int = 16
    training_count: int = 16


def _adapter(arm: str, *, proposals=None, ledgers=None) -> Phase2GGABlockAdapter:
    return Phase2GGABlockAdapter(
        arm=arm,
        evolution_seed=EVOLUTION_SEEDS[0],
        evaluator=_fake_evaluator,
        parent_selector=_fake_parent_selector,
        proposal_factory=proposals or ProposalFactory(),
        score_ledger_factory=ledgers or LedgerFactory(),
    )


def test_real_block_runs_exact_five_generations_with_historical_geometry() -> None:
    proposals = ProposalFactory()
    ledgers = LedgerFactory()
    adapter = _adapter("A", proposals=proposals, ledgers=ledgers)
    seed = EVOLUTION_SEEDS[0]
    bundle = FakeBundle("A", seed, 0)

    result = adapter.evolve_block(
        population=_population(),
        start_generation=0,
        end_generation=5,
        selection_enabled=True,
        model=bundle,
        shuffle_stream=None,
    )

    assert len(result) == 20
    assert len(set(result)) == 20
    assert len(proposals.calls) == 5
    assert all(count == 16 for count, _parents in proposals.calls)
    assert adapter.completed_generations == 5
    assert adapter.classical_evaluations == 100  # 20 initial + 5*16 unique proposals
    assert len(adapter.selection_events) == 10  # shortlist + survival per generation
    assert [event["stage"] for event in adapter.selection_events] == [
        stage for _ in range(5) for stage in ("shortlist", "survival")
    ]
    assert len(ledgers.calls) == 1
    assert ledgers.ledgers[0].score_calls  # neural pressure was actually consulted


def test_c_is_strict_audit_only_and_never_constructs_selection_score_ledger() -> None:
    ledgers = LedgerFactory()
    adapter = _adapter("C", ledgers=ledgers)
    bundle = FakeBundle("C", EVOLUTION_SEEDS[0], 0)

    result = adapter.evolve_block(
        population=_population(),
        start_generation=0,
        end_generation=5,
        selection_enabled=False,
        model=bundle,
        shuffle_stream=None,
    )

    assert len(result) == 20
    assert ledgers.calls == []
    assert all(event["neural_selection_enabled"] is False for event in adapter.selection_events)
    assert all(event["scored_candidate_count"] == 0 for event in adapter.selection_events)


def test_s_requires_matching_persistent_checkpoint_stream() -> None:
    seed = EVOLUTION_SEEDS[0]
    bundle = FakeBundle("S", seed, 0)
    stream = make_s_shuffle_stream(seed, 0)
    adapter = _adapter("S")

    result = adapter.evolve_block(
        population=_population(),
        start_generation=0,
        end_generation=5,
        selection_enabled=True,
        model=bundle,
        shuffle_stream=stream,
    )
    assert len(result) == 20
    assert all(event["shuffle_rng_seed"] == stream.rng_seed for event in adapter.selection_events)

    with pytest.raises(ValueError):
        _adapter("S").evolve_block(
            population=_population(),
            start_generation=0,
            end_generation=5,
            selection_enabled=True,
            model=bundle,
            shuffle_stream=None,
        )


def test_block_fails_closed_on_schedule_selection_or_bundle_identity_drift() -> None:
    seed = EVOLUTION_SEEDS[0]
    with pytest.raises(ValueError):
        _adapter("A").evolve_block(
            population=_population(),
            start_generation=0,
            end_generation=4,
            selection_enabled=True,
            model=FakeBundle("A", seed, 0),
            shuffle_stream=None,
        )
    with pytest.raises(ValueError):
        _adapter("C").evolve_block(
            population=_population(),
            start_generation=0,
            end_generation=5,
            selection_enabled=True,
            model=FakeBundle("C", seed, 0),
            shuffle_stream=None,
        )
    with pytest.raises(ValueError):
        _adapter("A").evolve_block(
            population=_population(),
            start_generation=0,
            end_generation=5,
            selection_enabled=True,
            model=FakeBundle("F", seed, 0),
            shuffle_stream=None,
        )
