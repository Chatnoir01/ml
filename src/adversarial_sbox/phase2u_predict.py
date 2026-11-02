"""Phase 2U: classical-only, source-bound FROZEN PREDICTION receipt.

This reuses the exact single-bit rule originally specified before any fresh
neural Phase 2T or Phase 2U outcomes:
    4-round ToySPN, historical fixed public keys, XOR differences 1 and 256,
    training-only output-bit selection, signed held-out advantage, equal mean.

A prediction is computed ONLY from the original raw source seed receipts
after re-running the entire Phase 2U source-panel admission gate. Manually
provided or incomplete panels are NOT accepted. No neural data is loaded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .phase2t_predict import (
    DEPTH, DIFFERENCES, TRAIN_PER_LABEL, TEST_PER_LABEL, FEATURE_RULE,
    classical_signal,
)
from .phase2u_generate import DESIGN, SOURCE_VERSION, TARGET_CANDIDATES, digest
from .phase2u_panel import AdmissionRejected, aggregate


class PredictionRejected(AdmissionRejected):
    """Do not generate or modify a prediction without a complete source ledger."""


def freeze_from_raw_seed_receipts(seed_receipts: list[dict[str, Any]]) -> dict[str, Any]:
    source = aggregate(seed_receipts)
    if source["status"] != "PANEL_COMPLETE_NO_NEURAL_OUTCOMES":
        raise PredictionRejected(
            "cannot freeze predictions until all twelve independent source candidates pass"
        )
    if source["selected_count"] != TARGET_CANDIDATES:
        raise PredictionRejected("source panel size changed")
    rows = []
    for entry in source["selected_candidates"]:
        sbox = tuple(entry["sbox"])
        components = [classical_signal(sbox, difference) for difference in DIFFERENCES]
        score = sum(x["signed_holdout_advantage"] for x in components) / len(components)
        rows.append({
            "seed":entry["seed"],
            "source_seed_receipt_sha256":entry["sha256"],
            "fingerprint":entry["fingerprint"],
            "feature_components":components,
            "classical_feature_score":score,
        })
    ranking = sorted(rows,key=lambda row:(
        -row["classical_feature_score"],row["fingerprint"]
    ))
    result = {
        "schema_version":1,
        "experiment":"phase2u_classical_predictions_sealed_before_neural",
        "source_version":SOURCE_VERSION,
        "source_design":DESIGN,
        "source_panel_receipt_sha256":source["panel_receipt_sha256"],
        "ordered_source_sha256":source["source_receipt_sha256_ordered"],
        "candidate_count":TARGET_CANDIDATES,
        "feature_rule":FEATURE_RULE,
        "depth":DEPTH,
        "public_key_schedule":"historical",
        "differences":list(DIFFERENCES),
        "train_per_label":TRAIN_PER_LABEL,
        "test_per_label":TEST_PER_LABEL,
        "predictions":rows,
        "best_first_fingerprints":[row["fingerprint"] for row in ranking],
        "new_neural_trainings":0,
        "neural_outcomes_accessed":False,
        "scientific_status":"PRECOMMITTED_PREDICTION_UNEVALUATED",
        "inference_limits":[
            "Source randomness, lineage independence and execution timing need independent review",
            "This hypothesis is reused from the historical Phase 2S/2T work",
            "The SHA-256 receipt is not an independently authenticated timestamp",
            "No real cipher or original cryptographic-security claim",
        ],
    }
    result["prediction_receipt_sha256"]=digest(result)
    return result


def verify_prediction_receipt(document: dict[str, Any]) -> None:
    if type(document) is not dict:
        raise PredictionRejected("prediction document is not a JSON mapping")
    unsigned = dict(document)
    receipt_sha = unsigned.pop("prediction_receipt_sha256",None)
    if not isinstance(receipt_sha,str) or len(receipt_sha)!=64 or digest(unsigned)!=receipt_sha:
        raise PredictionRejected("prediction receipt integrity failure")
    if (document.get("experiment")!="phase2u_classical_predictions_sealed_before_neural"
            or document.get("source_version")!=SOURCE_VERSION
            or document.get("feature_rule")!=FEATURE_RULE
            or document.get("depth")!=DEPTH
            or document.get("differences")!=list(DIFFERENCES)
            or document.get("candidate_count")!=TARGET_CANDIDATES
            or document.get("train_per_label")!=TRAIN_PER_LABEL
            or document.get("test_per_label")!=TEST_PER_LABEL
            or document.get("new_neural_trainings")!=0
            or document.get("neural_outcomes_accessed") is not False
            or document.get("scientific_status")!="PRECOMMITTED_PREDICTION_UNEVALUATED"):
        raise PredictionRejected("unexpected or unblinded prediction protocol")
    rows=document.get("predictions")
    if not isinstance(rows,list) or len(rows)!=TARGET_CANDIDATES:
        raise PredictionRejected("prediction row count mismatch")
    ids=[r["fingerprint"] for r in rows]
    if (len(set(ids))!=TARGET_CANDIDATES
            or len(set(r["seed"] for r in rows))!=TARGET_CANDIDATES
            or any(len(s)!=64 for s in ids)):
        raise PredictionRejected("duplicate or invalid prospective candidates")
    for row in rows:
        components=row["feature_components"]
        if (len(components)!=len(DIFFERENCES)
                or [x["difference"] for x in components]!=list(DIFFERENCES)
                or any(type(x["signed_holdout_advantage"]) not in (int,float)
                       or not -1<=x["signed_holdout_advantage"]<=1
                       for x in components)):
            raise PredictionRejected("invalid frozen feature components")
        score=sum(x["signed_holdout_advantage"] for x in components)/len(components)
        if row["classical_feature_score"]!=score:
            raise PredictionRejected("feature rule not applied correctly")
    order=sorted(rows,key=lambda r:(-r["classical_feature_score"],r["fingerprint"]))
    if document.get("best_first_fingerprints")!=[r["fingerprint"] for r in order]:
        raise PredictionRejected("ranking changed after freeze")


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-seed-receipts",nargs="+",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    if args.output.resolve() in {x.resolve() for x in args.raw_seed_receipts}:
        raise SystemExit("input and output paths must differ")
    receipts=[json.loads(path.read_text(encoding="utf-8"))
              for path in args.raw_seed_receipts]
    result=freeze_from_raw_seed_receipts(receipts)
    verify_prediction_receipt(result)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print("PHASE2U_PREDICTION_SEALED="+result["prediction_receipt_sha256"])


if __name__ == "__main__":
    main()
