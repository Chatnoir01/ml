"""Development-only Phase-1 configuration sweep.

The seeds in this module are tuning seeds, never confirmatory evidence. The
winner of this sweep must be re-tested on fresh seeds before any Gate-1 claim.
All configurations below use the same 154 unique evaluations per method/seed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import run_benchmark

DEV_SEEDS = (101, 103, 107)

CONFIGURATIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "local_1swap_x3",
        "population_size": 10,
        "generations": 6,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 1,
        "crossover_rate": 0.0,
        "offspring_multiplier": 3,
    },
    {
        "name": "local_3swap_x3",
        "population_size": 10,
        "generations": 6,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 3,
        "crossover_rate": 0.0,
        "offspring_multiplier": 3,
    },
    {
        "name": "local_5swap_x3",
        "population_size": 10,
        "generations": 6,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 5,
        "crossover_rate": 0.0,
        "offspring_multiplier": 3,
    },
    {
        "name": "mixed_3swap_25pct_x3",
        "population_size": 10,
        "generations": 6,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 3,
        "crossover_rate": 0.25,
        "offspring_multiplier": 3,
    },
    {
        "name": "deep_3swap_x2",
        "population_size": 10,
        "generations": 9,
        "elite_count": 2,
        "tournament_size": 3,
        "mutation_swaps": 3,
        "crossover_rate": 0.0,
        "offspring_multiplier": 2,
    },
)


def _selection_key(result: dict[str, Any]) -> tuple[float, ...]:
    summary = result["summary"]
    admissible_margin = float(
        summary["admissible_ga"] - summary["admissible_random"]
    )
    win_margin = float(summary["ga_wins"] - summary["random_wins"])
    nl_margin = float(
        summary["median_nonlinearity_ga"] - summary["median_nonlinearity_random"]
    )
    du_margin = float(
        summary["median_differential_uniformity_random"]
        - summary["median_differential_uniformity_ga"]
    )
    lat_margin = float(
        summary["median_max_linear_correlation_random"]
        - summary["median_max_linear_correlation_ga"]
    )
    return admissible_margin, win_margin, nl_margin, du_margin, lat_margin


def run_sweep() -> dict[str, Any]:
    experiments: list[dict[str, Any]] = []
    for configuration in CONFIGURATIONS:
        params = {key: value for key, value in configuration.items() if key != "name"}
        evidence = run_benchmark(seeds=DEV_SEEDS, **params)
        experiments.append(
            {
                "name": configuration["name"],
                "selection_key": list(_selection_key(evidence)),
                "evidence": evidence,
            }
        )

    selected = max(experiments, key=lambda item: tuple(item["selection_key"]))
    return {
        "schema_version": 2,
        "experiment": "phase1_development_configuration_sweep",
        "scientific_status": "development_only_not_confirmatory",
        "development_seeds": list(DEV_SEEDS),
        "selected_configuration": selected["name"],
        "selected_key": selected["selection_key"],
        "experiments": experiments,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("phase1-tuning.json"))
    args = parser.parse_args()
    result = run_sweep()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    concise = {
        "selected_configuration": result["selected_configuration"],
        "selected_key": result["selected_key"],
        "experiments": [
            {
                "name": item["name"],
                "summary": item["evidence"]["summary"],
            }
            for item in result["experiments"]
        ],
    }
    print(json.dumps(concise, sort_keys=True))


if __name__ == "__main__":
    main()
