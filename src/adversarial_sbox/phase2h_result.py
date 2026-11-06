"""Canonical Phase 2H result packaging.

This module packages diagnostics; it does not decide whether H1-H4 are supported.
Mechanism support remains unavailable until explicit frozen decision rules exist.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import Any


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def package_phase2h_result(
    diagnostics: Mapping[str, Any],
    evidence_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    if diagnostics.get("phase") != "2H-diagnostics":
        raise ValueError("expected Phase-2H diagnostics")
    if evidence_manifest.get("phase") != "2H-evidence-manifest":
        raise ValueError("expected Phase-2H evidence manifest")
    if diagnostics.get("parent_phase2g_aggregate_sha256") != evidence_manifest.get(
        "parent_phase2g_aggregate_sha256"
    ):
        raise ValueError("Phase-2H evidence/diagnostic parent mismatch")

    result: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2H-result-draft",
        "frozen": False,
        "diagnostic_sha256": diagnostics.get("diagnostic_sha256"),
        "evidence_manifest_sha256": evidence_manifest.get("manifest_sha256"),
        "parent_phase2g_commit": diagnostics.get("parent_phase2g_commit"),
        "parent_phase2g_aggregate_sha256": diagnostics.get(
            "parent_phase2g_aggregate_sha256"
        ),
        "supported_mechanisms": None,
        "verdict": "phase2h_mechanism_verdict_not_yet_authorized",
        "execution_authorized_for_phase2i": False,
        "reason": (
            "H1-H4 decision thresholds are not yet encoded as frozen machine rules; "
            "packaging must not convert exploratory diagnostics into a verdict"
        ),
    }
    result["result_draft_sha256"] = hashlib.sha256(_canonical(result)).hexdigest()
    return result
