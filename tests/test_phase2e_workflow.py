from pathlib import Path


MARKER_PATH = Path('research/PHASE2E_EXECUTE.md')
MARKER_TOKEN = 'AUTHORIZED_PHASE2E_ARTIFACT_DIAGNOSTICS'


def test_phase2e_workflow_is_marker_gated_and_artifact_only() -> None:
    workflow = Path('.github/workflows/phase2e.yml').read_text(encoding='utf-8')
    runner = Path('scripts/run_phase2e.py').read_text(encoding='utf-8')

    assert 'research/PHASE2E_EXECUTE.md' in workflow
    assert MARKER_TOKEN in workflow
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


def test_phase2e_marker_contract_is_fail_closed_if_present() -> None:
    # Before qualification the marker is absent. After explicit authorization it
    # may exist, but only with the exact frozen one-line token. This keeps the
    # same test valid for pre-marker, marker, result-freeze, and merged commits.
    if not MARKER_PATH.exists():
        return
    assert MARKER_PATH.read_text(encoding='utf-8').splitlines() == [MARKER_TOKEN]
