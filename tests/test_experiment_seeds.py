from adversarial_sbox.experiment_seeds import (
    CONFIRM_V1_SEEDS,
    CONFIRM_V2_RESERVED_SEEDS,
    DEV_V2_SEEDS,
    PHASE1C_CONFIRM_RESERVED_SEEDS,
    PHASE1C_DEV_SEEDS,
    PHASE1D_CONFIRM_RESERVED_SEEDS,
    PHASE1D_DEV_SEEDS,
    PHASE1E_CONFIRM_RESERVED_SEEDS,
    PHASE1E_DEV_SEEDS,
    STRICT_HISTORICAL_SEEDS,
    USED_BEFORE_V2,
    validate_seed_registry,
)


def test_seed_registry_is_disjoint_after_historical_overlap():
    validate_seed_registry()
    blocks = [
        set(DEV_V2_SEEDS),
        set(CONFIRM_V2_RESERVED_SEEDS),
        set(PHASE1C_DEV_SEEDS),
        set(PHASE1C_CONFIRM_RESERVED_SEEDS),
        set(PHASE1D_DEV_SEEDS),
        set(PHASE1D_CONFIRM_RESERVED_SEEDS),
        set(PHASE1E_DEV_SEEDS),
        set(PHASE1E_CONFIRM_RESERVED_SEEDS),
    ]
    for block in blocks:
        assert block.isdisjoint(USED_BEFORE_V2)
    for index, left in enumerate(blocks):
        for right in blocks[index + 1 :]:
            assert left.isdisjoint(right)


def test_historical_overlap_is_explicit_not_hidden():
    assert CONFIRM_V1_SEEDS & STRICT_HISTORICAL_SEEDS == {211, 223, 227}
