"""Pinned, synthetic Phase-2R reference curriculum. No training or security claim.

The candidate bytes are committed independently of Python's random API.
This is an intentionally new diagnostic fixture; it is NOT the original
Phase-2G seed's initial candidate population and cannot reproduce old weights.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FIXTURE_ID = "phase2r-synthetic-v1"
CURRICULUM_SHA256 = "09e94da031992240d857a139768445c042cb712abf866f15084300a4a267e8a2"
CANONICAL_FIXTURE_JSON_SHA256 = "ca6eea1f554b1004ad69d0da828ae2fac5cdb5a4d1f5f6ab80e5787ce5c9a106"
FIXTURE_FILE = "phase2r-synthetic-curriculum-v1.json"


def load_phase2r_fixture(path: Path | None = None) -> tuple[tuple[int, ...], ...]:
    """Read complete candidate bytes; reject even well-formed altered fixtures."""
    source = path if path is not None else (
        Path(__file__).resolve().parents[2] / "research" / "fixtures" / FIXTURE_FILE
    )
    try:
        payload: Any = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Phase-2R fixture file unreadable") from exc
    if not isinstance(payload, dict):
        raise ValueError("Phase-2R fixture must be an object")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != CANONICAL_FIXTURE_JSON_SHA256:
        raise ValueError("Phase-2R fixture content differs from preregistered bytes")
    if payload.get("fixture_id") != FIXTURE_ID:
        raise ValueError("Phase-2R fixture identity drift")
    if payload.get("curriculum_digest_sha256") != CURRICULUM_SHA256:
        raise ValueError("Phase-2R fixture curriculum hash drift")
    candidates = payload.get("candidate_hex")
    if not isinstance(candidates, list) or len(candidates) != 20:
        raise ValueError("Phase-2R fixture requires exactly 20 candidates")
    actual: list[tuple[int, ...]] = []
    fingerprints: list[str] = []
    for value in candidates:
        if not isinstance(value, str) or len(value) != 512:
            raise ValueError("Phase-2R candidate must contain exactly 256 bytes")
        try:
            decoded = bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError("Phase-2R candidate contains invalid hexadecimal") from exc
        if len(decoded) != 256 or set(decoded) != set(range(256)):
            raise ValueError("Phase-2R candidates must be bijective 8-bit S-Boxes")
        actual.append(tuple(decoded))
        fingerprints.append(hashlib.sha3_256(decoded).hexdigest())
    if len(set(actual)) != 20:
        raise ValueError("Phase-2R fixture duplicates a candidate")
    derived = hashlib.sha256("\n".join(sorted(fingerprints)).encode("ascii")).hexdigest()
    if derived != CURRICULUM_SHA256:
        raise ValueError("Phase-2R candidate fingerprints differ from declared curriculum")
    return tuple(sorted(actual, key=lambda candidate: hashlib.sha3_256(bytes(candidate)).hexdigest()))
