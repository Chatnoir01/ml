"""Training-free, in-process input-byte control for prospective Phase 2R.

This is a preflight instrument, NOT a scientific Phase-2R execution. It never
trains a neural model, loads historical held-out H, or modifies Phase 2G.
The repeated generation controls only dataset construction with identical
pinned S-Boxes and seeds in the SAME process.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .phase2g import TRAINING_DATASET_BASE_SEEDS
from .phase2g_shared_model import build_shared_training_splits
from .phase2r_fixture import CURRICULUM_SHA256, FIXTURE_ID, load_phase2r_fixture
from .phase2r_serialization import hash_pair_split

_DIFFERENCES = (1, 256)
_REPLICATES = tuple(range(8))
_PARTS = ("train", "validation", "test")
_EXPECTED_SPLIT_SIZES = (5600, 1200, 1200)


def _digest_cell(curriculum: tuple[tuple[int, ...], ...], *, difference: int, seed: int) -> dict[str, str]:
    splits = build_shared_training_splits(
        curriculum, difference=difference, dataset_seed=seed
    )
    if tuple(len(part) for part in splits) != _EXPECTED_SPLIT_SIZES:
        raise RuntimeError("Phase-2R input dataset geometry drift")
    return {
        name: hash_pair_split(part, split=name)
        for name, part in zip(_PARTS, splits)
    }


def preflight_phase2r_input_cell(*, difference: int = 1, replicate: int = 0) -> dict[str, Any]:
    """Test generation repeat/order invariance on new pinned synthetic inputs.

    Same-process equality is weaker than reproducibility across independent
    processes/hosts. A different byte hash or a malformed fixture fails closed.
    Output contains hashes and counts only, never ciphertext samples or keys.
    """
    if type(difference) is not int or difference not in _DIFFERENCES:
        raise ValueError("unregistered Phase-2R input difference")
    if type(replicate) is not int or replicate not in _REPLICATES:
        raise ValueError("unregistered Phase-2R replicate")
    fixture = load_phase2r_fixture()
    seed = TRAINING_DATASET_BASE_SEEDS[replicate]
    first = _digest_cell(fixture, difference=difference, seed=seed)
    repeated = _digest_cell(fixture, difference=difference, seed=seed)
    reversed_order = _digest_cell(tuple(reversed(fixture)), difference=difference, seed=seed)
    if first != repeated:
        raise RuntimeError("identical Phase-2R input generation produced different dataset bytes")
    if first != reversed_order:
        raise RuntimeError("S-Box input ordering changed canonical Phase-2R dataset bytes")

    summary = {
        "schema_version": 1,
        "status": "SAME_PROCESS_INPUT_PRECHECK_PASS",
        "fixture_id": FIXTURE_ID,
        "curriculum_sha256": CURRICULUM_SHA256,
        "difference": difference,
        "replicate": replicate,
        "dataset_seed": seed,
        "split_sizes": dict(zip(_PARTS, _EXPECTED_SPLIT_SIZES)),
        "split_sha256": first,
        "order_invariant": True,
        "same_process_reproducible": True,
        "neural_training_performed": False,
        "original_phase2g_artifacts_used": False,
        "cross_process_reproducibility_established": False,
        "historical_discrepancy_explained": False,
        "cryptographic_security_established": False,
    }
    payload = json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**summary, "report_sha256": hashlib.sha256(payload).hexdigest()}
