"""Pre-registered Phase2V-T7: differential input-byte activity in ToySPN.

Research-only classical control study, no model fits or cipher-security claim.
The signed preregistration was committed before these outcomes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import statistics
from collections import Counter
from pathlib import Path
from adversarial_sbox.spn import ToySPN

SEEDS = tuple(903011 + 37 * i for i in range(12))
DIFFERENCES = (0x00000001, 0x00000100, 0x00010100, 0x01010101)
ROUNDS = (4, 5)
N_CLASS = 128

def sha256_int(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("ascii")).digest(), "big")

def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")

def make_sbox(group: int, index: int) -> tuple[int, ...]:
    box = list(range(256))
    random.Random(sha256_int(f"phase2v-t7-sbox-v1|{group}|{index}")).shuffle(box)
    assert len(set(box)) == 256
    return tuple(box)

def make_keys(group: int, fingerprint: str) -> tuple[int, ...]:
    return tuple(
        int.from_bytes(hashlib.sha256(f"phase2v-t7-key-v1|{group}|{fingerprint}|{i}".encode("ascii")).digest()[:4], "big")
        for i in range(6)
    )

def sample_pairs(group: int, fingerprint: str, delta: int) -> list[tuple[int, int, int]]:
    rng = random.Random(sha256_int(f"phase2v-t7-pairs-v1|{group}|{fingerprint}|{delta}"))
    seen: set[int] = set()
    pairs: list[tuple[int, int, int]] = []
    draws = 0
    for label in (1, 0):
        accepted = 0
        while accepted < N_CLASS:
            draws += 1
            if draws > 50000:
                raise AssertionError("candidate draw cap breached")
            left = rng.getrandbits(32)
            right = (left ^ delta) if label else rng.getrandbits(32)
            if left == right or (not label and right == (left ^ delta)):
                continue
            if left in seen or right in seen:
                continue
            seen.add(left)
            seen.add(right)
            pairs.append((left, right, label))
            accepted += 1
    validate_pairs(pairs, delta)
    return pairs

def validate_pairs(pairs: list[tuple[int, int, int]], delta: int) -> None:
    if len(pairs) != 2 * N_CLASS or sum(label for _, _, label in pairs) != N_CLASS:
        raise ValueError("invalid pair count or class balance")
    blocks: set[int] = set()
    for left, right, label in pairs:
        if label not in (0, 1) or not (0 <= left <= 0xffffffff and 0 <= right <= 0xffffffff):
            raise ValueError("invalid pair entry")
        if left == right or (label == 1 and (left ^ right) != delta) or (label == 0 and (left ^ right) == delta):
            raise ValueError("invalid labeled difference")
        if left in blocks or right in blocks:
            raise ValueError("plaintext reuse")
        blocks.add(left)
        blocks.add(right)

def zero_bytes(left: int, right: int) -> int:
    difference = left ^ right
    return sum(((difference >> shift) & 0xff) == 0 for shift in (0, 8, 16, 24))

def tie_auc(scores: list[int], labels: list[int]) -> float:
    assert len(scores) == len(labels) == N_CLASS * 2
    pos = Counter(s for s, l in zip(scores, labels) if l == 1)
    neg = Counter(s for s, l in zip(scores, labels) if l == 0)
    assert sum(pos.values()) == sum(neg.values()) == N_CLASS
    numerator_twice = sum(pos[s] * neg[t] * (2 if s > t else 1 if s == t else 0) for s in range(5) for t in range(5))
    return numerator_twice / (2 * N_CLASS * N_CLASS)

def independent_auc(scores: list[int], labels: list[int]) -> float:
    pos = [v for v, label in zip(scores, labels) if label]
    neg = [v for v, label in zip(scores, labels) if not label]
    return sum((1 if a > b else 0.5 if a == b else 0) for a in pos for b in neg) / (len(pos) * len(neg))

def independent_encrypt(block: int, box: tuple[int, ...], keys: tuple[int, ...]) -> int:
    state = block
    for i, roundkey in enumerate(keys[:-1]):
        mixed = state ^ roundkey
        b = [(mixed >> shift) & 255 for shift in (24, 16, 8, 0)]
        state = int.from_bytes(bytes(box[x] for x in b), "big")
        if i + 2 < len(keys):
            state = ((state << 11) & 0xffffffff) | (state >> 21)
    return state ^ keys[-1]

def verify_core() -> None:
    box = make_sbox(SEEDS[0], 0)
    keys = make_keys(SEEDS[0], hashlib.sha256(bytes(box)).hexdigest())
    for rounds in ROUNDS:
        cipher = ToySPN(box, keys[:rounds + 1])
        for pt in (0, 1, 0x12345678, 0xffffffff):
            expected = independent_encrypt(pt, box, keys[:rounds + 1])
            assert cipher.encrypt_block(pt) == expected
            assert cipher.decrypt_block(expected) == pt
    assert tie_auc([0] * N_CLASS + [0] * N_CLASS, [1] * N_CLASS + [0] * N_CLASS) == 0.5
    assert tie_auc([4] * N_CLASS + [0] * N_CLASS, [1] * N_CLASS + [0] * N_CLASS) == 1.0
    assert tie_auc([0] * N_CLASS + [4] * N_CLASS, [1] * N_CLASS + [0] * N_CLASS) == 0.0
    pairs = sample_pairs(SEEDS[0], hashlib.sha256(bytes(box)).hexdigest(), DIFFERENCES[0])
    pairs[0] = pairs[1]
    try:
        validate_pairs(pairs, DIFFERENCES[0])
    except ValueError:
        pass
    else:
        raise AssertionError("plaintext tamper negative control failed")

def run() -> dict:
    verify_core()
    panels: list[dict] = []
    fingerprints: set[str] = set()
    key_fingerprints: set[str] = set()
    schedules: set[str] = set()
    groups: dict[int, dict] = {}
    spotchecks = 0
    for group in SEEDS:
        groups[group] = {str(rounds): {} for rounds in ROUNDS}
        for box_index in range(8):
            box = make_sbox(group, box_index)
            fp = hashlib.sha256(bytes(box)).hexdigest()
            if fp in fingerprints:
                raise AssertionError("duplicate box")
            fingerprints.add(fp)
            keys = make_keys(group, fp)
            key_id = hashlib.sha256(b"".join(k.to_bytes(4, "big") for k in keys)).hexdigest()
            if key_id in key_fingerprints:
                raise AssertionError("duplicate key schedule")
            key_fingerprints.add(key_id)
            ciphers = {rounds: ToySPN(box, keys[:rounds + 1]) for rounds in ROUNDS}
            for delta in DIFFERENCES:
                pairs = sample_pairs(group, fp, delta)
                sample_id = hashlib.sha256(canonical_json(pairs)).hexdigest()
                if sample_id in schedules:
                    raise AssertionError("duplicate sample schedule")
                schedules.add(sample_id)
                labels = [label for _, _, label in pairs]
                for rounds in ROUNDS:
                    cipher = ciphers[rounds]
                    scores = [zero_bytes(cipher.encrypt_block(a), cipher.encrypt_block(b)) for a, b, _ in pairs]
                    auc = tie_auc(scores, labels)
                    null_labels = labels[:]
                    random.Random(sha256_int(f"phase2v-t7-null-v1|{group}|{fp}|{delta}|{rounds}")).shuffle(null_labels)
                    null_auc = tie_auc(scores, null_labels)
                    if box_index in (0, 7) and delta in (DIFFERENCES[0], DIFFERENCES[-1]):
                        assert auc == independent_auc(scores, labels)
                        assert null_auc == independent_auc(scores, null_labels)
                        spotchecks += 2
                    pos_nonzero = sum(score > 0 for score, label in zip(scores, labels) if label) / N_CLASS
                    neg_nonzero = sum(score > 0 for score, label in zip(scores, labels) if not label) / N_CLASS
                    row = dict(group=group, sbox_index=box_index, sbox_sha256=fp, key_sha256=key_id,
                               pair_sha256=sample_id, delta=delta, rounds=rounds, auc=auc,
                               null_auc=null_auc, positive_any_zero_byte=pos_nonzero,
                               negative_any_zero_byte=neg_nonzero)
                    panels.append(row)
                    groups[group][str(rounds)].setdefault(str(delta), []).append(auc)
    if (len(fingerprints), len(key_fingerprints), len(schedules), len(panels), spotchecks) != (96, 96, 384, 768, 192):
        raise AssertionError("panel/source cardinality mismatch")
    group_rows = []
    for group in SEEDS:
        row = {"group": group}
        for rounds in ROUNDS:
            for delta in DIFFERENCES:
                row[f"auc_r{rounds}_delta_{delta}"] = statistics.mean(groups[group][str(rounds)][str(delta)])
            row[f"contrast_r{rounds}"] = ((row[f"auc_r{rounds}_delta_{DIFFERENCES[0]}"] + row[f"auc_r{rounds}_delta_{DIFFERENCES[1]}"]) / 2 - row[f"auc_r{rounds}_delta_{DIFFERENCES[-1]}"])
        group_rows.append(row)
    contrasts = [r["contrast_r4"] for r in group_rows]
    positive = sum(value > 0 for value in contrasts)
    median = statistics.median(contrasts)
    mean_null = statistics.mean(p["null_auc"] for p in panels)
    null_gate = 0.47 <= mean_null <= 0.53
    primary_supported = positive >= 10 and median >= 0.05 and null_gate
    metrics = dict(
        primary_contrasts_positive=positive,
        primary_contrast_median=median,
        mean_shuffled_label_null_auc=mean_null,
        null_quality_gate_pass=null_gate,
        primary_hypothesis_supported=primary_supported,
        secondary_r5_contrast_median=statistics.median(r["contrast_r5"] for r in group_rows),
        mean_auc_by_round_delta={f"r{r}_d{d}": statistics.mean(row[f"auc_r{r}_delta_{d}"] for row in group_rows) for r in ROUNDS for d in DIFFERENCES},
        panels=768, box_fingerprints=96, key_schedules=96, pair_schedules=384,
        independent_auc_spotchecks=spotchecks,
    )
    return {"study": "phase2v-t7-input-activity-v1", "source_main_sha": "b03da1d95e98709869d007571de4f8bbce234a1b",
            "seeds": SEEDS, "deltas": DIFFERENCES, "metrics": metrics, "groups": group_rows, "panels": panels}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="t7_audit.json")
    args = parser.parse_args()
    result = run()
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(result)
    target.write_bytes(payload)
    print(json.dumps({"audit_json": str(target), "sha256": hashlib.sha256(payload).hexdigest(), "metrics": result["metrics"]}, sort_keys=True))

if __name__ == "__main__":
    main()
