"""Physical held-out H isolation contract for Phase 2G.

Synthetic/static only. Pre-H evolution modules must not import or expose the
held-out H seed block. Exact H seeds live in the separate validation-only module.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
import sys

import adversarial_sbox.phase2g as phase2g
import adversarial_sbox.phase2g_arm_runner as arm_runner
import adversarial_sbox.phase2g_checkpoint_adapter as checkpoint_adapter
import adversarial_sbox.phase2g_experiment as experiment
import adversarial_sbox.phase2g_runner as lifecycle_runner
import adversarial_sbox.phase2g_selection as selection
import adversarial_sbox.phase2g_shared_model as shared_model
import adversarial_sbox.phase2g_terminal_freeze as terminal_freeze
from adversarial_sbox.phase2g_validation_seeds import (
    HELDOUT_DATASET_SEEDS,
    HELDOUT_MODEL_SEEDS,
)

VALIDATION_MODULE = "adversarial_sbox.phase2g_validation_seeds"


def _imports_validation_module(module) -> bool:
    tree = ast.parse(inspect.getsource(module))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == VALIDATION_MODULE for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            resolved = node.module or ""
            if resolved.endswith("phase2g_validation_seeds"):
                return True
    return False


def test_pre_h_modules_do_not_import_or_embed_h_seed_values() -> None:
    for module in (
        phase2g,
        arm_runner,
        checkpoint_adapter,
        experiment,
        lifecycle_runner,
        selection,
        shared_model,
        terminal_freeze,
    ):
        source = inspect.getsource(module)
        assert _imports_validation_module(module) is False
        assert "876003" not in source
        assert "886007" not in source

    phase2g_source = inspect.getsource(phase2g)
    assert "HELDOUT_DATASET_SEEDS =" not in phase2g_source
    assert "HELDOUT_MODEL_SEEDS =" not in phase2g_source


def test_importing_pre_h_modules_does_not_load_validation_module() -> None:
    code = """
import sys
import adversarial_sbox.phase2g
import adversarial_sbox.phase2g_arm_runner
import adversarial_sbox.phase2g_checkpoint_adapter
import adversarial_sbox.phase2g_experiment
import adversarial_sbox.phase2g_runner
import adversarial_sbox.phase2g_selection
import adversarial_sbox.phase2g_shared_model
import adversarial_sbox.phase2g_terminal_freeze
assert 'adversarial_sbox.phase2g_validation_seeds' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", code], check=True)


def test_qualification_static_pre_h_list_includes_scientific_cell_composer() -> None:
    workflow = Path(".github/workflows/phase2g-qualification.yml").read_text(encoding="utf-8")
    assert "'adversarial_sbox.phase2g_experiment'," in workflow


def test_exact_h_seed_block_exists_only_in_separate_validation_module() -> None:
    assert HELDOUT_DATASET_SEEDS == (
        876003,
        876017,
        876029,
        876043,
        876057,
        876071,
        876083,
        876099,
    )
    assert HELDOUT_MODEL_SEEDS == (
        886007,
        886019,
        886031,
        886043,
        886061,
        886073,
        886091,
        886103,
    )
