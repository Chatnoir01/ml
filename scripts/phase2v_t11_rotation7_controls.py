"""Phase 2V-T11: prospective ROTL7 SBox feature vs classical DDT controls.

Research-only, preregistered before new data at commit
207331148f05689f288d6b510e524db8668d41b2.
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

GROUPS = tuple(907011 + 61 * k for k in range(12))
DIFFS = (1, 256)
ROUNDS = (4, 5)
ARCHITECTURES = ("R11","R7")
ARMS = ("K0", "K1")
REPLICATES = (0, 1)
N_CLASS = 128
SOURCE_SHA = "b03da1d95e98709869d007571de4f8bbce234a1b"
PROTOCOL_SHA = "207331148f05689f288d6b510e524db8668d41b2"


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
    seeded(f"phase2v-t11-parent-v1|{group}").shuffle(values)
    if not is_bijective(values):
        raise AssertionError("parent is not a permutation")
    return tuple(values)


def make_variant(group: int, index: int):
    parent = make_parent(group)
    rng = seeded(f"phase2v-t11-variant-v1|{group}|{index}")
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
        f"phase2v-t11-key-v1|{group}|{arm}|{i}".encode("ascii")
    ).digest()[:4], "big") for i in range(6))


def input_pairs(group: int, delta: int, replicate: int):
    rng = seeded(f"phase2v-t11-pairs-v1|{group}|{delta}|{replicate}")
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



def early_byte_activity(box, delta, rotation):
    lane=0 if delta==1 else 1
    value=0
    for x in range(256):
        d=(box[x]^box[x^1])<<(8*lane)
        rotate=((d<<rotation)|(d>>(32-rotation)))&0xffffffff
        value+=sum((rotate>>shift &255)!=0 for shift in (0,8,16,24))
    return value/256

def ddt_row_baselines(box):
    counts=[0]*256
    for x in range(256):counts[box[x]^box[x^1]]+=1
    if sum(counts)!=256:raise AssertionError("DDT row invalid")
    return sum(v*v for v in counts)/(256*256),max(counts)/256

def source_predictors(box):
    collision,highest=ddt_row_baselines(box)
    return dict(f7=statistics.mean(early_byte_activity(box,d,7) for d in DIFFS),
                f11=statistics.mean(early_byte_activity(box,d,11) for d in DIFFS),
                d1collision=collision,d1maximum=highest)

class Rot7ToySPN:
    """Research-only 32-bit substitution/rotation/whitening toy SPN."""
    def __init__(self,box,keys):
        self.box=tuple(box)
        self.keys=tuple(keys)
        if len(self.box)!=256 or len(set(self.box))!=256 or len(self.keys)<2:
            raise ValueError("invalid SBox or key schedule")
        if any(k<0 or k>0xffffffff for k in self.keys):
            raise ValueError("key word out of range")
        self.inverse=[0]*256
        for i,x in enumerate(self.box):self.inverse[x]=i
    def encrypt_block(self,plain):
        if plain<0 or plain>0xffffffff:raise ValueError("bad plaintext")
        state=plain
        for index,key in enumerate(self.keys[:-1]):
            data=(state^key).to_bytes(4,"big")
            state=int.from_bytes(bytes(self.box[x] for x in data),"big")
            if index!=len(self.keys)-2:
                state=((state<<7)|(state>>25))&0xffffffff
        return state^self.keys[-1]
    def decrypt_block(self,cipher):
        if cipher<0 or cipher>0xffffffff:raise ValueError("bad ciphertext")
        state=cipher^self.keys[-1]
        for index in range(len(self.keys)-2,-1,-1):
            if index!=len(self.keys)-2:
                state=((state>>7)|(state<<25))&0xffffffff
            state=int.from_bytes(bytes(self.inverse[x] for x in state.to_bytes(4,"big")),"big")
            state^=self.keys[index]
        return state

def encrypt_rot7_reference(box,keys,plaintext):
    state=plaintext
    for index,word in enumerate(keys[:-1]):
        state^=word
        b0=box[(state>>24)&255]
        b1=box[(state>>16)&255]
        b2=box[(state>>8)&255]
        b3=box[state&255]
        state=(b0<<24)|(b1<<16)|(b2<<8)|b3
        if index!=len(keys)-2:
            state=((state<<7)|(state>>(32-7)))&0xffffffff
    return state^keys[-1]

def check_ciphers():
    box, _ = make_variant(GROUPS[0], 0)
    keys = key_words(GROUPS[0], "K0")
    for r in ROUNDS:
        for arch, cipher, reference in (
            ("R11",ToySPN(box,keys[:r+1]),independently_encrypt),
            ("R7",Rot7ToySPN(box,keys[:r+1]),encrypt_rot7_reference)):
            for plaintext in (0, 1, 0x12345678, 0xffffffff):
                actual=cipher.encrypt_block(plaintext)
                if actual!=reference(box,keys[:r+1],plaintext):
                    raise AssertionError("cipher parity "+arch)
                if cipher.decrypt_block(actual)!=plaintext:
                    raise AssertionError("roundtrip "+arch)
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
    parents=[];boxes=[];panels=[]
    seen_parents=set();seen_boxes=set();seen_keys=set();seen_sources=set()
    outcome={};pred={};independent_checks=0
    for group in GROUPS:
        p=make_parent(group)
        fingerprint=hexsha(bytes(p))
        if fingerprint in seen_parents:raise ValueError("duplicate parent")
        seen_parents.add(fingerprint)
        base=metric_vector(p)
        parents.append(dict(group=group,parent_sha256=fingerprint,global_metrics=base))
        pairs={}
        for delta in DIFFS:
            p0=input_pairs(group,delta,0)
            p1=input_pairs(group,delta,1)
            used0={v for a,b,_ in p0 for v in (a,b)}
            used1={v for a,b,_ in p1 for v in (a,b)}
            if used0 & used1:raise ValueError("replicates overlap")
            for rep,pp in ((0,p0),(1,p1)):
                sha=hexsha(canonical(pp))
                if sha in seen_sources:raise ValueError("duplicate source schedule")
                seen_sources.add(sha);pairs[delta,rep]=(pp,sha)
        keys={}
        for arm in ARMS:
            k=key_words(group,arm)
            ksha=hexsha(b"".join(v.to_bytes(4,"big") for v in k))
            if ksha in seen_keys:raise ValueError("duplicate key")
            seen_keys.add(ksha);keys[arm]=(k,ksha)
        for index in range(6):
            box,transform=make_variant(group,index)
            sha=hexsha(bytes(box))
            if sha in seen_boxes:raise ValueError("duplicate variant")
            seen_boxes.add(sha)
            metrics=metric_vector(box)
            if metrics!=base:raise ValueError("classical metric gate failed")
            features=source_predictors(box)
            pred[group,index]=features
            boxes.append(dict(group=group,index=index,sha256=sha,parent_sha256=fingerprint,
                         transform=transform,global_metrics=metrics,source_predictors=features))
            for arm in ARMS:
                key,keysha=keys[arm]
                cipher={(arch,r):ToySPN(box,key[:r+1]) if arch=="R11" else Rot7ToySPN(box,key[:r+1])
                        for arch in ARCHITECTURES for r in ROUNDS}
                for delta in DIFFS:
                    for rep in REPLICATES:
                        pp,pairsha=pairs[delta,rep]
                        labels=[label for _,_,label in pp]
                        for arch in ARCHITECTURES:
                            for r in ROUNDS:
                                enc=cipher[arch,r].encrypt_block
                                scores=[zero_byte_count(enc(a),enc(b)) for a,b,_ in pp]
                                auc=auc_discrete(scores,labels)
                                shuffled=labels[:]
                                seeded(f"phase2v-t11-null-v1|{group}|{sha}|{arch}|{arm}|{delta}|{rep}|{r}").shuffle(shuffled)
                                null=auc_discrete(scores,shuffled)
                                if index in (0,5) and delta==1 and rep==0:
                                    if (auc!=auc_pair_enumeration(scores,labels) or
                                        null!=auc_pair_enumeration(scores,shuffled)):
                                        raise AssertionError("AUC implementation mismatch")
                                    independent_checks+=2
                                panels.append(dict(group=group,box_index=index,box_sha256=sha,architecture=arch,
                                         key_arm=arm,key_sha256=keysha,delta=delta,replicate=rep,
                                         rounds=r,pairs_sha256=pairsha,auc=auc,null_auc=null,
                                         positive_any_zero_byte=sum(z>0 for z,y in zip(scores,labels) if y==1)/128,
                                         negative_any_zero_byte=sum(z>0 for z,y in zip(scores,labels) if y==0)/128))
                                outcome[group,index,arch,arm,delta,rep,r]=auc
    if (len(seen_parents),len(seen_boxes),len(seen_keys),len(seen_sources),len(panels),independent_checks)!=(12,72,24,48,2304,384):
        raise AssertionError("source/panel cardinality violation")
    groups=[]
    for group in GROUPS:
        data={name:[pred[group,i][name] for i in range(6)] for name in ("f7","f11","d1collision","d1maximum")}
        ys={arch:[statistics.mean(outcome[group,i,arch,arm,d,rep,4]
                  for arm in ARMS for d in DIFFS for rep in REPLICATES) for i in range(6)]
                  for arch in ARCHITECTURES}
        rhos={name:spearman(data[name],ys["R7"]) for name in data}
        r11={name:spearman(data[name],ys["R11"]) for name in ("f7","f11")}
        rr={arm:spearman(data["f7"],[statistics.mean(outcome[group,i,"R7",arm,d,rep,4]
                    for d in DIFFS for rep in REPLICATES) for i in range(6)]) for arm in ARMS}
        reps={str(rep):spearman(data["f7"],[statistics.mean(outcome[group,i,"R7",arm,d,rep,4]
                    for arm in ARMS for d in DIFFS) for i in range(6)]) for rep in REPLICATES}
        groups.append(dict(group=group,features=data,candidate_R7_auc=ys["R7"],
                    candidate_R11_auc=ys["R11"],rhos_R7=rhos,rhos_R11=r11,
                    key_rho_R7=rr,replicate_rho_R7=reps,
                    auc_range_R7=max(ys["R7"])-min(ys["R7"]),
                    feature_range_F7=max(data["f7"])-min(data["f7"]),
                    mean_R7_R4=statistics.mean(ys["R7"]),
                    mean_R11_R4=statistics.mean(ys["R11"]),
                    mean_R7_R5=statistics.mean(outcome[group,i,"R7",arm,d,rep,5]
                           for i in range(6) for arm in ARMS for d in DIFFS for rep in REPLICATES),
                    mean_R11_R5=statistics.mean(outcome[group,i,"R11",arm,d,rep,5]
                           for i in range(6) for arm in ARMS for d in DIFFS for rep in REPLICATES)))
    rhos=[group["rhos_R7"]["f7"] for group in groups]
    meanR7=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R7" and p["rounds"]==4)
    nullmean=statistics.mean(p["null_auc"] for p in panels)
    source_valid=.47<=nullmean<=.53
    if meanR7<.55:status="SIGNAL_INSUFFICIENT"
    elif sum(r<0 for r in rhos)>=10 and statistics.median(rhos)<=-.5 and source_valid:status="SUPPORTED"
    else:status="NOT_SUPPORTED"
    summary=dict(
        preregistered_primary_status=status,
        signal_gate_pass=meanR7>=.55,
        negative_F7_groups=sum(x<0 for x in rhos),
        median_F7_rho=statistics.median(rhos),
        mean_R7_R4_auc=meanR7,
        mean_R7_R5_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R7" and p["rounds"]==5),
        mean_R11_R4_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R11" and p["rounds"]==4),
        mean_R11_R5_auc=statistics.mean(p["auc"] for p in panels if p["architecture"]=="R11" and p["rounds"]==5),
        mean_shuffled_label_auc=nullmean,
        secondary_median_rhos_R7={name:statistics.median(g["rhos_R7"][name] for g in groups) for name in ("f7","f11","d1collision","d1maximum")},
        secondary_directional_counts_R7=dict(
            f7=sum(g["rhos_R7"]["f7"]<0 for g in groups),
            f11=sum(g["rhos_R7"]["f11"]<0 for g in groups),
            d1collision=sum(g["rhos_R7"]["d1collision"]>0 for g in groups),
            d1maximum=sum(g["rhos_R7"]["d1maximum"]>0 for g in groups)),
        source_integrity_pass=True,parents=12,candidates=72,key_schedules=24,
        source_schedules=48,panels=2304,independent_auc_spotchecks=384)
    return dict(study="phase2v-t11-rotation7-controls-v1",source_main_sha=SOURCE_SHA,
                preregistration_commit=PROTOCOL_SHA,groups=GROUPS,
                architectures=ARCHITECTURES,input_differences=DIFFS,
                parent_boxes=parents,candidate_boxes=boxes,group_reports=groups,
                summary=summary,panels=panels)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="phase2v-t11-raw.json")
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
