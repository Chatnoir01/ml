"""Independent auditor for preregistered Phase2V-T10.

No import from the primary experiment, original ToySPN implementation or metric
implementation. Reconstructs 72 SBoxes/metrics, 48 pair schedules, 24 keys,
2304 ciphertext AUCs, permutations, all group endpoints and decision.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

GROUPS=tuple(906011+59*i for i in range(12))
DELTAS=(1,256)
ARMS=("K0","K1")
ROUNDS=(4,5)
REPS=(0,1)
ARCH=("R","M")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def frozen_seed(data):
    return int.from_bytes(hashlib.sha256(data.encode("ascii")).digest(),"big")

def new_parent(group):
    values=list(range(256))
    random.Random(frozen_seed(f"phase2v-t10-parent-v1|{group}")).shuffle(values)
    return values


def new_variant(group,index):
    parent=new_parent(group)
    rng=random.Random(frozen_seed(f"phase2v-t10-variant-v1|{group}|{index}"))
    p=list(range(8));q=list(range(8))
    rng.shuffle(p);rng.shuffle(q)
    a=rng.getrandbits(8);b=rng.getrandbits(8)
    def bitmix(x,locs):
        value=0
        for i,dest in enumerate(locs):
            if x&(1<<i):value|=1<<dest
        return value
    box=[bitmix(parent[bitmix(x,p)^a],q)^b for x in range(256)]
    return box,dict(pin=p,pout=q,input_xor=a,output_xor=b)


def fresh_keys(group,arm):
    keys=[]
    for i in range(6):
        digest=hashlib.sha256(f"phase2v-t10-key-v1|{group}|{arm}|{i}".encode("ascii")).digest()
        keys.append(int.from_bytes(digest[:4],"big"))
    return keys,sha(b"".join(k.to_bytes(4,"big") for k in keys))

def fresh_pairs(group,delta,rep):
    r=random.Random(frozen_seed(f"phase2v-t10-pairs-v1|{group}|{delta}|{rep}"))
    seen=set();result=[]
    attempts=0
    for label in (1,0):
        good=0
        while good<128:
            attempts+=1
            if attempts>50000:raise ValueError("too many attempts")
            x=r.getrandbits(32);y=x^delta if label else r.getrandbits(32)
            if x==y or (not label and x^y==delta) or x in seen or y in seen:
                continue
            seen.update((x,y));result.append((x,y,label));good+=1
    if len(result)!=256 or len(seen)!=512:raise ValueError("duplicate plaintext")
    return result,seen,sha((json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=True)+"\n").encode("ascii"))

def cipher_encrypt(box,keys,plaintext):
    state=plaintext
    for k in range(len(keys)-1):
        x=state^keys[k]
        v=0
        for shift in (0,8,16,24):
            v|=box[(x>>shift)&255]<<shift
        state=v
        if k+2<len(keys):
            state=(state<<11 | state>>21)&0xffffffff
    return state^keys[-1]

def metric_reference(box):
    if len(box)!=256 or len(set(box))!=256:return None
    maxddt=0
    for dx in range(1,256):
        counts=[0]*256
        for x in range(256):
            counts[box[x]^box[x^dx]]+=1
        if max(counts)>maxddt:maxddt=max(counts)
    maxwalsh=0
    for out_mask in range(1,256):
        values=[-1 if (v&out_mask).bit_count()&1 else 1 for v in box]
        step=1
        while step<256:
            for left in range(0,256,2*step):
                for i in range(left,left+step):
                    a,b=values[i],values[i+step]
                    values[i]=a+b;values[i+step]=a-b
            step*=2
        maxwalsh=max(maxwalsh,max(abs(v) for v in values))
    highest=0
    for bit in range(8):
        ans=[(v>>bit)&1 for v in box]
        for j in range(8):
            for mask in range(256):
                if mask & (1<<j):ans[mask]^=ans[mask^(1<<j)]
        highest=max(highest,max((m.bit_count() for m,v in enumerate(ans) if v),default=0))
    changes=sum((box[x]^box[x^(1<<i)]).bit_count() for i in range(8) for x in range(256))
    return dict(du=maxddt,nl=128-maxwalsh//2,max_lat=maxwalsh,degree=highest,sac=changes/(8*8*256))

def early_activity(box,delta):
    shift=0 if delta==1 else 8
    summation=0
    for x in range(256):
        d=(box[x]^box[x^1])<<shift
        rot=((d<<11)|(d>>21))&0xffffffff
        for pos in (0,8,16,24):
            summation+= bool((rot>>pos)&255)
    return summation/256

def rankmid(values):
    ranked=sorted((value,index) for index,value in enumerate(values))
    answer=[0.0]*len(values)
    pos=0
    while pos<len(ranked):
        end=pos+1
        while end<len(ranked) and ranked[end][0]==ranked[pos][0]:end+=1
        center=((pos+1)+end)/2.0
        for _,index in ranked[pos:end]:
            answer[index]=center
        pos=end
    return answer

def rho(a,b):
    p=rankmid(a);q=rankmid(b)
    x=sum(p)/len(p);y=sum(q)/len(q)
    aa=[z-x for z in p];bb=[z-y for z in q]
    norm=math.sqrt(sum(z*z for z in aa)*sum(z*z for z in bb))
    return sum(u*v for u,v in zip(aa,bb))/norm if norm else 0.0

def auc_rank(scores,labels):
    if sum(labels)!=128 or len(scores)!=256:raise ValueError("AUC balance")
    ordered=sorted(zip(scores,labels))
    rank_positive=0.0
    i=0
    while i<256:
        j=i+1
        while j<256 and ordered[j][0]==ordered[i][0]:j+=1
        rank_positive+=((i+1+j)/2)*sum(y for _,y in ordered[i:j])
        i=j
    return (rank_positive-(128*129/2))/(128*128)

def auc_slow(scores,labels):
    positive=[s for s,l in zip(scores,labels) if l]
    negative=[s for s,l in zip(scores,labels) if not l]
    return sum(2 if x>y else 1 if x==y else 0 for x in positive for y in negative)/(2*128*128)


MIX_FORWARD=((2,3,1,1),(1,2,3,1),(1,1,2,3),(3,1,1,2))
MIX_INVERSE=((14,11,13,9),(9,14,11,13),(13,9,14,11),(11,13,9,14))

def gf8mul(a,b):
    out=0
    while b:
        if b&1:out ^= a
        a=((a<<1)&255) ^ (0x1b if a&128 else 0)
        b>>=1
    return out

def independent_mix(state, matrix=MIX_FORWARD):
    source=state.to_bytes(4,"big")
    b=bytes([gf8mul(source[0],row[0])^gf8mul(source[1],row[1])^
             gf8mul(source[2],row[2])^gf8mul(source[3],row[3]) for row in matrix])
    return int.from_bytes(b,"big")

def independent_mds_cipher(box,keys,plaintext):
    state=plaintext
    for index,key in enumerate(keys[:-1]):
        v=state^key
        state=(box[v&255] | (box[(v>>8)&255]<<8) |
               (box[(v>>16)&255]<<16) | (box[(v>>24)&255]<<24))
        if index<len(keys)-2:
            state=independent_mix(state)
    return state^keys[-1]

def verify_mds():
    for i in range(4):
        for k in range(1,256):
            v=k<<(8*i)
            after=independent_mix(v)
            if not all(after.to_bytes(4,"big")) or independent_mix(after,MIX_INVERSE)!=v:
                raise ValueError("MDS basis/inverse invariant failed")
    for i in range(30):
        value=frozen_seed(f"t10-dense-verify-v1|{i}")&0xffffffff
        if independent_mix(independent_mix(value),MIX_INVERSE)!=value:
            raise ValueError("MDS dense inverse failed")

def verify_shape(doc):
    if doc.get("study")!="phase2v-t10-mds-transfer-v1":
        raise ValueError("wrong protocol identity")
    if doc.get("source_main_sha")!="b03da1d95e98709869d007571de4f8bbce234a1b":
        raise ValueError("wrong source commit")
    if doc.get("preregistration_commit")!="c939b4809c25087da09bc6361a534d3e2ee451ba":
        raise ValueError("wrong preregistration")
    if tuple(doc.get("groups",[]))!=GROUPS or tuple(doc.get("input_differences",[]))!=DELTAS or tuple(doc.get("architectures",[]))!=ARCH:
        raise ValueError("wrong group/delta/architecture registry")
    rows=doc.get("panels",[])
    expected={(g,i,a,arm,d,rep,r) for g in GROUPS for i in range(6)
              for a in ARCH for arm in ARMS for d in DELTAS for rep in REPS for r in ROUNDS}
    observed={(z["group"],z["box_index"],z["architecture"],z["key_arm"],
               z["delta"],z["replicate"],z["rounds"]) for z in rows}
    if len(rows)!=2304 or observed!=expected or len(doc.get("candidate_boxes",[]))!=72 or len(doc.get("parent_boxes",[]))!=12 or len(doc.get("group_reports",[]))!=12:
        raise ValueError("missing/duplicate registered panel or source")
    if {(z["group"],z["index"]) for z in doc["candidate_boxes"]}!={(g,i) for g in GROUPS for i in range(6)}:
        raise ValueError("candidate registry mismatch")

def verify_panel(z):
    g=z["group"];i=z["box_index"];a=z["architecture"];arm=z["key_arm"]
    d=z["delta"];rep=z["replicate"];rounds=z["rounds"]
    box,_=new_variant(g,i)
    boxsha=sha(bytes(box))
    keys,keysha=fresh_keys(g,arm)
    pairs,seen,pairsha=fresh_pairs(g,d,rep)
    if (z["box_sha256"],z["key_sha256"],z["pairs_sha256"])!=(boxsha,keysha,pairsha):
        raise ValueError("forged source digest")
    labels=[l for _,_,l in pairs]
    scorer=cipher_encrypt if a=="R" else independent_mds_cipher
    scores=[]
    for left,right,_ in pairs:
        value=scorer(box,keys[:rounds+1],left)^scorer(box,keys[:rounds+1],right)
        scores.append(sum(((value>>(8*byte))&255)==0 for byte in range(4)))
    score=auc_rank(scores,labels)
    shuffled=labels[:]
    random.Random(frozen_seed(f"phase2v-t10-null-v1|{g}|{boxsha}|{a}|{arm}|{d}|{rep}|{rounds}")).shuffle(shuffled)
    null=auc_rank(scores,shuffled)
    p=sum(score>0 for score,l in zip(scores,labels) if l)/128
    n=sum(score>0 for score,l in zip(scores,labels) if not l)/128
    for field,target in (("auc",score),("null_auc",null),("positive_any_zero_byte",p),("negative_any_zero_byte",n)):
        if z[field]!=target:
            raise ValueError("forged panel field "+field)
    return score,null,scores,labels,shuffled

def audit(doc):
    verify_shape(doc)
    verify_mds()
    parents={z["group"]:z for z in doc["parent_boxes"]}
    boxes={(z["group"],z["index"]):z for z in doc["candidate_boxes"]}
    if len(parents)!=12 or len(boxes)!=72 or set(parents)!=set(GROUPS):
        raise ValueError("source identity missing")
    parentsha=set();candsha=set();feature={}
    for g in GROUPS:
        p=new_parent(g)
        fingerprint=sha(bytes(p))
        if fingerprint in parentsha:raise ValueError("duplicate parent")
        parentsha.add(fingerprint)
        met=metric_reference(p)
        if parents[g]["parent_sha256"]!=fingerprint or parents[g]["global_metrics"]!=met:
            raise ValueError("parent metric/hash error")
        for i in range(6):
            box,tr=new_variant(g,i)
            f=sha(bytes(box))
            if f in candsha:raise ValueError("duplicate SBox")
            candsha.add(f)
            sub=boxes[(g,i)]
            descriptor=(early_activity(box,1)+early_activity(box,256))/2
            if (sub["sha256"]!=f or sub["parent_sha256"]!=fingerprint or
                sub["transform"]!=tr or sub["global_metrics"]!=met or
                metric_reference(box)!=met or sub["early_active_bytes"]!=descriptor):
                raise ValueError("candidate metric/feature tampered")
            feature[g,i]=descriptor
    source_set=set();key_set=set()
    for g in GROUPS:
        for arm in ARMS:
            _,ksha=fresh_keys(g,arm)
            if ksha in key_set:raise ValueError("duplicate public key")
            key_set.add(ksha)
        for delta in DELTAS:
            a,aset,ah=fresh_pairs(g,delta,0)
            b,bset,bh=fresh_pairs(g,delta,1)
            if aset&bset or ah==bh or ah in source_set or bh in source_set:
                raise ValueError("source schedule overlap")
            source_set.update((ah,bh))
    rows={(z["group"],z["box_index"],z["architecture"],z["key_arm"],z["delta"],z["replicate"],z["rounds"]):z
          for z in doc["panels"]}
    if len(rows)!=2304:raise ValueError("duplicate panels")
    spot=0
    for key in sorted(rows):
        z=rows[key]
        val,null,scores,labels,shuf=verify_panel(z)
        if z["box_index"] in (0,5) and z["delta"]==1 and z["replicate"]==0:
            if val!=auc_slow(scores,labels) or null!=auc_slow(scores,shuf):
                raise ValueError("AUC independent enumeration disagrees")
            spot+=2
    if (len(parentsha),len(candsha),len(source_set),len(key_set),spot)!=(12,72,48,24,384):
        raise ValueError("source cardinality mismatch")
    groups={z["group"]:z for z in doc["group_reports"]}
    if set(groups)!=set(GROUPS):raise ValueError("group results missing")
    valuesM=[];valuesR=[]
    for g in GROUPS:
        x=[feature[g,i] for i in range(6)]
        ys={}
        for arch in ARCH:
            ys[arch]=[statistics.mean(rows[g,i,arch,arm,d,rep,4]["auc"]
                     for arm in ARMS for d in DELTAS for rep in REPS) for i in range(6)]
        expected=dict(
            predictor_rho_R=rho(x,ys["R"]),predictor_rho_M=rho(x,ys["M"]),
            range_R4_R=max(ys["R"])-min(ys["R"]),range_R4_M=max(ys["M"])-min(ys["M"]),
            mean_auc_R4_R=statistics.mean(ys["R"]),mean_auc_R4_M=statistics.mean(ys["M"]),
            mean_auc_R5_R=statistics.mean(rows[g,i,"R",arm,d,rep,5]["auc"]
                  for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS),
            mean_auc_R5_M=statistics.mean(rows[g,i,"M",arm,d,rep,5]["auc"]
                  for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS))
        gr=groups[g]
        if any(abs(gr[name]-value)>1e-12 for name,value in expected.items()):
            raise ValueError("group score/rho tampering")
        for label,v in (("source_features",x),("candidate_auc_R4_R",ys["R"]),("candidate_auc_R4_M",ys["M"])):
            if len(gr[label])!=6 or any(abs(a-b)>1e-12 for a,b in zip(gr[label],v)):
                raise ValueError("group candidate vector tampering")
        for arm in ARMS:
            target=rho(x,[statistics.mean(rows[g,i,"M",arm,d,rep,4]["auc"]
                     for d in DELTAS for rep in REPS) for i in range(6)])
            if abs(target-gr["key_rho_M"][arm])>1e-12:raise ValueError("key correlation tampered")
        valuesM.append(expected["predictor_rho_M"]);valuesR.append(expected["predictor_rho_R"])
    null=statistics.mean(z["null_auc"] for z in doc["panels"])
    decision=(sum(r<0 for r in valuesM)>=10 and statistics.median(valuesM)<=-.5 and .47<=null<=.53)
    expected_summary=dict(
        preregistered_transport_supported=decision,
        negative_M_group_correlations=sum(r<0 for r in valuesM),
        median_M_group_correlation=statistics.median(valuesM),
        negative_R_group_correlations=sum(r<0 for r in valuesR),
        median_R_group_correlation=statistics.median(valuesR),
        mean_M_R4_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="M" and z["rounds"]==4),
        mean_M_R5_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="M" and z["rounds"]==5),
        mean_R_R4_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R" and z["rounds"]==4),
        mean_R_R5_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R" and z["rounds"]==5),
        mean_shuffled_label_auc=null,
        source_integrity_gates_pass=True,nonzero_MDS_one_byte_basis_checks=1020,
        parents=12,candidates=72,source_schedules=48,key_schedules=24,panels=2304,
        independent_auc_spotchecks=384)
    for field,value in expected_summary.items():
        found=doc["summary"][field]
        if (abs(found-value)>1e-12 if isinstance(value,float) else found!=value):
            raise ValueError("summary tampering "+field)
    return dict(audited_parents=12,audited_boxes=72,audited_panels=2304,
                independent_auc_spotchecks=spot,primary_supported=decision,
                negative_M_groups=sum(x<0 for x in valuesM),
                median_M_group_correlation=statistics.median(valuesM))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    raw=Path(args.report).read_bytes()
    if sha(raw)!=args.expected_sha:raise ValueError("file SHA256 mismatch")
    print(json.dumps(audit(json.loads(raw)),sort_keys=True))
if __name__=="__main__":
    main()
