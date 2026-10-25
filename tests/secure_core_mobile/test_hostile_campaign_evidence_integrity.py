"""Adversarial evidence-integrity checks for development hostile-host campaign.

These tests are NOT execution against Android or a hostile pVM host.
"""
from __future__ import annotations

import pytest

from secure_core_mobile.hostile_boundary import development_boundary
from secure_core_mobile.hostile_campaign import (
    HostileCampaign, HostileScenario, REQUIRED_SCENARIOS, ScenarioResult,
)
from secure_core_mobile.hostile_receipt import hostile_campaign_receipt
from secure_core_mobile.security_gate import SecurityCapability


def _valid() -> tuple[ScenarioResult, ...]:
    return tuple(ScenarioResult(s, True, False) for s in REQUIRED_SCENARIOS)


def _development_receipt(results: tuple[ScenarioResult, ...]) -> dict:
    return hostile_campaign_receipt(
        campaign=HostileCampaign(),
        capability=SecurityCapability(development_boundary(), False, False, False, False),
        results=results,
    )


def test_exact_frozen_scenario_set_passes_in_any_order() -> None:
    campaign = HostileCampaign()
    assert campaign.evaluate(_valid())
    assert campaign.evaluate(tuple(reversed(_valid())))


def test_duplicate_success_cannot_overwrite_prior_failure() -> None:
    valid = _valid()
    attacked = (ScenarioResult(valid[0].scenario, False, True), *valid)
    # Before the fix, dict-comprehension retained only the final passing row.
    assert not HostileCampaign().evaluate(attacked)
    receipt = _development_receipt(attacked)
    assert receipt["campaign_passed"] is False
    assert receipt["qualifies_as_hostile_host_evidence"] is False
    assert receipt["qualifies_as_pkvm_evidence"] is False


def test_duplicate_failure_cannot_be_hidden_by_replacing_another_scenario() -> None:
    rows = list(_valid())
    rows[0] = ScenarioResult(rows[1].scenario, True, False)
    assert not HostileCampaign().evaluate(tuple(rows))


@pytest.mark.parametrize("denied,provider_reached", [
    (1, False), ("true", False), (None, False), (True, 0),
    (True, None), (True, "false"), (0, False), (True, 1),
])
def test_only_literal_bool_evidence_is_accepted(
    denied: object, provider_reached: object
) -> None:
    rows = list(_valid())
    rows[0] = ScenarioResult(rows[0].scenario, denied, provider_reached)
    assert not HostileCampaign().evaluate(tuple(rows))


def test_string_scenario_cannot_impersonate_enum_value() -> None:
    rows = list(_valid())
    rows[0] = ScenarioResult("UNKNOWN_HANDLE", True, False)
    assert not HostileCampaign().evaluate(tuple(rows))


@pytest.mark.parametrize("results", [
    (),
    _valid()[:-1],
    _valid() + (ScenarioResult(HostileScenario.UNKNOWN_HANDLE, True, False),),
    list(_valid()),
    "not-a-result",
])
def test_bad_shape_or_count_fails_closed(results: object) -> None:
    assert not HostileCampaign().evaluate(results)


@pytest.mark.parametrize("campaign", [
    HostileCampaign(protocol_version=True),
    HostileCampaign(protocol_version=1.0),
    HostileCampaign(protocol_version=2),
    HostileCampaign(frozen=1),
    HostileCampaign(frozen=False),
])
def test_protocol_identity_cannot_be_inferred_from_truthiness(campaign: HostileCampaign) -> None:
    assert not campaign.evaluate(_valid())
