import hashlib
import json
import random

import pytest

from adversarial_sbox.evolution import ClassicalMetrics, HardConstraints
from adversarial_sbox.phase2g_selection import (
    CheckpointScoreLedger,
    apply_phase2g_cutoff_order,
)
from adversarial_sbox.provenance import fingerprint_sbox


def _canonical(payload):
    clean = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _score_payload(candidate, score):
    payload = {
        "candidate_fingerprint": fingerprint_sbox(candidate),
        "training_count": 0,
        "neural_advantage": float(score),
    }
    payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload


def _metric(name, *, nl, du=4, lat=30, degree=7):
    return ClassicalMetrics(
        nonlinearity=nl,
        differential_uniformity=du,
        max_linear_correlation=lat,
        sac_score=0.5,
        algebraic_degree=degree,
        fingerprint=name,
    )


def test_checkpoint_score_ledger_caches_exact_checkpoint_identity():
    candidate = tuple(range(256))
    calls = []

    def scorer(sbox):
        calls.append(fingerprint_sbox(sbox))
        return _score_payload(sbox, 0.25)

    ledger = CheckpointScoreLedger(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=5,
        scorer=scorer,
    )
    assert ledger.score(candidate) == 0.25
    assert ledger.score(candidate) == 0.25
    assert len(calls) == 1
    assert len(ledger.receipts) == 1
    receipt = ledger.receipts[0]
    assert receipt.cache_key == ("A", 726011, 5, fingerprint_sbox(candidate))
    assert receipt.training_count == 0

    later = CheckpointScoreLedger(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=10,
        scorer=scorer,
    )
    assert later.score(candidate) == 0.25
    assert len(calls) == 2
    assert later.receipts[0].cache_key[2] == 10


def test_checkpoint_score_ledger_fails_closed_on_receipt_tamper():
    candidate = tuple(range(256))

    def scorer(sbox):
        payload = _score_payload(sbox, 0.25)
        payload["scientific_payload_sha256"] = "0" * 64
        return payload

    ledger = CheckpointScoreLedger(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=5,
        scorer=scorer,
    )
    with pytest.raises(RuntimeError, match="receipt"):
        ledger.score(candidate)


def test_phase2g_order_never_crosses_outside_frozen_b1_band():
    constraints = HardConstraints()
    outside_high = ("outside_high", _metric("outside_high", nl=112), 0.99)
    cutoff = ("cutoff", _metric("cutoff", nl=108), 0.90)
    eligible = ("eligible", _metric("eligible", nl=107, du=5, lat=31), 0.10)
    outside_low = ("outside_low", _metric("outside_low", nl=104), 0.00)
    items = [outside_high, cutoff, eligible, outside_low]

    classical = apply_phase2g_cutoff_order(
        items,
        constraints=constraints,
        arm="C",
        cutoff_metrics=cutoff[1],
        shuffle_rng=None,
    )
    adaptive = apply_phase2g_cutoff_order(
        items,
        constraints=constraints,
        arm="A",
        cutoff_metrics=cutoff[1],
        shuffle_rng=None,
    )
    fixed = apply_phase2g_cutoff_order(
        items,
        constraints=constraints,
        arm="F",
        cutoff_metrics=cutoff[1],
        shuffle_rng=None,
    )

    assert [item[0] for item in classical] == ["outside_high", "cutoff", "eligible", "outside_low"]
    assert [item[0] for item in adaptive] == ["outside_high", "eligible", "cutoff", "outside_low"]
    assert [item[0] for item in fixed] == ["outside_high", "eligible", "cutoff", "outside_low"]
    assert adaptive[0] == outside_high
    assert adaptive[-1] == outside_low


def test_shuffled_arm_is_deterministic_for_same_persistent_rng_state():
    constraints = HardConstraints()
    cutoff = ("cutoff", _metric("cutoff", nl=108), 0.90)
    items = [
        ("outside_high", _metric("outside_high", nl=112), 0.99),
        cutoff,
        ("eligible1", _metric("eligible1", nl=107, du=5, lat=31), 0.10),
        ("eligible2", _metric("eligible2", nl=106, du=6, lat=32), 0.40),
        ("outside_low", _metric("outside_low", nl=103), 0.00),
    ]

    first = apply_phase2g_cutoff_order(
        items,
        constraints=constraints,
        arm="S",
        cutoff_metrics=cutoff[1],
        shuffle_rng=random.Random(12345),
    )
    second = apply_phase2g_cutoff_order(
        items,
        constraints=constraints,
        arm="S",
        cutoff_metrics=cutoff[1],
        shuffle_rng=random.Random(12345),
    )
    assert [item[0] for item in first] == [item[0] for item in second]
    assert first[0][0] == "outside_high"
    assert first[-1][0] == "outside_low"
