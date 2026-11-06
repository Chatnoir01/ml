"""One-host, two-process CPU-kernel experiment for the Phase 2R *synthetic* fixture.

The Python/NumPy/BLAS versions and CPU must be the same; only the requested
OpenBLAS dynamic kernel changes (HASWELL vs NEHALEM). No neural training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .phase2r_forward_only_probe import (
    _STAGES,
    _array_receipt,
    _canonical,
    compare_forward_probes,
)

EXPECTED_NUMPY = "2.5.3"
EXPECTED_PYTHON = "3.12.14"
EXPECTED_KERNELS = ("Haswell", "Nehalem")
EXPERIMENT = "phase2r_same_host_haswell_vs_nehalem_forward_only_v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _actual_kernel(report: dict[str, Any]) -> str:
    profile = report["runtime_profile"]
    libs = profile.get("blas_libraries")
    if (type(libs) is not list or len(libs) != 1 or
            libs[0].get("internal_api") != "openblas" or
            type(libs[0].get("num_threads")) is not int or
            libs[0]["num_threads"] != 1 or
            type(libs[0].get("architecture")) is not str):
        raise ValueError("actual OpenBLAS library, core and single thread must be evidenced")
    if (profile.get("python_version") != EXPECTED_PYTHON or
            profile.get("numpy_version") != EXPECTED_NUMPY):
        raise ValueError("wrong pinned numerical software version")
    return libs[0]["architecture"]


def _normalized_without_core(profile: dict[str, Any]) -> dict[str, Any]:
    # Require all recorded CPU/SIMD and BLAS properties (including version)
    # to be equal; only the *selected OpenBLAS core* may change.
    copy = json.loads(json.dumps(profile))
    for lib in copy["blas_libraries"]:
        lib.pop("architecture")
    return copy


def audit_controlled_dispatch(
    haswell_receipt: dict[str, Any],
    nehalem_receipt: dict[str, Any],
    haswell_arrays_path: Path,
    nehalem_arrays_path: Path,
) -> dict[str, Any]:
    """Verify original JSON + source float32 tensors, measure exact differences."""
    import numpy as np

    h, n = haswell_receipt, nehalem_receipt
    # Reuse the previously validated exact-source, seeded, 7-stage probe checker.
    baseline = compare_forward_probes(h, n)
    if (_actual_kernel(h), _actual_kernel(n)) != EXPECTED_KERNELS:
        raise ValueError("forced HASWELL vs NEHALEM did not select the registered cores")
    if (_normalized_without_core(h["runtime_profile"]) !=
            _normalized_without_core(n["runtime_profile"])):
        raise ValueError("not one comparable numerical host / changed unrelated runtime feature")
    if baseline["stage_count"] != len(_STAGES):
        raise ValueError("incomplete forward stage coverage")

    bytes_h = haswell_arrays_path.read_bytes()
    bytes_n = nehalem_arrays_path.read_bytes()
    differences: list[dict[str, Any]] = []
    with np.load(haswell_arrays_path, allow_pickle=False) as ha, \
         np.load(nehalem_arrays_path, allow_pickle=False) as na:
        if set(ha.files) != set(_STAGES) or set(na.files) != set(_STAGES):
            raise ValueError("missing or extra synthetic array stages in NPZ")
        for name in _STAGES:
            a = ha[name]
            b = na[name]
            if _array_receipt(a) != h["stages"][name] or _array_receipt(b) != n["stages"][name]:
                raise ValueError("NPZ stage bytes do not match sealed original stage digest")
            if a.shape != b.shape:
                raise ValueError("different stage shapes across kernels")
            mismatched = int(np.count_nonzero(a.view(np.uint32) != b.view(np.uint32)))
            delta = np.abs(a.astype(np.float64) - b.astype(np.float64))
            summary = {
                "stage": name,
                "elements": int(a.size),
                "bitwise_differing_float32_values": mismatched,
                "maximum_absolute_difference": float(delta.max()) if a.size else 0.0,
                "mean_absolute_difference": float(delta.mean()) if a.size else 0.0,
                "haswell_sha256": h["stages"][name]["sha256"],
                "nehalem_sha256": n["stages"][name]["sha256"],
            }
            if ((mismatched == 0) !=
                    (h["stages"][name]["sha256"] == n["stages"][name]["sha256"])):
                raise ValueError("fingerprint and bytewise comparison disagree")
            differences.append(summary)

    if differences[0]["bitwise_differing_float32_values"] != 0:
        raise ValueError("synthetic input bytes differ before any BLAS computation")
    first = next((x["stage"] for x in differences
                  if x["bitwise_differing_float32_values"]), None)
    if baseline["earliest_different_stage"] != first:
        raise ValueError("first unequal stage did not match independently audited SHA")
    report = {
        "schema_version": 1,
        "experiment": EXPERIMENT,
        "historical_phase2g_experiment": False,
        "synthetic_fixture_only": True,
        "same_machine_by_workflow_design_not_hardware_attested": True,
        "source_commit": h["source_commit"],
        "original_blanks_preserved": False,
        "kernel_pair": ["Haswell", "Nehalem"],
        "pinned_python": EXPECTED_PYTHON,
        "pinned_numpy": EXPECTED_NUMPY,
        "identical_cpu_and_blas_properties_except_core": True,
        "numerical_runtime_shared_properties_sha256": _sha(
            _canonical(_normalized_without_core(h["runtime_profile"]))
        ),
        "original_receipt_sha256": {
            "haswell": h["receipt_sha256"],
            "nehalem": n["receipt_sha256"],
        },
        "original_npz_file_sha256": {
            "haswell": _sha(bytes_h),
            "nehalem": _sha(bytes_n),
        },
        "stages": differences,
        "first_bitwise_different_stage": first,
        "distinct_stage_count": sum(
            bool(x["bitwise_differing_float32_values"]) for x in differences
        ),
        "outcome": ("BITWISE_DIFFERENCE_OBSERVED_WITH_CONTROLLED_DISPATCH" if first
                    else "NO_BITWISE_DIFFERENCE_IN_SAMPLED_FORWARD_PASS"),
        "neural_training_performed": False,
        "gradients_computed": False,
        "optimizer_update_performed": False,
        "original_phase2g_64_of_144_explained": False,
        "scientific_status": "EXPLORATORY_SYNTHETIC_BACKEND_SENSITIVITY_ONLY",
    }
    report["report_sha256"] = _sha(_canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--haswell-json", type=Path, required=True)
    parser.add_argument("--nehalem-json", type=Path, required=True)
    parser.add_argument("--haswell-npz", type=Path, required=True)
    parser.add_argument("--nehalem-npz", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.haswell_json, args.nehalem_json, args.haswell_npz, args.nehalem_npz]
    if len({p.resolve() for p in (*inputs, args.output)}) != 5:
        parser.error("all four input and output paths must differ")
    report = audit_controlled_dispatch(
        json.loads(args.haswell_json.read_text(encoding="utf-8")),
        json.loads(args.nehalem_json.read_text(encoding="utf-8")),
        args.haswell_npz, args.nehalem_npz,
    )
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=2, allow_nan=False)
        f.write("\n")
    print(report["outcome"], "FIRST", report["first_bitwise_different_stage"],
          "CHANGED_STAGES", report["distinct_stage_count"])


if __name__ == "__main__":
    main()
