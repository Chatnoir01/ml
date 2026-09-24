from __future__ import annotations

import copy

import pytest

from adversarial_sbox.phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS
from adversarial_sbox.phase2h_evidence import build_evidence_manifest, verify_evidence_manifest


def _cell(seed: int, arm: str) -> dict:
    return {
        "seed": seed,
        "arm": arm,
        "checkpoints": [{"generation": g} for g in CHECKPOINT_GENERATIONS],
        "selection_events": [{"generation": 1}],
    }


def _all_cells() -> list[dict]:
    return [_cell(int(seed), arm) for seed in EVOLUTION_SEEDS for arm in ("A", "F")]


def test_evidence_manifest_is_order_invariant() -> None:
    cells = _all_cells()
    a = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    b = build_evidence_manifest(
        list(reversed(copy.deepcopy(cells))),
        parent_commit="c",
        parent_aggregate_sha256="a",
    )
    assert a == b
    assert a["cell_count"] == 18
    assert len(a["manifest_sha256"]) == 64


def test_evidence_manifest_rejects_missing_cell() -> None:
    cells = _all_cells()
    cells.pop()
    with pytest.raises(ValueError, match="missing"):
        build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")


def test_evidence_manifest_rejects_duplicate_cell() -> None:
    cells = _all_cells()
    cells.append(copy.deepcopy(cells[0]))
    with pytest.raises(ValueError, match="duplicate"):
        build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")


def test_evidence_manifest_rejects_unexpected_cell() -> None:
    cells = _all_cells()
    cells[-1]["arm"] = "S"
    with pytest.raises(ValueError, match="unexpected"):
        build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")


def test_evidence_manifest_hash_changes_on_payload_mutation() -> None:
    cells = _all_cells()
    first = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    cells[0]["selection_events"].append({"generation": 2})
    second = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    assert first["manifest_sha256"] != second["manifest_sha256"]


def test_verify_manifest_accepts_exact_frozen_inputs() -> None:
    cells = _all_cells()
    manifest = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    verify_evidence_manifest(cells, manifest)

def test_verify_manifest_rejects_payload_corruption() -> None:
    cells = _all_cells()
    manifest = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    cells[0]["selection_events"].append({"generation": 99})
    with pytest.raises(ValueError, match="evidence hash mismatch"):
        verify_evidence_manifest(cells, manifest)

def test_verify_manifest_rejects_manifest_tamper() -> None:
    cells = _all_cells()
    manifest = build_evidence_manifest(cells, parent_commit="c", parent_aggregate_sha256="a")
    manifest["cells"][0]["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="manifest hash mismatch"):
        verify_evidence_manifest(cells, manifest)
