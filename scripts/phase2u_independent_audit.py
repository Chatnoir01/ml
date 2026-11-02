"""Independent Phase 2U GitHub Actions ZIP audit. Python standard library only.

Does NOT import the research classical evaluator, source generator, or
prediction code. Recomputes NL, DU, LAT max, ANF degree and SAC directly
from each accepted 256-byte permutation; checks signed-by-nobody SHA-256
research receipts, SHA3-256 S-Box identity, ordered source seeds, and
simple XOR clones among accepted candidates.

It does NOT prove generator execution provenance or source-family
independence. For that, retain the original job logs and replay seeds.
No neural training or novel cryptographic security claims.
"""
from __future__ import annotations

import argparse
import collections
from hashlib import sha256, sha3_256
import json
from pathlib import Path
import sys
import zipfile

REGISTERED_SEEDS = (
    41003, 41011, 41017, 41027, 41039, 41047, 41051, 41057,
    41063, 41071, 41077, 41081, 41089, 41101, 41113, 41117,
    41131, 41141, 41143, 41149, 41161, 41177, 41183, 41189,
)
EXPECTED = {
    "nonlinearity": 100,
    "differential_uniformity": 8,
    "max_linear_correlation": 56,
    "algebraic_degree": 7,
}
MAX_UNCOMPRESSED = 128 * 1024
VERSION = "phase2u_source_v1"
DESIGN = "phase2u_bounded_unique_fallback_v1"


class AuditRejected(ValueError):
    """Source receipt and/or independent mathematical check failed."""


def classical_metrics(box: list[int]) -> dict:
    if (type(box) is not list or len(box) != 256
            or any(type(v) is not int for v in box)
            or sorted(box) != list(range(256))):
        raise AuditRejected("invalid bijective 8-bit S-Box")

    du = 0
    for difference in range(1, 256):
        counters = [0] * 256
        for x in range(256):
            counters[box[x] ^ box[x ^ difference]] += 1
        du = max(du, max(counters))

    max_w = 0
    max_lat = 0
    for output_mask in range(1, 256):
        row = [1 - 2 * ((box[x] & output_mask).bit_count() & 1)
               for x in range(256)]
        step = 1
        while step < 256:
            for off in range(0, 256, 2 * step):
                for i in range(off, off + step):
                    a, b = row[i], row[i + step]
                    row[i], row[i + step] = a + b, a - b
            step <<= 1
        max_w = max(max_w, max(abs(x) for x in row))
        max_lat = max(max_lat, max(abs(x) for x in row[1:]))

    degree = 0
    for output_bit in range(8):
        coeff = [(v >> output_bit) & 1 for v in box]
        for in_bit in range(8):
            for input_mask in range(256):
                if input_mask & (1 << in_bit):
                    coeff[input_mask] ^= coeff[input_mask ^ (1 << in_bit)]
        degree = max(degree, max((mask.bit_count() for mask, c
                                  in enumerate(coeff) if c), default=0))

    flips = sum((box[x] ^ box[x ^ (1 << bit)]).bit_count()
                for bit in range(8) for x in range(256))
    return {
        "nonlinearity": 128 - max_w // 2,
        "differential_uniformity": du,
        "max_linear_correlation": max_lat,
        "algebraic_degree": degree,
        "sac_score": flips / (256 * 8 * 8),
    }


def _digest(record: dict) -> str:
    return sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("ascii")
    ).hexdigest()


