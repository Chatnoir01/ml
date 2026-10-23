"""Independent TPM majority-flipping ensemble attack; research only.

The attackers receive public stimuli and public parities, never Alice's
weights. This is a simplified cooperative heuristic, not a published
attack's validated implementation and not evidence of key security.
"""
from __future__ import annotations
import random
from .sync import TPM, TPMProtocol, _signal


def ensemble_trial(protocol: TPMProtocol, *, trial_index: int, attackers: int = 9) -> dict:
    protocol.validate()
    if type(attackers) is not int or attackers < 3 or attackers > 101 or attackers % 2 == 0:
        raise ValueError("odd attacker ensemble size must be in [3,101]")
    if type(trial_index) is not int or not 0 <= trial_index < protocol.trials:
        raise ValueError("invalid trial index")
    root = protocol.master_seed + trial_index * 100_003
    public = random.Random(root + 1)
    alice = TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 10))
    bob = TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 20))
    eves = [TPM(k=protocol.hidden_units,n=protocol.inputs_per_unit,l=protocol.synaptic_depth,rng=random.Random(root + 1000 + i)) for i in range(attackers)]
    synchronized_at = None
    exact_matches = None
    for step in range(1,protocol.max_steps+1):
        signal = _signal(public,protocol.hidden_units,protocol.inputs_per_unit)
        ta,ha,_ = alice.evaluate(signal)
        tb,hb,_ = bob.evaluate(signal)
        if ta == tb:
            observations = [e.evaluate(signal) for e in eves]
            # Majority vote of candidate hidden-unit configurations among
            # Eves whose public parity disagrees with Alice. Tie-break
            # lexicographically for deterministic reproducibility.
            proposals = []
            for tau,hidden,fields in observations:
                candidate = list(hidden)
                if tau != ta:
                    index = min(range(protocol.hidden_units),key=lambda i:(abs(fields[i]),i))
                    candidate[index] *= -1
                proposals.append(tuple(candidate))
            majority = max(set(proposals),key=lambda x:(proposals.count(x),x))
            alice.update(signal,ta,ha)
            bob.update(signal,tb,hb)
            for eve,(tau,hidden,fields),proposal in zip(eves,observations,proposals):
                # Independent fallback if the collective hidden configuration
                # has incompatible parity; majority only when consistent.
                target = majority if _parity(majority)==ta else proposal
                eve.update(signal,ta,target)
        if alice.weights == bob.weights:
            synchronized_at = step
            exact_matches = sum(e.weights == alice.weights for e in eves)
            break
    return {
        "trial_index":trial_index,
        "ensemble_size":attackers,
        "synchronized":synchronized_at is not None,
        "steps_to_sync":synchronized_at,
        "exact_attackers_at_sync":exact_matches,
        "at_least_one_attacker_matches":None if exact_matches is None else exact_matches>0,
        "no_secret_key_exported":True,
        "not_a_security_proof":True,
    }


def _parity(hidden: tuple[int,...]) -> int:
    out=1
    for v in hidden:
        out*=v
    return out


def ensemble_study(protocol: TPMProtocol = TPMProtocol(), *, attackers: int = 9) -> dict:
    records=[ensemble_trial(protocol,trial_index=i,attackers=attackers) for i in range(protocol.trials)]
    synced=[r for r in records if r["synchronized"]]
    return {
        "protocol_sha256":protocol.sha256(),
        "ensemble_size":attackers,
        "trials":records,
        "synchronized_trials":len(synced),
        "at_least_one_exact_match_at_sync":sum(r["at_least_one_attacker_matches"] for r in synced),
        "attacker_denominator":len(synced),
        "no_secure_key_generated":True,
        "research_only":True,
    }
