"""RED contract for the dormant/fail-closed Phase 2G scientific workflow.

Static only. This test must never launch Phase 2G science. It requires the future
scientific workflow and CLI to exist in a form that cannot run before the exact
execution marker is added in its own commit.
"""

from __future__ import annotations

from pathlib import Path


MARKER = "research/PHASE2G_EXECUTE.md"
TOKEN = "AUTHORIZED_PHASE2G_ADAPTIVE_COEVOLUTION_EXPERIMENT"
WORKFLOW = Path(".github/workflows/phase2g.yml")
CLI = Path("scripts/run_phase2g.py")


def test_phase2g_scientific_workflow_is_marker_only_and_not_manually_dispatchable() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch" not in workflow
    assert "pull_request:" not in workflow
    assert "research/phase2g-adaptive-coevolution" in workflow
    assert MARKER in workflow
    assert TOKEN in workflow

    # A rerun of an old workflow must still fail closed without the exact marker.
    assert "marker.read_text" in workflow
    assert "git diff-tree" in workflow


def test_phase2g_scientific_workflow_has_exact_stage_order_and_budgets() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for job in ("preflight:", "arm:", "terminal_freeze:", "validation:", "aggregate:"):
        assert job in workflow
    assert "needs: preflight" in workflow
    assert "needs: arm" in workflow
    assert "needs: terminal_freeze" in workflow
    assert "needs: validation" in workflow

    assert "arm: [C, F, A, S]" in workflow
    assert "726011" in workflow and "726113" in workflow
    assert "2304" in workflow
    assert "576" in workflow
    assert "2880" in workflow

    # H validation must appear only after the terminal-freeze job in source order.
    assert workflow.index("terminal_freeze:") < workflow.index("validation:") < workflow.index("aggregate:")


def test_phase2g_cli_exposes_only_frozen_cell_freeze_validation_aggregate_modes() -> None:
    source = CLI.read_text(encoding="utf-8")

    assert "run_phase2g_scientific_cell" in source
    assert "freeze_phase2g_terminals" in source
    assert "validate_frozen_terminals" in source
    assert "aggregate_phase2g_results" in source

    assert "--freeze-arm-files" in source
    assert "--validate-terminal-freeze" in source
    assert "--aggregate-arm-files" in source
    assert "--terminal-freeze" in source
    assert "--heldout-validation" in source

    # Exact H seed values must remain absent from the orchestration layer.
    assert "876003" not in source
    assert "886007" not in source
