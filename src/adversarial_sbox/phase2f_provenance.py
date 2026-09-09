"""Independent pre-Block-X provenance checks for Phase 2F arm artifacts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .cryptoshield import is_bijective, validate_sbox
from .evolution import evaluate_classical
from .phase1m import _initial_population, _population_digest
from .phase2f import ARMS, EVOLUTION_SEEDS
from .provenance import fingerprint_sbox


def arm_provenance_report(run: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute deterministic seed provenance and terminal classical identity."""

    checks = {
        "registered_cell": True,
        "initial_population_digest": True,
        "terminal_sbox_valid": True,
        "terminal_fingerprint": True,
        "terminal_classical_metrics": True,
    }
    try:
        seed = int(run.get("seed", -1))
        arm = str(run.get("arm", ""))
    except (TypeError, ValueError):
        seed, arm = -1, ""
        checks["registered_cell"] = False

    checks["registered_cell"] = bool(seed in EVOLUTION_SEEDS and arm in ARMS)

    try:
        expected_digest = _population_digest(_initial_population(seed))
    except Exception:
        expected_digest = ""
    checks["initial_population_digest"] = bool(
        expected_digest
        and str(run.get("initial_population_digest_sha256", "")) == expected_digest
    )

    try:
        terminal = validate_sbox(run.get("terminal_sbox", ()))
        terminal_valid = bool(is_bijective(terminal))
    except (TypeError, ValueError):
        terminal = tuple()
        terminal_valid = False
    checks["terminal_sbox_valid"] = terminal_valid

    if terminal_valid:
        actual_fp = fingerprint_sbox(terminal)
        checks["terminal_fingerprint"] = str(run.get("terminal_fingerprint", "")) == actual_fp
        try:
            actual = evaluate_classical(terminal)
            claimed = run.get("terminal_classical", {})
            if not isinstance(claimed, Mapping):
                raise TypeError("terminal_classical must be a mapping")
            checks["terminal_classical_metrics"] = bool(
                int(claimed.get("nonlinearity", -1)) == int(actual.nonlinearity)
                and int(claimed.get("differential_uniformity", -1))
                == int(actual.differential_uniformity)
                and int(claimed.get("max_linear_correlation", -1))
                == int(actual.max_linear_correlation)
                and int(claimed.get("algebraic_degree", -1)) == int(actual.algebraic_degree)
                and math.isclose(
                    float(claimed.get("sac_score", float("nan"))),
                    float(actual.sac_score),
                    rel_tol=0.0,
                    abs_tol=1e-15,
                )
                and str(claimed.get("fingerprint", "")) == actual_fp
                and str(actual.fingerprint) == actual_fp
            )
        except (TypeError, ValueError, KeyError):
            checks["terminal_classical_metrics"] = False
    else:
        checks["terminal_fingerprint"] = False
        checks["terminal_classical_metrics"] = False

    return {
        "pass": all(checks.values()),
        "seed": int(seed),
        "arm": arm,
        "checks": checks,
    }


def all_arm_provenance_report(
    arm_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Recompute provenance for every supplied Phase 2F arm cell."""

    cells = [arm_provenance_report(run) for run in arm_results]
    failed = [
        {"seed": int(cell["seed"]), "arm": str(cell["arm"])}
        for cell in cells
        if not bool(cell["pass"])
    ]
    return {
        "pass": bool(cells) and not failed,
        "cell_count": len(cells),
        "failed_cells": failed,
        "cells": cells,
    }
