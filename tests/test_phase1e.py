import random

import pytest

from adversarial_sbox.experiment_seeds import PHASE1E_CONFIRM_RESERVED_SEEDS
from adversarial_sbox.phase1e import (
    cycle_mutation,
    ddt_hotspot_indices,
    guided_adaptive_search,
    hotspot_indices,
    lat_hotspot_indices,
    run_development,
    unguided_adaptive_search,
)
from adversarial_sbox.references import AES_SBOX


def test_hotspot_sets_are_deterministic_and_nonempty_for_aes():
    ddt = ddt_hotspot_indices(AES_SBOX)
    lat = lat_hotspot_indices(AES_SBOX)
    assert ddt
    assert lat
    assert ddt == ddt_hotspot_indices(AES_SBOX)
    assert lat == lat_hotspot_indices(AES_SBOX)
    assert set(hotspot_indices(AES_SBOX, "combined")) == set(ddt) | set(lat)


def test_cycle_mutation_preserves_permutation_and_uses_anchor():
    rng = random.Random(7)
    anchor = 19
    child, fallback = cycle_mutation(
        AES_SBOX,
        rng,
        cycle_length=3,
        anchor_indices=(anchor,),
    )
    changed = {idx for idx, (left, right) in enumerate(zip(AES_SBOX, child)) if left != right}
    assert not fallback
    assert anchor in changed
    assert len(changed) == 3
    assert sorted(child) == list(range(256))


def test_guided_and_unguided_search_charge_exact_budget():
    guided = guided_adaptive_search(
        AES_SBOX,
        seed=17,
        evaluations=2,
        beam_width=2,
        cycle_length=2,
        guidance="ddt",
    )
    unguided = unguided_adaptive_search(
        AES_SBOX,
        seed=19,
        evaluations=2,
        beam_width=2,
        cycle_length=2,
    )
    assert guided["evaluations"] == 2
    assert unguided["evaluations"] == 2
    assert guided["hotspot_fallbacks"] == 0


def test_confirmation_seeds_cannot_enter_development():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(
            guidance="ddt",
            cycle_length=2,
            seeds=(PHASE1E_CONFIRM_RESERVED_SEEDS[0],),
            evaluations=1,
        )
