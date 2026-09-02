import pytest

from adversarial_sbox.experiment_seeds import (
    PHASE1H_CONFIRM_RESERVED_SEEDS,
    PHASE1H_DEV_SEEDS,
)
from adversarial_sbox.phase1h_confirmation import (
    CONFIRM_BEAM_WIDTH,
    CONFIRM_EVALUATIONS,
    CONFIRM_PANEL_MODE,
    CONFIRM_PROPOSAL_POOL,
    CONFIRM_SEEDS,
    exact_one_sided_sign_p,
    validate_confirmation_seed,
)


def test_confirmation_registry_is_exact_and_disjoint_from_development():
    assert CONFIRM_SEEDS == tuple(PHASE1H_CONFIRM_RESERVED_SEEDS)
    assert set(CONFIRM_SEEDS).isdisjoint(PHASE1H_DEV_SEEDS)
    assert len(CONFIRM_SEEDS) == 9


def test_confirmation_configuration_is_frozen_to_selected_ties_p96():
    assert CONFIRM_PANEL_MODE == "ties"
    assert CONFIRM_PROPOSAL_POOL == 96
    assert CONFIRM_BEAM_WIDTH == 8
    assert CONFIRM_EVALUATIONS == 600


def test_exact_one_sided_sign_test_known_values():
    assert exact_one_sided_sign_p(8, 0) == pytest.approx(1 / 256)
    assert exact_one_sided_sign_p(5, 0) == pytest.approx(1 / 32)
    assert exact_one_sided_sign_p(4, 0) == pytest.approx(1 / 16)
    assert exact_one_sided_sign_p(4, 1) == pytest.approx(6 / 32)
    assert exact_one_sided_sign_p(0, 0) == 1.0
    assert exact_one_sided_sign_p(2, 2) == 1.0


def test_non_confirmation_seed_is_rejected_without_running_search():
    with pytest.raises(ValueError, match="frozen Phase-1H confirmation registry"):
        validate_confirmation_seed(PHASE1H_DEV_SEEDS[0])


def test_confirmation_seed_is_accepted():
    validate_confirmation_seed(CONFIRM_SEEDS[0])
