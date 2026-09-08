"""RED-first Phase 2F arm provenance and terminal-identity checks."""

from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.phase1m import _initial_population, _population_digest
from adversarial_sbox.phase2f_provenance import arm_provenance_report
from adversarial_sbox.provenance import fingerprint_sbox


def _run(seed=526011):
    terminal = tuple(range(256))
    metrics = evaluate_classical(terminal)
    return {
        "seed": seed,
        "arm": "C",
        "initial_population_digest_sha256": _population_digest(_initial_population(seed)),
        "terminal_sbox": list(terminal),
        "terminal_fingerprint": fingerprint_sbox(terminal),
        "terminal_classical": {
            "nonlinearity": metrics.nonlinearity,
            "differential_uniformity": metrics.differential_uniformity,
            "max_linear_correlation": metrics.max_linear_correlation,
            "sac_score": metrics.sac_score,
            "algebraic_degree": metrics.algebraic_degree,
            "fingerprint": metrics.fingerprint,
        },
    }


def test_valid_arm_provenance_recomputes_initial_digest_and_terminal_metrics():
    report = arm_provenance_report(_run())
    assert report["pass"] is True


def test_wrong_initial_population_digest_fails_closed():
    run = _run()
    run["initial_population_digest_sha256"] = "0" * 64
    report = arm_provenance_report(run)
    assert report["pass"] is False
    assert report["checks"]["initial_population_digest"] is False


def test_terminal_fingerprint_mismatch_fails_before_block_x():
    run = _run()
    run["terminal_fingerprint"] = "f" * 64
    report = arm_provenance_report(run)
    assert report["pass"] is False
    assert report["checks"]["terminal_fingerprint"] is False


def test_terminal_classical_metric_drift_fails_before_block_x():
    run = _run()
    run["terminal_classical"]["nonlinearity"] += 2
    report = arm_provenance_report(run)
    assert report["pass"] is False
    assert report["checks"]["terminal_classical_metrics"] is False
