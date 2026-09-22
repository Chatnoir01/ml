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
