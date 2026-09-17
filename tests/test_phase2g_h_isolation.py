"""RED contract for physical held-out H isolation in Phase 2G.

Synthetic/static only. Pre-H evolution modules must not import or expose the
held-out H seed block. The exact frozen H seeds live in a separate validation
module that can be imported only by the post-freeze validation stage.
"""

from __future__ import annotations

import importlib
import inspect
import sys

import adversarial_sbox.phase2g as phase2g
import adversarial_sbox.phase2g_arm_runner as arm_runner
import adversarial_sbox.phase2g_checkpoint_adapter as checkpoint_adapter
import adversarial_sbox.phase2g_runner as lifecycle_runner
import adversarial_sbox.phase2g_selection as selection
import adversarial_sbox.phase2g_shared_model as shared_model
import adversarial_sbox.phase2g_terminal_freeze as terminal_freeze


VALIDATION_MODULE = "adversarial_sbox.phase2g_validation_seeds"


def test_pre_h_modules_do_not_load_or_reference_validation_seed_module() -> None:
    assert VALIDATION_MODULE not in sys.modules

    for module in (
        phase2g,
        arm_runner,
        checkpoint_adapter,
        lifecycle_runner,
        selection,
        shared_model,
        terminal_freeze,
    ):
        source = inspect.getsource(module)
        assert "phase2g_validation_seeds" not in source
        assert "876003" not in source
        assert "886007" not in source

    phase2g_source = inspect.getsource(phase2g)
    assert "HELDOUT_DATASET_SEEDS" not in phase2g_source
    assert "HELDOUT_MODEL_SEEDS" not in phase2g_source


def test_exact_h_seed_block_exists_only_in_separate_validation_module() -> None:
    validation = importlib.import_module(VALIDATION_MODULE)
    assert validation.HELDOUT_DATASET_SEEDS == (
        876003,
        876017,
        876029,
        876043,
        876057,
        876071,
        876083,
        876099,
    )
    assert validation.HELDOUT_MODEL_SEEDS == (
        886007,
        886019,
        886031,
        886043,
        886061,
        886073,
        886091,
        886103,
    )
