"""Fail-closed static validator for the entire open research PR closure register.

No GitHub credentials, network, source code changes, original evidence updates,
workflows, merges, or user data. Does NOT claim any scientific result.

Usage:
  python scripts/validate_research_portfolio_closure.py \
    research/RESEARCH_PORTFOLIO_CLOSURE_MANIFEST_20261102.json

The exact 38 PR identities are an archived 2026-11-02 snapshot. New PRs
must create an explicit new snapshot version, not silently delete old work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPOSITORY = "Chatnoir01/ml"
EXPECTED_PRS = frozenset((
    25,26,81,120,121,122,123,124,125,126,127,129,131,
    132,133,134,135,136,138,139,140,141,143,144,145,
    146,147,148,149,150,151,152,153,154,155,156,157,158
))
EXPECTED_TRACKS = 15
VALID_PRIORITY = frozenset(("P0", "P1", "P2"))
VALID_STAGES = frozenset((
    "frozen_result_pr_disposition_open",
    "blocked_reproducibility",
    "exploratory_prospective_open",
    "valid_blocked_protocol_retained",
    "prediction_frozen_neural_unrun",
    "experimental_result_audit_open",
    "model_validated_hardware_and_persistence_open",
    "ci_failed_security_gate",
    "prototype_ci_green_security_open",
    "demonstrator_scope_complete",
    "smoke_only_full_experiment_open",
    "governance_reconciliation_open",
))


class RegistryInvalid(ValueError):
    """Registry omitted, misclassified or falsely closed research."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise RegistryInvalid(message)


def _valid_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _valid_string(x) for x in value
    )


def _check_dependency_graph(items: dict[str, dict]) -> None:
    """Acyclic dependency network, with no missing or self prerequisites."""
    state: dict[str, int] = {}

    def visit(name: str) -> None:
        if state.get(name) == 1:
            raise RegistryInvalid(f"dependency cycle at {name}")
        if state.get(name) == 2:
            return
        state[name] = 1
        for dep in items[name]["depends_on"]:
            _require(dep in items, f"unknown workstream dependency {dep!r}")
            _require(dep != name, f"self dependency at {name}")
            visit(dep)
        state[name] = 2

    for name in items:
        visit(name)


