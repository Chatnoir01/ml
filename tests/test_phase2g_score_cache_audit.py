"""RED contract for Phase 2G inference-cache audit counters."""

from __future__ import annotations

import hashlib
import json

from adversarial_sbox.phase2g_selection import CheckpointScoreLedger
from adversarial_sbox.provenance import fingerprint_sbox


def _canonical(payload):
    clean = {key: value for key, value in payload.items() if key != "scientific_payload_sha256"}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_checkpoint_score_ledger_receipts_cache_hits_and_misses_exactly():
    candidate = tuple(range(256))
    calls = 0

    def scorer(sbox):
        nonlocal calls
        calls += 1
        payload = {
            "candidate_fingerprint": fingerprint_sbox(sbox),
            "training_count": 0,
            "neural_advantage": 0.25,
        }
        payload["scientific_payload_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
        return payload

    ledger = CheckpointScoreLedger(
        arm="A",
        evolution_seed=726011,
        checkpoint_generation=5,
        scorer=scorer,
    )
    assert ledger.cache_hits == 0
    assert ledger.cache_misses == 0
    assert ledger.score(candidate) == 0.25
    assert ledger.cache_hits == 0
    assert ledger.cache_misses == 1
    assert ledger.score(candidate) == 0.25
    assert ledger.cache_hits == 1
    assert ledger.cache_misses == 1
    assert calls == 1
    assert ledger.cache_size == 1
    assert len(ledger.receipts) == 1
    assert ledger.receipts[0].training_count == 0
