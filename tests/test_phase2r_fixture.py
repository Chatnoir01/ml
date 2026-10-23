"""The synthetic reference curriculum is pinned byte-for-byte, never optimized."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from adversarial_sbox.phase2r_fixture import (
    CANONICAL_FIXTURE_JSON_SHA256,
    CURRICULUM_SHA256,
    FIXTURE_FILE,
    FIXTURE_ID,
    load_phase2r_fixture,
)


def _source() -> Path:
    return Path(__file__).resolve().parents[1] / "research" / "fixtures" / FIXTURE_FILE


def test_preregistered_fixture_is_exactly_20_distinct_byte_permutations() -> None:
    boxes = load_phase2r_fixture()
    assert len(boxes) == 20
    assert len(set(boxes)) == 20
    assert all(len(box) == 256 and set(box) == set(range(256)) for box in boxes)


def test_fixture_bytes_and_curriculum_hash_are_pinned() -> None:
    data = json.loads(_source().read_text(encoding="utf-8"))
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == CANONICAL_FIXTURE_JSON_SHA256
    assert data["fixture_id"] == FIXTURE_ID
    assert data["curriculum_digest_sha256"] == CURRICULUM_SHA256
    fingerprints = sorted(
        hashlib.sha3_256(bytes.fromhex(candidate)).hexdigest()
        for candidate in data["candidate_hex"]
    )
    assert hashlib.sha256("\n".join(fingerprints).encode("ascii")).hexdigest() == CURRICULUM_SHA256


def test_altered_candidate_bytes_fail_prior_to_any_training(tmp_path: Path) -> None:
    data = json.loads(_source().read_text(encoding="utf-8"))
    data["candidate_hex"][0] = data["candidate_hex"][0][2:] + data["candidate_hex"][0][:2]
    target = tmp_path / "tampered.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="preregistered bytes"):
        load_phase2r_fixture(target)


def test_candidate_loss_or_unregistered_identity_fails(tmp_path: Path) -> None:
    data = json.loads(_source().read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    bad["candidate_hex"].pop()
    target = tmp_path / "missing.json"
    target.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="preregistered bytes"):
        load_phase2r_fixture(target)
    bad = copy.deepcopy(data)
    bad["fixture_id"] = "replacement-fixture"
    target.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="preregistered bytes"):
        load_phase2r_fixture(target)


def test_unreadable_or_non_json_fixture_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "unreadable.json"
    with pytest.raises(ValueError, match="unreadable"):
        load_phase2r_fixture(target)
    target.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="unreadable"):
        load_phase2r_fixture(target)
