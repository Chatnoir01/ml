"""Prospective multi-scale TPM attacker evaluation, NOT key-security proof.

Three new seed cohorts, 32 sessions each. Nine cooperative Eves versus
nine independent geometric Eves at K=3 and increasing N/L. Both groups
use the same public transcript and have equal observed TPM forward-pass
counts, NOT a guaranteed equal CPU/GPU budget. No real secret/key export.

Everything is frozen before running these cohorts; if tests or outcomes
require changing attack algorithms or seeds, create a new protocol version
instead of quietly editing the preregistration.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import statistics
from typing import Any

from .comparison import wilson_interval
from .cost_audit import _instrument_once
from .ensemble import ensemble_trial
from .heldout import replicated_geometric_trial
from .paired_stats import exact_mcnemar_two_sided
from .sync import TPMProtocol


@dataclass(frozen=True)
class Scale:
    name: str
    n: int
    l: int
    seed: int


SCALES: tuple[Scale, ...] = (
    Scale("small_N8_L2", 8, 2, 25_102_311),
    Scale("medium_N16_L3", 16, 3, 25_102_319),
    Scale("large_N32_L4", 32, 4, 25_102_331),
)

PREREGISTERED_TRIALS_PER_SCALE = 32
PREREGISTERED_MAX_STEPS = 12_000
ATTACKER_CANDIDATES = 9


@dataclass(frozen=True)
class ScalePlan:
    trials_per_scale: int = PREREGISTERED_TRIALS_PER_SCALE
    max_steps: int = PREREGISTERED_MAX_STEPS
    candidates: int = ATTACKER_CANDIDATES

    def validate(self) -> None:
        if (
            type(self.trials_per_scale) is not int or
            not 1 <= self.trials_per_scale <= PREREGISTERED_TRIALS_PER_SCALE or
            type(self.max_steps) is not int or
            not 1 <= self.max_steps <= PREREGISTERED_MAX_STEPS or
            type(self.candidates) is not int or
            self.candidates != ATTACKER_CANDIDATES
        ):
            raise ValueError("invalid multi-scale TPM plan")
        if len({scale.name for scale in SCALES}) != len(SCALES):
            raise AssertionError("duplicate scale names")
        if len({scale.seed for scale in SCALES}) != len(SCALES):
            raise AssertionError("duplicate scale seeds")
        # Check none of the 96 prospective trial RNG roots accidentally
        # overlap the 32-seed pilot or 64-seed confirmation roots.
        for scale in SCALES:
            for index in range(PREREGISTERED_TRIALS_PER_SCALE):
                root = scale.seed + index * 100_003
                if any(root == previous + j * 100_003
                       for previous, count in ((782023, 32), (971023, 64))
                       for j in range(count)):
                    raise ValueError("new cohort overlaps previously viewed seeds")

    def sha256(self) -> str:
        self.validate()
        data = {
            "plan": asdict(self),
            "scales": [asdict(s) for s in SCALES],
            "candidates": ATTACKER_CANDIDATES,
            "contrast": "cooperative9_vs_geometric9",
            "endpoint": "exact_match_at_first_legitimate_sync",
            "p_correction": "Holm_across_three_scales",
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def _protocol(plan: ScalePlan, scale: Scale) -> TPMProtocol:
    plan.validate()
    protocol = TPMProtocol(
        hidden_units=3,
        inputs_per_unit=scale.n,
        synaptic_depth=scale.l,
        master_seed=scale.seed,
        trials=plan.trials_per_scale,
        max_steps=plan.max_steps,
    )
    protocol.validate()
    return protocol


def _pair_trial(plan: ScalePlan, scale: Scale, trial_index: int) -> dict[str, Any]:
    protocol = _protocol(plan, scale)
    if type(trial_index) is not int or not 0 <= trial_index < plan.trials_per_scale:
        raise ValueError("invalid scale trial index")

    coop, coop_cost = _instrument_once(
        lambda: ensemble_trial(
            protocol, trial_index=trial_index, attackers=plan.candidates
        )
    )
    geo, geo_cost = _instrument_once(
        lambda: replicated_geometric_trial(
            protocol, trial_index=trial_index, candidates=plan.candidates
        )
    )
    if coop["steps_to_sync"] != geo["steps_to_sync"]:
        raise AssertionError("legitimate Alice/Bob session diverged between arms")
    if coop["synchronized"] != geo["synchronized"]:
        raise AssertionError("censoring inconsistent between compared arms")
    if coop_cost["honest_evaluations"] != geo_cost["honest_evaluations"]:
        raise AssertionError("legitimate honest computational effort diverged")
    if coop_cost["attacker_evaluations"] != geo_cost["attacker_evaluations"]:
        raise AssertionError("attacker TPM forward evaluations are NOT balanced")
    if coop_cost["attacker_constructions"] != plan.candidates:
        raise AssertionError("unexpected cooperative attacker construction count")
    if geo_cost["attacker_constructions"] != plan.candidates:
        raise AssertionError("unexpected geometric attacker construction count")

    return {
        "trial_index": trial_index,
        "synchronized": coop["synchronized"],
        "steps_to_sync": coop["steps_to_sync"],
        "cooperative_success": coop["at_least_one_attacker_matches"],
        "geometric_success": geo["any_match_at_sync"],
        "cooperative_attacker_forward_evaluations": coop_cost["attacker_evaluations"],
        "geometric_attacker_forward_evaluations": geo_cost["attacker_evaluations"],
        "cooperative_attacker_updates": coop_cost["attacker_updates"],
        "geometric_attacker_updates": geo_cost["attacker_updates"],
        "cooperative_attempted_weight_writes": coop_cost["attacker_attempted_weight_writes"],
        "geometric_attempted_weight_writes": geo_cost["attacker_attempted_weight_writes"],
    }


def _holm_adjust(p: dict[str, float]) -> dict[str, float]:
    if set(p) != {s.name for s in SCALES}:
        raise ValueError("Holm correction requires all three frozen contrasts")
    ordered = sorted(p, key=lambda key: (p[key], key))
    adjusted = {}
    high_water = 0.0
    for index, name in enumerate(ordered):
        high_water = max(high_water, min(1.0, (len(ordered) - index) * p[name]))
        adjusted[name] = high_water
    return adjusted


def run_multiscale(plan: ScalePlan = ScalePlan()) -> dict[str, Any]:
    plan.validate()
    by_scale = {}
    raw_ps: dict[str, float] = {}
    for scale in SCALES:
        protocol = _protocol(plan, scale)
        rows = [_pair_trial(plan, scale, index)
                for index in range(plan.trials_per_scale)]
        observed = [r for r in rows if r["synchronized"]]
        first = sum(bool(r["cooperative_success"]) for r in observed)
        second = sum(bool(r["geometric_success"]) for r in observed)
        both = sum(bool(r["cooperative_success"]) and bool(r["geometric_success"]) for r in observed)
        first_only = sum(bool(r["cooperative_success"]) and not bool(r["geometric_success"]) for r in observed)
        second_only = sum(bool(r["geometric_success"]) and not bool(r["cooperative_success"]) for r in observed)
        neither = len(observed) - both - first_only - second_only
        p = exact_mcnemar_two_sided(first_only, second_only) if observed else None
        if p is not None:
            raw_ps[scale.name] = p

        by_scale[scale.name] = {
            "n": scale.n,
            "l": scale.l,
            "master_seed": scale.seed,
            "protocol_sha256": protocol.sha256(),
            "synchronized_trials": len(observed),
            "censored_trials": plan.trials_per_scale - len(observed),
            "median_steps_conditional": (
                statistics.median(r["steps_to_sync"] for r in observed)
                if observed else None
            ),
            "cooperative9_exact_matches": first,
            "geometric9_exact_matches": second,
            "cooperative9_wilson_95pct": wilson_interval(first, len(observed)),
            "geometric9_wilson_95pct": wilson_interval(second, len(observed)),
            "first_only": first_only,
            "second_only": second_only,
            "both": both,
            "neither": neither,
            "exact_two_sided_mcnemar_p": p,
            "adjusted_holm_p": None,
            "cooperative_minus_geometric_success_rate": (
                (first - second) / len(observed) if observed else None
            ),
            "forward_evaluations_balanced_per_trial": all(
                r["cooperative_attacker_forward_evaluations"] ==
                r["geometric_attacker_forward_evaluations"] for r in rows
            ),
            "trials": rows,
        }
    # Never drop a scale with all-censored trials from the multiplicity
    # family to artificially improve statistical significance. Use p=1.
    adjusted = _holm_adjust({
        name: raw_ps.get(name, 1.0) for name in (s.name for s in SCALES)
    })
    for name in adjusted:
        by_scale[name]["adjusted_holm_p"] = (
            adjusted[name] if by_scale[name]["exact_two_sided_mcnemar_p"] is not None
            else None
        )
    return {
        "schema_version": 1,
        "kind": "prospective_multiscale_neural_tpm_attack_comparison",
        "plan": asdict(plan),
        "plan_sha256": plan.sha256(),
        "prespecified_scales": [asdict(s) for s in SCALES],
        "registered_family": "three paired cooperative9_vs_geometric9 contrasts",
        "scales": by_scale,
        "new_seed_cohorts_disjoint_from_pilot_and_holdout": True,
        "attacker_candidate_counts_matched": True,
        "attacker_forward_evaluations_matched_per_trial": True,
        "CPU_runtime_memory_not_equalized": True,
        "posthoc_scales_or_trial_exclusions_not_permitted": True,
        "all_attackers_observe_public_transcript_only": True,
        "not_a_secure_key_exchange_or_cryptographic_proof": True,
        "no_private_keys_or_weights_exported": True,
    }
