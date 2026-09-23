"""Deterministic evidence-manifest contract for Phase 2H."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any

from .phase2g import EVOLUTION_SEEDS

PRIMARY_ARMS = ("A", "F")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_evidence_manifest(
    inputs: Sequence[Mapping[str, Any]],
    *,
    parent_commit: str,
    parent_aggregate_sha256: str,
) -> dict[str, Any]:
    """Identify every consumed scientific payload and fail closed on drift."""

    expected = {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in PRIMARY_ARMS}
    indexed: dict[tuple[int, str], Mapping[str, Any]] = {}

    for raw in inputs:
        seed = int(raw.get("seed", -1))
        arm = str(raw.get("arm", ""))
        key = (seed, arm)
        if key not in expected:
            raise ValueError(f"unexpected Phase-2H evidence cell {key!r}")
        if key in indexed:
            raise ValueError(f"duplicate Phase-2H evidence cell {key!r}")
        indexed[key] = raw

    missing = sorted(expected - set(indexed))
    if missing:
        raise ValueError(f"missing Phase-2H evidence cells: {missing!r}")

    cells = []
    for seed, arm in sorted(indexed):
        payload = indexed[(seed, arm)]
        cells.append(
            {
                "seed": seed,
                "arm": arm,
                "payload_sha256": canonical_sha256(payload),
                "checkpoint_count": len(payload.get("checkpoints", ())),
                "selection_event_count": len(payload.get("selection_events", ())),
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "phase": "2H-evidence-manifest",
        "parent_phase2g_commit": str(parent_commit),
        "parent_phase2g_aggregate_sha256": str(parent_aggregate_sha256),
        "cell_count": len(cells),
        "cells": cells,
    }
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    return manifest


def verify_evidence_manifest(
    inputs: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> None:
    """Re-hash all 18 frozen cells and reject any manifest/input drift."""
    cells = manifest.get("cells")
    if not isinstance(cells, Sequence) or isinstance(cells, (str, bytes, bytearray)):
        raise ValueError("malformed Phase-2H evidence manifest")
    expected_manifest_hash = str(manifest.get("manifest_sha256", ""))
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    if len(expected_manifest_hash) != 64 or canonical_sha256(unsigned) != expected_manifest_hash:
        raise ValueError("Phase-2H evidence manifest hash mismatch")

    expected = {(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in PRIMARY_ARMS}
    declared: dict[tuple[int, str], str] = {}
    for row in cells:
        if not isinstance(row, Mapping):
            raise ValueError("malformed Phase-2H evidence manifest cell")
        key = (int(row.get("seed", -1)), str(row.get("arm", "")))
        if key not in expected or key in declared:
            raise ValueError("unexpected or duplicate Phase-2H manifest cell")
        digest = str(row.get("payload_sha256", ""))
        if len(digest) != 64:
            raise ValueError("invalid Phase-2H payload digest")
        declared[key] = digest
    if set(declared) != expected:
        raise ValueError("incomplete Phase-2H evidence manifest")

    actual: dict[tuple[int, str], str] = {}
    for raw in inputs:
        key = (int(raw.get("seed", -1)), str(raw.get("arm", "")))
        if key not in expected or key in actual:
            raise ValueError("unexpected or duplicate Phase-2H input cell")
        actual[key] = canonical_sha256(raw)
    if set(actual) != expected:
        raise ValueError("incomplete Phase-2H input evidence")
    mismatched = sorted(key for key in expected if actual[key] != declared[key])
    if mismatched:
        raise ValueError(f"Phase-2H evidence hash mismatch: {mismatched!r}")
