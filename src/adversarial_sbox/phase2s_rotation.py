"""Phase 2S-C: controlled ToySPN rotation ablation (post-hoc, no neural work).

Changes only the intra-round 32-bit rotation amount relative to the
historical ToySPN. The original cipher module and previous scientific
result files are UNCHANGED. This is toy diffusion analysis, not a
proposed real cipher or a cryptographic security assessment.
"""
from __future__ import annotations

import hashlib
import json
from statistics import fmean

from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
from .phase2at import PANEL_DIGEST_SHA256 as FROZEN_PANEL
from .phase2s_singlebit import (
    DEPTHS, DIFFERENCES, LABEL_SHUFFLE_SEED, DEFAULT_TEST_PER_LABEL,
    DEFAULT_TRAIN_PER_LABEL, _control_shuffled_test,
    ciphertext_differences, learn_one_bit, matched_pairs, signed_test_advantage,
)
from .neural_heterogeneity import ROUND_KEYS
from .spn import MASK32, ToySPN

ROTATIONS = (7, 11, 13)
EXPECTED_ROUNDS = (3, 4, 5)


def rotl32(x: int, bits: int) -> int:
    return ((x << bits) | (x >> (32 - bits))) & MASK32


def rotr32(x: int, bits: int) -> int:
    return ((x >> bits) | (x << (32 - bits))) & MASK32


class RotatedToySPN:
    """Independent experimental round-permutation parameterization.

    Reuses the *same* byte S-Box and keys, but not ToySPN.encrypt_block.
    Rotation=11 MUST match the historical implementation byte-for-byte.
    """

    def __init__(self, sbox, keys, rotation: int):
        if type(rotation) is not int or rotation not in ROTATIONS:
            raise ValueError("unsupported fixed rotation ablation")
        base = ToySPN(sbox, keys)  # exact existing S-Box/keys validation
        self.sbox = base.sbox
        self.inverse_sbox = base.inverse_sbox
        self.round_keys = base.round_keys
        self.rounds = base.rounds
        self.rotation = rotation

    def encrypt_block(self, plaintext: int) -> int:
        if type(plaintext) is not int or not 0 <= plaintext <= MASK32:
            raise ValueError("plaintext must be a 32-bit integer")
        value = plaintext
        for r in range(self.rounds):
            value ^= self.round_keys[r]
            value = ToySPN._substitute(value, self.sbox)
            if r != self.rounds - 1:
                value = rotl32(value, self.rotation)
        return (value ^ self.round_keys[-1]) & MASK32

    def decrypt_block(self, ciphertext: int) -> int:
        if type(ciphertext) is not int or not 0 <= ciphertext <= MASK32:
            raise ValueError("ciphertext must be a 32-bit integer")
        value = ciphertext ^ self.round_keys[-1]
        for r in range(self.rounds - 1, -1, -1):
            if r != self.rounds - 1:
                value = rotr32(value, self.rotation)
            value = ToySPN._substitute(value, self.inverse_sbox)
            value ^= self.round_keys[r]
        return value & MASK32


def active_bytes(value: int) -> int:
    if type(value) is not int or not 0 <= value <= MASK32:
        raise ValueError("32-bit difference required")
    return sum(((value >> shift) & 0xFF) != 0 for shift in (0, 8, 16, 24))


def run_cell(
    *, candidate_index: int, rounds: int, difference: int, rotation: int,
    train_per_label: int, test_per_label: int,
) -> dict:
    if type(candidate_index) is not int or not 0 <= candidate_index < len(CANDIDATES):
        raise ValueError("invalid candidate index")
    if type(rounds) is not int or rounds not in DEPTHS or difference not in DIFFERENCES:
        raise ValueError("unregistered rotation cell")
    cipher = RotatedToySPN(CANDIDATES[candidate_index]["sbox"],
                           ROUND_KEYS[:rounds+1], rotation)
    tp, tn, hp, hn = matched_pairs(difference, train_per_label, test_per_label)
    trp, trn = ciphertext_differences(cipher, tp), ciphertext_differences(cipher, tn)
    tsp, tsn = ciphertext_differences(cipher, hp), ciphertext_differences(cipher, hn)
    choice = learn_one_bit(trp, trn)
    return {
        "candidate_index": candidate_index,
        "fingerprint": CANDIDATES[candidate_index]["fingerprint"],
        "rounds": rounds, "difference": difference, "rotation": rotation,
        "best_train_bit": choice.position,
        "signed_holdout_advantage": signed_test_advantage(choice, tsp, tsn),
        "shuffled_label_control": _control_shuffled_test(
            choice, tsp, tsn,
            seed=LABEL_SHUFFLE_SEED ^ difference ^ rounds ^ rotation ^ candidate_index,
        ),
        "mean_positive_active_bytes": fmean(active_bytes(v) for v in tsp),
        "mean_negative_active_bytes": fmean(active_bytes(v) for v in tsn),
    }


def run_experiment(*, train_per_label: int = DEFAULT_TRAIN_PER_LABEL,
                   test_per_label: int = DEFAULT_TEST_PER_LABEL) -> dict:
    if PANEL_DIGEST_SHA256 != FROZEN_PANEL or len(CANDIDATES) != 6:
        raise RuntimeError("historical panel drift")
    data = [
        run_cell(candidate_index=i, rounds=r, difference=d, rotation=rot,
                 train_per_label=train_per_label, test_per_label=test_per_label)
        for rot in ROTATIONS for r in DEPTHS for d in DIFFERENCES
        for i in range(len(CANDIDATES))
    ]
    summary = []
    for rot in ROTATIONS:
        for r in DEPTHS:
            for d in DIFFERENCES:
                rows = [x for x in data if (x["rotation"],x["rounds"],x["difference"])
                        == (rot,r,d)]
                values = [x["signed_holdout_advantage"] for x in rows]
                summary.append({
                    "rotation": rot, "rounds": r, "difference": d,
                    "mean_signed_advantage": fmean(values),
                    "candidate_advantage_range": max(values) - min(values),
                    "mean_positive_active_bytes":
                        fmean(x["mean_positive_active_bytes"] for x in rows),
                    "mean_negative_active_bytes":
                        fmean(x["mean_negative_active_bytes"] for x in rows),
                    "selected_bit_positions": [x["best_train_bit"] for x in rows],
                })
    output = {
        "schema_version": 1, "experiment": "phase2s_posthoc_rotation_ablation",
        "toy_cipher_only": True, "new_neural_trainings": 0,
        "panel_sha256": PANEL_DIGEST_SHA256,
        "rotations": list(ROTATIONS), "depths": list(DEPTHS),
        "differences": list(DIFFERENCES), "candidate_count": len(CANDIDATES),
        "train_per_label": train_per_label, "test_per_label": test_per_label,
        "cell_count": len(data), "cells": data, "summary": summary,
        "inference": "EXPLORATORY_POSTHOC_GEOMETRY_NOT_NEURAL_CAUSALITY",
    }
    payload = json.dumps(output,sort_keys=True,separators=(",",":"),allow_nan=False)
    output["receipt_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return output


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--smoke",action="store_true")
    args = p.parse_args()
    kwargs = {"train_per_label":64,"test_per_label":128} if args.smoke else {}
    print(json.dumps(run_experiment(**kwargs),sort_keys=True,indent=2))


if __name__ == "__main__":
    main()
