"""Independent auditor for preregistered Phase2V-T11.

No import from the primary experiment, original ToySPN implementation or metric
implementation. Reconstructs 72 SBoxes/metrics, 48 pair schedules, 24 keys,
2304 paired ciphertext AUCs, permutations, all group endpoints and decision.
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

GROUPS=tuple(907011+61*i for i in range(12))
DELTAS=(1,256)
ARMS=("K0","K1")
ROUNDS=(4,5)
REPS=(0,1)
ARCH=("R11","R7")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def frozen_seed(data):
    return int.from_bytes(hashlib.sha256(data.encode("ascii")).digest(),"big")

def new_parent(group):
    values=list(range(256))
    random.Random(frozen_seed(f"phase2v-t11-parent-v1|{group}")).shuffle(values)
    return values


def new_variant(group,index):
    parent=new_parent(group)
    rng=random.Random(frozen_seed(f"phase2v-t11-variant-v1|{group}|{index}"))
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
        digest=hashlib.sha256(f"phase2v-t11-key-v1|{group}|{arm}|{i}".encode("ascii")).digest()
        keys.append(int.from_bytes(digest[:4],"big"))
    return keys,sha(b"".join(k.to_bytes(4,"big") for k in keys))

def fresh_pairs(group,delta,rep):
    r=random.Random(frozen_seed(f"phase2v-t11-pairs-v1|{group}|{delta}|{rep}"))
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


def rot7_encrypt(box,keys,plaintext):
    state=plaintext
    for key_index in range(len(keys)-1):
        state^=keys[key_index]
        state=sum(box[(state>>(8*i))&255]<<(8*i) for i in range(4))
        if key_index<len(keys)-2:
            state=((state<<7)|(state>>25))&0xffffffff
    return state^keys[-1]

def early_rot(box,delta,rot):
    lane=0 if delta==1 else 1
    active=0
    for x in range(256):
        d=(box[x]^box[x^1])<<(lane*8)
        v=((d<<rot)|(d>>(32-rot)))&0xffffffff
        active+=sum(bool((v>>(8*i))&255) for i in range(4))
    return active/256

def ddt1_baselines(box):
    row=[0]*256
    for x in range(256):
        row[box[x]^box[x^1]]+=1
    if sum(row)!=256:raise ValueError("bad differential row")
    return sum(c*c for c in row)/(256*256),max(row)/256

def independent_features(box):
    collision,maxrow=ddt1_baselines(box)
    return dict(
        f7=(early_rot(box,1,7)+early_rot(box,256,7))/2,
        f11=(early_rot(box,1,11)+early_rot(box,256,11))/2,
        d1collision=collision,
        d1maximum=maxrow)

def verify_shape(doc):
    if doc.get("study")!="phase2v-t11-rotation7-controls-v1":
        raise ValueError("wrong study")
    if doc.get("source_main_sha")!="b03da1d95e98709869d007571de4f8bbce234a1b":
        raise ValueError("wrong source")
    if doc.get("preregistration_commit")!="207331148f05689f288d6b510e524db8668d41b2":
        raise ValueError("wrong original protocol")
    if tuple(doc.get("groups",[]))!=GROUPS or tuple(doc.get("input_differences",[]))!=DELTAS or tuple(doc.get("architectures",[]))!=ARCH:
        raise ValueError("unregistered groups, deltas or architectures")
    rows=doc.get("panels",[])
    expected={(g,i,a,arm,d,rep,r) for g in GROUPS for i in range(6) for a in ARCH
        for arm in ARMS for d in DELTAS for rep in REPS for r in ROUNDS}
    actual={(z["group"],z["box_index"],z["architecture"],z["key_arm"],
             z["delta"],z["replicate"],z["rounds"]) for z in rows}
    if len(rows)!=2304 or actual!=expected or len(doc.get("candidate_boxes",[]))!=72 or len(doc.get("parent_boxes",[]))!=12 or len(doc.get("group_reports",[]))!=12:
        raise ValueError("missing/duplicate test panel or source")
    if {(z["group"],z["index"]) for z in doc["candidate_boxes"]}!={(g,i) for g in GROUPS for i in range(6)}:
        raise ValueError("wrong SBox registry")

def verify_panel(z):
    g=z["group"];i=z["box_index"];a=z["architecture"];arm=z["key_arm"]
    d=z["delta"];rep=z["replicate"];rounds=z["rounds"]
    box,_=new_variant(g,i)
    boxsha=sha(bytes(box))
    keys,keysha=fresh_keys(g,arm)
    pairs,seen,pairsha=fresh_pairs(g,d,rep)
    if (z["box_sha256"],z["key_sha256"],z["pairs_sha256"])!=(boxsha,keysha,pairsha):
        raise ValueError("forged panel fingerprint")
    labels=[label for _,_,label in pairs]
    encrypt=cipher_encrypt if a=="R11" else rot7_encrypt
    scores=[]
    for left,right,_ in pairs:
        value=encrypt(box,keys[:rounds+1],left)^encrypt(box,keys[:rounds+1],right)
        scores.append(sum(((value>>(8*j))&255)==0 for j in range(4)))
    auc=auc_rank(scores,labels)
    control=labels[:]
    random.Random(frozen_seed(f"phase2v-t11-null-v1|{g}|{boxsha}|{a}|{arm}|{d}|{rep}|{rounds}")).shuffle(control)
    null=auc_rank(scores,control)
    pos=sum(s>0 for s,label in zip(scores,labels) if label==1)/128
    neg=sum(s>0 for s,label in zip(scores,labels) if label==0)/128
    for name,val in (("auc",auc),("null_auc",null),("positive_any_zero_byte",pos),("negative_any_zero_byte",neg)):
        if z[name]!=val:raise ValueError("forged panel field "+name)
    return auc,null,scores,labels,control

def audit(doc):
    verify_shape(doc)
    parents={z["group"]:z for z in doc["parent_boxes"]}
    boxes={(z["group"],z["index"]):z for z in doc["candidate_boxes"]}
    if len(parents)!=12 or len(boxes)!=72 or set(parents)!=set(GROUPS):
        raise ValueError("source registry altered")
    parentsha=set();boxsha=set();features={}
    for g in GROUPS:
        par=new_parent(g)
        sha_parent=sha(bytes(par))
        if sha_parent in parentsha:raise ValueError("duplicate parent")
        parentsha.add(sha_parent)
        metrics=metric_reference(par)
        if metrics is None:raise ValueError("nonbijective parent")
        if parents[g]["parent_sha256"]!=sha_parent or parents[g]["global_metrics"]!=metrics:
            raise ValueError("parent metric or identity changed")
        for i in range(6):
            box,trans=new_variant(g,i)
            fingerprint=sha(bytes(box))
            if fingerprint in boxsha:raise ValueError("duplicate candidate")
            boxsha.add(fingerprint)
            sources=independent_features(box)
            row=boxes[(g,i)]
            if (row["sha256"]!=fingerprint or row["parent_sha256"]!=sha_parent or
                row["transform"]!=trans or row["global_metrics"]!=metrics or
                row["source_predictors"]!=sources or metric_reference(box)!=metrics):
                raise ValueError("candidate metric, transform or feature altered")
            features[g,i]=sources
    source_set=set();key_set=set()
    for g in GROUPS:
        for arm in ARMS:
            _,fingerprint=fresh_keys(g,arm)
            if fingerprint in key_set:raise ValueError("duplicate public key schedule")
            key_set.add(fingerprint)
        for d in DELTAS:
            _,used0,sha0=fresh_pairs(g,d,0)
            _,used1,sha1=fresh_pairs(g,d,1)
            if used0&used1 or sha0 in source_set or sha1 in source_set or sha0==sha1:
                raise ValueError("pair source reuse")
            source_set.update((sha0,sha1))
    cells={(z["group"],z["box_index"],z["architecture"],z["key_arm"],z["delta"],z["replicate"],z["rounds"]):z
           for z in doc["panels"]}
    if len(cells)!=2304:raise ValueError("duplicate panels")
    independent_controls=0
    for key in sorted(cells):
        z=cells[key]
        auc,null,scores,labels,control=verify_panel(z)
        if z["box_index"] in (0,5) and z["delta"]==1 and z["replicate"]==0:
            if auc!=auc_slow(scores,labels) or null!=auc_slow(scores,control):
                raise ValueError("AUC independent enumeration mismatch")
            independent_controls+=2
    if (len(parentsha),len(boxsha),len(source_set),len(key_set),independent_controls)!=(12,72,48,24,384):
        raise ValueError("source or audit geometry mismatch")
    group_rows={z["group"]:z for z in doc["group_reports"]}
    if set(group_rows)!=set(GROUPS):raise ValueError("group endpoint missing")
    rho7=[]
    for g in GROUPS:
        feats={name:[features[g,i][name] for i in range(6)] for name in ("f7","f11","d1collision","d1maximum")}
        ys={a:[statistics.mean(cells[g,i,a,arm,d,rep,4]["auc"] for arm in ARMS for d in DELTAS for rep in REPS)
               for i in range(6)] for a in ARCH}
        gr=group_rows[g]
        rhos={name:rho(feats[name],ys["R7"]) for name in feats}
        reference={name:rho(feats[name],ys["R11"]) for name in ("f7","f11")}
        keyrhos={arm:rho(feats["f7"],[
            statistics.mean(cells[g,i,"R7",arm,d,rep,4]["auc"] for d in DELTAS for rep in REPS)
            for i in range(6)]) for arm in ARMS}
        rep_rhos={str(rep):rho(feats["f7"],[
            statistics.mean(cells[g,i,"R7",arm,d,rep,4]["auc"] for arm in ARMS for d in DELTAS)
            for i in range(6)]) for rep in REPS}
        expected=dict(rhos_R7=rhos,rhos_R11=reference,key_rho_R7=keyrhos,replicate_rho_R7=rep_rhos,
            auc_range_R7=max(ys["R7"])-min(ys["R7"]),
            feature_range_F7=max(feats["f7"])-min(feats["f7"]),
            mean_R7_R4=statistics.mean(ys["R7"]),mean_R11_R4=statistics.mean(ys["R11"]),
            mean_R7_R5=statistics.mean(cells[g,i,"R7",arm,d,rep,5]["auc"] for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS),
            mean_R11_R5=statistics.mean(cells[g,i,"R11",arm,d,rep,5]["auc"] for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS))
        for name,values in (("features",feats),("candidate_R7_auc",ys["R7"]),("candidate_R11_auc",ys["R11"])):
            if gr[name]!=values and (not isinstance(values,list) or len(gr[name])!=len(values)
                  or any(abs(x-y)>1e-12 for x,y in zip(gr[name],values))):
                raise ValueError("candidate/source descriptor tampering")
        for name,value in expected.items():
            actual=gr[name]
            if isinstance(value,dict):
                if any(abs(actual[k]-v)>1e-12 for k,v in value.items()):raise ValueError("group rank tampered "+name)
            elif abs(actual-value)>1e-12:raise ValueError("group mean tampered "+name)
        rho7.append(rhos["f7"])
    meanR7=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R7" and z["rounds"]==4)
    nul=statistics.mean(z["null_auc"] for z in doc["panels"])
    if meanR7<.55:status="SIGNAL_INSUFFICIENT"
    elif sum(x<0 for x in rho7)>=10 and statistics.median(rho7)<=-.5 and .47<=nul<=.53:status="SUPPORTED"
    else:status="NOT_SUPPORTED"
    expected_summary=dict(
        preregistered_primary_status=status,signal_gate_pass=meanR7>=.55,
        negative_F7_groups=sum(x<0 for x in rho7),median_F7_rho=statistics.median(rho7),
        mean_R7_R4_auc=meanR7,
        mean_R7_R5_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R7" and z["rounds"]==5),
        mean_R11_R4_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R11" and z["rounds"]==4),
        mean_R11_R5_auc=statistics.mean(z["auc"] for z in doc["panels"] if z["architecture"]=="R11" and z["rounds"]==5),
        mean_shuffled_label_auc=nul,
        secondary_median_rhos_R7={name:statistics.median(group_rows[g]["rhos_R7"][name] for g in GROUPS)
             for name in ("f7","f11","d1collision","d1maximum")},
        secondary_directional_counts_R7=dict(
            f7=sum(group_rows[g]["rhos_R7"]["f7"]<0 for g in GROUPS),
            f11=sum(group_rows[g]["rhos_R7"]["f11"]<0 for g in GROUPS),
            d1collision=sum(group_rows[g]["rhos_R7"]["d1collision"]>0 for g in GROUPS),
            d1maximum=sum(group_rows[g]["rhos_R7"]["d1maximum"]>0 for g in GROUPS)),
        source_integrity_pass=True,parents=12,candidates=72,key_schedules=24,source_schedules=48,
        panels=2304,independent_auc_spotchecks=384)
    for name,value in expected_summary.items():
        observed=doc["summary"][name]
        if isinstance(value,dict):
            if any(abs(observed[k]-v)>1e-12 for k,v in value.items()):raise ValueError("summary tampered "+name)
        elif isinstance(value,float):
            if abs(observed-value)>1e-12:raise ValueError("summary tampered "+name)
        elif observed!=value:raise ValueError("summary tampered "+name)
    return dict(audited_parents=12,audited_candidates=72,audited_panels=2304,
        primary_status=status,median_F7_rho=statistics.median(rho7),
        negative_F7_groups=sum(x<0 for x in rho7),mean_R7_auc=meanR7)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    raw=Path(args.report).read_bytes()
    if sha(raw)!=args.expected_sha:raise ValueError("full input SHA256 mismatch")
    print(json.dumps(audit(json.loads(raw)),sort_keys=True))

if __name__=="__main__":
    main()
