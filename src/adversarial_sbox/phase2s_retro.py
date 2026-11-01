"""Phase 2S: artifact-only, post-hoc diagnostic of the frozen depth-four peak.

NO neural training, no evolutionary feedback, no new seeds, no recomputation
of a frozen scientific verdict. All correlations are descriptive (n=6), and
the six candidates have matched headline classical metrics.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import statistics
from collections.abc import Sequence
from typing import Any

from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
from .phase2at import (
    CANDIDATE_COUNT, DEPTHS, PANEL_DIGEST_SHA256 as FROZEN_DIGEST,
    TOTAL_TRAININGS,
)
from .provenance import fingerprint_sbox

EXPECTED_PROFILE_MEANS = {
    3: 0.988990860130687,
    4: 0.32838066594698173,
    5: 0.04280126283748886,
}
EXPECTED_DEPTH4_RANGE = 0.10658153113805419
METRIC_FIELDS = (
    "differential_uniformity", "nonlinearity",
    "max_linear_correlation", "algebraic_degree",
)
EXPECTED_CLASSICAL = (8, 100, 56, 7)


class DiagnosticRejected(ValueError):
    """Frozen artifact violated a fixed audit requirement."""


def load_score_arrays(text: str) -> dict[int, tuple[float, ...]]:
    if "phase2at_depth4_peak_replicated" not in text:
        raise DiagnosticRejected("not the frozen Phase 2A-T result")
    matches = list(re.finditer(r"^Depth ([345]):\s*\n\`(\[[^\n]+\])\`", text, re.M))
    if len(matches) != len(DEPTHS):
        raise DiagnosticRejected("missing or duplicated frozen depth rows")
    rows: dict[int, tuple[float, ...]] = {}
    for match in matches:
        depth = int(match.group(1))
        if depth in rows:
            raise DiagnosticRejected("duplicate depth")
        try:
            parsed = json.loads(match.group(2))
        except (json.JSONDecodeError, ValueError) as exc:
            raise DiagnosticRejected("invalid candidate score encoding") from exc
        if (not isinstance(parsed, list) or len(parsed) != CANDIDATE_COUNT
                or any(type(x) not in (float, int) or not math.isfinite(x)
                       or not 0 <= x <= 1 for x in parsed)):
            raise DiagnosticRejected("wrong candidate score count or domain")
        values = tuple(float(x) for x in parsed)
        if abs(statistics.fmean(values) - EXPECTED_PROFILE_MEANS[depth]) > 1e-12:
            raise DiagnosticRejected("frozen mean/score mismatch")
        rows[depth] = values
    if set(rows) != set(DEPTHS):
        raise DiagnosticRejected("depth set mismatch")
    if abs(max(rows[4]) - min(rows[4]) - EXPECTED_DEPTH4_RANGE) > 1e-12:
        raise DiagnosticRejected("frozen depth-four range mismatch")
    return rows


def local_difference_row(sbox: Sequence[int], delta: int = 1) -> tuple[int, ...]:
    """DDT row for an 8-bit input difference; NOT a multi-round cryptanalysis."""
    if type(delta) is not int or not 1 <= delta <= 255:
        raise DiagnosticRejected("delta must be 1..255")
    if len(sbox) != 256 or any(type(x) is not int or x < 0 or x > 255
                               for x in sbox) or len(set(sbox)) != 256:
        raise DiagnosticRejected("expected bijective 8-bit S-box")
    values = [0] * 256
    for x in range(256):
        values[sbox[x] ^ sbox[x ^ delta]] += 1
    if sum(values) != 256 or any(x % 2 for x in values):
        raise DiagnosticRejected("invalid DDT row")
    return tuple(values)


def row_statistics(row: Sequence[int]) -> dict[str, float | int]:
    if (len(row) != 256 or any(type(v) is not int or v < 0 for v in row)
            or sum(row) != 256):
        raise DiagnosticRejected("invalid differential row")
    probs = [x / 256.0 for x in row if x]
    return {
        "support": len(probs),
        "maximum": max(row),
        "collision": math.fsum(x * x for x in probs),
        "entropy_bits": -math.fsum(x * math.log2(x) for x in probs),
    }


def pearson(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 3:
        raise DiagnosticRejected("paired observations required")
    if any(not math.isfinite(float(x)) for x in (*left, *right)):
        raise DiagnosticRejected("non-finite observations")
    center_left = statistics.fmean(left)
    center_right = statistics.fmean(right)
    x = [v - center_left for v in left]
    y = [v - center_right for v in right]
    denom = math.sqrt(math.fsum(v * v for v in x) * math.fsum(v * v for v in y))
    if denom <= 0:
        raise DiagnosticRejected("zero variance")
    return math.fsum(a * b for a, b in zip(x, y)) / denom


def audit(
    *, report: str,
    candidates: Sequence[dict[str, Any]],
    claimed_panel_digest: str,
) -> dict[str, Any]:
    if claimed_panel_digest != FROZEN_DIGEST or PANEL_DIGEST_SHA256 != FROZEN_DIGEST:
        raise DiagnosticRejected("not the frozen six-S-box panel")
    if len(candidates) != CANDIDATE_COUNT:
        raise DiagnosticRejected("not six frozen candidates")
    scores = load_score_arrays(report)
    validated: list[dict[str, Any]] = []
    for index, item in enumerate(candidates):
        sbox = tuple(item["sbox"])
        if fingerprint_sbox(sbox) != item["fingerprint"]:
            raise DiagnosticRejected(f"candidate {index} fingerprint mismatch")
        classical = tuple(item[field] for field in METRIC_FIELDS)
        if classical != EXPECTED_CLASSICAL:
            raise DiagnosticRejected(f"candidate {index} headline metrics differ")
        row = local_difference_row(sbox, 1)
        validated.append({
            "index": index,
            "fingerprint": item["fingerprint"],
            "source_seed": item["source_seed"],
            "r3_advantage": scores[3][index],
            "r4_advantage": scores[4][index],
            "r5_advantage": scores[5][index],
            "ddt_row_delta1": row_statistics(row),
            "ddt_row_sha256": hashlib.sha256(bytes(row)).hexdigest(),
        })
    collisions = tuple(row["ddt_row_delta1"]["collision"] for row in validated)
    entropy = tuple(row["ddt_row_delta1"]["entropy_bits"] for row in validated)
    r4 = scores[4]
    if len(set(row["ddt_row_sha256"] for row in validated)) < 2:
        raise DiagnosticRejected("unexpected identical local DDT rows")
    return {
        "schema_version": 1,
        "experiment": "phase2s_frozen_artifact_only_posthoc",
        "source": "research/PHASE2AT_RESULT.md + src/adversarial_sbox/phase2a_candidates.py",
        "panel_digest_sha256": FROZEN_DIGEST,
        "frozen_trainings_already_completed": TOTAL_TRAININGS,
        "new_training_count": 0,
        "frozen_verdict_changed": False,
        "candidate_count": CANDIDATE_COUNT,
        "matched_global_metrics": dict(zip(METRIC_FIELDS, EXPECTED_CLASSICAL)),
        "round_mean_advantage": {str(d): EXPECTED_PROFILE_MEANS[d] for d in DEPTHS},
        "r4_candidate_range": max(r4) - min(r4),
        "delta1_row_count_distinct": len(set(row["ddt_row_sha256"] for row in validated)),
        "pearson_r4_vs_delta1_collision": pearson(r4, collisions),
        "pearson_r4_vs_delta1_entropy": pearson(r4, entropy),
        "candidate_results": validated,
        "inference": "DESCRIPTIVE_ONLY_N6_NO_CAUSAL_OR_SECURITY_CLAIM",
    }


def report_from_frozen_repository() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    frozen = (root / "research" / "PHASE2AT_RESULT.md").read_text(encoding="utf-8")
    return audit(report=frozen, candidates=CANDIDATES,
                 claimed_panel_digest=PANEL_DIGEST_SHA256)


def main() -> None:
    print(json.dumps(report_from_frozen_repository(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
