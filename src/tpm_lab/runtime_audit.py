"""Retrospective TPM same-host wall-time benchmark, not cryptographic evidence.

This instrument replays already observed 64 holdout trials. It never
generates a new confirmatory security sample. Timing noise and the
Python interpreter prohibit portable equal-compute security conclusions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gc
import random
import statistics
import time
from typing import Any, Callable

from .ensemble import ensemble_trial
from .genetic import genetic_trial
from .heldout import HoldoutPlan, replicated_geometric_trial

ARMS = ("ensemble9", "geometric9", "genetic16", "geometric16")
CONTRASTS = (("ensemble9", "geometric9"), ("genetic16", "geometric16"))


@dataclass(frozen=True)
class TimingProtocol:
    """Fixed replay cohort and repetitions; not new held-out seeds."""
    first_trials: int = 64
    repeats: int = 2
    order_seed: int = 449901

    def validate(self, plan: HoldoutPlan) -> None:
        plan.validated_protocol()
        if type(self.first_trials) is not int or not 1 <= self.first_trials <= plan.trials:
            raise ValueError("first_trials outside previously observed cohort")
        if type(self.repeats) is not int or not 1 <= self.repeats <= 3:
            raise ValueError("repeats must be 1, 2, or 3")
        if type(self.order_seed) is not int or not 0 <= self.order_seed < 2**32:
            raise ValueError("invalid order randomization seed")


def _score(result: dict[str, Any], arm: str) -> bool | None:
    if arm == "ensemble9":
        return result["at_least_one_attacker_matches"]
    if arm == "genetic16":
        return result["at_least_one_exact_match"]
    return result["any_match_at_sync"]


def run_runtime_audit(
    plan: HoldoutPlan = HoldoutPlan(),
    timing: TimingProtocol = TimingProtocol(),
) -> dict[str, Any]:
    timing.validate(plan)
    protocol = plan.validated_protocol()
    measurements: list[dict[str, Any]] = []
    rng = random.Random(timing.order_seed)

    for trial_index in range(timing.first_trials):
        functions: dict[str, Callable[[], dict[str, Any]]] = {
            "ensemble9": lambda i=trial_index: ensemble_trial(
                protocol, trial_index=i, attackers=plan.ensemble_candidates
            ),
            "geometric9": lambda i=trial_index: replicated_geometric_trial(
                protocol, trial_index=i, candidates=plan.ensemble_candidates
            ),
            "genetic16": lambda i=trial_index: genetic_trial(
                protocol, trial_index=i, population=plan.genetic_candidates
            ),
            "geometric16": lambda i=trial_index: replicated_geometric_trial(
                protocol, trial_index=i, candidates=plan.genetic_candidates
            ),
        }
        per_arm: dict[str, dict[str, Any]] = {}
        baseline_steps: set[int | None] = set()
        for repetition in range(timing.repeats):
            # Randomization is independent of outcomes and varies with
            # repetition, avoiding systematic geometric-first advantages.
            randomized_order = list(ARMS)
            rng.shuffle(randomized_order)
            for arm in randomized_order:
                # Prevent previous trial's unreachable objects from causing
                # a periodic full GC pause inside one competitor's run.
                gc.collect()
                start_ns = time.perf_counter_ns()
                result = functions[arm]()
                elapsed_ns = time.perf_counter_ns() - start_ns
                if elapsed_ns <= 0:
                    raise AssertionError("nonpositive elapsed wall-clock time")
                baseline_steps.add(result["steps_to_sync"])
                metric = per_arm.setdefault(arm, {
                    "success": _score(result, arm),
                    "elapsed_ns": [],
                })
                if metric["success"] != _score(result, arm):
                    raise AssertionError("nondeterministic attacker success")
                metric["elapsed_ns"].append(elapsed_ns)
        if len(baseline_steps) != 1:
            raise AssertionError("legitimate pair synchronization differs")
        for arm in ARMS:
            if len(per_arm[arm]["elapsed_ns"]) != timing.repeats:
                raise AssertionError("not all arm repeats were measured")
        measurements.append({
            "trial_index": trial_index,
            "steps_to_sync": next(iter(baseline_steps)),
            "synchronized": next(iter(baseline_steps)) is not None,
            "arms": per_arm,
        })

    summaries = {}
    for arm in ARMS:
        trial_medians = [
            statistics.median(row["arms"][arm]["elapsed_ns"]) for row in measurements
        ]
        summaries[arm] = {
            "median_per_trial_elapsed_ns": statistics.median(trial_medians),
            "min_per_trial_median_ns": min(trial_medians),
            "max_per_trial_median_ns": max(trial_medians),
            "exact_match_trials": sum(
                bool(row["arms"][arm]["success"])
                for row in measurements if row["synchronized"]
            ),
            "trial_count": timing.first_trials,
            "repeats_per_trial": timing.repeats,
        }

    pairwise = {}
    for first, second in CONTRASTS:
        ratios = [
            statistics.median(row["arms"][first]["elapsed_ns"])
            / statistics.median(row["arms"][second]["elapsed_ns"])
            for row in measurements
        ]
        pairwise[f"{first}_vs_{second}"] = {
            "median_of_paired_wall_time_ratios": statistics.median(ratios),
            "ratios_computed_per_trial": len(ratios),
            "not_equalized_for_algorithmic_work": True,
        }

    return {
        "schema_version": 1,
        "kind": "retrospective_same_runner_wall_time_tpm_attack",
        "holdout_plan_sha256": plan.sha256(),
        "holdout_plan": asdict(plan),
        "timing_protocol": asdict(timing),
        "measurements": measurements,
        "summary": summaries,
        "paired_runtime_ratios": pairwise,
        "cohort_already_observed_not_new_confirmation": True,
        "single_process_sequential_workloads": True,
        "garbage_collection_preceded_each_measurement": True,
        "no_claim_of_equalized_cpu_gpu_or_security": True,
        "no_secret_key_or_private_weights_exported": True,
    }
