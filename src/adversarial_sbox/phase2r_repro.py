"""Read-only, preregistered control for future Phase-2R reproducibility receipts.

No training, no model reconstruction, no held-out H, no Phase-2I authorization.
The four comparison pairs are fixed before any prospective results exist.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from typing import Any

from .phase2g import TRAINING_DATASET_BASE_SEEDS, TRAINING_MODEL_BASE_SEEDS

# Only the pre-adaptation checkpoint-0 geometry is eligible for the control.
MODEL_GRID = tuple((d, r) for d in (1, 256) for r in range(8))
RUN_GRID = (("A", 1), ("A", 2), ("F", 1), ("F", 2))
PAIR_GRID = (
    (("A", 1), ("A", 2), "A_repeat"),
    (("F", 1), ("F", 2), "F_repeat"),
    (("A", 1), ("F", 1), "AF_repeat_1"),
    (("A", 2), ("F", 2), "AF_repeat_2"),
)
PROTOCOL = {
    "schema_version": 1,
    "purpose": "post_2g_independent_checkpoint0_reproducibility_control",
    "checkpoint": 0,
    "run_grid": [list(run) for run in RUN_GRID],
    "pair_grid": [[list(a), list(b), label] for a, b, label in PAIR_GRID],
    "model_grid": [list(cell) for cell in MODEL_GRID],
    "constraint": "no_training_or_original_2g_mutation",
}
PROTOCOL_SHA256 = hashlib.sha256(
    json.dumps(PROTOCOL, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
_HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")
_THREAD_VARS = (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
)
_RUNTIME_FIELDS = (
    "python_version", "numpy_version", "platform", "blas_provider",
    "blas_version", "machine", "source_sha256", "dependency_lock_sha256",
)


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise ValueError(f"invalid or missing {label} SHA-256")
    return value.lower()


def _metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("runtime evidence must be a mapping")
    for name in _RUNTIME_FIELDS:
        item = value.get(name)
        if name.endswith("_sha256"):
            _digest(item, name)
        elif not isinstance(item, str) or not item.strip():
            raise ValueError(f"missing runtime field {name}")
    threads = value.get("thread_limits")
    if not isinstance(threads, Mapping) or set(threads) != set(_THREAD_VARS):
        raise ValueError("incomplete thread-limit provenance")
    for name, amount in threads.items():
        if type(amount) is not int or amount < 1:
            raise ValueError(f"invalid thread-limit {name}")
    return {
        **{name: (_digest(value[name], name) if name.endswith("_sha256") else value[name])
           for name in _RUNTIME_FIELDS},
        "thread_limits": {name: threads[name] for name in _THREAD_VARS},
    }


def _models(value: Any, *, curriculum_digest: str) -> dict[tuple[int, int], dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError("missing model cell receipts")
    found: dict[tuple[int, int], dict[str, Any]] = {}
    for raw in value:
        if not isinstance(raw, Mapping):
            raise ValueError("invalid model cell")
        try:
            key = (int(raw["difference"]), int(raw["replicate"]))
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise ValueError("invalid model identity") from exc
        if key not in MODEL_GRID or key in found:
            raise ValueError("duplicate or unexpected model cell")
        d, r = key
        try:
            seeds = (int(raw["dataset_seed"]), int(raw["model_seed"]))
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise ValueError("missing model seeds") from exc
        if seeds != (TRAINING_DATASET_BASE_SEEDS[r], TRAINING_MODEL_BASE_SEEDS[r]):
            raise ValueError("model seeds differ from frozen checkpoint-0 registry")
        if _digest(raw.get("curriculum_sha256"), "model curriculum") != curriculum_digest:
            raise ValueError("model curriculum receipt differs from run fixture")
        hashes = raw.get("dataset_sha256")
        if not isinstance(hashes, Mapping) or set(hashes) != {"train", "validation", "test"}:
            raise ValueError("incomplete train/validation/test dataset hashes")
        found[key] = {
            "dataset_sha256": {
                part: _digest(hashes[part], f"{part} dataset")
                for part in ("train", "validation", "test")
            },
            "initialization_sha256": _digest(raw.get("initialization_sha256"), "initialization"),
            "state_sha256": _digest(raw.get("state_sha256"), "model state"),
        }
    if set(found) != set(MODEL_GRID):
        raise ValueError("incomplete 16-model grid")
    return found


def audit_prospective_receipts(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate a *future*, externally produced 4-run fixture; never generate it.

    Reject missing/ambiguous evidence rather than pronounce successful
    reproducibility. State SHA differences are not a root-cause determination.
    """
    if not isinstance(bundle, Mapping):
        raise ValueError("receipt bundle must be a mapping")
    if bundle.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ValueError("protocol hash does not match pre-registered contract")
    runs = bundle.get("runs")
    if not isinstance(runs, Sequence) or isinstance(runs, (str, bytes, bytearray)):
        raise ValueError("missing four-run receipts")
    indexed: dict[tuple[str, int], dict[str, Any]] = {}
    for raw in runs:
        if not isinstance(raw, Mapping):
            raise ValueError("invalid run receipt")
        if isinstance(raw.get("repeat"), bool):
            raise ValueError("invalid repeat identifier")
        key = (raw.get("arm"), raw.get("repeat"))
        if key not in RUN_GRID or key in indexed:
            raise ValueError("duplicate or unexpected run identity")
        curriculum = _digest(raw.get("curriculum_sha256"), "fixture curriculum")
        indexed[key] = {
            "runtime": _metadata(raw.get("runtime")),
            "curriculum_sha256": curriculum,
            "models": _models(raw.get("models"), curriculum_digest=curriculum),
        }
    if set(indexed) != set(RUN_GRID):
        raise ValueError("incomplete A1/A2/F1/F2 run grid")

    paired = []
    for left_key, right_key, label in PAIR_GRID:
        left, right = indexed[left_key], indexed[right_key]
        same_runtime = left["runtime"] == right["runtime"]
        same_curriculum = left["curriculum_sha256"] == right["curriculum_sha256"]
        dataset_differences = 0
        initialization_differences = 0
        model_state_differences = 0
        for cell in MODEL_GRID:
            l, r = left["models"][cell], right["models"][cell]
            dataset_differences += int(l["dataset_sha256"] != r["dataset_sha256"])
            initialization_differences += int(
                l["initialization_sha256"] != r["initialization_sha256"]
            )
            model_state_differences += int(l["state_sha256"] != r["state_sha256"])
        if not same_runtime or not same_curriculum:
            status = "INCOMPARABLE_DIFFERENT_RUNTIME_OR_CURRICULUM"
        elif dataset_differences:
            status = "FAIL_DATA_BYTES_DIFFER"
        elif initialization_differences:
            status = "FAIL_INITIALIZATION_BYTES_DIFFER"
        elif model_state_differences:
            status = "FAIL_SERIALIZED_MODEL_BYTES_DIFFER"
        else:
            status = "PASS_REPRODUCIBLE_BYTES_IN_CONTROL"
        paired.append({
            "comparison": label,
            "left": list(left_key),
            "right": list(right_key),
            "same_runtime_provenance": same_runtime,
            "same_curriculum_digest": same_curriculum,
            "dataset_hash_different_cell_count": dataset_differences,
            "initialization_hash_different_cell_count": initialization_differences,
            "model_state_hash_different_cell_count": model_state_differences,
            "status": status,
        })

    passed = all(p["status"] == "PASS_REPRODUCIBLE_BYTES_IN_CONTROL" for p in paired)
    result = {
        "schema_version": 1,
        "phase": "2R_prospective_receipt_audit",
        "protocol_sha256": PROTOCOL_SHA256,
        "source": "externally_generated_receipts_only",
        "run_count": len(indexed),
        "model_cells_per_run": len(MODEL_GRID),
        "paired_comparisons": paired,
        "status": "PASS_CONTROL_BYTE_REPRODUCIBILITY" if passed else "NOT_REPRODUCIBLE_OR_INCOMPARABLE",
        "causal_explanation_established": False,
        "authorizes_phase_2i": False,
        "does_not_modify_phase_2g": True,
        "caveat": (
            "Receipt consistency does not prove hardware equality, honest "
            "collection, cryptographic security, or the cause of the frozen 2G anomaly."
        ),
    }
    result["audit_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result
