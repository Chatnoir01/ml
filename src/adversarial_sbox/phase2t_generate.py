"""Phase 2T fresh S-Box generator, replayable classical-only Phase-1O derivative.

Uses the exact established Phase-1O 340-evaluation multi-hotspot proposal
geometry with NEW publicly frozen source seeds. Does not call any neural oracle.
Each seed must be run as a separate classical job; aggregate the first twelve
eligible outputs in order. If 24 seeds yield fewer than 12 EXACT matched-metric
S-Boxes, declare PANEL_INCOMPLETE instead of silently relaxing constraints.

This is a research candidate-generation implementation, not a proof of
independent sample families or of real cryptographic resistance.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
from typing import Any

from .cryptoshield import improved_transparency_order
from .evolution import HardConstraints, evaluate_classical
from .pareto import ITOAwareMetrics, select_nsga2
from .phase1m import (
    POPULATION_SIZE, SHORTLIST_SIZE, PARENT_COUNT, GENERATIONS,
    CLASSICAL_BUDGET, ClassicalEvaluationLedger,
    _initial_population, _population_digest, _ranked_population,
)
from .phase1o import _collect_unique_batch, _proposal_audit_digest
from .phase2t_predict import (
    DESIGN, GENERATING_ALGORITHM, PROSPECTIVE_SEEDS,
    TARGET_CANDIDATES, EXPECTED_CLASSICAL,
    canonical, digest,
)


def _eligible(metrics) -> bool:
    return (
        metrics.nonlinearity,
        metrics.differential_uniformity,
        metrics.max_linear_correlation,
        metrics.algebraic_degree,
    ) == EXPECTED_CLASSICAL and abs(metrics.sac_score - .5) <= .05


def run_seed(seed: int) -> dict[str, Any]:
    """One full 340-evaluation classical run; no neural experiments."""
    if type(seed) is not int or seed not in PROSPECTIVE_SEEDS:
        raise ValueError("unregistered prospective source seed")
    initial = _initial_population(seed)
    initial_digest = _population_digest(initial)
    constraints = HardConstraints()
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    population = list(initial)
    seen_ever = set(initial)
    rng = random.Random(seed)
    ito_cache: dict[tuple[int, ...], ITOAwareMetrics] = {}
    proposals_audit = []
    for candidate in population:
        ledger.evaluate(candidate)

    def with_ito(candidate):
        cached = ito_cache.get(candidate)
        if cached is None:
            metrics = ledger.evaluate(candidate)
            cached = ITOAwareMetrics.from_classical(
                metrics, improved_transparency_order_value=improved_transparency_order(candidate)
            )
            ito_cache[candidate] = cached
        return cached

    for _ in range(GENERATIONS):
        ranked = _ranked_population(population, ledger, constraints)
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        shortlist_ito = tuple(with_ito(candidate) for candidate in shortlist)
        chosen_indices = select_nsga2(shortlist_ito, PARENT_COUNT)
        parents = tuple(shortlist[index] for index in chosen_indices)
        proposals, audit = _collect_unique_batch(parents, rng, seen_ever=seen_ever)
        proposals_audit.extend(audit)
        for candidate in proposals:
            ledger.evaluate(candidate)
        population = _ranked_population(
            [*population,*proposals], ledger, constraints
        )[:POPULATION_SIZE]
    if ledger.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError("Phase-1O-derived exact classical budget drift")
    hits = [(candidate, metric) for candidate, metric in ledger.cache.items()
            if _eligible(metric)]
    # Selection depends ONLY on classical feasibility and a lexical fingerprint.
    # It does not inspect held-out neural labels or Phase 2T prediction scores.
    hits.sort(key=lambda t: t[1].fingerprint)
    common = {
        "seed":seed, "evaluations":ledger.evaluations,
        "initial_population_sha256":initial_digest,
        "proposal_audit_sha256":_proposal_audit_digest(proposals_audit),
        "exact_metric_hits_in_ledger":len(hits),
        "method":"fixed_budget_340_phase1o_multihotspot_classical_only",
        "neural_training_count":0,
    }
    if not hits:
        output = {**common,"status":"ineligible","reason":"no_exact_metric_evaluated"}
    else:
        sbox, metrics = hits[0]
        output = {
            **common,"status":"accepted",
            "fingerprint":metrics.fingerprint,
            "sbox":list(sbox),
            "metrics":{
                "nonlinearity":metrics.nonlinearity,
                "differential_uniformity":metrics.differential_uniformity,
                "max_linear_correlation":metrics.max_linear_correlation,
                "algebraic_degree":metrics.algebraic_degree,
                "sac_score":metrics.sac_score,
            },
        }
    output["source_payload_sha256"] = digest(output)
    return output


def _verify_seed_run(run: dict[str, Any], seed: int) -> None:
    if type(run) is not dict or run.get("seed") != seed:
        raise ValueError("wrong or missing registered seed")
    seal = run.get("source_payload_sha256")
    unsigned = dict(run)
    unsigned.pop("source_payload_sha256",None)
    if seal != digest(unsigned):
        raise ValueError("candidate generation receipt integrity mismatch")
    if run.get("neural_training_count") != 0:
        raise ValueError("neural contamination in generator")
    if run.get("evaluations") != CLASSICAL_BUDGET:
        raise ValueError("incorrect classical evaluation budget")
    if run.get("method") != "fixed_budget_340_phase1o_multihotspot_classical_only":
        raise ValueError("unexpected experiment method")
    if run.get("status") not in ("accepted","ineligible"):
        raise ValueError("unknown candidate status")
    if run["status"] == "accepted" and run.get("exact_metric_hits_in_ledger",0) < 1:
        raise ValueError("accepted result without exact hit")
    if run["status"] == "ineligible" and run.get("exact_metric_hits_in_ledger") != 0:
        raise ValueError("ineligible result while exact hit exists")


def aggregate_attempts(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Accept only contiguous preregistered seed prefix, stopping at 12 successes."""
    if not isinstance(runs,list) or len(runs) < 1 or len(runs) > len(PROSPECTIVE_SEEDS):
        raise ValueError("invalid seed run count")
    if [r.get("seed") for r in runs] != list(PROSPECTIVE_SEEDS[:len(runs)]):
        raise ValueError("source seed ledger reordered or skipped")
    attempts = []
    successful = 0
    for i,run in enumerate(runs):
        _verify_seed_run(run,PROSPECTIVE_SEEDS[i])
        if successful >= TARGET_CANDIDATES:
            raise ValueError("continued generation after panel already complete")
        selected = {
            k:run[k] for k in ("seed","status","evaluations",
                               "initial_population_sha256","proposal_audit_sha256",
                               "source_payload_sha256","exact_metric_hits_in_ledger")
        }
        if run["status"] == "accepted":
            selected.update({
                "fingerprint":run["fingerprint"],
                "sbox":run["sbox"],
            })
            successful+=1
        else:
            selected["reason"]="no_exact_metric_evaluated"
        attempts.append(selected)
    if successful == TARGET_CANDIDATES:
        status = "PANEL_COMPLETE_CLASSICAL_ONLY"
    elif len(runs) == len(PROSPECTIVE_SEEDS):
        status = "PANEL_INCOMPLETE_DO_NOT_RUN_NEURAL"
    else:
        status = "PARTIAL_SEED_LEDGER_DO_NOT_RUN_NEURAL"
    output = {
        "schema_version":1,
        "design":DESIGN,
        "generator":GENERATING_ALGORITHM,
        "attempts":attempts,
        "selected_count":successful,
        "status":status,
        "source":"phase2t_generate_v1_exact_340_evals_per_seed",
        "independence_assumption":"new independent seed populations; audit required",
        "neural_trainings":0,
    }
    output["source_panel_receipt_sha256"] = digest(output)
    return output


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest="mode",required=True)
    seed_p=subs.add_parser("seed")
    seed_p.add_argument("--seed",type=int,required=True)
    seed_p.add_argument("--output",type=Path,required=True)
    agg_p=subs.add_parser("aggregate")
    agg_p.add_argument("--results",type=Path,nargs="+",required=True)
    agg_p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.mode=="seed":
        payload=run_seed(args.seed)
    else:
        payload=aggregate_attempts(
            [json.loads(path.read_text(encoding="utf-8")) for path in args.results]
        )
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(payload,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write("\n")
    print(payload.get("status"),payload.get("source_payload_sha256",
                                         payload.get("source_panel_receipt_sha256")))


if __name__=="__main__":
    main()
