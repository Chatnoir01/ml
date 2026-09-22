"""Canonical receipt for hostile-host campaign executions."""

from __future__ import annotations
import hashlib
import json

from .hostile_campaign import HostileCampaign, ScenarioResult
from .security_gate import SecurityCapability


def hostile_campaign_receipt(
    *, campaign: HostileCampaign, capability: SecurityCapability,
    results: tuple[ScenarioResult, ...],
) -> dict:
    passed = campaign.evaluate(results)
    qualifies = capability.hostile_host_ready and passed
    body = {
        "schema_version": 1,
        "campaign_sha256": campaign.spec_sha256,
        "boundary_evidence_sha256": capability.boundary.evidence_sha256,
        "hostile_host_ready": capability.hostile_host_ready,
        "campaign_passed": passed,
        "qualifies_as_hostile_host_evidence": qualifies,
        "results": [
            {
                "scenario": r.scenario.value,
                "denied": r.denied,
                "provider_reached": r.provider_reached,
            }
            for r in sorted(results, key=lambda x: x.scenario.value)
        ],
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "sha256": hashlib.sha256(canonical).hexdigest()}
