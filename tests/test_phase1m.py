import pytest

from adversarial_sbox.experiment_seeds import (
    PHASE1M_CONFIRM_RESERVED_SEEDS,
    PHASE1M_DEV_SEEDS,
    validate_seed_registry,
)
from adversarial_sbox.phase1h import ProposalScore
from adversarial_sbox.phase1m import (
    DISCOVERY_BUDGET,
    REPAIR_BUDGET,
    TOTAL_BUDGET,
    ddt_first_ranking_key,
    validate_frozen_design,
)


def test_phase1m_seed_registry_is_fresh_and_exact():
    validate_seed_registry()
    assert PHASE1M_DEV_SEEDS == (2111, 2113, 2129, 2131, 2137)
    assert PHASE1M_CONFIRM_RESERVED_SEEDS == (
        2203,
        2207,
        2213,
        2221,
        2237,
        2239,
        2243,
        2251,
        2267,
    )
    assert set(PHASE1M_DEV_SEEDS).isdisjoint(PHASE1M_CONFIRM_RESERVED_SEEDS)


def test_phase1m_frozen_budget_contract():
    validate_frozen_design()
    assert DISCOVERY_BUDGET == 532
    assert REPAIR_BUDGET == 1088
    assert TOTAL_BUDGET == 1620
    assert DISCOVERY_BUDGET + REPAIR_BUDGET == TOTAL_BUDGET


def test_ddt_first_key_prefers_lower_ddt_when_lat_guard_is_equal():
    lower_ddt = ProposalScore(
        projected_lat_max=60,
        projected_ddt_max=8,
        lat_max_cells_reduced=0,
        ddt_max_cells_reduced=1,
        projected_lat_sum=120,
        projected_ddt_sum=18,
        order=1,
    )
    lower_lat_but_worse_ddt = ProposalScore(
        projected_lat_max=56,
        projected_ddt_max=10,
        lat_max_cells_reduced=2,
        ddt_max_cells_reduced=0,
        projected_lat_sum=100,
        projected_ddt_sum=24,
        order=0,
    )

    assert ddt_first_ranking_key(lower_ddt, current_lat_max=60) < ddt_first_ranking_key(
        lower_lat_but_worse_ddt,
        current_lat_max=60,
    )


def test_ddt_first_key_rejects_lat_regression_before_ddt_gain():
    guarded = ProposalScore(
        projected_lat_max=60,
        projected_ddt_max=10,
        lat_max_cells_reduced=0,
        ddt_max_cells_reduced=0,
        projected_lat_sum=120,
        projected_ddt_sum=24,
        order=1,
    )
    regressing = ProposalScore(
        projected_lat_max=64,
        projected_ddt_max=8,
        lat_max_cells_reduced=0,
        ddt_max_cells_reduced=2,
        projected_lat_sum=128,
        projected_ddt_sum=16,
        order=0,
    )

    assert ddt_first_ranking_key(guarded, current_lat_max=60) < ddt_first_ranking_key(
        regressing,
        current_lat_max=60,
    )


def test_ddt_first_key_rewards_more_max_ddt_cells_reduced_after_same_maximum():
    more_reduced = ProposalScore(
        projected_lat_max=60,
        projected_ddt_max=10,
        lat_max_cells_reduced=0,
        ddt_max_cells_reduced=3,
        projected_lat_sum=120,
        projected_ddt_sum=20,
        order=1,
    )
    fewer_reduced = ProposalScore(
        projected_lat_max=60,
        projected_ddt_max=10,
        lat_max_cells_reduced=2,
        ddt_max_cells_reduced=1,
        projected_lat_sum=100,
        projected_ddt_sum=18,
        order=0,
    )

    assert ddt_first_ranking_key(more_reduced, current_lat_max=60) < ddt_first_ranking_key(
        fewer_reduced,
        current_lat_max=60,
    )
