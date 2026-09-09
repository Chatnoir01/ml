"""RED-first tests for the exact Phase 2F numerical runtime lock."""

from pathlib import Path

from adversarial_sbox.phase2f import NUMPY_VERSION


ROOT = Path(__file__).resolve().parents[1]


def test_phase2f_numpy_version_is_frozen():
    assert NUMPY_VERSION == "2.5.3"


def test_scientific_workflow_installs_exact_numpy_runtime():
    workflow = (ROOT / ".github/workflows/phase2f.yml").read_text(encoding="utf-8")
    assert "numpy==2.5.3" in workflow
    assert "numpy>=2.0" not in workflow


def test_pre_marker_qualification_uses_same_exact_numpy_runtime():
    workflow = (ROOT / ".github/workflows/phase2f-qualification.yml").read_text(encoding="utf-8")
    assert "numpy==2.5.3" in workflow
    assert "np.__version__ == NUMPY_VERSION" in workflow


def test_oracle_receipt_records_and_guards_exact_numpy_version():
    source = (ROOT / "src/adversarial_sbox/phase2f_oracle.py").read_text(encoding="utf-8")
    assert '"numpy_version": NUMPY_VERSION' in source
    assert 'np.__version__' in source
    assert "Phase 2F NumPy runtime drift" in source


def test_both_fitness_and_validation_integrity_require_runtime_version():
    freeze = (ROOT / "src/adversarial_sbox/phase2f_terminal_freeze.py").read_text(encoding="utf-8")
    aggregate = (ROOT / "src/adversarial_sbox/phase2f_aggregate.py").read_text(encoding="utf-8")
    assert 'payload.get("numpy_version"' in freeze
    assert 'payload.get("numpy_version"' in aggregate
