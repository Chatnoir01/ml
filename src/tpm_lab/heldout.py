"""Predeclared *held-out* TPM attacker comparison on new, disjoint seeds.

Compare geometric 9-vs-cooperative 9 and geometric 16-vs-genetic-style 16.
'Equal candidates' does NOT mean equal CPU work, cryptographic strength,
or independent cryptanalytic validation. No private weights are exported.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import random
import statistics
from typing import Any

from .sync import TPM, TPMProtocol, _signal, trial
from .ensemble import ensemble_trial
from .genetic import genetic_trial
from .comparison import wilson_interval
from .paired_stats import exact_mcnemar_two_sided

CONFIRMATION_MASTER_SEED = 971023
CONFIRMATION_TRIALS = 64
COMPARISONS = (("ensemble9", "geometric9"), ("genetic16", "geometric16"))


@dataclass(frozen=True)
class HoldoutPlan:
    """FROZEN research constants: change only with new protocol + justification."""

    master_seed: int = CONFIRMATION_MASTER_SEED
    trials: int = CONFIRMATION_TRIALS
    max_steps: int = 8000
    ensemble_candidates: int = 9
    genetic_candidates: int = 16
    hidden_units: int = 3
    inputs_per_unit: int = 8
    synaptic_depth: int = 2

    def validated_protocol(self) -> TPMProtocol:
        if (
            type(self.master_seed) is not int or not 0 <= self.master_seed < 2**32
            or type(self.trials) is not int or not 1 <= self.trials <= 100
            or type(self.max_steps) is not int or not 1 <= self.max_steps <= 100_000
            or type(self.ensemble_candidates) is not int or self.ensemble_candidates != 9
            or type(self.genetic_candidates) is not int or self.genetic_candidates != 16
            or self.hidden_units != 3 or self.inputs_per_unit != 8 or self.synaptic_depth != 2
        ):
            raise ValueError("invalid held-out protocol")
        protocol = TPMProtocol(
            master_seed=self.master_seed,
            trials=self.trials,
            max_steps=self.max_steps,
            hidden_units=self.hidden_units,
            inputs_per_unit=self.inputs_per_unit,
            synaptic_depth=self.synaptic_depth,
        )
        protocol.validate()
        return protocol

    def sha256(self) -> str:
        self.validated_protocol()
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def replicated_geometric_trial(
    protocol: TPMProtocol, *, trial_index: int, candidates: int,
) -> dict[str, Any]:
    """Independent geometric Eves observing the *same* legitimate session.

    The scorer can read partner weights **only** to determine the first
    legitimate synchronization and record Eve exact matches. During each
    update all Eve candidates use solely their weights, common public input
    and the public Alice/Bob parity exchange.
    """
    protocol.validate()
    if type(candidates) is not int or not 1 <= candidates <= 128:
        raise ValueError("invalid geometric candidate budget")
    if type(trial_index) is not int or not 0 <= trial_index < protocol.trials:
        raise ValueError("invalid trial index")

    root = protocol.master_seed + trial_index * 100_003
    public = random.Random(root + 1)
    alice = TPM(
        k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth,
        rng=random.Random(root + 10),
    )
    bob = TPM(
        k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth,
        rng=random.Random(root + 20),
    )
    eves = [
        TPM(
            k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth,
            rng=random.Random(root + 5000 + index),
        )
        for index in range(candidates)
    ]

    sync_step = None
    matches_at_sync = None
    for step in range(1, protocol.max_steps + 1):
        signal = _signal(public, protocol.hidden_units, protocol.inputs_per_unit)
        tau_a, hidden_a, _ = alice.evaluate(signal)
        tau_b, hidden_b, _ = bob.evaluate(signal)

        if tau_a == tau_b:
            # Read adversary observations before any party updates, as in
            # the individually frozen geometric attacker in sync.py.
            eve_observations = [eve.evaluate(signal) for eve in eves]
            alice.update(signal, tau_a, hidden_a)
            bob.update(signal, tau_b, hidden_b)
            for eve, (tau_e, sig_e, local_fields) in zip(eves, eve_observations):
                proposal = list(sig_e)
                if tau_e != tau_a:
                    flip = min(
                        range(protocol.hidden_units),
                        key=lambda i: (abs(local_fields[i]), i),
                    )
                    proposal[flip] *= -1
                eve.update(signal, tau_a, tuple(proposal))

        # Privileged simulation-only scoring; NEVER used for attacker updates.
        if alice.weights == bob.weights:
            sync_step = step
            matches_at_sync = sum(eve.weights == alice.weights for eve in eves)
            break

    return {
        "trial_index": trial_index,
        "candidates": candidates,
        "synchronized": sync_step is not None,
        "steps_to_sync": sync_step,
        "exact_matches_at_sync": matches_at_sync,
        "any_match_at_sync": None if matches_at_sync is None else matches_at_sync > 0,
        "research_only_no_key_export": True,
    }


def _holms_two(p_values: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni for two preregistered comparisons."""
    if len(p_values) != len(COMPARISONS):
        raise ValueError("only two predeclared contrasts allowed")
    ranked = sorted(p_values, key=lambda name: (p_values[name], name))
    corrections: dict[str, float] = {}
    running = 0.0
    for rank, name in enumerate(ranked):
        running = max(running, min(1.0, (len(ranked) - rank) * p_values[name]))
        corrections[name] = running
    return corrections


