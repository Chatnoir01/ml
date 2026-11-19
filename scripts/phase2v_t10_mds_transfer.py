"""Phase 2V-T10: prospective ROTL11 to MixColumns predictor transport test.

Research-only. Registered before any T10 source outcomes at commit
c939b4809c25087da09bc6361a534d3e2ee451ba.
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

from adversarial_sbox.cryptoshield import (
    algebraic_degree, differential_uniformity, is_bijective,
    max_linear_correlation, nonlinearity, sac_score,
)
from adversarial_sbox.spn import ToySPN

GROUPS = tuple(906011 + 59 * k for k in range(12))
DIFFS = (1, 256)
ROUNDS = (4, 5)
ARMS = ("K0", "K1")
REPLICATES = (0, 1)
ARCHITECTURES = ("R", "M")
N_CLASS = 128
SOURCE_SHA = "b03da1d95e98709869d007571de4f8bbce234a1b"
PROTOCOL_SHA = "c939b4809c25087da09bc6361a534d3e2ee451ba"


def hexsha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seeded(domain: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(domain.encode("ascii")).digest(), "big"))


def canonical(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def bit_permute(byte: int, positions: list[int]) -> int:
    return sum(((byte >> bit) & 1) << positions[bit] for bit in range(8))


def make_parent(group: int) -> tuple[int, ...]:
    values = list(range(256))
    seeded(f"phase2v-t10-parent-v1|{group}").shuffle(values)
    if not is_bijective(values):
        raise AssertionError("parent is not a permutation")
    return tuple(values)


def make_variant(group: int, index: int):
    parent = make_parent(group)
    rng = seeded(f"phase2v-t10-variant-v1|{group}|{index}")
    pin, pout = list(range(8)), list(range(8))
    rng.shuffle(pin)
    rng.shuffle(pout)
    offset_in, offset_out = rng.getrandbits(8), rng.getrandbits(8)
    box = tuple(bit_permute(parent[bit_permute(x, pin) ^ offset_in], pout) ^ offset_out
                for x in range(256))
    if not is_bijective(box):
        raise AssertionError("candidate not bijective")
    return box, dict(pin=pin, pout=pout, input_xor=offset_in, output_xor=offset_out)


def key_words(group: int, arm: str) -> tuple[int, ...]:
    return tuple(int.from_bytes(hashlib.sha256(
        f"phase2v-t10-key-v1|{group}|{arm}|{i}".encode("ascii")
    ).digest()[:4], "big") for i in range(6))


def input_pairs(group: int, delta: int, replicate: int):
    rng = seeded(f"phase2v-t10-pairs-v1|{group}|{delta}|{replicate}")
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



def xtime(value):
    return ((value << 1) & 255) ^ (0x1b if value & 128 else 0)

def mul_reference(a, b):
    result=0
    for _ in range(8):
        if b & 1: result ^= a
        a=xtime(a); b>>=1
    return result

MIX_FORWARD=((2,3,1,1),(1,2,3,1),(1,1,2,3),(3,1,1,2))
MIX_INVERSE=((14,11,13,9),(9,14,11,13),(13,9,14,11),(11,13,9,14))

def mix_matrix(value, matrix=MIX_FORWARD):
    data=value.to_bytes(4,"big")
    return int.from_bytes(bytes([
        mul_reference(data[0],row[0]) ^ mul_reference(data[1],row[1]) ^
        mul_reference(data[2],row[2]) ^ mul_reference(data[3],row[3])
        for row in matrix
    ]),"big")

def mix_optimized(value):
    data=list(value.to_bytes(4,"big"))
    total=data[0]^data[1]^data[2]^data[3]
    return int.from_bytes(bytes(data[i]^total^xtime(data[i]^data[(i+1)%4])
                  for i in range(4)),"big")

class MixColumnsToySPN:
    """Non-production 32-bit SPN: fixed SBox + AES MixColumns between rounds."""
    def __init__(self,sbox,keys):
        self.sbox=tuple(sbox)
        self.keys=tuple(keys)
        if len(self.sbox)!=256 or len(set(self.sbox))!=256 or len(self.keys)<2:
            raise ValueError("invalid cipher arguments")
        self.inverse=[0]*256
        for x,y in enumerate(self.sbox):self.inverse[y]=x

    def encrypt_block(self,plaintext):
        if not 0<=plaintext<=0xffffffff:raise ValueError("bad 32-bit plaintext")
        state=plaintext
        for index,key in enumerate(self.keys[:-1]):
            sub=(state^key).to_bytes(4,"big")
            state=int.from_bytes(bytes(self.sbox[x] for x in sub),"big")
            if index!=len(self.keys)-2:state=mix_optimized(state)
        return state^self.keys[-1]

    def decrypt_block(self,ciphertext):
        if not 0<=ciphertext<=0xffffffff:raise ValueError("bad 32-bit ciphertext")
        state=ciphertext^self.keys[-1]
        for index in range(len(self.keys)-2,-1,-1):
            if index!=len(self.keys)-2:state=mix_matrix(state,MIX_INVERSE)
            state=int.from_bytes(bytes(self.inverse[x] for x in state.to_bytes(4,"big")),"big")
            state ^= self.keys[index]
        return state

def check_mds_controls():
    for lane in range(4):
        for x in range(1,256):
            source=x<<(8*lane)
            value=mix_optimized(source)
            if value!=mix_matrix(source) or mix_matrix(value,MIX_INVERSE)!=source:
                raise AssertionError("forward/inverse MixColumns mismatch")
            if any(byte==0 for byte in value.to_bytes(4,"big")):
                raise AssertionError("MDS single-active-byte diffusion violated")
    for k in range(24):
        word=seeded(f"phase2v-t10-dense-control-v1|{k}").getrandbits(32)
        if mix_optimized(word)!=mix_matrix(word) or mix_matrix(mix_optimized(word),MIX_INVERSE)!=word:
            raise AssertionError("dense MixColumns parity failed")
    box,_=make_variant(GROUPS[0],0)
    keys=key_words(GROUPS[0],"K0")
    for rounds in (4,5):
        cipher=MixColumnsToySPN(box,keys[:rounds+1])
        for pt in (0,1,0x12345678,0xffffffff):
            ct=cipher.encrypt_block(pt)
            if cipher.decrypt_block(ct)!=pt:raise AssertionError("M cipher roundtrip failed")
            state=pt
            for idx,key in enumerate(keys[:rounds]):
                value=state^key
                state=int.from_bytes(bytes(box[x] for x in value.to_bytes(4,"big")),"big")
                if idx!=rounds-1:state=mix_matrix(state)
            if ct!=(state^keys[rounds]):raise AssertionError("independent M encryption mismatch")

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
    check_mds_controls()
    parents=[];boxes=[];panels=[]
    seen_parents=set();seen_boxes=set();seen_keys=set();seen_pairs=set()
    lookup={};feature={};independent_auc_checks=0
    for group in GROUPS:
        parent=make_parent(group)
        parent_sha=hexsha(bytes(parent))
        if parent_sha in seen_parents:raise ValueError("duplicate parent")
        seen_parents.add(parent_sha)
        metrics=metric_vector(parent)
        parents.append(dict(group=group,parent_sha256=parent_sha,global_metrics=metrics))
        source={}
        for delta in DIFFS:
            pair0=input_pairs(group,delta,0)
            pair1=input_pairs(group,delta,1)
            ids0={value for a,b,_ in pair0 for value in (a,b)}
            ids1={value for a,b,_ in pair1 for value in (a,b)}
            if ids0 & ids1:raise ValueError("cross-replicate plaintext collision")
            for rep, pairs in ((0,pair0),(1,pair1)):
                sh=hexsha(canonical(pairs))
                if sh in seen_pairs:raise ValueError("duplicate plaintext source schedule")
                seen_pairs.add(sh);source[(delta,rep)]=(pairs,sh)
        arms={}
        for arm in ARMS:
            keys=key_words(group,arm)
            sh=hexsha(b"".join(v.to_bytes(4,"big") for v in keys))
            if sh in seen_keys:raise ValueError("duplicate key schedule")
            seen_keys.add(sh);arms[arm]=(keys,sh)
        for index in range(6):
            box,transform=make_variant(group,index)
            box_sha=hexsha(bytes(box))
            if box_sha in seen_boxes:raise ValueError("duplicate candidate SBox")
            seen_boxes.add(box_sha)
            box_metrics=metric_vector(box)
            if box_metrics!=metrics:raise ValueError("full global metric mismatch")
            feature[group,index]=statistics.mean(expected_early_active_bytes(box,d) for d in DIFFS)
            boxes.append(dict(group=group,index=index,sha256=box_sha,parent_sha256=parent_sha,
                              transform=transform,global_metrics=box_metrics,early_active_bytes=feature[group,index]))
            for arm in ARMS:
                keys,keysha=arms[arm]
                cipher={(arch,rounds):(ToySPN(box,keys[:rounds+1]) if arch=="R"
                      else MixColumnsToySPN(box,keys[:rounds+1]))
                      for arch in ARCHITECTURES for rounds in ROUNDS}
                for delta in DIFFS:
                    for rep in REPLICATES:
                        pairs,pair_sha=source[delta,rep]
                        labels=[label for _,_,label in pairs]
                        for arch in ARCHITECTURES:
                            for rounds in ROUNDS:
                                e=cipher[arch,rounds].encrypt_block
                                scores=[zero_byte_count(e(a),e(b)) for a,b,_ in pairs]
                                auc=auc_discrete(scores,labels)
                                altered=labels[:]
                                seeded(f"phase2v-t10-null-v1|{group}|{box_sha}|{arch}|{arm}|{delta}|{rep}|{rounds}").shuffle(altered)
                                null=auc_discrete(scores,altered)
                                if index in (0,5) and delta==1 and rep==0:
                                    if (auc!=auc_pair_enumeration(scores,labels) or
                                        null!=auc_pair_enumeration(scores,altered)):
                                        raise AssertionError("AUC tie-aware parity failed")
                                    independent_auc_checks+=2
                                panels.append(dict(group=group,box_index=index,box_sha256=box_sha,
                                    architecture=arch,key_arm=arm,key_sha256=keysha,delta=delta,
                                    replicate=rep,rounds=rounds,pairs_sha256=pair_sha,
                                    auc=auc,null_auc=null,
                                    positive_any_zero_byte=sum(z>0 for z,y in zip(scores,labels) if y==1)/128,
                                    negative_any_zero_byte=sum(z>0 for z,y in zip(scores,labels) if y==0)/128))
                                lookup[group,index,arch,arm,delta,rep,rounds]=auc
    if (len(seen_parents),len(seen_boxes),len(seen_keys),len(seen_pairs),
        len(panels),independent_auc_checks)!=(12,72,24,48,2304,384):
        raise AssertionError("study source or panel cardinality mismatch")
    groups=[]
    for group in GROUPS:
        x=[feature[group,i] for i in range(6)]
        ys={}
        for arch in ARCHITECTURES:
            ys[arch]=[statistics.mean(lookup[group,i,arch,arm,delta,rep,4]
                           for arm in ARMS for delta in DIFFS for rep in REPLICATES)
                      for i in range(6)]
        groups.append(dict(group=group,source_features=x,
            candidate_auc_R4_R=ys["R"],candidate_auc_R4_M=ys["M"],
            predictor_rho_R=spearman(x,ys["R"]),predictor_rho_M=spearman(x,ys["M"]),
            range_R4_R=max(ys["R"])-min(ys["R"]),range_R4_M=max(ys["M"])-min(ys["M"]),
            mean_auc_R4_R=statistics.mean(ys["R"]),mean_auc_R4_M=statistics.mean(ys["M"]),
            mean_auc_R5_R=statistics.mean(lookup[group,i,"R",arm,delta,rep,5]
                           for i in range(6) for arm in ARMS for delta in DIFFS for rep in REPLICATES),
            mean_auc_R5_M=statistics.mean(lookup[group,i,"M",arm,delta,rep,5]
                           for i in range(6) for arm in ARMS for delta in DIFFS for rep in REPLICATES),
            key_rho_M={arm:spearman(x,[statistics.mean(lookup[group,i,"M",arm,d,r,4]
                                  for d in DIFFS for r in REPLICATES) for i in range(6)])
                                  for arm in ARMS}))
    rhoM=[g["predictor_rho_M"] for g in groups]
    rhoR=[g["predictor_rho_R"] for g in groups]
    null_mean=statistics.mean(p["null_auc"] for p in panels)
    supported=(sum(r<0 for r in rhoM)>=10 and statistics.median(rhoM)<=-.5
               and .47<=null_mean<=.53)
    summary=dict(
        preregistered_transport_supported=supported,
        negative_M_group_correlations=sum(x<0 for x in rhoM),
        median_M_group_correlation=statistics.median(rhoM),
        negative_R_group_correlations=sum(x<0 for x in rhoR),
        median_R_group_correlation=statistics.median(rhoR),
        mean_M_R4_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="M" and p["rounds"]==4),
        mean_M_R5_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="M" and p["rounds"]==5),
        mean_R_R4_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R" and p["rounds"]==4),
        mean_R_R5_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R" and p["rounds"]==5),
        mean_shuffled_label_auc=null_mean,
        source_integrity_gates_pass=True,nonzero_MDS_one_byte_basis_checks=1020,
        parents=12,candidates=72,source_schedules=48,key_schedules=24,panels=2304,
        independent_auc_spotchecks=independent_auc_checks)
    return dict(study="phase2v-t10-mds-transfer-v1",source_main_sha=SOURCE_SHA,
        preregistration_commit=PROTOCOL_SHA,groups=GROUPS,
        input_differences=DIFFS,architectures=ARCHITECTURES,
        parent_boxes=parents,candidate_boxes=boxes,
        group_reports=groups,summary=summary,panels=panels)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="phase2v-t10-raw.json")
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
