import json
import random

import pytest

from adversarial_sbox.evolution import (
    HardConstraints,
    equivalent_random_budget,
    evaluate_classical,
    random_sbox,
)
from adversarial_sbox.experiment_seeds import (
    PHASE1I_CONFIRM_RESERVED_SEEDS,
    PHASE1I_DEV_SEEDS,
)
from adversarial_sbox.phase1i import (
    ARCHIVE_WIDTH,
    DISCOVERY_BUDGET,
    DISCOVERY_GENERATIONS,
    FULL_GA_GENERATIONS,
    PANEL_MODE,
    PROPOSAL_POOL,
    REPAIR_BUDGET,
    TOTAL_BUDGET,
    aggregate_development_files,
    fresh_plateau_repair,
    ga_config,
    run_development,
)


def test_phase1i_frozen_budget_math():
    assert DISCOVERY_GENERATIONS == 16
    assert FULL_GA_GENERATIONS == 50
    assert DISCOVERY_BUDGET == 532
    assert REPAIR_BUDGET == 1088
    assert TOTAL_BUDGET == 1620
    assert DISCOVERY_BUDGET + REPAIR_BUDGET == TOTAL_BUDGET
    assert equivalent_random_budget(ga_config(seed=0, generations=16)) == 532
    assert equivalent_random_budget(ga_config(seed=0, generations=50)) == 1620


def test_phase1i_frozen_transfer_shape():
    assert ARCHIVE_WIDTH == 8
    assert PROPOSAL_POOL == 96
    assert PANEL_MODE == "ties"
    assert PHASE1I_DEV_SEEDS == (1709, 1721, 1723, 1733, 1741)
    assert len(PHASE1I_CONFIRM_RESERVED_SEEDS) == 9
    assert set(PHASE1I_DEV_SEEDS).isdisjoint(PHASE1I_CONFIRM_RESERVED_SEEDS)


def test_phase1i_development_rejects_confirmation_seed_before_execution():
    with pytest.raises(ValueError, match="confirmation seeds"):
        run_development(seeds=(PHASE1I_CONFIRM_RESERVED_SEEDS[0],))


def test_phase1i_aggregate_requires_exact_five_development_seeds(tmp_path):
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"runs": [{"seed": 1709}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="exact Phase-1I development seeds"):
        aggregate_development_files((partial,))


def test_fresh_plateau_repair_charges_exact_new_full_evaluations():
    rng = random.Random(424242)
    start = random_sbox(rng)
    cache = {start: evaluate_classical(start)}
    before = len(cache)

    result = fresh_plateau_repair(
        seed=99,
        evaluations=2,
        evaluated_cache=cache,
        constraints=HardConstraints(),
        archive_width=1,
        proposal_pool=4,
        panel_mode="ties",
    )

    assert result["evaluations"] == 2
    assert result["proposal_pools_generated"] == 2
    assert len(cache) == before + 2
    assert result["archive_size"] == 1


def test_fresh_plateau_repair_rejects_nonfrozen_panel():
    rng = random.Random(7)
    start = random_sbox(rng)
    cache = {start: evaluate_classical(start)}
    with pytest.raises(ValueError, match="frozen ties panel"):
        fresh_plateau_repair(
            seed=1,
            evaluations=0,
            evaluated_cache=cache,
            archive_width=1,
            proposal_pool=1,
            panel_mode="band",
        )