def run_holdout(plan: HoldoutPlan = HoldoutPlan()) -> dict[str, Any]:
    """Execute research comparison; no pilot-seed reuse or hypothesis tuning."""
    protocol = plan.validated_protocol()
    arms = ("ensemble9", "geometric9", "genetic16", "geometric16")
    rows = []
    for i in range(plan.trials):
        baseline = trial(protocol, trial_index=i)
        ensemble = ensemble_trial(
            protocol, trial_index=i, attackers=plan.ensemble_candidates
        )
        geo9 = replicated_geometric_trial(
            protocol, trial_index=i, candidates=plan.ensemble_candidates
        )
        genetic = genetic_trial(
            protocol, trial_index=i, population=plan.genetic_candidates
        )
        geo16 = replicated_geometric_trial(
            protocol, trial_index=i, candidates=plan.genetic_candidates
        )
        clocks = (
            baseline["steps_to_sync"],
            ensemble["steps_to_sync"],
            geo9["steps_to_sync"],
            genetic["steps_to_sync"],
            geo16["steps_to_sync"],
        )
        if len(set(clocks)) != 1:
            raise AssertionError("legitimate Alice/Bob states diverged across arms")
        rows.append({
            "trial_index": i,
            "synchronized": baseline["synchronized"],
            "steps_to_sync": baseline["steps_to_sync"],
            "ensemble9": ensemble["at_least_one_attacker_matches"],
            "geometric9": geo9["any_match_at_sync"],
            "genetic16": genetic["at_least_one_exact_match"],
            "geometric16": geo16["any_match_at_sync"],
        })

    observed = [r for r in rows if r["synchronized"]]
    attack_counts = {
        arm: {
            "exact_match_trials": sum(bool(row[arm]) for row in observed),
            "denominator": len(observed),
            "conditional_rate": (
                sum(bool(row[arm]) for row in observed) / len(observed)
                if observed else None
            ),
            "wilson_95pct_descriptive": wilson_interval(
                sum(bool(row[arm]) for row in observed), len(observed)
            ),
        }
        for arm in arms
    }

    contrasts = {}
    raw_p_values = {}
    for first, second in COMPARISONS:
        both = sum(bool(row[first]) and bool(row[second]) for row in observed)
        first_only = sum(bool(row[first]) and not bool(row[second]) for row in observed)
        second_only = sum(bool(row[second]) and not bool(row[first]) for row in observed)
        neither = len(observed) - both - first_only - second_only
        key = f"{first}_vs_{second}"
        raw = exact_mcnemar_two_sided(first_only, second_only)
        contrasts[key] = {
            "first_only": first_only,
            "second_only": second_only,
            "both": both,
            "neither": neither,
            "paired_difference": (
                (first_only - second_only) / len(observed) if observed else None
            ),
            "exact_mcnemar_two_sided_p": raw if observed else None,
        }
        if observed:
            raw_p_values[key] = raw

    if observed:
        holm = _holms_two(raw_p_values)
        for key, corrected in holm.items():
            contrasts[key]["holm_two_contrasts_adjusted_p"] = corrected
    else:
        for key in contrasts:
            contrasts[key]["holm_two_contrasts_adjusted_p"] = None

    return {
        "schema_version": 1,
        "kind": "tpm_reserved_seeds_candidate_matched_not_compute_equated",
        "plan_sha256": plan.sha256(),
        "protocol_sha256": protocol.sha256(),
        "plan": asdict(plan),
        "registered_contrasts": [list(pair) for pair in COMPARISONS],
        "synchronized_trials": len(observed),
        "censored_trials": plan.trials - len(observed),
        "median_steps_conditional_on_sync": (
            statistics.median(r["steps_to_sync"] for r in observed)
            if observed else None
        ),
        "arms": attack_counts,
        "paired_contrasts": contrasts,
        "trial_records": rows,
        "attack_population_sizes_matched_within_contrast": True,
        "runtime_and_optimizer_operations_not_equated": True,
        "no_cryptographic_security_proven": True,
        "no_private_weights_or_key_exported": True,
    }
