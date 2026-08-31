from adversarial_sbox.experiment_seeds import (
    CONFIRM_V1_SEEDS,
    CONFIRM_V2_RESERVED_SEEDS,
    DEV_V2_SEEDS,
    STRICT_HISTORICAL_SEEDS,
    USED_BEFORE_V2,
    validate_seed_registry,
)


def test_v2_seed_registry_is_disjoint_from_prior_evidence():
    validate_seed_registry()
    assert set(DEV_V2_SEEDS).isdisjoint(USED_BEFORE_V2)
    assert set(CONFIRM_V2_RESERVED_SEEDS).isdisjoint(USED_BEFORE_V2)
    assert set(DEV_V2_SEEDS).isdisjoint(CONFIRM_V2_RESERVED_SEEDS)


def test_historical_overlap_is_explicit_not_hidden():
    assert CONFIRM_V1_SEEDS & STRICT_HISTORICAL_SEEDS == {211, 223, 227}
