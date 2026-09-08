from pathlib import Path


def test_phase2e_workflow_is_marker_gated_and_artifact_only() -> None:
    workflow = Path('.github/workflows/phase2e.yml').read_text(encoding='utf-8')
    runner = Path('scripts/run_phase2e.py').read_text(encoding='utf-8')

    assert 'research/PHASE2E_EXECUTE.md' in workflow
    assert 'AUTHORIZED_PHASE2E_ARTIFACT_DIAGNOSTICS' in workflow
    assert "SOURCE_RUN_ID: '34147455097'" in workflow
    assert "SOURCE_MARKER_SHA: '2cc913e33cc5848f12ae5493f992b49fa89bc3d2'" in workflow
    assert 'phase2d-arm-*-${SOURCE_MARKER_SHA}' in workflow
    assert 'phase2d-terminal-freeze-${SOURCE_MARKER_SHA}' in workflow
    assert 'phase2d-summary-${SOURCE_MARKER_SHA}' in workflow
    assert 'pip install -e .' in workflow

    # The workflow must never request Phase 2D held-out validation artifacts or
    # install the neural extra. These checks are intentionally outside the YAML
    # so the forbidden literal itself is not embedded in the workflow source.
    assert 'phase2d-validation-' not in workflow
    assert ".[neural]" not in workflow

    for forbidden in (
        'phase2d_oracle',
        'phase2d_validation',
        'score_fitness_candidate',
        'score_validation_candidate',
    ):
        assert forbidden not in runner


def test_phase2e_marker_is_still_absent_prequalification() -> None:
    assert not Path('research/PHASE2E_EXECUTE.md').exists()