def audit_receipt(raw: dict) -> tuple[dict, tuple[int, ...] | None]:
    if type(raw) is not dict:
        raise AuditRejected("source receipt must be a JSON mapping")
    record = dict(raw)
    claimed = record.pop("source_payload_sha256", None)
    if (type(claimed) is not str or len(claimed) != 64
            or claimed != _digest(record)):
        raise AuditRejected("source SHA-256 mismatch")
    seed = raw.get("seed")
    status = raw.get("status")
    if (type(seed) is not int or seed not in REGISTERED_SEEDS
            or raw.get("source_version") != VERSION
            or raw.get("design") != DESIGN
            or type(raw.get("new_neural_training_count")) is not int
            or raw["new_neural_training_count"] != 0):
        raise AuditRejected("wrong source version/seed or neural contamination")
    attempts = raw.get("classical_evaluations")
    proposals = raw.get("proposal_count")
    guided = raw.get("guided_proposal_count")
    fallback = raw.get("random_swap_fallback_count")
    hits = raw.get("exact_metric_hits")
    if any(type(v) is not int or v < 0 for v in (
        attempts, proposals, guided, fallback, hits
    )) or proposals != guided + fallback or attempts > 340:
        raise AuditRejected("inconsistent source evaluation budget")
    base = {
        "seed": seed, "status": status,
        "evaluations": attempts, "proposals": proposals,
        "fallback": fallback, "exact_metric_hits": hits,
        "source_sha256": claimed,
    }
    if status == "source_exhausted":
        if attempts >= 340 or raw.get("reason") != "bounded_fallback_exhausted":
            raise AuditRejected("incorrect exhausted source record")
        return base, None
    if status not in ("accepted", "ineligible"):
        raise AuditRejected("unregistered outcome")
    if attempts != 340 or proposals != 320:
        raise AuditRejected("completed source budget is not 340/320")
    if status == "ineligible":
        if hits != 0 or raw.get("reason") != "no_exact_metric_evaluated":
            raise AuditRejected("false ineligible classification")
        if "sbox" in raw or "fingerprint" in raw:
            raise AuditRejected("ineligible receipt contains candidate")
        return base, None

    if hits < 1:
        raise AuditRejected("accepted seed reports no classical hit")
    box = raw.get("sbox")
    measured = classical_metrics(box)
    if {k: measured[k] for k in EXPECTED} != EXPECTED:
        raise AuditRejected("accepted source S-Box has wrong classical metrics")
    if abs(measured["sac_score"] - 0.5) > 0.05:
        raise AuditRejected("SAC constraint fails")
    if measured != raw.get("metrics"):
        raise AuditRejected("source declared metrics disagree with independent recomputation")
    fingerprint = sha3_256(bytes(box)).hexdigest()
    if fingerprint != raw.get("fingerprint"):
        raise AuditRejected("source candidate SHA3-256 mismatch")
    base.update({"fingerprint": fingerprint, "independent_metrics": measured})
    return base, tuple(box)


def xor_clone(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    """Detect a(x) == b(x XOR input_mask) XOR output_mask."""
    if len(a) != 256 or len(b) != 256:
        raise AuditRejected("bad clone inputs")
    for input_mask in range(256):
        out = a[0] ^ b[input_mask]
        if all(a[x] == (b[x ^ input_mask] ^ out) for x in range(256)):
            return True
    return False


def audit_zip(path: Path) -> tuple[dict, tuple[int, ...] | None]:
    with zipfile.ZipFile(path) as zf:
        members = zf.infolist()
        if len(members) != 1:
            raise AuditRejected("expected exactly one original source JSON")
        member = members[0]
        if (member.file_size > MAX_UNCOMPRESSED
                or member.file_size <= 0 or not member.filename.startswith("seed-")
                or not member.filename.endswith(".json")
                or "/" in member.filename):
            raise AuditRejected("malformed or oversized source archive")
        raw = json.loads(zf.read(member))
        if member.filename != f"seed-{raw.get('seed')}.json":
            raise AuditRejected("seed filename/content mismatch")
        return audit_receipt(raw)


def audit_files(paths: list[Path]) -> dict:
    if not paths:
        raise AuditRejected("no original source artifacts")
    results = []
    boxes: list[tuple[int, tuple[int, ...]]] = []
    for path in paths:
        record, box = audit_zip(path)
        results.append(record)
        if box is not None:
            for seed, prior in boxes:
                if xor_clone(box, prior):
                    raise AuditRejected(
                        f"prospective S-Boxes {seed} and {record['seed']} are XOR clones"
                    )
            boxes.append((record["seed"], box))
    results.sort(key=lambda r: r["seed"])
    seeds = [r["seed"] for r in results]
    if len(set(seeds)) != len(seeds):
        raise AuditRejected("duplicated source receipt")
    if seeds != list(REGISTERED_SEEDS[:len(seeds)]):
        raise AuditRejected("source receipts do not form complete registered prefix")
    status = ("SOURCE_BLOCKED" if any(x["status"] == "source_exhausted"
                                    for x in results)
              else "PARTIAL_SOURCE_AUDIT_NO_NEURAL")
    data = {
        "schema_version": 1,
        "source_version": VERSION,
        "status": status,
        "registered_seed_prefix": seeds,
        "audited_seed_count": len(results),
        "new_source_candidates": len(boxes),
        "new_neural_trainings": 0,
        "all_source_receipts_and_independent_classical_checks_pass": True,
        "prior_family_and_general_affine_lineage_checks_not_proven": True,
        "rows": results,
    }
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_source_zips", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit_files(args.original_source_zips)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(report, out, sort_keys=True, indent=2, allow_nan=False)
        out.write("\n")
    print(report["status"], report["audited_seed_count"],
          report["new_source_candidates"])


if __name__ == "__main__":
    main()
