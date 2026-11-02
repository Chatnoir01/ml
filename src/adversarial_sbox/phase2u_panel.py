"""Phase 2U: immutable-source provenance checks and prospective PANEL ADMISSION.

Zero neural training and zero new candidate evolution. This collects version-2
public-source receipts only, in exact registered seed order. It can produce a
PARTIAL diagnostic but NEVER accept or predict from a partial source ledger.

Source receipt SHA-256 is not an authenticated origin proof. Every source
run must also be independently replayed to claim independently established
source provenance; this module checks contents and mathematical eligibility.
"""
from __future__ import annotations

import argparse
from hashlib import sha3_256
import json
import math
from pathlib import Path
from typing import Any

from .evolution import evaluate_classical
from .phase2a_candidates import CANDIDATES as HISTORICAL
from .phase2u_generate import (
    DESIGN, SOURCE_VERSION, PUBLIC_SEEDS, TARGET_CANDIDATES,
    EXPECTED_CLASSICAL, CLASSICAL_BUDGET, GENERATIONS,
    PROPOSALS_PER_GENERATION, POPULATION_SIZE, digest,
)
from .provenance import fingerprint_sbox


class AdmissionRejected(ValueError):
    """Refuse to claim a valid prospective panel when provenance is insufficient."""


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        ch in "0123456789abcdef" for ch in value)


def exclusion_history() -> tuple[tuple[int, ...], ...]:
    """Previously observed v1 source candidates plus original six S-Boxes."""
    file = Path(__file__).resolve().parents[2] / "research" / "PHASE2U_EXCLUDE_V1_CANDIDATES.json"
    raw = json.loads(file.read_text(encoding="utf-8"))
    old = raw.get("candidates")
    if raw.get("source_study") != "phase2t_frozen_v1_BLOCKED" or len(old) != 2:
        raise AdmissionRejected("untrusted known-source exclusion record")
    expected_seeds = (31019, 31039)
    excluded = [tuple(item["sbox"]) for item in HISTORICAL]
    if len(excluded) != 6:
        raise AdmissionRejected("historical candidate registry drift")
    for seed, item in zip(expected_seeds, old):
        try:
            candidate = tuple(item["sbox"])
        except (KeyError, TypeError) as exc:
            raise AdmissionRejected("missing v1 exclusion S-Box") from exc
        if (item.get("seed") != seed or len(candidate) != 256
                or sorted(candidate) != list(range(256))
                or not _digest(item.get("fingerprint"))
                or fingerprint_sbox(candidate) != item["fingerprint"]):
            raise AdmissionRejected("corrupted historical source exclusion")
        excluded.append(candidate)
    if len({fingerprint_sbox(x) for x in excluded}) != 8:
        raise AdmissionRejected("duplicated reference exclusion")
    return tuple(excluded)


def simple_xor_clone(candidate: tuple[int, ...],
                     references: tuple[tuple[int, ...], ...]) -> bool:
    """Reject S(x XOR input_mask) XOR output_mask of any old S-Box.

    Only this small obvious equivalence family is excluded; general affine
    equivalence remains unaddressed and requires further analysis.
    """
    for reference in references:
        for input_mask in range(256):
            output_mask = candidate[0] ^ reference[input_mask]
            if all(candidate[x] == reference[x ^ input_mask] ^ output_mask
                   for x in range(256)):
                return True
    return False


