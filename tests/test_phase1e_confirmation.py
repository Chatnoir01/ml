import pytest

from adversarial_sbox.experiment_seeds import PHASE1E_CONFIRM_RESERVED_SEEDS
from adversarial_sbox.phase1e_confirmation import (
    CONFIRM_BEAM_WIDTH,
    CONFIRM_CYCLE_LENGTH,
    CONFIRM_EVALUATIONS,
    CONFIRM_GUIDANCE,
    exact_one_sided_sign_p,
    validate_confirmation_seed,
)


def test_frozen_confirmation_configuration_has_no_tuning_drift():
    assert CONFIRM_GUIDANCE == "combined"
    assert CONFIRM_CYCLE_LENGTH == 4
    assert CONFIRM_BEAM_WIDTH == 8
    assert CONFIRM_EVALUATIONS == 600


def test_exact_one_sided_sign_p_known_values():
    assert exact_one_sided_sign_p(9, 0) == pytest.approx(1 / 512)
    assert exact_one_sided_sign_p(8, 1) == pytest.approx(10 / 512)
    assert exact_one_sided_sign_p(5, 4) == pytest.approx(0.5)
    assert exact_one_sided_sign_p(0, 0) == 1.0


def test_exact_sign_test_rejects_negative_counts():
    with pytest.raises(ValueError, match="non-negative"):
        exact_one_sided_sign_p(-1, 2)


def test_only_reserved_confirmation_seeds_are_accepted():
    for seed in PHASE1E_CONFIRM_RESERVED_SEEDS:
        validate_confirmation_seed(seed)
    with pytest.raises(ValueError, match="frozen Phase-1E confirmation registry"):
        validate_confirmation_seed(907)
