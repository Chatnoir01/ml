#!/usr/bin/env python3
"""Deterministic Phase 2H runner over frozen Phase-2G A/F receipt files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adversarial_sbox.phase2h import (
    PARENT_AGGREGATE_SHA256,
    PARENT_PHASE2G_COMMIT,
    diagnose_phase2g_receipts,
)
from adversarial_sbox.phase2h_evidence import (
    build_evidence_manifest,
    canonical_sha256,
    verify_evidence_manifest,
)


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Phase 2H input must be a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_arm_files(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[tuple[int, str], str]]:
    payloads: list[dict[str, Any]] = []
    source_paths: dict[tuple[int, str], str] = {}
    for path in paths:
        payload = _read(path)
        key = (int(payload.get("seed", -1)), str(payload.get("arm", "")))
        if key in source_paths:
            raise SystemExit(f"duplicate Phase 2H input cell {key!r}")
        source_paths[key] = path.as_posix()
        payloads.append(payload)
    return payloads, source_paths


def prepare_manifest(paths: list[Path]) -> dict[str, Any]:
    payloads, source_paths = _load_arm_files(paths)
    manifest = build_evidence_manifest(
        payloads,
        parent_commit=PARENT_PHASE2G_COMMIT,
        parent_aggregate_sha256=PARENT_AGGREGATE_SHA256,
    )
    digest_by_key = {
        (int(row["seed"]), str(row["arm"])): str(row["payload_sha256"])
        for row in manifest["cells"]
    }
    manifest["source_files"] = [
        {
            "seed": seed,
            "arm": arm,
            "path": source_paths[(seed, arm)],
            "payload_sha256": digest_by_key[(seed, arm)],
        }
        for seed, arm in sorted(source_paths)
    ]
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = canonical_sha256(manifest)
    return manifest


def _bind_runtime_metadata(
    diagnostics: dict[str, Any],
    *,
    manifest: dict[str, Any],
    implementation_commit: str,
) -> dict[str, Any]:
    if len(implementation_commit) != 40:
        raise SystemExit("--implementation-commit must be a 40-character Git commit SHA")
    bound = dict(diagnostics)
    bound.pop("diagnostic_sha256", None)
    bound["implementation_commit"] = implementation_commit
    bound["evidence_manifest_sha256"] = str(manifest["manifest_sha256"])
    bound["input_payload_sha256"] = [
        {
            "seed": int(row["seed"]),
            "arm": str(row["arm"]),
            "payload_sha256": str(row["payload_sha256"]),
        }
        for row in manifest["cells"]
    ]
    bound["diagnostic_sha256"] = canonical_sha256(bound)
    return bound


def render_result_markdown(payload: dict[str, Any]) -> str:
    basis = payload["mechanism_verdict_basis"]
    causal = payload["causal_interpretation"]
    availability = payload["availability"]
    lines = [
        "# Phase 2H — Mechanistic diagnostic result",
        "",
        "Status: **receipt-bound diagnostic; Phase 2G remains immutable**",
        "",
        f"- Parent Phase 2G commit: `{payload['parent_phase2g_commit']}`",
        f"- Parent aggregate SHA-256: `{payload['parent_phase2g_aggregate_sha256']}`",
        f"- Evidence manifest SHA-256: `{payload['evidence_manifest_sha256']}`",
        f"- Implementation commit: `{payload['implementation_commit']}`",
        f"- Diagnostic SHA-256: `{payload['diagnostic_sha256']}`",
        "",
        "## Receipt-level mechanism verdict",
        "",
        f"`{payload['mechanism_verdict']}`",
        "",
        f"- cycling seeds: {basis['cycling_seed_count']}",
        f"- rank-reversal seeds: {basis['rank_reversal_seed_count']}",
        f"- scope: `{basis['scope']}`",
        f"- modifies Phase 2G verdict: {not bool(basis['does_not_modify_phase2g_verdict'])}",
        "",
        "## Availability",
        "",
        f"- forgetting matrix available: {bool(availability['forgetting_matrix'])}",
        f"- classical-distortion evidence available: {bool(availability['candidate_level_classical_distortion'])}",
        "",
        "## Causal firewall",
        "",
        f"- causal claim supported: {bool(causal['causal_claim_supported'])}",
        f"- reason: {causal['reason']}",
        "",
        "This report is generated from the machine-readable diagnostics and does not authorize Phase 2I.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm-files", type=Path, nargs="+", required=True)
    parser.add_argument("--prepare-manifest", action="store_true")
    parser.add_argument("--evidence-manifest", type=Path)
    parser.add_argument("--implementation-commit")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--result-md", type=Path)
    args = parser.parse_args()

    if args.prepare_manifest:
        if args.evidence_manifest is not None or args.implementation_commit is not None or args.result_md is not None:
            raise SystemExit("manifest preparation cannot be mixed with diagnostic execution")
        _write_json(args.output, prepare_manifest(args.arm_files))
        return

    if args.evidence_manifest is None:
        raise SystemExit("diagnostic execution requires --evidence-manifest")
    if args.implementation_commit is None:
        raise SystemExit("diagnostic execution requires --implementation-commit")

    payloads, _ = _load_arm_files(args.arm_files)
    manifest = _read(args.evidence_manifest)
    verify_evidence_manifest(payloads, manifest)
    diagnostics = diagnose_phase2g_receipts(
        payloads,
        phase2g_aggregate_sha256=PARENT_AGGREGATE_SHA256,
        evidence_manifest=manifest,
    )
    diagnostics = _bind_runtime_metadata(
        diagnostics,
        manifest=manifest,
        implementation_commit=str(args.implementation_commit),
    )
    _write_json(args.output, diagnostics)
    if args.result_md is not None:
        args.result_md.write_text(render_result_markdown(diagnostics), encoding="utf-8")


if __name__ == "__main__":
    main()
