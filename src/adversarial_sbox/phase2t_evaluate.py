"""Phase 2T sealed-label evaluation of pre-committed fresh-S-Box rankings.

This module must only be called AFTER a prediction receipt has been frozen
and independently timestamped. It does not generate candidates, train neural
networks, select new predictive features, or amend earlier scientific results.
A positive result would be a toy-cipher predictive association, not a proof
of cryptographic strength, new primitives, or general neural cryptanalysis.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any

from .phase2t_predict import (
    DIFFERENCES, TARGET_CANDIDATES, PredictionRejected,
    check_frozen, canonical, digest,
)

DATASET_SEEDS = (930101, 930113, 930127, 930139)
MODEL_SEEDS = (940101, 940113, 940127, 940139)
PERMUTATIONS = 19999
PERMUTATION_SEED = 950101
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 950113
EXPECTED_TOTAL_NEURAL_TRAININGS = TARGET_CANDIDATES * len(DIFFERENCES) * len(DATASET_SEEDS)
SPEARMAN_MINIMUM = 0.60
PERMUTATION_P_THRESHOLD = 0.05
MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL = 0.02


def _hex_digest(s: object) -> bool:
    return (isinstance(s, str) and len(s) == 64
            and all(ch in "0123456789abcdef" for ch in s))


def _rank_ties(values: list[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        mean_rank = ((start + 1) + end) / 2.0
        for j in range(start, end):
            ranks[ordered[j]] = mean_rank
        start = end
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        raise PredictionRejected("paired observations required")
    if any(not math.isfinite(float(z)) for z in (*x, *y)):
        raise PredictionRejected("non-finite predictive observations")
    a, b = _rank_ties(x), _rank_ties(y)
    u, v = statistics.fmean(a), statistics.fmean(b)
    numerator = math.fsum((p-u)*(q-v) for p,q in zip(a,b))
    xvar = math.fsum((p-u)**2 for p in a)
    yvar = math.fsum((q-v)**2 for q in b)
    if xvar == 0 or yvar == 0:
        return None
    return numerator / math.sqrt(xvar*yvar)


def one_sided_permutation_p(x: list[float], y: list[float],
                            observed: float) -> float:
    """Monte Carlo rank-label permutation test, one prespecified direction."""
    rng = random.Random(PERMUTATION_SEED)
    null = list(y)
    exceed = 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(null)
        rho = spearman(x, null)
        if rho is not None and rho >= observed - 1e-12:
            exceed += 1
    return (exceed + 1) / (PERMUTATIONS + 1)


def bootstrap_spearman_ci(x: list[float], y: list[float]) -> list[float] | None:
    rng = random.Random(BOOTSTRAP_SEED)
    values: list[float] = []
    n = len(x)
    for _ in range(BOOTSTRAP_REPS):
        indices = [rng.randrange(n) for _ in range(n)]
        rho = spearman([x[i] for i in indices], [y[i] for i in indices])
        if rho is not None:
            values.append(rho)
    if len(values) < BOOTSTRAP_REPS * .90:
        return None
    values.sort()
    return [values[int(.025*len(values))], values[min(len(values)-1, int(.975*len(values)))]]


def validate_neural_outcomes(receipt: dict[str, Any],
                             outcomes: dict[str, Any]) -> list[dict[str, Any]]:
    check_frozen(receipt)
    if type(outcomes) is not dict or outcomes.get("schema_version") != 1:
        raise PredictionRejected("invalid neural outcome document")
    if outcomes.get("experiment") != "phase2t_fresh_12_neural_only":
        raise PredictionRejected("unexpected neural outcome experiment")
    if (outcomes.get("prediction_receipt_sha256") != receipt["receipt_sha256"]
            or outcomes.get("panel_sha256") != receipt["source_panel_sha256"]):
        raise PredictionRejected("neural outcomes unbound to frozen prediction")
    if outcomes.get("protocol") != "phase2t-4round-byte-tanh-v1":
        raise PredictionRejected("neural runner protocol changed")
    runs = outcomes.get("runs")
    if (not isinstance(runs, list)
            or len(runs) != EXPECTED_TOTAL_NEURAL_TRAININGS):
        raise PredictionRejected("incomplete neural run count")
    expected_ids = {r["fingerprint"] for r in receipt["predictions"]}
    expected_pairs = {(delta, rep)
                      for delta in DIFFERENCES for rep in range(len(DATASET_SEEDS))}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str,int,int]] = set()
    for row in runs:
        if type(row) is not dict:
            raise PredictionRejected("invalid outcome run")
        fingerprint = row.get("fingerprint")
        delta = row.get("difference")
        replicate = row.get("replicate")
        if (fingerprint not in expected_ids
                or type(delta) is not int or delta not in DIFFERENCES
                or type(replicate) is not int
                or not 0 <= replicate < len(DATASET_SEEDS)):
            raise PredictionRejected("neural row not in frozen design")
        key = (fingerprint, delta, replicate)
        if key in seen:
            raise PredictionRejected("duplicate candidate/difference/replicate")
        seen.add(key)
        if (row.get("dataset_seed") != DATASET_SEEDS[replicate]
                or row.get("model_seed") != MODEL_SEEDS[replicate]):
            raise PredictionRejected("seed or replicate mismatch")
        for field in ("test_auc", "null_auc"):
            value = row.get(field)
            if type(value) not in (int,float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise PredictionRejected("invalid AUC")
        if (not _hex_digest(row.get("dataset_fingerprint_sha256"))
                or not _hex_digest(row.get("model_init_fingerprint_sha256"))
                or not _hex_digest(row.get("runner_commit_sha256"))):
            raise PredictionRejected("missing independently verifiable provenance")
        groups[fingerprint].append(row)
    if set(groups) != expected_ids:
        raise PredictionRejected("missing candidate")
    result = []
    for item in receipt["predictions"]:
        fp = item["fingerprint"]
        if {(row["difference"],row["replicate"]) for row in groups[fp]} != expected_pairs:
            raise PredictionRejected("incomplete paired replicates")
        advantage = statistics.fmean(2*abs(row["test_auc"]-.5) for row in groups[fp])
        shuffled = statistics.fmean(2*abs(row["null_auc"]-.5) for row in groups[fp])
        result.append({"fingerprint":fp, "classical_feature_score":item["classical_feature_score"],
                       "mean_neural_advantage":advantage, "mean_neural_null_advantage":shuffled,
                       "mean_signal_minus_null":advantage-shuffled,
                       "neural_replicates":len(groups[fp])})
    return result


def evaluate(receipt: dict[str, Any], outcomes: dict[str, Any]) -> dict[str, Any]:
    rows = validate_neural_outcomes(receipt, outcomes)
    x = [r["classical_feature_score"] for r in rows]
    y = [r["mean_neural_advantage"] for r in rows]
    rho = spearman(x, y)
    p = None if rho is None else one_sided_permutation_p(x,y,rho)
    ci = bootstrap_spearman_ci(x,y)
    mean_margin = statistics.fmean(r["mean_signal_minus_null"] for r in rows)
    preregistered_gate = (
        rho is not None and rho >= SPEARMAN_MINIMUM
        and p is not None and p < PERMUTATION_P_THRESHOLD
        and mean_margin >= MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL
    )
    output = {
        "schema_version":1,"experiment":"phase2t_sealed_prediction_evaluation",
        "prediction_receipt_sha256":receipt["receipt_sha256"],
        "neural_outcome_sha256":digest(outcomes),
        "candidate_count":TARGET_CANDIDATES,
        "completed_training_count":EXPECTED_TOTAL_NEURAL_TRAININGS,
        "predefined_primary_metric":"spearman_one_sided_rho",
        "spearman_rho":rho,
        "one_sided_permutation_p":p,
        "permutation_repetitions":PERMUTATIONS,
        "bootstrap_95pct_exploratory_ci":ci,
        "mean_neural_minus_shuffled_null":mean_margin,
        "preregistered_thresholds":{
            "spearman_minimum":SPEARMAN_MINIMUM,
            "one_sided_permutation_p_max":PERMUTATION_P_THRESHOLD,
            "mean_null_margin_min":MIN_MEAN_SIGNAL_OVER_SHUFFLED_NULL,
        },
        "preregistered_gate_pass":bool(preregistered_gate),
        "scientific_verdict":(
            "SUPPORTED_WITHIN_PINNED_TOY_CIPHER_PANEL"
            if preregistered_gate else "NOT_SUPPORTED_OR_INCONCLUSIVE"
        ),
        "individual_candidate_rows":rows,
        "inference_limit":(
            "A gate pass is NOT evidence of novel cryptography, general cipher "
            "security, independent source provenance, or neural causality."
        ),
    }
    output["receipt_sha256"] = digest(output)
    return output


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predictions",type=Path,required=True)
    p.add_argument("--neural-outcomes",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args = p.parse_args()
    paths = {args.predictions.resolve(),args.neural_outcomes.resolve(),args.output.resolve()}
    if len(paths) != 3:
        raise SystemExit("input and output paths must differ")
    predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    outcomes = json.loads(args.neural_outcomes.read_text(encoding="utf-8"))
    result = evaluate(predictions,outcomes)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)
        f.write("\n")
    print(result["scientific_verdict"],result["receipt_sha256"])


if __name__ == "__main__":
    main()
