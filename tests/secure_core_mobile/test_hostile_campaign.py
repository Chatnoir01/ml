from secure_core_mobile.hostile_boundary import development_boundary
from secure_core_mobile.hostile_campaign import (
    HostileCampaign, HostileScenario, REQUIRED_SCENARIOS, ScenarioResult,
)
from secure_core_mobile.hostile_receipt import hostile_campaign_receipt
from secure_core_mobile.security_gate import SecurityCapability


def _passing_results():
    return tuple(ScenarioResult(s, True, False) for s in REQUIRED_SCENARIOS)


def test_campaign_requires_every_frozen_scenario():
    campaign = HostileCampaign()
    assert campaign.evaluate(_passing_results())
    assert not campaign.evaluate(_passing_results()[:-1])


def test_any_provider_reach_fails_campaign():
    results = list(_passing_results())
    results[0] = ScenarioResult(results[0].scenario, True, True)
    assert not HostileCampaign().evaluate(tuple(results))


def test_development_campaign_can_pass_behavior_but_never_qualify_as_evidence():
    capability = SecurityCapability(development_boundary(), False, False, False, False)
    receipt = hostile_campaign_receipt(
        campaign=HostileCampaign(), capability=capability, results=_passing_results()
    )
    assert receipt["schema_version"] == 2
    assert receipt["scope"] == "development-host-only"
    assert receipt["campaign_passed"] is True
    assert receipt["hostile_host_ready"] is False
    assert receipt["qualifies_as_hostile_host_evidence"] is False
    assert receipt["qualifies_as_pkvm_evidence"] is False
    assert receipt["campaign_sha256"] == receipt["campaign_spec_sha256"]
    assert len(receipt["campaign_results_sha256"]) == 64
    assert len(receipt["sha256"]) == 64


def test_campaign_results_digest_is_order_invariant():
    campaign = HostileCampaign()
    capability = SecurityCapability(
        development_boundary(), False, False, False, False
    )
    forward = _passing_results()
    reverse = tuple(reversed(forward))

    left = hostile_campaign_receipt(
        campaign=campaign,
        capability=capability,
        results=forward,
    )
    right = hostile_campaign_receipt(
        campaign=campaign,
        capability=capability,
        results=reverse,
    )

    assert left["campaign_results_sha256"] == right["campaign_results_sha256"]
    assert left["sha256"] == right["sha256"]
