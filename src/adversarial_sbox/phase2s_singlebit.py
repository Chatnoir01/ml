"""Phase 2S: training-free one-bit differential distinguisher, toy cipher only.

A cheap, classical single-bit XOR baseline to challenge the interpretation of
the previously observed 4-round neural heterogeneity. This is exploratory,
post-hoc work following inspection of the frozen Phase 2A-T outcomes.
No learned model, key recovery, cipher recommendation or security claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
import statistics
from typing import Sequence

from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
from .phase2at import PANEL_DIGEST_SHA256 as PHASE2AT_PANEL
from .neural_heterogeneity import ROUND_KEYS
from .spn import MASK32, ToySPN

DIFFERENCES = (0x00000001, 0x00000100)
DEPTHS = (3, 4, 5)
SCHEDULES = ("historical", "xor_perturbed", "rotated_perturbed")
# Frozen diagnostic seeds: publicly known, NOT CSPRNG and NOT new neural seeds.
TRAIN_PAIR_SEED = 0x52010471
TEST_PAIR_SEED = 0x520104A5
LABEL_SHUFFLE_SEED = 0x520104E9
DEFAULT_TRAIN_PER_LABEL = 2048
DEFAULT_TEST_PER_LABEL = 4096


@dataclass(frozen=True)
class BitDecision:
    position: int
    sign: int
    train_gap: float


def schedule(name: str) -> tuple[int, ...]:
    if name == "historical":
        return tuple(ROUND_KEYS)
    if name == "xor_perturbed":
        return tuple((v ^ ((0x01020408 + i * 0x01010101) & MASK32))
                     & MASK32 for i, v in enumerate(ROUND_KEYS))
    if name == "rotated_perturbed":
        def rot(v: int, n: int) -> int:
            return ((v << n) | (v >> (32 - n))) & MASK32
        return tuple(rot(v ^ 0x9E3779B9, 3 + i)
                     for i, v in enumerate(ROUND_KEYS))
    raise ValueError("unregistered diagnostic key schedule")


def plaintext_pairs(
    *, difference: int, per_label: int, seed: int,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Matched independent train/test plaintext sources with block-disjointness.

    The same generated pairs are reused for every S-Box, depth and key schedule
    in a condition. This prevents differential input-selection confounding.
    """
    if type(difference) is not int or difference not in DIFFERENCES:
        raise ValueError("unregistered input difference")
    if type(per_label) is not int or not 1 <= per_label <= 50000:
        raise ValueError("per-label count out of bounds")
    if type(seed) is not int or not 0 <= seed < (1 << 64):
        raise ValueError("invalid non-cryptographic random seed")
    rnd = random.Random(seed ^ difference)
    used: set[int] = set()
    positive: list[tuple[int, int]] = []
    negative: list[tuple[int, int]] = []
    while len(positive) < per_label:
        x = rnd.getrandbits(32)
        y = x ^ difference
        if x in used or y in used:
            continue
        used.update((x, y))
        positive.append((x, y))
    while len(negative) < per_label:
        x = rnd.getrandbits(32)
        y = rnd.getrandbits(32)
        if x == y or x ^ y == difference or x in used or y in used:
            continue
        used.update((x, y))
        negative.append((x, y))
    return tuple(positive), tuple(negative)


def ciphertext_differences(
    cipher: ToySPN, plaintext_pair_source: Sequence[tuple[int, int]],
) -> tuple[int, ...]:
    """Only an exploratory chosen-plaintext XOR-difference diagnostic."""
    return tuple(cipher.encrypt_block(p0) ^ cipher.encrypt_block(p1)
                 for p0, p1 in plaintext_pair_source)


def bit_frequencies(values: Sequence[int]) -> tuple[float, ...]:
    if not values:
        raise ValueError("at least one observation required")
    if any(type(v) is not int or not 0 <= v <= MASK32 for v in values):
        raise ValueError("expected unsigned 32-bit differences")
    n = len(values)
    return tuple(sum((v >> bit) & 1 for v in values) / n
                 for bit in range(32))


def learn_one_bit(
    positive: Sequence[int], negative: Sequence[int],
) -> BitDecision:
    """Select one ciphertext-XOR bit using TRAIN data only (fixed tie rule)."""
    pos = bit_frequencies(positive)
    neg = bit_frequencies(negative)
    diffs = [a - b for a, b in zip(pos, neg)]
    bit = max(range(32), key=lambda k: abs(diffs[k]))
    return BitDecision(bit, 1 if diffs[bit] >= 0 else -1, diffs[bit])


def signed_test_advantage(
    choice: BitDecision, positive: Sequence[int], negative: Sequence[int],
) -> float:
    """Two-sided AUC advantage with direction fixed on train only.

    For a binary feature: 2*(AUC-0.5) = p_pos(feature=1)-p_neg(feature=1).
    Signed (not absolute) test result protects against sign-flip optimism.
    """
    if not 0 <= choice.position < 32 or choice.sign not in (-1, 1):
        raise ValueError("invalid bit decision")
    return choice.sign * (
        bit_frequencies(positive)[choice.position]
        - bit_frequencies(negative)[choice.position]
    )


