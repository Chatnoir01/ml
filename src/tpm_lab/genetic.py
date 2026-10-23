"""Bounded branching/genetic-style TPM attacker: research only.

This is a *heuristic* beam of candidate private weights, not a validated
reproduction of the literature's genetic attack or secure key agreement.
The attacker receives public stimulus/parity only, not Alice/Bob weights.
"""
from __future__ import annotations

import random
from .sync import TPM, TPMProtocol, _signal


def _clone(source: TPM) -> TPM:
    candidate = TPM(k=source.k,n=source.n,l=source.l,rng=random.Random(0))
    candidate.weights = [row.copy() for row in source.weights]
    return candidate


def genetic_trial(protocol: TPMProtocol, *, trial_index: int, population: int = 16) -> dict:
    protocol.validate()
    if type(population) is not int or not 2 <= population <= 128:
        raise ValueError("population must be integer in [2,128]")
    if type(trial_index) is not int or not 0 <= trial_index < protocol.trials:
        raise ValueError("invalid trial index")
    root = protocol.master_seed + trial_index * 100_003
    public = random.Random(root + 1)
    alice = TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 10))
    bob = TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 20))
    attackers = [TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 3000 + i)) for i in range(population)]
    rng = random.Random(root + 4000)
    synchronized_at = None
    exact_matches = None
    for step in range(1,protocol.max_steps+1):
        stimulus = _signal(public,protocol.hidden_units,protocol.inputs_per_unit)
        tau_a,hidden_a,_ = alice.evaluate(stimulus)
        tau_b,hidden_b,_ = bob.evaluate(stimulus)
        if tau_a == tau_b:
            alice.update(stimulus,tau_a,hidden_a)
            bob.update(stimulus,tau_b,hidden_b)
            candidates = []
            for eve in attackers:
                tau_e,hidden_e,fields_e = eve.evaluate(stimulus)
                # Enumerate every single hidden-unit flip compatible with
                # public parity, plus unmodified configuration when valid.
                configs = [hidden_e] if tau_e == tau_a else [
                    tuple(-value if i==j else value for i,value in enumerate(hidden_e))
                    for j in range(protocol.hidden_units)
                ]
                for cfg in configs:
                    child = _clone(eve)
                    child.update(stimulus,tau_a,cfg)
                    # Score ONLY public agreement and local field margins.
                    # Do not score against Alice's hidden/private state.
                    score = sum(abs(v) for v in fields_e)
                    candidates.append((score,rng.random(),child))
            # Bounded population resampling. Random tie break is seeded.
            candidates.sort(key=lambda item:(item[0],item[1]),reverse=True)
            attackers = [item[2] for item in candidates[:population]]
        if alice.weights == bob.weights:
            synchronized_at = step
            exact_matches = sum(e.weights == alice.weights for e in attackers)
            break
    return {
        "trial_index":trial_index,
        "population":population,
        "synchronized":synchronized_at is not None,
        "steps_to_sync":synchronized_at,
        "exact_candidates_at_sync":exact_matches,
        "at_least_one_exact_match":None if exact_matches is None else exact_matches>0,
        "no_private_weights_exported":True,
        "not_a_cryptographic_security_claim":True,
    }


def genetic_study(protocol: TPMProtocol = TPMProtocol(), *, population: int = 16) -> dict:
    results=[genetic_trial(protocol,trial_index=i,population=population) for i in range(protocol.trials)]
    observed=[r for r in results if r["synchronized"]]
    return {
        "protocol_sha256":protocol.sha256(),
        "population":population,
        "trials":results,
        "legitimate_sync_count":len(observed),
        "censored_count":len(results)-len(observed),
        "attacker_any_exact_match_at_sync":sum(r["at_least_one_exact_match"] for r in observed),
        "attacker_denominator":len(observed),
        "not_secure_key_exchange":True,
    }
