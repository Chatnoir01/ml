from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from adversarial_sbox.phase2g import CHECKPOINT_GENERATIONS, EVOLUTION_SEEDS


RUNNER = Path("scripts/run_phase2h.py")


def _receipt(seed: int, arm: str, adaptive: bool) -> dict:
    checkpoints = []
    for generation in CHECKPOINT_GENERATIONS:
        token = generation if adaptive else 0
        checkpoints.append(
            {
                "generation": generation,
                "training_count": 16,
                "training_receipt_sha256": ("%064x" % (seed + generation + 1)),
                "curriculum_digest_sha256": ("%064x" % (seed + token + 1000)),
                "curriculum_fingerprints": [f"c-{token}"],
                "population_after_fingerprints": [f"p-{token}"],
            }
        )
    return {
        "phase": "2G",
        "seed": seed,
        "arm": arm,
        "checkpoints": checkpoints,
        "selection_events": [],
    }


def _write_inputs(root: Path) -> list[Path]:
    paths: list[Path] = []
    for seed in EVOLUTION_SEEDS:
        for arm, adaptive in (("A", True), ("F", False)):
            path = root / f"{int(seed)}-{arm}.json"
            path.write_text(
                json.dumps(_receipt(int(seed), arm, adaptive), sort_keys=True),
                encoding="utf-8",
            )
            paths.append(path)
    return paths


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_phase2h_runner_manifest_is_order_invariant(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)
    first = tmp_path / "manifest-a.json"
    second = tmp_path / "manifest-b.json"

    one = _run(
        "--arm-files",
        *map(str, paths),
        "--prepare-manifest",
        "--output",
        str(first),
    )
    two = _run(
        "--arm-files",
        *map(str, reversed(paths)),
        "--prepare-manifest",
        "--output",
        str(second),
    )

    assert one.returncode == 0, one.stderr
    assert two.returncode == 0, two.stderr
    assert first.read_bytes() == second.read_bytes()


def test_phase2h_runner_emits_bound_json_and_report(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "phase2h-diagnostics.json"
    report = tmp_path / "PHASE2H_RESULT.md"

    prepared = _run(
        "--arm-files",
        *map(str, paths),
        "--prepare-manifest",
        "--output",
        str(manifest),
    )
    assert prepared.returncode == 0, prepared.stderr

    executed = _run(
        "--arm-files",
        *map(str, paths),
        "--evidence-manifest",
        str(manifest),
        "--implementation-commit",
        "a" * 40,
        "--output",
        str(output),
        "--result-md",
        str(report),
    )
    assert executed.returncode == 0, executed.stderr

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["implementation_commit"] == "a" * 40
    assert len(payload["evidence_manifest_sha256"]) == 64
    assert len(payload["diagnostic_sha256"]) == 64
    assert len(payload["input_payload_sha256"]) == 18
    assert payload["mechanism_verdict_basis"]["does_not_modify_phase2g_verdict"] is True
    assert "causal claim supported: False" in report.read_text(encoding="utf-8")


def test_phase2h_runner_rejects_corrupted_payload(tmp_path: Path) -> None:
    paths = _write_inputs(tmp_path)
    manifest = tmp_path / "manifest.json"
    prepared = _run(
        "--arm-files",
        *map(str, paths),
        "--prepare-manifest",
        "--output",
        str(manifest),
    )
    assert prepared.returncode == 0, prepared.stderr

    corrupted = json.loads(paths[0].read_text(encoding="utf-8"))
    corrupted["selection_events"] = [{"generation": 5}]
    paths[0].write_text(json.dumps(corrupted, sort_keys=True), encoding="utf-8")

    result = _run(
        "--arm-files",
        *map(str, paths),
        "--evidence-manifest",
        str(manifest),
        "--implementation-commit",
        "b" * 40,
        "--output",
        str(tmp_path / "out.json"),
    )
    assert result.returncode != 0
    assert "evidence hash mismatch" in result.stderr