def verify_source(receipt: dict[str, Any], registered_seed: int) -> dict[str, Any]:
    if type(receipt) is not dict or type(registered_seed) is not int:
        raise AdmissionRejected("invalid source receipt")
    unsealed = dict(receipt)
    claimed = unsealed.pop("source_payload_sha256", None)
    if not _digest(claimed) or digest(unsealed) != claimed:
        raise AdmissionRejected("source receipt hash mismatch")
    if (receipt.get("source_version") != SOURCE_VERSION
            or receipt.get("design") != DESIGN
            or type(receipt.get("seed")) is not int
            or receipt["seed"] != registered_seed
            or type(receipt.get("new_neural_training_count")) is not int
            or receipt["new_neural_training_count"] != 0):
        raise AdmissionRejected("source version/seed or neural provenance mismatch")
    for attr in ("original_population_sha256", "proposal_transcript_sha256"):
        if not _digest(receipt.get(attr)):
            raise AdmissionRejected("missing source transcript digests")
    evaluated = receipt.get("classical_evaluations")
    proposed = receipt.get("proposal_count")
    guided = receipt.get("guided_proposal_count")
    rescue = receipt.get("random_swap_fallback_count")
    hits = receipt.get("exact_metric_hits")
    if any(type(v) is not int or v < 0 for v in (
        evaluated, proposed, guided, rescue, hits,
    )):
        raise AdmissionRejected("invalid source budget metadata")
    if (evaluated > CLASSICAL_BUDGET or proposed != guided + rescue
            or proposed > GENERATIONS * PROPOSALS_PER_GENERATION):
        raise AdmissionRejected("source proposal/budget mismatch")
    status = receipt.get("status")
    if status == "source_exhausted":
        if (receipt.get("reason") != "bounded_fallback_exhausted"
                or evaluated >= CLASSICAL_BUDGET
                or "sbox" in receipt):
            raise AdmissionRejected("invalid exhausted-source record")
        return {"status":status, "seed":registered_seed,
                "sha256":claimed, "evaluations":evaluated}
    if status not in ("ineligible", "accepted"):
        raise AdmissionRejected("invalid source classification")
    if (evaluated != CLASSICAL_BUDGET
            or proposed != CLASSICAL_BUDGET-POPULATION_SIZE):
        raise AdmissionRejected("completed source must satisfy 340 unique evaluations")
    if status == "ineligible":
        if (hits != 0 or receipt.get("reason") != "no_exact_metric_evaluated"
                or "sbox" in receipt):
            raise AdmissionRejected("false ineligible source")
        return {"status":status,"seed":registered_seed,
                "sha256":claimed,"evaluations":evaluated}

    if hits < 1:
        raise AdmissionRejected("accepted seed without eligible classical hits")
    sbox = receipt.get("sbox")
    if (not isinstance(sbox, list) or len(sbox) != 256
            or any(type(v) is not int for v in sbox)
            or sorted(sbox) != list(range(256))):
        raise AdmissionRejected("not a bijective 8-bit S-Box")
    frozen = tuple(sbox)
    if fingerprint_sbox(frozen) != receipt.get("fingerprint"):
        raise AdmissionRejected("fingerprint does not match accepted permutation")
    met = evaluate_classical(frozen)
    metrics = (
        met.nonlinearity, met.differential_uniformity,
        met.max_linear_correlation, met.algebraic_degree,
    )
    if metrics != EXPECTED_CLASSICAL or abs(met.sac_score - .5) > .05:
        raise AdmissionRejected("candidate fails independently checked frozen metrics")
    declared = receipt.get("metrics")
    if type(declared) is not dict or declared != {
        "nonlinearity":met.nonlinearity,
        "differential_uniformity":met.differential_uniformity,
        "max_linear_correlation":met.max_linear_correlation,
        "algebraic_degree":met.algebraic_degree,
        "sac_score":met.sac_score,
    }:
        raise AdmissionRejected("source metrics differ from recomputed metrics")
    return {
        "status":"accepted", "seed":registered_seed, "sha256":claimed,
        "evaluations":evaluated, "fingerprint":met.fingerprint,
        "sbox":list(frozen), "metrics":declared,
    }


def aggregate(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    if (not isinstance(receipts, list) or not 1 <= len(receipts) <= len(PUBLIC_SEEDS)):
        raise AdmissionRejected("source ledger size invalid")
    if [x.get("seed") for x in receipts] != list(PUBLIC_SEEDS[:len(receipts)]):
        raise AdmissionRejected("source ledger must be contiguous fixed-seed prefix")
    references = exclusion_history()
    observed = {fingerprint_sbox(x) for x in references}
    records = []
    selected = []
    for i, receipt in enumerate(receipts):
        result = verify_source(receipt, PUBLIC_SEEDS[i])
        if len(selected) == TARGET_CANDIDATES:
            raise AdmissionRejected("source continued after twelfth candidate")
        records.append({k:v for k,v in result.items() if k not in ("sbox","metrics")})
        if result["status"] == "source_exhausted":
            # No candidate downstream of an incomplete source can rescue an
            # invalid contiguous provenance ledger.
            status = "SOURCE_EXHAUSTED_BLOCKED"
            break
        if result["status"] == "accepted":
            box = tuple(result["sbox"])
            if result["fingerprint"] in observed:
                status = "SOURCE_FAMILY_DUPLICATE_BLOCKED"
                break
            # Prevent within-panel XOR-equivalent copies as well as
            # clones of the eight earlier observed S-Boxes.
            new_panel_origins = tuple(tuple(item["sbox"]) for item in selected)
            if simple_xor_clone(box, references + new_panel_origins):
                status = "SOURCE_FAMILY_CLONE_BLOCKED"
                break
            observed.add(result["fingerprint"])
            selected.append(result)
    else:
        if len(selected) == TARGET_CANDIDATES:
            status = "PANEL_COMPLETE_NO_NEURAL_OUTCOMES"
        elif len(receipts) == len(PUBLIC_SEEDS):
            status = "PANEL_INCOMPLETE_DO_NOT_PREDICT"
        else:
            status = "SOURCE_PREFIX_PARTIAL_DO_NOT_PREDICT"

    output = {
        "schema_version":1,
        "experiment":"phase2u_frozen_source_admission",
        "source_version":SOURCE_VERSION,
        "registered_seed_prefix":[x["seed"] for x in records],
        "source_receipt_sha256_ordered":[x["sha256"] for x in records],
        "examined_seed_count":len(records),
        "selected_count":len(selected),
        "status":status,
        "selected_candidates":selected,
        "new_neural_trainings":0,
        "scientific_interpretation":"SOURCE_ONLY_NOT_NEURAL_PREDICTION",
    }
    output["panel_receipt_sha256"] = digest(output)
    return output


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed-receipts",nargs="+",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=[json.loads(path.read_text(encoding="utf-8")) for path in args.seed_receipts]
    document=aggregate(data)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(document,f,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print(document["status"], document["panel_receipt_sha256"])
    if document["status"].endswith("BLOCKED"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
