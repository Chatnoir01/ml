"""Preregistered comparative TPM attacker benchmark. No secure key claims.

All arms share the exact same legitimate Alice/Bob seeds and public inputs
via the fixed TPMProtocol; they have distinct independent attacker seeds.
This is descriptive research, not a proof of cryptographic security.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import statistics
from .sync import TPMProtocol, trial
from .ensemble import ensemble_trial
from .genetic import genetic_trial


@dataclass(frozen=True)
class ComparisonPlan:
    trials: int = 32
    master_seed: int = 782023
    max_steps: int = 8000
    ensemble_size: int = 9
    genetic_population: int = 16

    def protocol(self) -> TPMProtocol:
        p=TPMProtocol(trials=self.trials,master_seed=self.master_seed,max_steps=self.max_steps)
        p.validate()
        if type(self.ensemble_size) is not int or self.ensemble_size < 3 or self.ensemble_size > 101 or self.ensemble_size%2==0:
            raise ValueError("invalid ensemble size")
        if type(self.genetic_population) is not int or not 2<=self.genetic_population<=128:
            raise ValueError("invalid genetic population")
        return p

    def sha256(self) -> str:
        self.protocol()
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True,separators=(",",":")).encode()).hexdigest()


def wilson_interval(success: int,total: int,z: float=1.96) -> tuple[float,float] | None:
    if total == 0:
        return None
    if not (0<=success<=total):
        raise ValueError("invalid numerator")
    p=success/total
    denom=1+z*z/total
    mid=(p+z*z/(2*total))/denom
    half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denom
    return max(0.,mid-half),min(1.,mid+half)


def compare(plan: ComparisonPlan=ComparisonPlan()) -> dict:
    protocol=plan.protocol()
    rows=[]
    for i in range(plan.trials):
        baseline=trial(protocol,trial_index=i)
        ensemble=ensemble_trial(protocol,trial_index=i,attackers=plan.ensemble_size)
        genetic=genetic_trial(protocol,trial_index=i,population=plan.genetic_population)
        # Strong paired-design invariant: identical legitimate parties in
        # all arms, independent attacker implementations only.
        clocks=[baseline["steps_to_sync"],ensemble["steps_to_sync"],genetic["steps_to_sync"]]
        if len(set(clocks)) != 1:
            raise AssertionError("legitimate pair diverged across attack arms")
        baseline_attacks=baseline["attacker_exact_match_at_sync"]
        rows.append({
            "trial_index":i,
            "synchronized":baseline["synchronized"],
            "steps_to_sync":baseline["steps_to_sync"],
            "naive":None if baseline_attacks is None else baseline_attacks["naive"],
            "geometric":None if baseline_attacks is None else baseline_attacks["geometric"],
            "random_flip":None if baseline_attacks is None else baseline_attacks["random_flip"],
            "ensemble":ensemble["at_least_one_attacker_matches"],
            "genetic":genetic["at_least_one_exact_match"],
        })
    observed=[r for r in rows if r["synchronized"]]
    names=("naive","geometric","random_flip","ensemble","genetic")
    attacks={
        name:{
            "exact_match_trials":sum(bool(r[name]) for r in observed),
            "denominator_synchronized":len(observed),
            "rate_conditional_on_sync":sum(bool(r[name]) for r in observed)/len(observed) if observed else None,
            "wilson_95pct_descriptive":wilson_interval(sum(bool(r[name]) for r in observed),len(observed)),
        } for name in names
    }
    return {
        "schema_version":1,
        "kind":"descriptive_tpm_paired_attacker_comparison",
        "plan_sha256":plan.sha256(),
        "protocol_sha256":protocol.sha256(),
        "plan":asdict(plan),
        "synchronized_trials":len(observed),
        "censored_trials":plan.trials-len(observed),
        "median_sync_steps_conditional":statistics.median(r["steps_to_sync"] for r in observed) if observed else None,
        "attack_results":attacks,
        "trial_records":rows,
        "resource_budgets_differ_across_arms":True,
        "not_proof_of_security":True,
        "no_private_weights_or_keys_exported":True,
    }
