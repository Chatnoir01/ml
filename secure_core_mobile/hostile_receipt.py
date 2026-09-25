"""Canonical diagnostic receipt for hostile-host campaign executions.

A receipt records behavior and bindings. It is not authority for claim
promotion by itself; ADVERSARIALLY_TESTED promotion additionally requires the
verifier-issued token enforced by claim_gate.
"""

from __future__ import annotations

import hashlib
import json

from .hostile_campaign import HostileCampaign, ScenarioResult
from .security_gate import SecurityCapability


HOSTILE_RECEIPT_SCHEMA_VERSION = 2


def _results_body(results: tuple[ScenarioResult, ...]) -> list[dict]:
    return [
        {
            "scenario": result.scenario.value,
            "denied": result.denied,
            "provider_reached": result.provider_reached,
        }
        for result in sorted(results, key=lambda item: item.scenario.value)
    ]


def hostile_campaign_receipt(
    *,
    campaign: HostileCampaign,
    capability: SecurityCapability,
    results: tuple[ScenarioResult, ...],
) -> dict:
    passed = campaign.evaluate(results)
    qualifies = capability.hostile_host_ready and passed
    result_items = _results_body(results)
    results_canonical = json.dumps(
        result_items,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    results_sha = hashlib.sha256(results_canonical).hexdigest()

    scope = (
        "hostile-host-isolated-boundary"
        if capability.boundary.qualifies_for_hostile_host_experiment
        else "development-host-only"
    )

    body = {
        "schema_version": HOSTILE_RECEIPT_SCHEMA_VERSION,
        "scope": scope,
        # campaign_sha256 remains for compatibility with earlier receipts.
        "campaign_sha256": campaign.spec_sha256,
        "campaign_spec_sha256": campaign.spec_sha256,
        "campaign_results_sha256": results_sha,
        "boundary_evidence_sha256": capability.boundary.evidence_sha256,
        "hostile_host_ready": capability.hostile_host_ready,
        "campaign_passed": passed,
        "qualifies_as_hostile_host_evidence": qualifies,
        "qualifies_as_pkvm_evidence": qualifies,
        "results": result_items,
    }
    canonical = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return {
        **body,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }
