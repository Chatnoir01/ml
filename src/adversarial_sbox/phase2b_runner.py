"""Scientific runner for Phase 2B first controlled GA <- Neural Oracle pressure.

The neural arm is the only evolutionary arm whose rank consults the pressure
Oracle. Control and sham remain neural-free during evolution. After all three
arms terminate, a separate blind Oracle block scores each terminal best S-box.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
import hashlib
import json
from pathlib import Path
from statistics import fmean, median
from typing import Any

from .datasets import generate_balanced_pairs, split_dataset
from .evolution import (
    ClassicalMetrics,
    EvolutionConfig,
    HardConstraints,
    evaluate_classical,
    evolve_permutations,
)
from .neural_heterogeneity import ROUND_KEYS, _train_byte_tanh_mlp
from .phase2b import (
    ARCHITECTURE,
    ARM_NAMES,
    BLIND_DATASET_SEEDS,
    BLIND_MODEL_SEEDS,
    BLIND_NEURAL_TRAININGS,
    CLASSICAL_EVALUATIONS_PER_ARM,
    CLASSICAL_EVALUATIONS_TOTAL,
    DEPTH,
    DIFFERENCES,
    EVOLUTION_SEEDS,
    EXPECTED_TEST_SIZE,
    EXPECTED_TRAIN_SIZE,
    EXPECTED_VALIDATION_SIZE,
    GA_CONFIG_KWARGS,
    NEURAL_TRAININGS_TOTAL,
    PAIR_COUNT,
    PANEL_DIGEST_SHA256,
    PRESSURE_DATASET_SEEDS,
    PRESSURE_MODEL_SEEDS,
    PRESSURE_NEURAL_TRAININGS,
    TRAININGS_PER_ORACLE_SCORE,
    build_arm_rank,
    classify_phase2b,
    neural_seed_blocks_disjoint,
    primary_support_checks,
    protected_classical_key,
    sham_pressure_from_fingerprint,
)
from .provenance import fingerprint_sbox
from .spn import ToySPN

SBox = tuple[int, ...]
OracleScorer = Callable[[SBox, str], dict[str, Any]]


def _canonical_without_receipt(payload: dict[str, Any], field: str) -> bytes:
    stripped = {key: value for key, value in payload.items() if key != field}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _with_receipt(payload: dict[str, Any], field: str) -> dict[str, Any]:
    payload[field] = hashlib.sha256(_canonical_without_receipt(payload, field)).hexdigest()
    return payload


def load_frozen_initial_panel() -> tuple[SBox, ...]:
    from .phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256 as COMMITTED_DIGEST

    if COMMITTED_DIGEST != PANEL_DIGEST_SHA256:
        raise RuntimeError("Phase 2B frozen panel digest drift")
    if len(CANDIDATES) != 6:
        raise RuntimeError("Phase 2B requires exactly six frozen initial candidates")
    panel: list[SBox] = []
    for index, candidate in enumerate(CANDIDATES):
        sbox = tuple(int(value) for value in candidate["sbox"])
        metrics = evaluate_classical(sbox)
        checks = {
            "fingerprint": fingerprint_sbox(sbox) == str(candidate["fingerprint"]),
            "differential_uniformity": metrics.differential_uniformity == 8,
            "nonlinearity": metrics.nonlinearity == 100,
            "max_linear_correlation": metrics.max_linear_correlation == 56,
            "algebraic_degree": metrics.algebraic_degree == 7,
            "sac": abs(float(metrics.sac_score) - 0.5) <= 0.05,
            "bijective": len(sbox) == 256 and len(set(sbox)) == 256,
        }
        if not all(checks.values()):
            raise RuntimeError(f"Phase 2B initial candidate {index} revalidation failed: {checks}")
        panel.append(sbox)
    return tuple(panel)


def initial_population_digest() -> str:
    payload = "\n".join(fingerprint_sbox(sbox) for sbox in load_frozen_initial_panel())
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _block_seeds(block: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if block == "pressure":
        return PRESSURE_DATASET_SEEDS, PRESSURE_MODEL_SEEDS
    if block == "blind":
        return BLIND_DATASET_SEEDS, BLIND_MODEL_SEEDS
    raise ValueError(f"unknown Phase 2B Oracle block {block!r}")


def score_oracle(sbox: SBox, block: str) -> dict[str, Any]:
    """Score one S-box under exactly one frozen 16-training Phase-2B block."""

    if not neural_seed_blocks_disjoint():
        raise RuntimeError("Phase 2B pressure/blind neural seeds are not fully fresh")
    dataset_seeds, model_seeds = _block_seeds(block)
    keys = ROUND_KEYS[: DEPTH + 1]
    cipher = ToySPN(sbox, keys)
    if cipher.rounds != DEPTH:
        raise RuntimeError("Phase 2B ToySPN depth drift")

    runs: list[dict[str, Any]] = []
    for difference in DIFFERENCES:
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(dataset_seeds, model_seeds, strict=True)
        ):
            samples = generate_balanced_pairs(
                cipher,
                pair_count=PAIR_COUNT,
                input_difference=int(difference),
                seed=int(dataset_seed),
            )
            train_samples, validation_samples, test_samples = split_dataset(samples)
            if len(train_samples) != EXPECTED_TRAIN_SIZE:
                raise RuntimeError("Phase 2B train-size drift")
            if len(validation_samples) != EXPECTED_VALIDATION_SIZE:
                raise RuntimeError("Phase 2B validation-size drift")
            if len(test_samples) != EXPECTED_TEST_SIZE:
                raise RuntimeError("Phase 2B test-size drift")
            endpoint = _train_byte_tanh_mlp(
                train_samples=train_samples,
                validation_samples=validation_samples,
                test_samples=test_samples,
                model_seed=int(model_seed),
            )
            runs.append(
                {
                    "input_difference": int(difference),
                    "replicate": int(replicate),
                    "dataset_seed": int(dataset_seed),
                    "model_seed": int(model_seed),
                    "train_size": len(train_samples),
                    "validation_size": len(validation_samples),
                    "test_size": len(test_samples),
                    **endpoint,
                }
            )

    if len(runs) != TRAININGS_PER_ORACLE_SCORE:
        raise RuntimeError("Phase 2B Oracle score training-count drift")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2b_oracle_score",
        "block": block,
        "architecture": ARCHITECTURE,
        "depth": DEPTH,
        "differences": list(DIFFERENCES),
        "pair_count": PAIR_COUNT,
        "fingerprint": fingerprint_sbox(sbox),
        "runs": runs,
        "training_count": len(runs),
        "mean_neural_advantage": float(fmean(float(run["neural_advantage"]) for run in runs)),
        "mean_null_advantage": float(fmean(float(run["null_advantage"]) for run in runs)),
    }
    return _with_receipt(payload, "oracle_payload_sha256")


def _verify_oracle_score(payload: dict[str, Any], *, block: str, fingerprint: str) -> None:
    if str(payload.get("block", "")) != block:
        raise ValueError("Phase 2B Oracle block mismatch")
    if str(payload.get("architecture", "")) != ARCHITECTURE or int(payload.get("depth", -1)) != DEPTH:
        raise ValueError("Phase 2B Oracle regime mismatch")
    if list(payload.get("differences", ())) != list(DIFFERENCES):
        raise ValueError("Phase 2B Oracle differences mismatch")
    if int(payload.get("pair_count", -1)) != PAIR_COUNT:
        raise ValueError("Phase 2B Oracle pair-count mismatch")
    if str(payload.get("fingerprint", "")) != fingerprint:
        raise ValueError("Phase 2B Oracle fingerprint mismatch")
    if int(payload.get("training_count", -1)) != TRAININGS_PER_ORACLE_SCORE:
        raise ValueError("Phase 2B Oracle training-count mismatch")
    runs = list(payload.get("runs", ()))
    if len(runs) != TRAININGS_PER_ORACLE_SCORE:
        raise ValueError("Phase 2B Oracle run-list mismatch")
    dataset_seeds, model_seeds = _block_seeds(block)
    expected = [
        (int(difference), int(replicate), int(dataset_seed), int(model_seed))
        for difference in DIFFERENCES
        for replicate, (dataset_seed, model_seed) in enumerate(
            zip(dataset_seeds, model_seeds, strict=True)
        )
    ]
    actual = []
    for run in runs:
        if int(run.get("train_size", -1)) != EXPECTED_TRAIN_SIZE:
            raise ValueError("Phase 2B Oracle train-size mismatch")
        if int(run.get("validation_size", -1)) != EXPECTED_VALIDATION_SIZE:
            raise ValueError("Phase 2B Oracle validation-size mismatch")
        if int(run.get("test_size", -1)) != EXPECTED_TEST_SIZE:
            raise ValueError("Phase 2B Oracle test-size mismatch")
        actual.append(
            (
                int(run["input_difference"]),
                int(run["replicate"]),
                int(run["dataset_seed"]),
                int(run["model_seed"]),
            )
        )
    if actual != expected:
        raise ValueError("Phase 2B Oracle seed/provenance order mismatch")
    expected_receipt = hashlib.sha256(
        _canonical_without_receipt(payload, "oracle_payload_sha256")
    ).hexdigest()
    if str(payload.get("oracle_payload_sha256", "")) != expected_receipt:
        raise ValueError("Phase 2B Oracle receipt mismatch")


def _metrics_dict(metrics: ClassicalMetrics) -> dict[str, Any]:
    return {
        "nonlinearity": int(metrics.nonlinearity),
        "differential_uniformity": int(metrics.differential_uniformity),
        "max_linear_correlation": int(metrics.max_linear_correlation),
        "sac_score": float(metrics.sac_score),
        "algebraic_degree": int(metrics.algebraic_degree),
        "fingerprint": str(metrics.fingerprint),
    }


def _run_arm(
    *,
    arm: str,
    seed: int,
    initial: tuple[SBox, ...],
    scorer: OracleScorer,
) -> tuple[dict[str, Any], SBox]:
    constraints = HardConstraints()
    classical_cache: dict[SBox, ClassicalMetrics] = {}
    pressure_cache: dict[SBox, dict[str, Any]] = {}

    def evaluator(sbox: SBox) -> tuple[float, ...]:
        metrics = classical_cache.get(sbox)
        if metrics is None:
            metrics = evaluate_classical(sbox)
            classical_cache[sbox] = metrics
        if arm == "neural":
            pressure = pressure_cache.get(sbox)
            if pressure is None:
                pressure = scorer(sbox, "pressure")
                _verify_oracle_score(
                    pressure, block="pressure", fingerprint=metrics.fingerprint
                )
                pressure_cache[sbox] = pressure
            intervention_value = float(pressure["mean_neural_advantage"])
        elif arm == "sham":
            intervention_value = sham_pressure_from_fingerprint(metrics.fingerprint)
        else:
            intervention_value = 0.0
        return build_arm_rank(
            metrics,
            constraints,
            arm=arm,
            pressure_value=intervention_value,
        )

    config = EvolutionConfig(seed=int(seed), **GA_CONFIG_KWARGS)
    result = evolve_permutations(evaluator, config, initial_population=initial)
    if result.evaluations != CLASSICAL_EVALUATIONS_PER_ARM:
        raise RuntimeError("Phase 2B classical arm budget drift")
    if len(classical_cache) != CLASSICAL_EVALUATIONS_PER_ARM:
        raise RuntimeError("Phase 2B unique classical evaluation count drift")
    if arm == "neural" and len(pressure_cache) != CLASSICAL_EVALUATIONS_PER_ARM:
        raise RuntimeError("Phase 2B pressure Oracle candidate count drift")
    if arm != "neural" and pressure_cache:
        raise RuntimeError("Phase 2B non-neural arm consulted pressure Oracle")

    terminal_metrics = classical_cache[result.best_sbox]
    initial_best_key = max(
        protected_classical_key(evaluate_classical(candidate), constraints)
        for candidate in initial
    )
    terminal_key = protected_classical_key(terminal_metrics, constraints)
    classical_safety = terminal_key >= initial_best_key
    if not classical_safety:
        raise RuntimeError("Phase 2B terminal protected key regressed below initial panel")

    payload = {
        "arm": arm,
        "classical_evaluations": int(result.evaluations),
        "pressure_oracle_candidate_count": len(pressure_cache),
        "pressure_neural_trainings": len(pressure_cache) * TRAININGS_PER_ORACLE_SCORE,
        "best_fingerprint": terminal_metrics.fingerprint,
        "best_metrics": _metrics_dict(terminal_metrics),
        "best_protected_classical_key": list(terminal_key),
        "best_rank": list(result.best_rank),
        "best_rank_history": [list(rank) for rank in result.best_rank_history],
        "classical_safety_invariant": bool(classical_safety),
        "pressure_scores": [
            pressure_cache[candidate]
            for candidate in sorted(
                pressure_cache, key=lambda item: fingerprint_sbox(item)
            )
        ],
    }
    return payload, result.best_sbox


def run_seed(seed: int, *, oracle_scorer: OracleScorer = score_oracle) -> dict[str, Any]:
    """Run all three matched Phase-2B arms for one preregistered evolution seed."""

    seed = int(seed)
    if seed not in EVOLUTION_SEEDS:
        raise ValueError(f"undeclared Phase 2B evolution seed {seed}")
    if not neural_seed_blocks_disjoint():
        raise RuntimeError("Phase 2B neural seed blocks overlap prior provenance")

    initial = load_frozen_initial_panel()
    digest = initial_population_digest()
    arm_payloads: dict[str, dict[str, Any]] = {}
    terminal_sboxes: dict[str, SBox] = {}

    # All arms receive exactly the same initial population and exactly the same GA
    # RNG seed. Only their frozen secondary intervention differs.
    for arm in ARM_NAMES:
        arm_payload, best_sbox = _run_arm(
            arm=arm,
            seed=seed,
            initial=initial,
            scorer=oracle_scorer,
        )
        arm_payloads[arm] = arm_payload
        terminal_sboxes[arm] = best_sbox

    # Blind scoring occurs only after all evolutionary arms have terminated.
    blind_scores: dict[str, dict[str, Any]] = {}
    for arm in ARM_NAMES:
        score = oracle_scorer(terminal_sboxes[arm], "blind")
        _verify_oracle_score(
            score,
            block="blind",
            fingerprint=arm_payloads[arm]["best_fingerprint"],
        )
        blind_scores[arm] = score
        arm_payloads[arm]["blind_final_score"] = score

    pressure_trainings = sum(
        int(arm_payloads[arm]["pressure_neural_trainings"]) for arm in ARM_NAMES
    )
    blind_trainings = sum(
        int(blind_scores[arm]["training_count"]) for arm in ARM_NAMES
    )
    if pressure_trainings != CLASSICAL_EVALUATIONS_PER_ARM * TRAININGS_PER_ORACLE_SCORE:
        raise RuntimeError("Phase 2B per-seed pressure neural budget drift")
    if blind_trainings != len(ARM_NAMES) * TRAININGS_PER_ORACLE_SCORE:
        raise RuntimeError("Phase 2B per-seed blind neural budget drift")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2b_first_neural_pressure_seed",
        "seed": seed,
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "initial_population_digest_sha256": digest,
        "same_initial_population_all_arms": True,
        "same_ga_seed_all_arms": True,
        "ga_config": dict(GA_CONFIG_KWARGS),
        "arms": arm_payloads,
        "pressure_neural_trainings": pressure_trainings,
        "blind_neural_trainings": blind_trainings,
        "neural_trainings": pressure_trainings + blind_trainings,
        "blind_scoring_after_all_evolution": True,
        "neural_evolutionary_pressure": True,
        "oracle_adapts_from_ga_outcomes": False,
    }
    return _with_receipt(payload, "scientific_payload_sha256")


def _verify_seed_payload(item: dict[str, Any]) -> None:
    seed = int(item.get("seed", -1))
    if seed not in EVOLUTION_SEEDS:
        raise ValueError("Phase 2B aggregate contains undeclared seed")
    if str(item.get("panel_digest_sha256", "")) != PANEL_DIGEST_SHA256:
        raise ValueError("Phase 2B panel digest mismatch")
    if dict(item.get("ga_config", {})) != GA_CONFIG_KWARGS:
        raise ValueError("Phase 2B GA config mismatch")
    if not bool(item.get("same_initial_population_all_arms", False)):
        raise ValueError("Phase 2B initial population pairing failed")
    if not bool(item.get("same_ga_seed_all_arms", False)):
        raise ValueError("Phase 2B GA seed pairing failed")
    if not bool(item.get("blind_scoring_after_all_evolution", False)):
        raise ValueError("Phase 2B blind-score isolation failed")
    if bool(item.get("oracle_adapts_from_ga_outcomes", True)):
        raise ValueError("Phase 2B forbids Oracle adaptation from GA outcomes")
    arms = dict(item.get("arms", {}))
    if tuple(arms) != ARM_NAMES:
        raise ValueError("Phase 2B arm set/order mismatch")
    for arm in ARM_NAMES:
        payload = arms[arm]
        if int(payload.get("classical_evaluations", -1)) != CLASSICAL_EVALUATIONS_PER_ARM:
            raise ValueError("Phase 2B classical budget mismatch")
        if not bool(payload.get("classical_safety_invariant", False)):
            raise ValueError("Phase 2B classical safety invariant failed")
        expected_pressure_candidates = CLASSICAL_EVALUATIONS_PER_ARM if arm == "neural" else 0
        if int(payload.get("pressure_oracle_candidate_count", -1)) != expected_pressure_candidates:
            raise ValueError("Phase 2B pressure Oracle candidate-count mismatch")
        _verify_oracle_score(
            payload["blind_final_score"],
            block="blind",
            fingerprint=str(payload["best_fingerprint"]),
        )
        for score in payload.get("pressure_scores", ()):  # neural arm only
            _verify_oracle_score(
                score,
                block="pressure",
                fingerprint=str(score["fingerprint"]),
            )
    if int(item.get("pressure_neural_trainings", -1)) != (
        CLASSICAL_EVALUATIONS_PER_ARM * TRAININGS_PER_ORACLE_SCORE
    ):
        raise ValueError("Phase 2B per-seed pressure training budget mismatch")
    if int(item.get("blind_neural_trainings", -1)) != (
        len(ARM_NAMES) * TRAININGS_PER_ORACLE_SCORE
    ):
        raise ValueError("Phase 2B per-seed blind training budget mismatch")
    expected_receipt = hashlib.sha256(
        _canonical_without_receipt(item, "scientific_payload_sha256")
    ).hexdigest()
    if str(item.get("scientific_payload_sha256", "")) != expected_receipt:
        raise ValueError("Phase 2B per-seed receipt mismatch")


def aggregate_seed_results(results: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Apply the frozen Phase-2B primary decision rule to five paired seed runs."""

    if len(results) != len(EVOLUTION_SEEDS):
        raise ValueError("Phase 2B aggregation requires exactly five seed results")
    by_seed: dict[int, dict[str, Any]] = {}
    for item in results:
        _verify_seed_payload(item)
        seed = int(item["seed"])
        if seed in by_seed:
            raise ValueError("duplicate Phase 2B seed result")
        by_seed[seed] = item
    if tuple(sorted(by_seed)) != tuple(sorted(EVOLUTION_SEEDS)):
        raise ValueError("Phase 2B aggregate seed set mismatch")

    ordered = [by_seed[seed] for seed in EVOLUTION_SEEDS]
    control_scores = [
        float(item["arms"]["control"]["blind_final_score"]["mean_neural_advantage"])
        for item in ordered
    ]
    neural_scores = [
        float(item["arms"]["neural"]["blind_final_score"]["mean_neural_advantage"])
        for item in ordered
    ]
    sham_scores = [
        float(item["arms"]["sham"]["blind_final_score"]["mean_neural_advantage"])
        for item in ordered
    ]
    paired_deltas = [control - neural for control, neural in zip(control_scores, neural_scores)]
    neural_vs_sham = [sham - neural for sham, neural in zip(sham_scores, neural_scores)]
    control_vs_sham = [sham - control for sham, control in zip(sham_scores, control_scores)]

    total_classical = sum(
        int(item["arms"][arm]["classical_evaluations"])
        for item in ordered
        for arm in ARM_NAMES
    )
    pressure_trainings = sum(int(item["pressure_neural_trainings"]) for item in ordered)
    blind_trainings = sum(int(item["blind_neural_trainings"]) for item in ordered)
    neural_trainings = pressure_trainings + blind_trainings

    prerequisites = {
        "seed_registry_exact_and_disjoint": neural_seed_blocks_disjoint(),
        "evolution_seed_set_exact": tuple(int(item["seed"]) for item in ordered) == EVOLUTION_SEEDS,
        "classical_budget_exact": total_classical == CLASSICAL_EVALUATIONS_TOTAL,
        "pressure_neural_budget_exact": pressure_trainings == PRESSURE_NEURAL_TRAININGS,
        "blind_neural_budget_exact": blind_trainings == BLIND_NEURAL_TRAININGS,
        "total_neural_budget_exact": neural_trainings == NEURAL_TRAININGS_TOTAL,
        "same_initial_population_all_arms": all(
            bool(item["same_initial_population_all_arms"]) for item in ordered
        ),
        "same_ga_seed_all_arms": all(bool(item["same_ga_seed_all_arms"]) for item in ordered),
        "classical_safety_all_arms": all(
            bool(item["arms"][arm]["classical_safety_invariant"])
            for item in ordered
            for arm in ARM_NAMES
        ),
        "blind_isolation": all(bool(item["blind_scoring_after_all_evolution"]) for item in ordered),
        "oracle_not_adaptive": all(not bool(item["oracle_adapts_from_ga_outcomes"]) for item in ordered),
    }
    prerequisites_pass = all(prerequisites.values())
    primary_checks = primary_support_checks(paired_deltas)
    verdict = classify_phase2b(
        prerequisites_pass=prerequisites_pass,
        paired_deltas=paired_deltas,
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "phase2b_first_neural_pressure_aggregate",
        "panel_digest_sha256": PANEL_DIGEST_SHA256,
        "evolution_seeds": list(EVOLUTION_SEEDS),
        "total_classical_evaluations": total_classical,
        "pressure_neural_trainings": pressure_trainings,
        "blind_neural_trainings": blind_trainings,
        "total_neural_trainings": neural_trainings,
        "prerequisite_checks": prerequisites,
        "prerequisites_pass": prerequisites_pass,
        "primary": {
            "blind_control_mean_advantages": control_scores,
            "blind_neural_mean_advantages": neural_scores,
            "paired_control_minus_neural_deltas": paired_deltas,
            "mean_delta": float(fmean(paired_deltas)),
            "median_delta": float(median(paired_deltas)),
            "positive_pair_count": sum(value > 0.0 for value in paired_deltas),
            "checks": primary_checks,
        },
        "secondary": {
            "blind_sham_mean_advantages": sham_scores,
            "paired_sham_minus_neural_deltas": neural_vs_sham,
            "paired_sham_minus_control_deltas": control_vs_sham,
            "mean_sham_minus_neural": float(fmean(neural_vs_sham)),
            "mean_sham_minus_control": float(fmean(control_vs_sham)),
        },
        "per_seed": ordered,
        "verdict": verdict,
        "full_bidirectional_coevolution": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["aggregate_payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def write_json(payload: dict[str, Any], output: Path) -> None:
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
