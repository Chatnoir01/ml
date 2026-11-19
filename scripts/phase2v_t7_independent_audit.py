"""Second, implementation-independent verifier for Phase2V-T7.

Imports no code from the primary study or ToySPN. Reconstructs every
registered raw input, key, ciphertext pair, AUC, null and group contrast.
"""
import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
import statistics

SEEDS = tuple(903011+37*i for i in range(12))
DELTAS = (1, 256, 65792, 16843009)
ROUNDS = (4, 5)

def seed_for(text):
    return int.from_bytes(hashlib.sha256(text.encode("ascii")).digest(),"big")

def encrypt_direct(box,keys,pt):
    state=pt
    for index in range(len(keys)-1):
        state ^= keys[index]
        state = int.from_bytes(bytes(box[x] for x in state.to_bytes(4,"big")),"big")
        if index < len(keys)-2:
            state = ((state << 11) | (state >> 21)) & 0xFFFFFFFF
    return state ^ keys[-1]

def pairs_for(group,boxsha,delta):
    gen=random.Random(seed_for(f"phase2v-t7-pairs-v1|{group}|{boxsha}|{delta}"))
    pairs=[]
    used=set()
    trials=0
    for label in (1,0):
        accepted=0
        while accepted<128:
            trials+=1
            if trials>50000: raise ValueError("draw budget exhausted")
            a=gen.getrandbits(32)
            b=a^delta if label else gen.getrandbits(32)
            if a==b or (not label and (a^b)==delta) or a in used or b in used:
                continue
            used.update((a,b))
            pairs.append((a,b,label))
            accepted+=1
    if len(pairs)!=256 or len(used)!=512: raise ValueError("input reuse")
    return pairs

def auc_independent(scores,labels):
    positive=[s for s,y in zip(scores,labels) if y==1]
    negative=[s for s,y in zip(scores,labels) if y==0]
    if len(positive)!=128 or len(negative)!=128: raise ValueError("unbalanced labels")
    return sum(2 if a>b else 1 if a==b else 0 for a in positive for b in negative)/(2*128*128)

def validate_shape(report):
    if report.get("study")!="phase2v-t7-input-activity-v1": raise ValueError("wrong study")
    if tuple(report["seeds"])!=SEEDS or tuple(report["deltas"])!=DELTAS:
        raise ValueError("registration changed")
    if report["source_main_sha"]!="b03da1d95e98709869d007571de4f8bbce234a1b":
        raise ValueError("source identity changed")
    rows=report["panels"]
    expected={(g,i,d,r) for g in SEEDS for i in range(8) for d in DELTAS for r in ROUNDS}
    ids={(p["group"],p["sbox_index"],p["delta"],p["rounds"]) for p in rows}
    if len(rows)!=768 or ids!=expected or len(report["groups"])!=12:
        raise ValueError("missing, extra or duplicate panels")
    if report["metrics"]["panels"]!=768 or report["metrics"]["box_fingerprints"]!=96:
        raise ValueError("invalid source counts")
    if any(not(0<=p["auc"]<=1 and 0<=p["null_auc"]<=1) for p in rows):
        raise ValueError("invalid score")

def verify(report):
    validate_shape(report)
    rows={(p["group"],p["sbox_index"],p["delta"],p["rounds"]):p for p in report["panels"]}
    accumulated=defaultdict(list)
    allnull=[]
    boxids=set()
    sampleids=set()
    num=0
    for g in SEEDS:
        for index in range(8):
            box=list(range(256))
            random.Random(seed_for(f"phase2v-t7-sbox-v1|{g}|{index}")).shuffle(box)
            fingerprint=hashlib.sha256(bytes(box)).hexdigest()
            if fingerprint in boxids: raise ValueError("duplicate box")
            boxids.add(fingerprint)
            keys=[int.from_bytes(hashlib.sha256(f"phase2v-t7-key-v1|{g}|{fingerprint}|{k}".encode("ascii")).digest()[:4],"big") for k in range(6)]
            keysha=hashlib.sha256(b"".join(x.to_bytes(4,"big") for x in keys)).hexdigest()
            for delta in DELTAS:
                pairs=pairs_for(g,fingerprint,delta)
                raw=(json.dumps(pairs,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("ascii")
                pairsha=hashlib.sha256(raw).hexdigest()
                if pairsha in sampleids: raise ValueError("duplicated sample")
                sampleids.add(pairsha)
                labels=[z for _,_,z in pairs]
                for rounds in ROUNDS:
                    row=rows[(g,index,delta,rounds)]
                    if (row["sbox_sha256"],row["key_sha256"],row["pair_sha256"])!=(fingerprint,keysha,pairsha):
                        raise ValueError("fingerprint mismatched")
                    ct=[(encrypt_direct(box,keys[:rounds+1],a),encrypt_direct(box,keys[:rounds+1],b)) for a,b,_ in pairs]
                    scores=[sum((((a^b) >> (shift*8)) & 255)==0 for shift in range(4)) for a,b in ct]
                    auc=auc_independent(scores,labels)
                    shuffled=labels[:]
                    random.Random(seed_for(f"phase2v-t7-null-v1|{g}|{fingerprint}|{delta}|{rounds}")).shuffle(shuffled)
                    null=auc_independent(scores,shuffled)
                    posrate=sum(s>0 for s,y in zip(scores,labels) if y==1)/128
                    negrate=sum(s>0 for s,y in zip(scores,labels) if y==0)/128
                    if (auc,null,posrate,negrate)!=(row["auc"],row["null_auc"],row["positive_any_zero_byte"],row["negative_any_zero_byte"]):
                        raise ValueError("AUC/null/class-rate mismatch")
                    accumulated[(g,rounds,delta)].append(auc)
                    allnull.append(null)
                    num+=1
    if (len(boxids),len(sampleids),num)!=(96,384,768): raise ValueError("count mismatch")
    contrasts=[]
    for gr in report["groups"]:
        g=gr["group"]
        for rounds in ROUNDS:
            avgs={d:sum(accumulated[(g,rounds,d)])/8 for d in DELTAS}
            for d,m in avgs.items():
                if abs(m-gr[f"auc_r{rounds}_delta_{d}"])>1e-14: raise ValueError("group AUC mismatch")
            diff=(avgs[1]+avgs[256])/2-avgs[16843009]
            if abs(diff-gr[f"contrast_r{rounds}"])>1e-14: raise ValueError("contrast mismatch")
            if rounds==4: contrasts.append(diff)
    m=report["metrics"]
    if abs(statistics.median(contrasts)-m["primary_contrast_median"])>1e-14:
        raise ValueError("median mismatch")
    if sum(x>0 for x in contrasts)!=m["primary_contrasts_positive"]:
        raise ValueError("direction mismatch")
    if abs(statistics.mean(allnull)-m["mean_shuffled_label_null_auc"])>1e-14:
        raise ValueError("null mismatch")
    accepted=(sum(x>0 for x in contrasts)>=10 and statistics.median(contrasts)>=0.05 and 0.47<=statistics.mean(allnull)<=0.53)
    if accepted!=m["primary_hypothesis_supported"]: raise ValueError("invalid decision")
    return dict(verified_panels=num,verified_sboxes=len(boxids),verified_schedules=len(sampleids),registered_primary_supported=accepted)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True)
    ap.add_argument("--expected-sha",required=True)
    a=ap.parse_args()
    raw=Path(a.report).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.expected_sha:
        raise ValueError("file digest mismatch")
    print(json.dumps(verify(json.loads(raw)),sort_keys=True))

if __name__=="__main__":
    main()
