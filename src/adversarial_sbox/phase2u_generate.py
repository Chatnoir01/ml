"""Phase 2U: VERSIONED classical-only source search, not a Phase 2T-v1 rerun.

The frozen Phase 2T-v1 design halted on seed 31013 because its strict
multi-hotspot proposal collector exceeded 512 duplicate-only attempts.
This NEW experiment declares an explicit deterministic bounded fallback:
after 32 consecutive no-new-proposal parent rounds, supplement candidates
by unique RNG-chosen transpositions of one of the already-selected parents.

All results use *new* public seeds, distinct source-version IDs and hashes.
No old Phase 2T results can be mixed with this version.
No neural data, training, key recovery or production cryptography.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Sequence

from .cryptoshield import improved_transparency_order
from .evolution import HardConstraints, evaluate_classical
from .pareto import ITOAwareMetrics, select_nsga2
from .phase1m import (
    CLASSICAL_BUDGET, GENERATIONS, POPULATION_SIZE, SHORTLIST_SIZE,
    PARENT_COUNT, PROPOSALS_PER_GENERATION, PROPOSALS_PER_PARENT,
    ClassicalEvaluationLedger, _initial_population,
    _population_digest, _ranked_population,
)
from .phase1o import multihotspot_walsh_swap_proposals
from .provenance import fingerprint_sbox

DESIGN = "phase2u_bounded_unique_fallback_v1"
SOURCE_VERSION = "phase2u_source_v1"
PUBLIC_SEEDS = (
    41003,41011,41017,41027,41039,41047,41051,41057,
    41063,41071,41077,41081,41089,41101,41113,41117,
    41131,41141,41143,41149,41161,41177,41183,41189,
)
TARGET_CANDIDATES = 12
EXPECTED_CLASSICAL = (100, 8, 56, 7)
STALL_THRESHOLD = 32
MAX_FALLBACK_ATTEMPTS = 8192
if len(PUBLIC_SEEDS) != 24 or len(set(PUBLIC_SEEDS)) != 24:
    raise RuntimeError("invalid frozen new-source registry")


class SourceExhausted(RuntimeError):
    pass


def digest(obj: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True, allow_nan=False).encode("ascii")
    ).hexdigest()


def _bounded_unique_batch(
    parents: Sequence[tuple[int, ...]],
    rng: random.Random,
    seen_ever: set[tuple[int, ...]],
) -> tuple[list[tuple[int, ...]], list[dict[str, Any]]]:
    """Reproduce guided search until bounded stagnation, then random-swap rescue.

    Each accepted S-Box is unique across all generations. No fallback uses any
    neural labels or classical FEASIBILITY SCORES to select candidates.
    """
    if not parents or not all(len(p) == 256 and len(set(p)) == 256 for p in parents):
        raise ValueError("invalid frozen parent permutations")
    accepted: list[tuple[int, ...]] = []
    audit: list[dict[str, Any]] = []
    parent_index = 0
    stalled = 0
    while len(accepted) < PROPOSALS_PER_GENERATION and stalled < STALL_THRESHOLD:
        parent = parents[parent_index % len(parents)]
        parent_index += 1
        needed = min(PROPOSALS_PER_PARENT, PROPOSALS_PER_GENERATION - len(accepted))
        batch = multihotspot_walsh_swap_proposals(parent, rng, count=needed)
        added = 0
        for proposal in batch:
            if proposal.sbox in seen_ever:
                continue
            seen_ever.add(proposal.sbox)
            accepted.append(proposal.sbox)
            audit.append({
                "mode": "guided_multihotspot",
                "fingerprint": fingerprint_sbox(proposal.sbox),
                "parent_index": (parent_index - 1) % len(parents),
                "fallback": bool(proposal.fallback),
            })
            added += 1
            if len(accepted) == PROPOSALS_PER_GENERATION:
                break
        stalled = 0 if added else stalled + 1

    # If the guided geometry becomes trapped, switch to a declared,
    # bounded fallback using SAME parent pool and RNG stream.
    attempts = 0
    while len(accepted) < PROPOSALS_PER_GENERATION:
        attempts += 1
        if attempts > MAX_FALLBACK_ATTEMPTS:
            raise SourceExhausted("bounded unique-swap fallback exhausted")
        parent_idx = rng.randrange(len(parents))
        parent = parents[parent_idx]
        a, b = rng.sample(range(256), 2)
        moved = list(parent)
        moved[a], moved[b] = moved[b], moved[a]
        candidate = tuple(moved)
        if candidate in seen_ever:
            continue
        seen_ever.add(candidate)
        accepted.append(candidate)
        audit.append({
            "mode": "bounded_random_swap",
            "fingerprint": fingerprint_sbox(candidate),
            "parent_index": parent_idx,
            "swap_positions": (a, b),
            "fallback": True,
        })
    assert len(accepted) == PROPOSALS_PER_GENERATION
    return accepted, audit


def _eligible(metrics) -> bool:
    return (metrics.nonlinearity, metrics.differential_uniformity,
            metrics.max_linear_correlation, metrics.algebraic_degree) == EXPECTED_CLASSICAL \
        and abs(metrics.sac_score - .5) <= .05


def run_seed(seed: int) -> dict[str, Any]:
    if type(seed) is not int or seed not in PUBLIC_SEEDS:
        raise ValueError("seed not registered for Phase 2U")
    initial = _initial_population(seed)
    rng = random.Random(seed)
    population = list(initial)
    seen_ever = set(initial)
    constraints = HardConstraints()
    ledger = ClassicalEvaluationLedger(evaluate_classical, budget=CLASSICAL_BUDGET)
    for candidate in initial:
        ledger.evaluate(candidate)

    cached_ito: dict[tuple[int,...], ITOAwareMetrics] = {}
    audit: list[dict[str, Any]] = []

    def with_ito(box):
        result = cached_ito.get(box)
        if result is None:
            result = ITOAwareMetrics.from_classical(
                ledger.evaluate(box),
                improved_transparency_order_value=improved_transparency_order(box),
            )
            cached_ito[box] = result
        return result

    failure: str | None = None
    for generation in range(GENERATIONS):
        ranked = _ranked_population(population, ledger, constraints)
        shortlist = tuple(ranked[:SHORTLIST_SIZE])
        chosen = select_nsga2(tuple(with_ito(b) for b in shortlist), PARENT_COUNT)
        parents = tuple(shortlist[i] for i in chosen)
        try:
            new, provenance = _bounded_unique_batch(parents, rng, seen_ever)
        except SourceExhausted:
            failure = "bounded_fallback_exhausted"
            break
        for entry in provenance:
            audit.append({"generation": generation, **entry})
        for box in new:
            ledger.evaluate(box)
        population = _ranked_population([*population, *new], ledger, constraints)[:POPULATION_SIZE]

    matched = [(box,metric) for box,metric in ledger.cache.items() if _eligible(metric)]
    matched.sort(key=lambda x: x[1].fingerprint)

    common: dict[str, Any] = {
        "source_version": SOURCE_VERSION, "design": DESIGN, "seed": seed,
        "classical_evaluations": ledger.evaluations,
        "required_classical_evaluations": CLASSICAL_BUDGET,
        "original_population_sha256": _population_digest(initial),
        "proposal_transcript_sha256": hashlib.sha256(
            json.dumps(audit,sort_keys=True,separators=(",", ":")).encode()
        ).hexdigest(),
        "proposal_count": len(audit),
        "random_swap_fallback_count": sum(x["mode"]=="bounded_random_swap" for x in audit),
        "guided_proposal_count": sum(x["mode"]=="guided_multihotspot" for x in audit),
        "exact_metric_hits": len(matched),
        "new_neural_training_count": 0,
    }
    if failure is not None:
        # A partial-budget source is NOT an eligible, completed seed.
        receipt = {**common, "status": "source_exhausted",
                   "reason": failure}
    elif ledger.evaluations != CLASSICAL_BUDGET:
        raise RuntimeError("unexpected completed classical budget")
    elif not matched:
        receipt = {**common,"status":"ineligible",
                   "reason":"no_exact_metric_evaluated"}
    else:
        box,metric=matched[0]
        receipt = {
            **common, "status":"accepted",
            "fingerprint":metric.fingerprint, "sbox":list(box),
            "metrics":{
                "nonlinearity":metric.nonlinearity,
                "differential_uniformity":metric.differential_uniformity,
                "max_linear_correlation":metric.max_linear_correlation,
                "algebraic_degree":metric.algebraic_degree,
                "sac_score":metric.sac_score,
            },
        }
    receipt["source_payload_sha256"] = digest(receipt)
    return receipt


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    receipt=run_seed(args.seed)
    with args.output.open("x",encoding="utf-8") as out:
        json.dump(receipt,out,sort_keys=True,indent=2,allow_nan=False)
        out.write("\n")
    print("PHASE2U_SOURCE_STATUS="+receipt["status"])
    print("PHASE2U_SOURCE_SHA256="+receipt["source_payload_sha256"])
    if receipt["status"] == "source_exhausted":
        raise SystemExit(2)


if __name__=="__main__":
    main()
