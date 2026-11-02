"""Phase 2U software gates only: no classical evolution or neural training."""
import json
import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.phase2t_predict import PROSPECTIVE_SEEDS as OLD_SEEDS
from adversarial_sbox.phase2u_generate import (
    CLASSICAL_BUDGET, DESIGN, PUBLIC_SEEDS, SOURCE_VERSION,
    PROPOSALS_PER_GENERATION, MAX_FALLBACK_ATTEMPTS,
    STALL_THRESHOLD, _bounded_unique_batch, _eligible, digest, run_seed,
)


def _forced_stall(count, *, seed):
    parent=tuple(CANDIDATES[0]["sbox"])
    rng=random.Random(seed)
    seen={parent}
    # The guided engine deliberately returns ONLY already-seen parents.
    with patch("adversarial_sbox.phase2u_generate.multihotspot_walsh_swap_proposals",
               side_effect=lambda parent,rng,count: tuple(
                   SimpleNamespace(sbox=parent) for _ in range(count))):
        candidates,audit=_bounded_unique_batch((parent,),rng,seen)
    return candidates,audit


def test_new_registry_is_fixed_and_disjoint_from_historical_t_set():
    assert len(PUBLIC_SEEDS)==24
    assert len(set(PUBLIC_SEEDS))==24
    assert set(PUBLIC_SEEDS).isdisjoint(OLD_SEEDS)
    assert CLASSICAL_BUDGET==340
    assert DESIGN=="phase2u_bounded_unique_fallback_v1"
    assert SOURCE_VERSION=="phase2u_source_v1"


def test_forced_guided_stagnation_rescued_without_duplicate_candidates():
    generated,audit=_forced_stall(16,seed=41003)
    assert len(generated)==PROPOSALS_PER_GENERATION
    assert len(set(generated))==PROPOSALS_PER_GENERATION
    assert len(audit)==PROPOSALS_PER_GENERATION
    assert all(a["mode"]=="bounded_random_swap" for a in audit)
    assert len({a["fingerprint"] for a in audit})==PROPOSALS_PER_GENERATION
    assert all(a["fallback"] is True for a in audit)


def test_fallback_proposal_transcript_replays_exactly():
    a,aa=_forced_stall(16,seed=41003)
    b,bb=_forced_stall(16,seed=41003)
    assert a==b and aa==bb
    assert digest({"audit":aa})==digest({"audit":bb})


def test_alternative_seed_changes_fallback_transcript():
    _,a=_forced_stall(16,seed=41003)
    _,b=_forced_stall(16,seed=41011)
    assert digest({"audit":a}) != digest({"audit":b})


def test_recovery_transpositions_preserve_each_bijective_sbox():
    boxes,audit=_forced_stall(16,seed=41003)
    assert all(sorted(box)==list(range(256)) for box in boxes)


@pytest.mark.parametrize("seed",[31013,31019,True,-1,41004])
def test_original_or_invalid_source_seeds_are_not_admitted(seed):
    with pytest.raises(ValueError,match="registered"):
        run_seed(seed)


def test_invalid_parent_fails_before_creating_proposals():
    with pytest.raises(ValueError,match="parent"):
        _bounded_unique_batch([],random.Random(1),set())


def test_fallback_metadata_does_not_expose_neural_labels():
    _,audit=_forced_stall(16,seed=41003)
    text=json.dumps(audit,sort_keys=True)
    assert "neural" not in text and "test_auc" not in text
    assert all(a["parent_index"]==0 for a in audit)
    assert all(len(a["swap_positions"])==2 for a in audit)


def test_old_exact_metrics_match_is_not_a_neural_measurement():
    from adversarial_sbox.evolution import evaluate_classical
    metrics=evaluate_classical(CANDIDATES[0]["sbox"])
    assert _eligible(metrics) is True
    assert metrics.nonlinearity==100 and metrics.differential_uniformity==8