def validate_manifest(raw: dict[str, Any]) -> dict[str, Any]:
    _require(type(raw) is dict, "manifest is not an object")
    _require(raw.get("schema_version") == 1, "schema_version must be 1")
    _require(raw.get("repository") == REPOSITORY, "wrong repository")
    _require(raw.get("snapshot_date") == "2026-11-02", "snapshot date changed")
    _require(raw.get("open_pr_count") == len(EXPECTED_PRS), "open PR count drift")
    _require(_valid_string(raw.get("snapshot_scope")), "missing snapshot provenance")

    safeguards = raw.get("review_rules")
    _require(type(safeguards) is dict, "missing review policy")
    _require(safeguards.get("no_merge_from_registry") is True, "registry cannot authorize merges")
    _require(safeguards.get("no_automatic_close_or_delete") is True, "no auto PR closure/deletion")
    _require(safeguards.get("frozen_negative_is_a_result") is True, "do not erase negative results")
    _require(_valid_string(safeguards.get("gate_policy")), "missing fail-closed review gate")
    _require(_valid_string(safeguards.get("authenticity_note")), "missing receipt provenance caution")
    _require(_valid_nonempty_strings(raw.get("frozen_baselines")), "frozen scientific baselines absent")
    _require(_valid_nonempty_strings(raw.get("cross_cutting_critical_path")), "critical path absent")

    stages = raw.get("status_vocabulary")
    _require(isinstance(stages,dict) and set(stages)==VALID_STAGES,
             "status glossary incomplete or altered")

    tracks = raw.get("workstreams")
    _require(isinstance(tracks,list) and len(tracks)==EXPECTED_TRACKS,
             "number of independent workstreams changed")
    ids: dict[str, dict] = {}
    assigned: list[int] = []
    priorities = {"P0":0,"P1":0,"P2":0}
    for item in tracks:
        _require(type(item) is dict, "workstream must be a map")
        name = item.get("id")
        _require(_valid_string(name) and name not in ids,
                 f"duplicate/missing workstream {name!r}")
        ids[name] = item
        _require(_valid_string(item.get("title")), f"{name}: missing title")
        priority = item.get("priority")
        _require(priority in VALID_PRIORITY, f"{name}: invalid priority")
        priorities[priority] += 1
        _require(item.get("stage") in VALID_STAGES,
                 f"{name}: unknown stage")
        _require(_valid_string(item.get("verified")), f"{name}: missing verified facts")
        _require(_valid_string(item.get("not_yet")), f"{name}: missing open limitations")
        for key in ("evidence", "next", "exit"):
            _require(_valid_nonempty_strings(item.get(key)),
                     f"{name}: missing {key} checklist")
        deps = item.get("depends_on")
        _require(type(deps) is list and all(_valid_string(d) for d in deps)
                 and len(set(deps)) == len(deps), f"{name}: bad dependency list")
        _require(_valid_string(item.get("dependency_meaning")),
                 f"{name}: dependency semantics missing")
        prs = item.get("prs")
        _require(isinstance(prs, list) and bool(prs)
                 and all(type(n) is int and n > 0 for n in prs)
                 and len(set(prs))==len(prs), f"{name}: invalid PR IDs")
        links = item.get("pr_links")
        expected_links = [f"https://github.com/{REPOSITORY}/pull/{n}" for n in prs]
        _require(links == expected_links, f"{name}: PR links changed")
        assigned.extend(prs)

    _require(priorities=={"P0":3,"P1":7,"P2":5}, "priority partition changed")
    _require(len(assigned)==len(EXPECTED_PRS), "PR records missing or duplicated")
    _require(len(set(assigned))==len(assigned), "PR allocated to multiple workstreams")
    _require(set(assigned)==EXPECTED_PRS, "frozen PR inventory differs from actual snapshot")
    _require(raw.get("sorted_open_prs")==sorted(EXPECTED_PRS),
             "sorted PR snapshot differs from workstream inventory")
    _check_dependency_graph(ids)

    # Detect the most dangerous scientific-status promotions.
    u=ids.get("phase2u_prospective")
    _require(u is not None and u["stage"]=="prediction_frozen_neural_unrun",
             "Phase 2U promoted to unproven neural confirmation")
    _require("no" in u["not_yet"].lower() or "freeze" in " ".join(u["next"]).lower()
             or "prediction" in u["not_yet"].lower(),
             "Phase 2U missing outstanding neural validation gate")
    _require(ids["phase2t_original_blocked"]["stage"]=="valid_blocked_protocol_retained",
             "original v1 failure must stay separate from new Phase 2U")
    _require(ids["secure_core"]["stage"]=="ci_failed_security_gate",
             "Secure Core CI failures are unresolved")
    _require(ids["phase2_adaptive_repro"]["stage"]=="blocked_reproducibility",
             "GA/NN reproducibility not yet demonstrated")
    for ident in ("fhe_bfv","bb84_simulation"):
        _require(ids[ident]["stage"]=="demonstrator_scope_complete",
                 "do not mistake narrow demos for production security")
    return {
        "repository": REPOSITORY,
        "snapshot_date":raw["snapshot_date"],
        "workstreams":len(tracks),
        "open_prs_accounted_for":len(EXPECTED_PRS),
        "priorities":priorities,
        "registry_policy":"EVIDENCE_GATED_NO_AUTOMATIC_MERGE",
        "neural_2u_confirmation":"NOT_YET_PRODUCED",
        "secure_core_production_gate":"BLOCKED_BY_CI_FAILURE",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest",type=Path)
    args = p.parse_args()
    document=json.loads(args.manifest.read_text(encoding="utf-8"))
    verdict=validate_manifest(document)
    print(json.dumps(verdict,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