def _control_shuffled_test(
    choice: BitDecision, positive: Sequence[int], negative: Sequence[int],
    *, seed: int,
) -> float:
    pooled = list(positive) + list(negative)
    if len(positive) != len(negative):
        raise ValueError("class balance required")
    random.Random(seed).shuffle(pooled)
    n = len(positive)
    return signed_test_advantage(choice, pooled[:n], pooled[n:])


def run_cell(
    *, candidate_index: int, depth: int, difference: int, key_schedule: str,
    train_per_label: int, test_per_label: int,
) -> dict:
    if not (type(candidate_index) is int and 0 <= candidate_index < len(CANDIDATES)):
        raise ValueError("invalid candidate index")
    if depth not in DEPTHS or difference not in DIFFERENCES:
        raise ValueError("unregistered diagnostic cell")
    round_keys = schedule(key_schedule)[:depth + 1]
    cipher = ToySPN(CANDIDATES[candidate_index]["sbox"], round_keys)
    # The training and test random streams have different pinned seeds, and
    # both sides are independent of S-Box identity and key-schedule label.
    tp, tn = plaintext_pairs(difference=difference, per_label=train_per_label,
                             seed=TRAIN_PAIR_SEED)
    hp, hn = plaintext_pairs(difference=difference, per_label=test_per_label,
                             seed=TEST_PAIR_SEED)
    trp, trn = ciphertext_differences(cipher, tp), ciphertext_differences(cipher, tn)
    tsp, tsn = ciphertext_differences(cipher, hp), ciphertext_differences(cipher, hn)
    choice = learn_one_bit(trp, trn)
    return {
        "candidate_index": candidate_index,
        "fingerprint": CANDIDATES[candidate_index]["fingerprint"],
        "depth": depth,
        "difference": difference,
        "key_schedule": key_schedule,
        "selected_bit": choice.position,
        "train_signed_gap": choice.sign * choice.train_gap,
        "test_signed_advantage": signed_test_advantage(choice, tsp, tsn),
        "test_label_shuffle_control": _control_shuffled_test(
            choice, tsp, tsn,
            seed=LABEL_SHUFFLE_SEED ^ depth ^ difference ^ candidate_index,
        ),
    }


def run_experiment(
    *, train_per_label: int = DEFAULT_TRAIN_PER_LABEL,
    test_per_label: int = DEFAULT_TEST_PER_LABEL,
) -> dict:
    if PANEL_DIGEST_SHA256 != PHASE2AT_PANEL or len(CANDIDATES) != 6:
        raise RuntimeError("historical panel drift")
    for item in CANDIDATES:
        if tuple(item[k] for k in (
            "differential_uniformity", "nonlinearity",
            "max_linear_correlation", "algebraic_degree",
        )) != (8, 100, 56, 7):
            raise RuntimeError("frozen classical-metric panel changed")

    results = [
        run_cell(
            candidate_index=i, depth=d, difference=diff,
            key_schedule=scheme, train_per_label=train_per_label,
            test_per_label=test_per_label,
        )
        for scheme in SCHEDULES for d in DEPTHS for diff in DIFFERENCES
        for i in range(len(CANDIDATES))
    ]
    summary: list[dict] = []
    for scheme in SCHEDULES:
        for d in DEPTHS:
            for diff in DIFFERENCES:
                rows = [
                    row for row in results
                    if (row["key_schedule"], row["depth"], row["difference"])
                    == (scheme, d, diff)
                ]
                values = [row["test_signed_advantage"] for row in rows]
                controls = [row["test_label_shuffle_control"] for row in rows]
                summary.append({
                    "key_schedule": scheme, "depth": d, "difference": diff,
                    "mean_signed_test_advantage": statistics.fmean(values),
                    "candidate_signed_advantage_range": max(values) - min(values),
                    "mean_abs_label_shuffle_control":
                        statistics.fmean(abs(x) for x in controls),
                })
    result = {
        "schema_version": 1,
        "experiment": "phase2s_posthoc_single_bit_baseline",
        "frozen_panel_sha256": PANEL_DIGEST_SHA256,
        "trained_neural_networks": 0,
        "new_neural_seed_count": 0,
        "candidate_count": len(CANDIDATES),
        "cells": len(results),
        "train_per_label": train_per_label,
        "test_per_label": test_per_label,
        "schedules": list(SCHEDULES),
        "depths": list(DEPTHS),
        "differences": list(DIFFERENCES),
        "results": results,
        "summary": summary,
        "interpretation": "POSTHOC_TOYSPN_NO_CLAIM_OF_CAUSALITY_OR_CIPHER_SECURITY",
    }
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    result["receipt_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    kwargs = {"train_per_label": 64, "test_per_label": 128} if args.smoke else {}
    print(json.dumps(run_experiment(**kwargs), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
