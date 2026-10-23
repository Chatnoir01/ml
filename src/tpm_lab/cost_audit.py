"""Retrospective TPM attack workload audit using deterministic counters.

The fixed 64-seed holdout outcomes already exist. This module instruments
their *unchanged* attacker algorithms to compare candidate costs. A matching
candidate count is not the same as equal work and no cost metric implies
real cryptographic secrecy.

During a single-threaded call, only the first two TPMs constructed are
allowed to represent honest Alice/Bob; all subsequent TPMs are attacker
candidates, including candidate clones. This is an explicit implementation
contract checked by tests. Do NOT use this global instrumentation concurrently.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import statistics
from unittest.mock import patch
from typing import Any, Callable

from .sync import TPM
from .heldout import HoldoutPlan, replicated_geometric_trial
from .ensemble import ensemble_trial
from .genetic import genetic_trial

ARM_NAMES = ("ensemble9", "geometric9", "genetic16", "geometric16")


def _instrument_once(action: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], dict[str, int]]:
    """Count actual model method invocations without altering weights."""
    original_init = TPM.__init__
    original_eval = TPM.evaluate
    original_update = TPM.update

    counts = {
        "honest_constructions": 0,
        "attacker_constructions": 0,
        "honest_evaluations": 0,
        "attacker_evaluations": 0,
        "honest_updates": 0,
        "attacker_updates": 0,
        "honest_attempted_weight_writes": 0,
        "attacker_attempted_weight_writes": 0,
    }
    initialized = [0]

    def counted_init(self: TPM, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        is_attacker = initialized[0] >= 2
        initialized[0] += 1
        self._tpm_cost_audit_is_attacker = is_attacker
        prefix = "attacker" if is_attacker else "honest"
        counts[f"{prefix}_constructions"] += 1

    def _role(self: TPM) -> str:
        if not hasattr(self, "_tpm_cost_audit_is_attacker"):
            raise AssertionError("TPM model constructed outside cost-audit scope")
        return "attacker" if self._tpm_cost_audit_is_attacker else "honest"

    def counted_evaluate(self: TPM, signal: tuple) -> tuple:
        counts[f"{_role(self)}_evaluations"] += 1
        return original_eval(self, signal)

    def counted_update(self: TPM, signal: tuple, tau: int, hidden: tuple) -> None:
        prefix = _role(self)
        counts[f"{prefix}_updates"] += 1
        counts[f"{prefix}_attempted_weight_writes"] += sum(v == tau for v in hidden) * self.n
        return original_update(self, signal, tau, hidden)

    with (
        patch.object(TPM, "__init__", counted_init),
        patch.object(TPM, "evaluate", counted_evaluate),
        patch.object(TPM, "update", counted_update),
    ):
        result = action()

    # These algorithms ALWAYS create honest Alice and Bob first.
    if counts["honest_constructions"] != 2 or counts["attacker_constructions"] < 1:
        raise AssertionError("TPM attacker/honest constructor ordering changed")
    if counts["honest_evaluations"] < 2 or counts["honest_updates"] % 2 != 0:
        raise AssertionError("TPM honest model method-call invariants failed")
    return result, counts


def cost_trial(plan: HoldoutPlan, *, trial_index: int) -> dict[str, Any]:
    """Retrospective cost at a reserved, unchanged legitimate trial index."""
    protocol = plan.validated_protocol()
    if type(trial_index) is not int or not 0 <= trial_index < protocol.trials:
        raise ValueError("trial index outside preregistered holdout")
    call_specs = {
        "ensemble9": lambda: ensemble_trial(
            protocol, trial_index=trial_index, attackers=plan.ensemble_candidates
        ),
        "geometric9": lambda: replicated_geometric_trial(
            protocol, trial_index=trial_index, candidates=plan.ensemble_candidates
        ),
        "genetic16": lambda: genetic_trial(
            protocol, trial_index=trial_index, population=plan.genetic_candidates
        ),
        "geometric16": lambda: replicated_geometric_trial(
            protocol, trial_index=trial_index, candidates=plan.genetic_candidates
        ),
    }
    records = {}
    clocks = set()
    for name in ARM_NAMES:
        result, counts = _instrument_once(call_specs[name])
        clocks.add(result["steps_to_sync"])
        # Different simulation routines use different return-field names.
        if name == "ensemble9":
            found = result["at_least_one_attacker_matches"]
        elif name == "genetic16":
            found = result["at_least_one_exact_match"]
        else:
            found = result["any_match_at_sync"]
        records[name] = {
            "at_least_one_exact_state_match": found,
            "work": counts,
        }
    if len(clocks) != 1:
        raise AssertionError("legitimate sync time diverged across attack budgets")
    return {
        "trial_index": trial_index,
        "synchronized": next(iter(clocks)) is not None,
        "steps_to_sync": next(iter(clocks)),
        "arms": records,
    }


def run_cost_audit(
    plan: HoldoutPlan = HoldoutPlan(), *, first_trials: int = 8,
) -> dict[str, Any]:
    """Measure costs for a fixed first-N cohort, NOT additional held-out data.

    This is an explicitly post-hoc workload analysis of the ALREADY
    evaluated holdout seeds. It does not add a new confirmatory sample.
    """
    plan.validated_protocol()
    if type(first_trials) is not int or not 1 <= first_trials <= plan.trials:
        raise ValueError("invalid fixed cost-audit trial count")
    rows = [cost_trial(plan, trial_index=i) for i in range(first_trials)]
    summary = {}
    fields = (
        "attacker_constructions",
        "attacker_evaluations",
        "attacker_updates",
        "attacker_attempted_weight_writes",
    )
    for arm in ARM_NAMES:
        summary[arm] = {
            "median_" + field: statistics.median(row["arms"][arm]["work"][field] for row in rows)
            for field in fields
        }
        summary[arm]["total_" + "attacker_evaluations"] = sum(
            row["arms"][arm]["work"]["attacker_evaluations"] for row in rows
        )
        summary[arm]["exact_state_matches"] = sum(
            bool(row["arms"][arm]["at_least_one_exact_state_match"])
            for row in rows if row["synchronized"]
        )
    return {
        "schema_version": 1,
        "kind": "retrospective_tpm_algorithmic_work_audit",
        "plan_sha256": plan.sha256(),
        "plan": asdict(plan),
        "audited_first_n_trials": first_trials,
        "cohort_already_used_for_holdout": True,
        "trial_records": rows,
        "workload_summary": summary,
        "operations_are_invocation_counts_not_CPU_equivalence": True,
        "models_constructed_first_two_are_alice_bob": True,
        "global_class_patching_single_thread_only": True,
        "no_private_weights_or_keys_exported": True,
        "not_crypto_security_assurance": True,
    }
