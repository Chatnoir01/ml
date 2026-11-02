"""Independent standard-library audit for raw Phase 2T seed ZIP artifacts.

This intentionally DOES NOT import the research evaluator; it recomputes
8-bit S-Box NL, DDT maximum, LAT maximum, ANF degree and SAC directly.

Usage:
    python scripts/phase2t_audit_artifacts.py github-actions-artifact-*.zip

It does not prove the random search was executed faithfully. Full seed-run
replay and the original GitHub job logs remain required for source provenance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile


def metrics(box: list[int]) -> dict:
    if len(box) != 256 or sorted(box) != list(range(256)):
        raise ValueError("not a bijective 8-bit S-Box")
    du = 0
    for delta in range(1, 256):
        row = [0] * 256
        for x in range(256):
            row[box[x] ^ box[x ^ delta]] += 1
        du = max(du, max(row))
    max_walsh = 0
    max_lat = 0
    for output_mask in range(1, 256):
        w = [1 - 2 * ((box[x] & output_mask).bit_count() & 1)
             for x in range(256)]
        step = 1
        while step < 256:
            for offset in range(0, 256, step * 2):
                for j in range(offset, offset + step):
                    a, b = w[j], w[j + step]
                    w[j], w[j + step] = a + b, a - b
            step *= 2
        max_walsh = max(max_walsh, max(abs(x) for x in w))
        max_lat = max(max_lat, max(abs(x) for x in w[1:]))
    degree = 0
    for bit in range(8):
        a = [(v >> bit) & 1 for v in box]
        for coordinate in range(8):
            for mask in range(256):
                if mask & (1 << coordinate):
                    a[mask] ^= a[mask ^ (1 << coordinate)]
        degree = max(degree, max((mask.bit_count() for mask, value
                                  in enumerate(a) if value), default=0))
    sac_count = sum((box[x] ^ box[x ^ (1 << bit)]).bit_count()
                    for bit in range(8) for x in range(256))
    return {
        "nonlinearity": 128 - max_walsh // 2,
        "differential_uniformity": du,
        "max_linear_correlation": max_lat,
        "algebraic_degree": degree,
        "sac_score": sac_count / (256 * 8 * 8),
    }


def audit_receipt(receipt: dict) -> dict:
    unsigned = dict(receipt)
    claimed = unsigned.pop("source_payload_sha256")
    actual = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("ascii")
    ).hexdigest()
    if claimed != actual:
        raise ValueError("source receipt SHA-256 does not match")
    if receipt.get("evaluations") != 340 or receipt.get("neural_training_count") != 0:
        raise ValueError("scientific fixed budget or neural separation violated")
    result = {
        "seed":receipt["seed"], "status":receipt["status"],
        "evaluations":340, "neural_trainings":0,
        "source_payload_sha256":claimed,
    }
    if receipt["status"] == "accepted":
        box = receipt["sbox"]
        if hashlib.sha3_256(bytes(box)).hexdigest() != receipt["fingerprint"]:
            raise ValueError("source S-Box fingerprint mismatch")
        calculated = metrics(box)
        if calculated != receipt["metrics"]:
            raise ValueError(f"reported metrics disagree: {calculated}")
        result["fingerprint"] = receipt["fingerprint"]
        result["independent_metrics"] = calculated
    elif receipt["status"] == "ineligible":
        if receipt.get("exact_metric_hits_in_ledger") != 0:
            raise ValueError("false ineligibility receipt")
    else:
        raise ValueError("unrecognized source receipt status")
    return result


def audit_zip(path: Path) -> list[dict]:
    out = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if len(names) != 1 or not names[0].startswith("seed-") or not names[0].endswith(".json"):
            raise ValueError("expected one original seed JSON per GitHub artifact")
        if zf.getinfo(names[0]).file_size > 128 * 1024:
            raise ValueError("oversized source artifact")
        data = json.loads(zf.read(names[0]))
        out.append(audit_receipt(data))
    return out


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        raise SystemExit("pass original archived GitHub Actions ZIPs as inputs")
    verified = [item for path in paths for item in audit_zip(path)]
    seeds = [r["seed"] for r in verified]
    if len(seeds) != len(set(seeds)):
        raise ValueError("duplicate source seed receipts")
    print(json.dumps({"independent_audit":True, "results":sorted(
        verified, key=lambda r:r["seed"])}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
