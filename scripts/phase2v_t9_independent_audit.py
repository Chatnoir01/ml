"""Independent auditor for preregistered Phase2V-T9.

No import from the primary experiment, original ToySPN implementation or metric
implementation. Reconstructs 72 SBoxes/metrics, 48 pair schedules, 24 keys,
1152 ciphertext AUCs, permutations, all group endpoints and decision.
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

GROUPS=tuple(905011+53*i for i in range(12))
DELTAS=(1,256)
ARMS=("K0","K1")
ROUNDS=(4,5)
REPS=(0,1)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def frozen_seed(data):
    return int.from_bytes(hashlib.sha256(data.encode("ascii")).digest(),"big")

def new_parent(group):
    values=list(range(256))
    random.Random(frozen_seed(f"phase2v-t9-parent-v1|{group}")).shuffle(values)
    return values


def new_variant(group,index):
    parent=new_parent(group)
    rng=random.Random(frozen_seed(f"phase2v-t9-variant-v1|{group}|{index}"))
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
        digest=hashlib.sha256(f"phase2v-t9-key-v1|{group}|{arm}|{i}".encode("ascii")).digest()
        keys.append(int.from_bytes(digest[:4],"big"))
    return keys,sha(b"".join(k.to_bytes(4,"big") for k in keys))

def fresh_pairs(group,delta,rep):
    r=random.Random(frozen_seed(f"phase2v-t9-pairs-v1|{group}|{delta}|{rep}"))
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

def verify_shape(report):
    if report.get("study")!="phase2v-t9-cross-parent-prediction-v1":raise ValueError("wrong study")
    if report.get("source_main_sha")!="b03da1d95e98709869d007571de4f8bbce234a1b" or report.get("preregistration_commit")!="7cec70cbcff7ffb4dcb01f39c160867142e25c47":
        raise ValueError("unregistered provenance")
    if tuple(report.get("groups",[]))!=GROUPS or tuple(report.get("input_differences",[]))!=DELTAS:
        raise ValueError("unregistered cohort")
    ps=report.get("panels",[])
    candidates=report.get("candidate_boxes",[])
    grouped=report.get("group_reports",[])
    expected={(g,i,arm,d,rep,r) for g in GROUPS for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS for r in ROUNDS}
    actual={(p["group"],p["box_index"],p["key_arm"],p["delta"],p["replicate"],p["rounds"]) for p in ps}
    if len(ps)!=1152 or actual!=expected or len(candidates)!=72 or len(grouped)!=12 or len(report.get("parent_boxes",[]))!=12:raise ValueError("missing/duplicate test cell")
    boxids={(b["group"],b["index"]) for b in candidates}
    if boxids!={(g,i) for g in GROUPS for i in range(6)}:raise ValueError("S-Box cohort changed")

def check_one_panel(report,entry):
    group=entry["group"];idx=entry["box_index"];arm=entry["key_arm"];delta=entry["delta"];rep=entry["replicate"];rounds=entry["rounds"]
    box,trans=new_variant(group,idx)
    f=sha(bytes(box))
    keys,keysha=fresh_keys(group,arm)
    pairs,_,pairs_sha=fresh_pairs(group,delta,rep)
    if (entry["box_sha256"],entry["key_sha256"],entry["pairs_sha256"])!=(f,keysha,pairs_sha):
        raise ValueError("panel fingerprint mismatch")
    labels=[z for x,y,z in pairs]
    scores=[]
    for x,y,_ in pairs:
        a=cipher_encrypt(box,keys[:rounds+1],x)
        b=cipher_encrypt(box,keys[:rounds+1],y)
        diff=a^b
        scores.append(sum((diff>>(j*8)&255)==0 for j in range(4)))
    result=auc_rank(scores,labels)
    shuffled=labels[:]
    random.Random(frozen_seed(f"phase2v-t9-null-v1|{group}|{f}|{arm}|{delta}|{rep}|{rounds}")).shuffle(shuffled)
    null=auc_rank(scores,shuffled)
    pos_rate=sum(score>0 for score,l in zip(scores,labels) if l)/128
    neg_rate=sum(score>0 for score,l in zip(scores,labels) if not l)/128
    for field,value in (("auc",result),("null_auc",null),("positive_any_zero_byte",pos_rate),("negative_any_zero_byte",neg_rate)):
        if entry[field]!=value:raise ValueError("panel "+field+" mismatch")
    return result,null,scores,labels,shuffled

def audit(report):
    verify_shape(report)
    if report.get("source_reference")!="INDEPENDENT_RANDOM_PERMUTATION_PARENTS":
        raise ValueError("invalid parent source")
    parents={item["group"]:item for item in report["parent_boxes"]}
    if len(parents)!=12 or set(parents)!=set(GROUPS):
        raise ValueError("source parents missing")
    parent_shas=set()
    expected_parent_metrics={}
    for g in GROUPS:
        base=new_parent(g)
        sha_parent=sha(bytes(base))
        if sha_parent in parent_shas:raise ValueError("duplicated parent")
        parent_shas.add(sha_parent)
        source_metrics=metric_reference(base)
        if source_metrics is None:raise ValueError("invalid source parent")
        stored=parents[g]
        if stored["parent_sha256"]!=sha_parent or stored["global_metrics"]!=source_metrics:
            raise ValueError("parent source metric tampered")
        expected_parent_metrics[g]=source_metrics
    candidates={(b["group"],b["index"]):b for b in report["candidate_boxes"]}
    if len(candidates)!=72:raise ValueError("missing candidates")
    found_shas=set()
    descriptors={}
    for g in GROUPS:
        for i in range(6):
            box,trans=new_variant(g,i)
            obj=candidates[(g,i)]
            f=sha(bytes(box))
            if f in found_shas:raise ValueError("duplicated transformed box")
            found_shas.add(f)
            expected=metric_reference(box)
            descriptor=(early_activity(box,1)+early_activity(box,256))/2
            if (obj["sha256"]!=f or obj["transform"]!=trans or
                obj["parent_sha256"]!=parents[g]["parent_sha256"] or
                obj["global_metrics"]!=expected_parent_metrics[g] or
                expected!=expected_parent_metrics[g] or obj["early_active_bytes"]!=descriptor):
                raise ValueError("transformed SBox metric, source or descriptor tampered")
            descriptors[(g,i)]=descriptor
    all_keys=set()
    pairs_seen=set()
    for g in GROUPS:
        for arm in ARMS:
            _, keysha=fresh_keys(g,arm)
            if keysha in all_keys:raise ValueError("duplicate group key")
            all_keys.add(keysha)
        for d in DELTAS:
            a,ua,sa=fresh_pairs(g,d,0)
            b,ub,sb=fresh_pairs(g,d,1)
            if ua & ub:raise ValueError("replicate source reuse")
            if sa in pairs_seen or sb in pairs_seen or sa==sb:raise ValueError("duplicate pair schedule")
            pairs_seen.update((sa,sb))
    cell_rows={(p["group"],p["box_index"],p["key_arm"],p["delta"],p["replicate"],p["rounds"]):p for p in report["panels"]}
    if len(cell_rows)!=1152:raise ValueError("duplicate panel entries")
    verified=0
    auc_controls=0
    for key in sorted(cell_rows):
        entry=cell_rows[key]
        value,null,scores,labels,shuffled=check_one_panel(report,entry)
        if entry["box_index"] in (0,5) and entry["key_arm"]=="K0" and entry["delta"]==1 and entry["replicate"]==0:
            if value!=auc_slow(scores,labels) or null!=auc_slow(scores,shuffled):raise ValueError("rank-vs-pair AUC mismatch")
            auc_controls+=2
        verified+=1
    if (len(found_shas),len(pairs_seen),len(all_keys),verified,auc_controls)!=(72,48,24,1152,96):
        raise ValueError("cohort counts or independent controls invalid")
    reports={g["group"]:g for g in report["group_reports"]}
    if set(reports)!=set(GROUPS):raise ValueError("groups mismatch")
    rhos=[]
    for g in GROUPS:
        rep_a=[];rep_b=[];key_a=[];key_b=[];desc=[];means=[]
        for i in range(6):
            avg_rep={}
            for rep in REPS:
                avg_rep[rep]=statistics.mean(cell_rows[(g,i,arm,d,rep,4)]["auc"] for arm in ARMS for d in DELTAS)
            rep_a.append(avg_rep[0]);rep_b.append(avg_rep[1])
            means.append(statistics.mean(avg_rep.values()))
            key_a.append(statistics.mean(cell_rows[(g,i,"K0",d,rep,4)]["auc"] for d in DELTAS for rep in REPS))
            key_b.append(statistics.mean(cell_rows[(g,i,"K1",d,rep,4)]["auc"] for d in DELTAS for rep in REPS))
            desc.append(descriptors[(g,i)])
        rr=reports[g]
        r4=statistics.mean(means)
        r5=statistics.mean(cell_rows[(g,i,arm,d,rep,5)]["auc"] for i in range(6) for arm in ARMS for d in DELTAS for rep in REPS)
        shuf=means[:]
        random.Random(frozen_seed(f"phase2v-t9-feature-null-v1|{g}")).shuffle(shuf)
        vals=dict(
            replicate_spearman_r4=rho(rep_a,rep_b),
            key_spearman_r4=rho(key_a,key_b),
            early_descriptor_spearman_r4=rho(desc,means),
            feature_null_spearman_r4=rho(desc,shuf),
            arm0_feature_spearman_r4=rho(desc,key_a),
            arm1_feature_spearman_r4=rho(desc,key_b),
            replicate0_feature_spearman_r4=rho(desc,rep_a),
            replicate1_feature_spearman_r4=rho(desc,rep_b),
            mean_auc_r4=r4,mean_auc_r5=r5,
            across_box_auc_r4_range=max(means)-min(means))
        for field,v in vals.items():
            if abs(rr[field]-v)>1e-12:raise ValueError("tampered group "+field)
        for field,vals in (("replicate_a",rep_a),("replicate_b",rep_b),
                           ("source_features",desc),("source_candidate_mean_auc_r4",means)):
            observed=rr[field]
            if len(observed)!=len(vals) or any(abs(a-b)>1e-12 for a,b in zip(observed,vals)):
                raise ValueError("tampered group vectors "+field)
        rhos.append(vals["early_descriptor_spearman_r4"])
    control_mean=statistics.mean(x["null_auc"] for x in report["panels"])
    support=(sum(x<0 for x in rhos)>=10 and statistics.median(rhos)<=-0.50 and 0.47<=control_mean<=0.53)
    summary=report["summary"]
    expected_fields=dict(
        preregistered_directional_supported=support,
        negative_group_predictor_correlations=sum(x<0 for x in rhos),
        median_group_predictor_correlation=statistics.median(rhos),
        median_feature_null_spearman=statistics.median(reports[g]["feature_null_spearman_r4"] for g in GROUPS),
        negative_key_arm0_groups=sum(reports[g]["arm0_feature_spearman_r4"]<0 for g in GROUPS),
        negative_key_arm1_groups=sum(reports[g]["arm1_feature_spearman_r4"]<0 for g in GROUPS),
        group_key_r4_median_spearman=statistics.median(reports[g]["key_spearman_r4"] for g in GROUPS),
        group_early_diffusion_median_spearman=statistics.median(reports[g]["early_descriptor_spearman_r4"] for g in GROUPS),
        mean_r4_auc=statistics.mean(p["auc"] for p in report["panels"] if p["rounds"]==4),
        mean_r5_auc=statistics.mean(p["auc"] for p in report["panels"] if p["rounds"]==5),
        mean_null_auc=control_mean,
        metric_gate_pass=True,parent_sboxes=12,sboxes=72,source_schedules=48,key_schedules=24,
        panels=1152,spotcheck_auc_recomputations=192)
    for key,value in expected_fields.items():
        if isinstance(value,float):
            if abs(summary[key]-value)>1e-12:raise ValueError("tampered summary "+key)
        elif summary[key]!=value:raise ValueError("tampered summary "+key)
    return dict(verified_parents=12,verified_sboxes=72,verified_panels=1152,
                source_schedules=48,metric_equivalence=True,control_checks=auc_controls,
                primary_supported=support,median_predictor_spearman=statistics.median(rhos),
                negative_groups=sum(x<0 for x in rhos))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",required=True)
    ap.add_argument("--expected-sha",required=True)
    args=ap.parse_args()
    raw=Path(args.report).read_bytes()
    if sha(raw)!=args.expected_sha:raise ValueError("report SHA256 mismatch")
    print(json.dumps(audit(json.loads(raw)),sort_keys=True))

if __name__=="__main__":
    main()
