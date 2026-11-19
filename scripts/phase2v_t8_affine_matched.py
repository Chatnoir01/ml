"""Phase 2V-T8: preregistered affine-equivalent S-box controlled ToySPN study.

Research-only. Registered before any T8 samples/outcomes at commit
d8c5e96eeaadd3411b02071707881b9f58d223ff.
No neural training, no Phase2U sealed labels, no production cryptography.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from adversarial_sbox.references import AES_SBOX
from adversarial_sbox.cryptoshield import (
    algebraic_degree, differential_uniformity, is_bijective,
    max_linear_correlation, nonlinearity, sac_score,
)
from adversarial_sbox.spn import ToySPN

GROUPS = tuple(904011 + 47 * k for k in range(12))
DIFFS = (1, 256)
ROUNDS = (4, 5)
ARMS = ("K0", "K1")
REPLICATES = (0, 1)
N_CLASS = 128
SOURCE_SHA = "b03da1d95e98709869d007571de4f8bbce234a1b"
PROTOCOL_SHA = "d8c5e96eeaadd3411b02071707881b9f58d223ff"


def hexsha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seeded(domain: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(domain.encode("ascii")).digest(), "big"))


def canonical(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def bit_permute(byte: int, positions: list[int]) -> int:
    return sum(((byte >> bit) & 1) << positions[bit] for bit in range(8))


def make_variant(group: int, index: int):
    rng = seeded(f"phase2v-t8-affine-v1|{group}|{index}")
    pin, pout = list(range(8)), list(range(8))
    rng.shuffle(pin)
    rng.shuffle(pout)
    offset_in, offset_out = rng.getrandbits(8), rng.getrandbits(8)
    box = tuple(bit_permute(AES_SBOX[bit_permute(x, pin) ^ offset_in], pout) ^ offset_out
                for x in range(256))
    assert is_bijective(box)
    return box, dict(pin=pin, pout=pout, input_xor=offset_in, output_xor=offset_out)


def key_words(group: int, arm: str) -> tuple[int, ...]:
    return tuple(int.from_bytes(hashlib.sha256(
        f"phase2v-t8-key-v1|{group}|{arm}|{i}".encode("ascii")
    ).digest()[:4], "big") for i in range(6))


def input_pairs(group: int, delta: int, replicate: int):
    rng = seeded(f"phase2v-t8-pairs-v1|{group}|{delta}|{replicate}")
    seen: set[int] = set()
    pairs: list[tuple[int, int, int]] = []
    attempts = 0
    for label in (1, 0):
        accepted = 0
        while accepted < N_CLASS:
            attempts += 1
            if attempts > 50000:
                raise RuntimeError("sampling budget reached")
            left = rng.getrandbits(32)
            right = left ^ delta if label else rng.getrandbits(32)
            if left == right or (label == 0 and (left ^ right) == delta):
                continue
            if left in seen or right in seen:
                continue
            seen.update((left, right))
            pairs.append((left, right, label))
            accepted += 1
    verify_input_pairs(pairs, delta)
    return pairs


def verify_input_pairs(pairs, delta):
    if len(pairs) != 256 or sum(label for _, _, label in pairs) != N_CLASS:
        raise ValueError("class/cardinality violation")
    seen = set()
    for left, right, label in pairs:
        if label not in (0, 1) or left == right or min(left, right) < 0 or max(left, right) > 0xffffffff:
            raise ValueError("bad pair")
        if (left ^ right == delta) != (label == 1):
            raise ValueError("incorrect pair class")
        if left in seen or right in seen:
            raise ValueError("plaintext block reused")
        seen.update((left, right))
    if len(seen) != 512:
        raise ValueError("wrong number of unique plaintext blocks")


def expected_early_active_bytes(box, delta):
    lane = 0 if delta == 1 else 1
    total = 0
    for x in range(256):
        d = (box[x] ^ box[x ^ 1]) << (8 * lane)
        rotated = ((d << 11) | (d >> 21)) & 0xffffffff
        total += sum(((rotated >> (8 * offset)) & 255) != 0 for offset in range(4))
    return total / 256


def independently_encrypt(box, keys, plaintext):
    state = plaintext
    for index, key in enumerate(keys[:-1]):
        state ^= key
        state = int.from_bytes(bytes(box[x] for x in state.to_bytes(4, "big")), "big")
        if index < len(keys) - 2:
            state = ((state << 11) | (state >> 21)) & 0xffffffff
    return state ^ keys[-1]


def zero_byte_count(cipher0, cipher1):
    d = cipher0 ^ cipher1
    return sum(((d >> offset) & 255) == 0 for offset in (0, 8, 16, 24))


def auc_discrete(scores, labels):
    if len(scores) != 256 or len(labels) != 256:
        raise ValueError("invalid score cardinality")
    pos = Counter(s for s, label in zip(scores, labels) if label == 1)
    neg = Counter(s for s, label in zip(scores, labels) if label == 0)
    if sum(pos.values()) != N_CLASS or sum(neg.values()) != N_CLASS:
        raise ValueError("unbalanced data")
    return sum(pos[s] * neg[t] * (2 if s > t else 1 if s == t else 0)
               for s in range(5) for t in range(5)) / (2 * N_CLASS * N_CLASS)


def auc_pair_enumeration(scores, labels):
    positive = [s for s, label in zip(scores, labels) if label == 1]
    negative = [s for s, label in zip(scores, labels) if label == 0]
    return sum(2 if x > y else 1 if x == y else 0
               for x in positive for y in negative) / (2 * N_CLASS * N_CLASS)


def ranks_mid(values):
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    rank = [0.0] * len(values)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        middle = (start + 1 + end) / 2
        for index in ordered[start:end]:
            rank[index] = middle
        start = end
    return rank


def spearman(a, b):
    if len(a) != len(b) or len(a) != 6:
        raise ValueError("expected exactly six matched candidates")
    x, y = ranks_mid(a), ranks_mid(b)
    mx, my = statistics.mean(x), statistics.mean(y)
    centered_x = [v - mx for v in x]
    centered_y = [v - my for v in y]
    numerator = sum(u * v for u, v in zip(centered_x, centered_y))
    denominator = math.sqrt(sum(u*u for u in centered_x) * sum(v*v for v in centered_y))
    return numerator / denominator if denominator else 0.0


def metric_vector(box):
    return dict(du=differential_uniformity(box),
                nl=nonlinearity(box),
                max_lat=max_linear_correlation(box),
                degree=algebraic_degree(box),
                sac=sac_score(box))


def check_ciphers():
    box, _ = make_variant(GROUPS[0], 0)
    keys = key_words(GROUPS[0], "K0")
    for r in ROUNDS:
        cipher = ToySPN(box, keys[:r + 1])
        for plaintext in (0, 1, 0x12345678, 0xffffffff):
            actual = cipher.encrypt_block(plaintext)
            if actual != independently_encrypt(box, keys[:r + 1], plaintext):
                raise AssertionError("reference cipher parity failed")
            if cipher.decrypt_block(actual) != plaintext:
                raise AssertionError("reference cipher roundtrip failed")
    labels = [1]*128 + [0]*128
    assert auc_discrete([0]*256, labels) == 0.5
    assert auc_discrete([4]*128+[0]*128, labels) == 1.0
    assert auc_discrete([0]*128+[4]*128, labels) == 0.0
    corrupted = input_pairs(GROUPS[0], DIFFS[0], 0)
    corrupted[0] = corrupted[1]
    try:
        verify_input_pairs(corrupted, DIFFS[0])
    except ValueError:
        pass
    else:
        raise AssertionError("corruption test failed")


def run():
    check_ciphers()
    base_metrics = metric_vector(AES_SBOX)
    boxes = []
    panels = []
    seen_boxes = set()
    seen_source_schedules = set()
    seen_key_schedules = set()
    scores_by_cell = defaultdict(list)
    early_feature = {}
    source_schedule_count = 0
    independent_auc_checks = 0

    for group in GROUPS:
        # Matched pair schedules for every box and key arm within a group.
        pair_source = {}
        for delta in DIFFS:
            a, b = input_pairs(group, delta, 0), input_pairs(group, delta, 1)
            if {p for left, right, _ in a for p in (left, right)} & {p for left, right, _ in b for p in (left, right)}:
                raise ValueError("replicate A/B share plaintext blocks")
            for rep, pairs in ((0, a), (1, b)):
                digest = hexsha(canonical(pairs))
                if digest in seen_source_schedules:
                    raise ValueError("duplicate pair source schedule")
                seen_source_schedules.add(digest)
                pair_source[(delta, rep)] = (pairs, digest)
                source_schedule_count += 1

        keys_by_arm = {}
        for arm in ARMS:
            keys = key_words(group, arm)
            digest = hexsha(b"".join(k.to_bytes(4, "big") for k in keys))
            if digest in seen_key_schedules:
                raise ValueError("duplicate key schedule")
            seen_key_schedules.add(digest)
            keys_by_arm[arm] = (keys, digest)

        for box_index in range(6):
            box, transform = make_variant(group, box_index)
            boxsha = hexsha(bytes(box))
            if boxsha in seen_boxes:
                raise ValueError("duplicate SBox")
            seen_boxes.add(boxsha)
            metrics = metric_vector(box)
            if metrics != base_metrics:
                raise ValueError("metric equivalence gate failed")
            descriptor = statistics.mean(expected_early_active_bytes(box, delta) for delta in DIFFS)
            early_feature[(group, box_index)] = descriptor
            boxes.append(dict(group=group, index=box_index, sha256=boxsha,
                              transform=transform, global_metrics=metrics,
                              early_active_bytes=descriptor))
            for arm in ARMS:
                keys, keysha = keys_by_arm[arm]
                cipher_by_round = {r: ToySPN(box, keys[:r + 1]) for r in ROUNDS}
                for delta in DIFFS:
                    for rep in REPLICATES:
                        pairs, pairs_sha = pair_source[(delta, rep)]
                        labels = [label for _, _, label in pairs]
                        for rounds in ROUNDS:
                            cipher = cipher_by_round[rounds]
                            scores = [zero_byte_count(cipher.encrypt_block(left),
                                                      cipher.encrypt_block(right))
                                      for left, right, _ in pairs]
                            auc = auc_discrete(scores, labels)
                            shuffled = labels[:]
                            seeded(f"phase2v-t8-null-v1|{group}|{boxsha}|{arm}|{delta}|{rep}|{rounds}").shuffle(shuffled)
                            null_auc = auc_discrete(scores, shuffled)
                            if box_index in (0, 5) and delta == 1 and rep == 0:
                                if auc != auc_pair_enumeration(scores, labels) or null_auc != auc_pair_enumeration(scores, shuffled):
                                    raise AssertionError("independent AUC mismatch")
                                independent_auc_checks += 2
                            row = dict(group=group, box_index=box_index, box_sha256=boxsha,
                                       key_arm=arm, key_sha256=keysha, delta=delta,
                                       replicate=rep, rounds=rounds, pairs_sha256=pairs_sha,
                                       auc=auc, null_auc=null_auc,
                                       positive_any_zero_byte=sum(score>0 for score, label in zip(scores,labels) if label==1)/128,
                                       negative_any_zero_byte=sum(score>0 for score, label in zip(scores,labels) if label==0)/128)
                            panels.append(row)
                            scores_by_cell[(group, box_index, arm, delta, rep, rounds)] = [auc]
    if (len(boxes), len(panels), len(seen_key_schedules), source_schedule_count, independent_auc_checks)!=(72, 1152, 24, 48, 96):
        raise AssertionError("source, panel or AUC control count mismatch")

    group_summaries = []
    for group in GROUPS:
        replicate_means = []
        key_means = {"K0": [], "K1": []}
        desc = []
        mean_auc = []
        for box_index in range(6):
            per_replicate = []
            for rep in REPLICATES:
                cells = [scores_by_cell[(group,box_index,arm,delta,rep,4)][0]
                         for arm in ARMS for delta in DIFFS]
                per_replicate.append(statistics.mean(cells))
            replicate_means.append(per_replicate)
            for arm in ARMS:
                key_means[arm].append(statistics.mean(
                    scores_by_cell[(group,box_index,arm,delta,rep,4)][0]
                    for delta in DIFFS for rep in REPLICATES))
            desc.append(early_feature[(group,box_index)])
            mean_auc.append(statistics.mean(per_replicate))
        rho_rep = spearman([x[0] for x in replicate_means],[x[1] for x in replicate_means])
        rho_key = spearman(key_means["K0"],key_means["K1"])
        rho_early = spearman(desc, mean_auc)
        r4 = statistics.mean(mean_auc)
        r5 = statistics.mean(scores_by_cell[(group,idx,arm,delta,rep,5)][0]
                for idx in range(6) for arm in ARMS for delta in DIFFS for rep in REPLICATES)
        group_summaries.append(dict(group=group, replicate_spearman_r4=rho_rep,
                                    key_spearman_r4=rho_key, early_descriptor_spearman_r4=rho_early,
                                    mean_auc_r4=r4, mean_auc_r5=r5,
                                    across_box_auc_r4_range=max(mean_auc)-min(mean_auc),
                                    replicate_a=[x[0] for x in replicate_means],
                                    replicate_b=[x[1] for x in replicate_means]))

    null_mean = statistics.mean(row["null_auc"] for row in panels)
    rhos = [g["replicate_spearman_r4"] for g in group_summaries]
    success = (sum(rho>0 for rho in rhos)>=10
               and statistics.median(rhos)>=0.5
               and 0.47<=null_mean<=0.53)
    summary = dict(
        preregistered_directional_supported=success,
        positive_group_rep_correlations=sum(rho>0 for rho in rhos),
        median_group_rep_correlation=statistics.median(rhos),
        group_key_r4_median_spearman=statistics.median(g["key_spearman_r4"] for g in group_summaries),
        group_early_diffusion_median_spearman=statistics.median(g["early_descriptor_spearman_r4"] for g in group_summaries),
        mean_r4_auc=statistics.mean(row["auc"] for row in panels if row["rounds"]==4),
        mean_r5_auc=statistics.mean(row["auc"] for row in panels if row["rounds"]==5),
        mean_null_auc=null_mean,
        metric_gate_pass=True,
        sboxes=72, source_schedules=48, key_schedules=24,
        panels=1152, spotcheck_auc_recomputations=independent_auc_checks)
    return dict(study="phase2v-t8-affine-matched-v1",
                source_main_sha=SOURCE_SHA, preregistration_commit=PROTOCOL_SHA,
                source_reference="AES_SBOX", groups=GROUPS, input_differences=DIFFS,
                global_reference_metrics=base_metrics, summary=summary,
                candidate_boxes=boxes, group_reports=group_summaries, panels=panels)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="phase2v-t8-raw.json")
    args=parser.parse_args()
    result=run()
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    data=canonical(result)
    target.write_bytes(data)
    print(json.dumps(dict(out=str(target),sha256=hexsha(data),summary=result["summary"]),
                     sort_keys=True))


if __name__=="__main__":
    main()
