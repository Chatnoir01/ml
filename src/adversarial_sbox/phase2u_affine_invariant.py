"""Phase 2U necessary affine/extended-affine inequivalence certificate.

The FULL histogram of all differential distribution table entries is
invariant under invertible affine changes of input/output coordinates,
and under an additional affine map from input to output (EA transform).
Two functions with different global DDT histograms therefore cannot be
EA-equivalent. Equal histograms do NOT prove equivalence.

This is a mathematical **independence check on equivalence families**,
not evidence of statistically independent sample generation, real cipher
security, an original cryptographic theorem, or predictive neural learning.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .phase2u_generate import SOURCE_VERSION, digest
from .phase2u_panel import AdmissionRejected, aggregate, exclusion_history


def global_differential_spectrum(sbox: Sequence[int]) -> tuple[int, ...]:
    """Complete 255 nonzero-input rows x 256 output columns DDT histogram."""
    if (len(sbox) != 256 or any(type(v) is not int or v < 0 or v > 255 for v in sbox)
            or len(set(sbox)) != 256):
        raise AdmissionRejected("differential spectrum requires bijective 8-bit S-Box")
    count = [0] * 257
    for delta in range(1, 256):
        row = [0] * 256
        for x in range(256):
            row[sbox[x] ^ sbox[x ^ delta]] += 1
        for value in row:
            count[value] += 1
    if sum(count) != 255 * 256:
        raise AdmissionRejected("invalid full DDT grid")
    return tuple(count)


def certify_full_source_panel(source_receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Check all 12 selected + 8 earlier observed S-Boxes for EA inequivalence."""
    panel = aggregate(source_receipts)
    if panel["status"] != "PANEL_COMPLETE_NO_NEURAL_OUTCOMES":
        raise AdmissionRejected("cannot certify an incomplete or unadmitted source panel")
    references = exclusion_history()
    if len(references) != 8 or len(panel["selected_candidates"]) != 12:
        raise AdmissionRejected("unexpected candidate counts")
    rows: list[dict[str, Any]] = []
    observed: dict[tuple[int, ...], str] = {}
    original = [("historical-"+str(i), s) for i, s in enumerate(references[:6])]
    original += [("blocked-v1-31019", references[6]),
                 ("blocked-v1-31039", references[7])]
    selected = [("phase2u-"+str(c["seed"]), tuple(c["sbox"]))
                for c in panel["selected_candidates"]]
    for label, sbox in (*original, *selected):
        sig = global_differential_spectrum(sbox)
        if sig in observed:
            raise AdmissionRejected(
                f"candidate EA-family exclusion unresolved: {observed[sig]} vs {label}"
            )
        observed[sig] = label
        rows.append({
            "candidate": label,
            "differential_spectrum": list(sig),
            "nonzero_ddt_output_counts": {
                str(i): sig[i] for i in range(len(sig)) if sig[i] and i > 0
            },
        })
    report = {
        "schema_version": 1,
        "experiment": "phase2u_global_ddt_spectrum_affine_necessary_invariant",
        "source_version": SOURCE_VERSION,
        "source_panel_sha256": panel["panel_receipt_sha256"],
        "registered_seed_count": panel["examined_seed_count"],
        "new_candidate_count": 12,
        "excluded_prior_candidate_count": 8,
        "distinct_spectrum_count": len(observed),
        "certifies": "ALL_20_PAIRWISE_EA_INEQUIVALENT_BY_DIFFERENT_GLOBAL_DDT_SPECTRA",
        "does_not_certify": [
            "statistical independence of generator seeds or sampled candidate families",
            "unknown-key robustness or deployed cipher security",
            "general discovery beyond a standard affine-invariant property",
            "cryptanalytic resistance or neural predictive generalization",
        ],
        "new_neural_trainings": 0,
        "rows": rows,
    }
    report["certificate_sha256"] = digest(report)
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-source-receipts", nargs="+", required=True, type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    inputs = [json.loads(f.read_text(encoding="utf-8"))
              for f in args.original_source_receipts]
    report = certify_full_source_panel(inputs)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print("PAIRWISE_EA_INEQUIVALENCE=PASS")
    print("CERTIFICATE_SHA256=" + report["certificate_sha256"])


if __name__ == "__main__":
    main()
