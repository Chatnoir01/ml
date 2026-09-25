"""Deterministic experiment receipt aggregation."""

from __future__ import annotations
from collections.abc import Sequence
import hashlib
import json

from .hostile_host import AttackObservation


def experiment_receipt(observations: Sequence[AttackObservation]) -> dict:
    rows = [
        {
            "kind": item.kind.value,
            "denied": item.denied,
            "provider_reached": item.provider_reached,
            "receipt_sha256": item.receipt_sha256,
        }
        for item in observations
    ]
    body = {
        "schema_version": 1,
        "experiment": "hostile-host-api-harness",
        "scope": "development-host-only",
        "qualifies_as_pkvm_evidence": False,
        "observations": rows,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {**body, "sha256": hashlib.sha256(canonical).hexdigest()}
