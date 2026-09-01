import random

import pytest

from adversarial_sbox.experiment_seeds import (
    CONFIRM_PHASE1E_RESERVED_SEEDS,
    DEV_PHASE1E_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1e import (
    build_structural_guide,
    guided_mutation,
    run_development,
    worst_ddt_hotspot,
    worst_walsh_hotspot,
)
from adversarial_sbox.references import AES_SBOX


def test_phase1e_seed_registry_is_disjoint():
    validate_seed_registry()
    assert not (set(DEV_PHASE1E_SEEDS) & set(CONFIRM_PHASE1E_RESERVED_SEEDS))


def test_aes_hotspot_diagnostics_match_reference_metrics():
    _, _, correlation = worst_walsh_hotspot(AES_SBOX)
    _, _, ddt_count = worst_ddt_hotspot(AES_SBOX)
    assert abs(correlation) == 32
    assert ddt_count == 4


def test_guided_mutation_is_deterministic_and_preserves_permutation():
    guide = build_structural_guide(AES_SBOX)
    first, first_proxy = guided_mutation(
        AES_SBOX,
        random.Random(1234),
        guide=guide,
        mode="hybrid",
        proposal_pairs=24,
        swaps=1,
    )
    second, second_proxy = guided_mutation(
        AES_SBOX,
        random.Random(1234),
        guide=guide,
        mode="hybrid",
        proposal_pairs=24,
        swaps=1,
    )
    assert first == second
    assert first_proxy == second_proxy
    assert sorted(first) == list(range(256))
    assert first != AES_SBOX


def test_phase1e_confirmation_seed_cannot_enter_development():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(seeds=(CONFIRM_PHASE1E_RESERVED_SEEDS[0],), evaluations=1)
