"""Phase 2T: freeze classical predictions BEFORE independent neural outcomes.

Research-only, 32-bit ToySPN. This uses ONE fixed posthoc hypothesis from
Phase 2S: one-bit differential holdout advantage at four rounds under the
historical public keys, averaged over two input differences.

IMPORTANT: a prediction receipt is not a cryptographic signature. The external
candidate-generation ledger must be audited/replayed independently. Running
this module does not train or read any new neural scores.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

from .evolution import evaluate_classical
from .phase2a_candidates import CANDIDATES as HISTORICAL
from .phase2at import PANEL_DIGEST_SHA256 as HISTORICAL_PANEL_DIGEST
from .phase2s_singlebit import (
    DIFFERENCES, matched_pairs, ciphertext_differences, learn_one_bit,
    signed_test_advantage,
)
from .neural_heterogeneity import ROUND_KEYS
from .provenance import fingerprint_sbox
from .spn import ToySPN

DESIGN = "phase2t_fresh_12_exact_metric_panel_v1"
GENERATING_ALGORITHM = "phase1o_multihotspot_new_independent_initial_population"
# Public, new, ordered, never used for Phase 1O / Phase 2A development.
PROSPECTIVE_SEEDS = (
    31001,31013,31019,31033,31039,31051,31063,31069,
    31079,31081,31091,31103,31121,31139,31153,31159,
    31171,31177,31181,31189,31201,31211,31219,31223,
)
TARGET_CANDIDATES = 12
EXPECTED_CLASSICAL = (100, 8, 56, 7)
TRAIN_PER_LABEL = 2048
TEST_PER_LABEL = 4096
DEPTH = 4
FEATURE_RULE = "mean_signed_onebit_holdout_advantage_depth4_delta1_delta256"
OLD_FINGERPRINTS = frozenset(c["fingerprint"] for c in HISTORICAL)


class PredictionRejected(ValueError):
    """An admission, sealing, or tampering gate failed."""


def canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(payload: dict[str, Any]) -> str:
    return sha256(canonical(payload)).hexdigest()


def _strict_hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


def _known_simple_copy(sbox: tuple[int, ...]) -> bool:
    """Reject historical clones shifted in input/output by XOR constants.

    This does not detect general affine-equivalent or other correlated families.
    Independent sourcing remains a scientific/provenance assumption.
    """
    for known in HISTORICAL:
        original = known["sbox"]
        for inp_xor in range(256):
            out_xor = sbox[0] ^ original[inp_xor]
            if all(sbox[x] == (original[x ^ inp_xor] ^ out_xor)
                   for x in range(256)):
                return True
    return False


def admit_panel(panel: dict[str, Any]) -> list[dict[str, Any]]:
    """Enforce a full seed-prefix attempt ledger; do NOT select on neural data.

    Externally supplied attempt ledgers are NOT cryptographic attestations of
    source independence or exact optimizer budgets: replay audit required.
    """
    if type(panel) is not dict or panel.get("design") != DESIGN:
        raise PredictionRejected("unregistered panel design")
    if panel.get("generator") != GENERATING_ALGORITHM:
        raise PredictionRejected("wrong candidate generation algorithm")
    attempts = panel.get("attempts")
    if not isinstance(attempts, list) or not 1 <= len(attempts) <= len(PROSPECTIVE_SEEDS):
        raise PredictionRejected("invalid seed attempt ledger")
    if len(HISTORICAL) != 6:
        raise PredictionRejected("historical panel drift")
    successes: list[dict[str, Any]] = []
    observed_fingerprints: set[str] = set()
    for i, entry in enumerate(attempts):
        if type(entry) is not dict or entry.get("seed") != PROSPECTIVE_SEEDS[i]:
            raise PredictionRejected("seed order, prefix or type mismatch")
        status = entry.get("status")
        if status == "ineligible":
            if "sbox" in entry or "fingerprint" in entry:
                raise PredictionRejected("ineligible attempts must not conceal candidates")
            if entry.get("reason") not in ("no_exact_metric_terminal", "budget_exhausted"):
                raise PredictionRejected("unregistered ineligibility reason")
            if type(entry.get("evaluations")) is not int or entry["evaluations"] != 340:
                raise PredictionRejected("missing fixed classical evaluation budget")
            continue
        if status != "accepted":
            raise PredictionRejected("unrecognized attempt status")
        if len(successes) >= TARGET_CANDIDATES:
            raise PredictionRejected("attempts continued after panel reached target")
        if type(entry.get("evaluations")) is not int or entry["evaluations"] != 340:
            raise PredictionRejected("accepted candidate lacks fixed evaluation budget")
        try:
            sbox = tuple(entry["sbox"])
        except (TypeError, KeyError) as exc:
            raise PredictionRejected("candidate missing S-Box") from exc
        if (len(sbox) != 256 or any(type(x) is not int or x < 0 or x > 255 for x in sbox)
                or len(set(sbox)) != 256):
            raise PredictionRejected("invalid 8x8 permutation")
        fingerprint = fingerprint_sbox(sbox)
        if fingerprint != entry.get("fingerprint") or not _strict_hex(fingerprint):
            raise PredictionRejected("fingerprint mismatch")
        if fingerprint in OLD_FINGERPRINTS or fingerprint in observed_fingerprints:
            raise PredictionRejected("duplicate or historical S-Box")
        if _known_simple_copy(sbox):
            raise PredictionRejected("simple XOR-affine clone of historical S-Box")
        measured = evaluate_classical(sbox)
        classical = (
            measured.nonlinearity, measured.differential_uniformity,
            measured.max_linear_correlation, measured.algebraic_degree,
        )
        if classical != EXPECTED_CLASSICAL:
            raise PredictionRejected(f"candidate not exact-metric matched: {classical}")
        if abs(float(measured.sac_score) - 0.5) > 0.05:
            raise PredictionRejected("SAC constraint failure")
        observed_fingerprints.add(fingerprint)
        successes.append({"seed":entry["seed"], "fingerprint":fingerprint,
                          "sbox":sbox, "classical_metrics":classical,
                          "sac_score":float(measured.sac_score)})
    if len(successes) != TARGET_CANDIDATES:
        raise PredictionRejected("panel incomplete; fail closed, do not replace seeds")
    if attempts[-1]["status"] != "accepted":
        raise PredictionRejected("ledger must stop on twelfth exact-metric match")
    return successes


def classical_signal(sbox: tuple[int, ...], difference: int) -> dict[str, Any]:
    if difference not in DIFFERENCES:
        raise PredictionRejected("unexpected input difference")
    cipher = ToySPN(sbox, ROUND_KEYS[:DEPTH + 1])
    tp, tn, hp, hn = matched_pairs(difference, TRAIN_PER_LABEL, TEST_PER_LABEL)
    chosen = learn_one_bit(ciphertext_differences(cipher, tp),
                           ciphertext_differences(cipher, tn))
    score = signed_test_advantage(chosen, ciphertext_differences(cipher, hp),
                                 ciphertext_differences(cipher, hn))
    if not math.isfinite(score) or not -1.0 <= score <= 1.0:
        raise PredictionRejected("invalid classical signal")
    return {"difference":difference, "bit":chosen.position,
            "signed_holdout_advantage":score}


def freeze(panel: dict[str, Any]) -> dict[str, Any]:
    candidates = admit_panel(panel)
    rows = []
    for item in candidates:
        features = [classical_signal(item["sbox"], d) for d in DIFFERENCES]
        rule_score = sum(x["signed_holdout_advantage"] for x in features) / len(features)
        rows.append({
            "seed":item["seed"], "fingerprint":item["fingerprint"],
            "classical_feature_score":rule_score,
            "feature_components":features,
        })
    ranked = sorted(rows, key=lambda x: (-x["classical_feature_score"],
                                        x["fingerprint"]))
    receipt = {
        "schema_version":1,
        "phase":"2T-prediction-frozen-before-neural",
        "design":DESIGN,
        "source_panel_sha256":digest(panel),
        "historical_panel_digest":HISTORICAL_PANEL_DIGEST,
        "feature_rule":FEATURE_RULE,
        "depth":DEPTH,
        "differences":list(DIFFERENCES),
        "train_per_label":TRAIN_PER_LABEL,
        "test_per_label":TEST_PER_LABEL,
        "candidate_count":TARGET_CANDIDATES,
        "new_neural_trainings":0,
        "neural_labels_available":False,
        "predictions":rows,
        "ranking_best_first":[r["fingerprint"] for r in ranked],
        "scientific_status":"PROSPECTIVE_PREDICTIONS_UNEVALUATED",
        "limitations":(
            "posthoc rule selected after inspecting prior six-SBox results",
            "new panel source provenance requires independent replay",
            "no prediction of real cipher security or key recovery",
        ),
    }
    receipt["receipt_sha256"] = digest(receipt)
    return receipt


def check_frozen(receipt: dict[str, Any]) -> None:
    if type(receipt) is not dict:
        raise PredictionRejected("invalid receipt")
    copied = dict(receipt)
    observed = copied.pop("receipt_sha256", None)
    if not _strict_hex(observed) or digest(copied) != observed:
        raise PredictionRejected("frozen receipt digest mismatch")
    if (copied.get("phase") != "2T-prediction-frozen-before-neural"
            or copied.get("scientific_status") != "PROSPECTIVE_PREDICTIONS_UNEVALUATED"
            or copied.get("design") != DESIGN
            or copied.get("feature_rule") != FEATURE_RULE
            or copied.get("candidate_count") != TARGET_CANDIDATES
            or copied.get("neural_labels_available") is not False
            or copied.get("new_neural_trainings") != 0):
        raise PredictionRejected("wrong predictive protocol")
    predicted = copied.get("predictions")
    if not isinstance(predicted, list) or len(predicted) != TARGET_CANDIDATES:
        raise PredictionRejected("prediction count mismatch")
    ids = [x.get("fingerprint") for x in predicted]
    if len(set(ids)) != TARGET_CANDIDATES or not all(_strict_hex(x) for x in ids):
        raise PredictionRejected("duplicate or invalid prediction identifiers")
    if any(type(x.get("classical_feature_score")) not in (int,float)
           or not math.isfinite(x["classical_feature_score"]) for x in predicted):
        raise PredictionRejected("invalid prediction scores")
    expected_order = sorted(predicted, key=lambda x: (-x["classical_feature_score"],
                                                     x["fingerprint"]))
    if copied.get("ranking_best_first") != [x["fingerprint"] for x in expected_order]:
        raise PredictionRejected("prediction ranking mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.panel.resolve() == args.output.resolve():
        raise SystemExit("input and output paths must differ")
    panel = json.loads(args.panel.read_text(encoding="utf-8"))
    receipt = freeze(panel)
    check_frozen(receipt)
    # Exclusive create: a second invocation never silently rewrites predictions.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(receipt["receipt_sha256"])


if __name__ == "__main__":
    main()
