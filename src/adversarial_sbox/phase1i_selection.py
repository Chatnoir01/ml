"""Frozen automatic selector for the ten Phase-1I development artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .phase1i import CONFIGURATIONS

DECLARATION_ORDER = tuple(CONFIGURATIONS)


def _eligible(summary: dict[str, Any]) -> bool:
    return (
        int(summary["directed_admissible_runs"]) >= 2
        and int(summary["directed_target_runs"]) >= 2
        and int(summary["directed_admissible_runs"])
        > int(summary["comparator_admissible_runs"])
    )


def selection_key(configuration: str, summary: dict[str, Any]) -> tuple[float, ...]:
    """Return the exact lexicographic key preregistered in Phase-1I."""

    if configuration not in DECLARATION_ORDER:
        raise ValueError(f"unknown Phase-1I configuration: {configuration}")
    first = summary.get("median_first_admissible_evaluation")
    first_score = -float(first) if first is not None else float("-inf")
    order_score = -float(DECLARATION_ORDER.index(configuration))
    return (
        float(summary["directed_admissible_runs"]),
        float(summary["directed_target_runs"]),
        float(summary["directed_admissible_runs"] - summary["comparator_admissible_runs"]),
        float(summary["directed_target_runs"] - summary["comparator_target_runs"]),
        float(summary["directed_wins"] - summary["comparator_wins"]),
        float(summary["median_nonlinearity_directed"]),
        -float(summary["median_du_directed"]),
        -float(summary["median_max_corr_directed"]),
        first_score,
        order_score,
    )


def select_from_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    if len(documents) != len(DECLARATION_ORDER):
        raise ValueError("Phase-1I selection requires exactly ten development documents")

    by_name: dict[str, dict[str, Any]] = {}
    for document in documents:
        if document.get("experiment") != "phase1i_fresh_population_vns_batch_development":
            raise ValueError("unexpected experiment document in Phase-1I selection")
        name = document["configuration"]["name"]
        if name in by_name:
            raise ValueError(f"duplicate Phase-1I configuration document: {name}")
        by_name[name] = document

    if set(by_name) != set(DECLARATION_ORDER):
        missing = sorted(set(DECLARATION_ORDER) - set(by_name))
        extra = sorted(set(by_name) - set(DECLARATION_ORDER))
        raise ValueError(f"Phase-1I configuration set mismatch; missing={missing}, extra={extra}")

    rows = []
    for name in DECLARATION_ORDER:
        summary = by_name[name]["summary"]
        eligible = _eligible(summary)
        key = selection_key(name, summary) if eligible else None
        rows.append(
            {
                "configuration": name,
                "eligible": eligible,
                "selection_key": list(key) if key is not None else None,
                "summary": summary,
            }
        )

    eligible_rows = [row for row in rows if row["eligible"]]
    if not eligible_rows:
        return {
            "schema_version": 1,
            "experiment": "phase1i_frozen_development_selection",
            "selected_configuration": None,
            "development_gate": "fail",
            "confirmation_allowed": False,
            "rows": rows,
        }

    selected = max(
        eligible_rows,
        key=lambda row: tuple(row["selection_key"]),
    )
    return {
        "schema_version": 1,
        "experiment": "phase1i_frozen_development_selection",
        "selected_configuration": selected["configuration"],
        "development_gate": "pass",
        "confirmation_allowed": True,
        "selected_key": selected["selection_key"],
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=Path("phase1i-selection.json"))
    args = parser.parse_args()
    documents = [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs]
    result = select_from_documents(documents)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_configuration": result["selected_configuration"],
        "development_gate": result["development_gate"],
        "confirmation_allowed": result["confirmation_allowed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
