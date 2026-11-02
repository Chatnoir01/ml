"""Independent Phase 2U source-bound classical score reproduction.

Python standard library only. Does not import the original ToySPN cipher,
pair generator, feature selector, package modules or new neural data.
Use only original frozen JSON artifacts from GitHub run 41539098859:
    python scripts/phase2u_independent_precommit_replay.py \
      --source-panel source-panel.json \
      --predictions prediction.json --output audit.json

NOT a proof of future neural generalization or real cipher security.
"""
from __future__ import annotations

import argparse
from hashlib import sha256, sha3_256
import json
from pathlib import Path
import random

MASK32 = (1 << 32)-1
KEYS = (0x243F6A88,0x85A308D3,0x13198A2E,0x03707344,0xA4093822)
DIFFERENCES = (1,256)
TRAIN_SEED = 0x52010471
TEST_SEED = 0x520104A5
TRAIN_PER_LABEL = 2048
TEST_PER_LABEL = 4096
SOURCE_SHA = "512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef"
PREDICTION_SHA = "cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4"


def canonical_sha256(obj: dict, key: str) -> str:
    unpack=dict(obj)
    claimed=unpack.pop(key,None)
    digest=sha256(json.dumps(unpack,sort_keys=True,separators=(",",":"),
                             ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()
    if claimed!=digest:
        raise ValueError(f"Original artifact {key} mismatch")
    return digest


def source_pairs(delta: int, count: int, seed: int, excluded=()):
    rng=random.Random(seed ^ delta)
    used=set(excluded)
    positives=[]
    negatives=[]
    while len(positives)<count:
        x=rng.getrandbits(32)
        y=x^delta
        if x in used or y in used:
            continue
        used.update((x,y))
        positives.append((x,y))
    while len(negatives)<count:
        x=rng.getrandbits(32)
        y=rng.getrandbits(32)
        if x==y or x^y==delta or x in used or y in used:
            continue
        used.update((x,y))
        negatives.append((x,y))
    return positives,negatives


def pair_sets(delta: int):
    tp,tn=source_pairs(delta,TRAIN_PER_LABEL,TRAIN_SEED)
    old={x for a,b in (*tp,*tn) for x in (a,b)}
    hp,hn=source_pairs(delta,TEST_PER_LABEL,TEST_SEED,old)
    held={x for a,b in (*hp,*hn) for x in (a,b)}
    if old & held:
        raise ValueError("train/test plaintext reuse")
    return tp,tn,hp,hn


def encrypt(plaintext: int, box: list[int]) -> int:
    state=plaintext
    for index in range(4):
        state ^= KEYS[index]
        state=(
            (box[(state>>24)&255]<<24)
            |(box[(state>>16)&255]<<16)
            |(box[(state>>8)&255]<<8)
            |box[state&255]
        )
        if index<3:
            state=((state<<11)|(state>>21))&MASK32
    return state^KEYS[4]


def xor_samples(box: list[int], pairs):
    for a,b in pairs:
        yield encrypt(a,box)^encrypt(b,box)


def frequency_counts(box: list[int], pairs) -> list[int]:
    counts=[0]*32
    for value in xor_samples(box,pairs):
        for i in range(32):
            counts[i]+=(value>>i)&1
    return counts


def single_bit_probe(box: list[int], delta: int, pairs):
    tp,tn,hp,hn=pairs
    p=frequency_counts(box,tp)
    n=frequency_counts(box,tn)
    gaps=[(a-b)/TRAIN_PER_LABEL for a,b in zip(p,n)]
    chosen=max(range(32), key=lambda bit:abs(gaps[bit]))
    sign=1 if gaps[chosen]>=0 else -1
    # Only the selected bit is needed for heldout discrimination.
    positive=sum((v>>chosen)&1 for v in xor_samples(box,hp))
    negative=sum((v>>chosen)&1 for v in xor_samples(box,hn))
    return {
        "difference":delta,
        "bit":chosen,
        "signed_holdout_advantage":sign*(positive-negative)/TEST_PER_LABEL,
    }


def independent_audit(source: dict, frozen: dict) -> dict:
    source_sha=canonical_sha256(source,"panel_receipt_sha256")
    freeze_sha=canonical_sha256(frozen,"prediction_receipt_sha256")
    if source_sha!=SOURCE_SHA or freeze_sha!=PREDICTION_SHA:
        raise ValueError("not the exact frozen Phase 2U source/prediction pair")
    if (frozen.get("source_panel_receipt_sha256")!=SOURCE_SHA
            or source.get("examined_seed_count")!=19
            or source.get("selected_count")!=12
            or frozen.get("candidate_count")!=12
            or source.get("new_neural_trainings")!=0
            or frozen.get("new_neural_trainings")!=0
            or frozen.get("neural_outcomes_accessed") is not False):
        raise ValueError("neural contamination or source provenance mismatch")
    bases={x["seed"]:x for x in source["selected_candidates"]}
    predicted={x["seed"]:x for x in frozen["predictions"]}
    if len(bases)!=12 or len(predicted)!=12 or set(bases)!=set(predicted):
        raise ValueError("incomplete prediction identities")
    matched={delta:pair_sets(delta) for delta in DIFFERENCES}
    rows=[]
    for seed,item in bases.items():
        box=item["sbox"]
        if sorted(box)!=list(range(256)):
            raise ValueError("nonbijective selected S-Box")
        if sha3_256(bytes(box)).hexdigest()!=item["fingerprint"]:
            raise ValueError("fingerprint changed")
        component=[single_bit_probe(box,d,matched[d]) for d in DIFFERENCES]
        score=sum(x["signed_holdout_advantage"] for x in component)/len(component)
        original=predicted[seed]
        if (component!=original["feature_components"]
                or score!=original["classical_feature_score"]
                or item["fingerprint"]!=original["fingerprint"]):
            raise ValueError(f"independent probe mismatch for seed {seed}")
        rows.append({
            "seed":seed,"fingerprint":item["fingerprint"],
            "classical_score":score,"components":component,
        })
    ordered=sorted(rows,key=lambda x:(-x["classical_score"],x["fingerprint"]))
    if [x["fingerprint"] for x in ordered]!=frozen["best_first_fingerprints"]:
        raise ValueError("independent rank mismatch")
    return {
        "schema_version":1,
        "experiment":"phase2u_independent_classical_precommit_score_replay",
        "status":"PASS_ALL_12_CLASSICAL_BITS_AND_SCORES",
        "source_panel_sha256":source_sha,
        "original_prediction_sha256":freeze_sha,
        "distinct_candidates":12,
        "depth":4,
        "input_differences":list(DIFFERENCES),
        "train_per_label":TRAIN_PER_LABEL,
        "test_per_label":TEST_PER_LABEL,
        "matched_train_test_plaintexts_disjoint":True,
        "new_neural_trainings":0,
        "neural_outcomes_accessed":False,
        "scientific_scope":"TOYSPN_CLASSICAL_PREDICTOR_REPRODUCED_NOT_NEURAL_GENERALIZATION",
        "ranked":ordered,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-panel",type=Path,required=True)
    p.add_argument("--predictions",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    source=json.loads(args.source_panel.read_text(encoding="utf-8"))
    predicted=json.loads(args.predictions.read_text(encoding="utf-8"))
    result=independent_audit(source,predicted)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
        f.write("\n")
    print("PHASE2U_INDEPENDENT_CLASSICAL_REPLAY=PASS")
    print("SOURCE_SHA256="+SOURCE_SHA)
    print("PREDICTION_SHA256="+PREDICTION_SHA)


if __name__=="__main__":
    main()
