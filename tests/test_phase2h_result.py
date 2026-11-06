from __future__ import annotations

import pytest

from adversarial_sbox.phase2h_result import package_phase2h_result


def _diagnostics() -> dict:
    return {
        "phase": "2H-diagnostics",
        "diagnostic_sha256": "d" * 64,
        "parent_phase2g_commit": "c" * 40,
        "parent_phase2g_aggregate_sha256": "a" * 64,
    }


def _manifest() -> dict:
    return {
        "phase": "2H-evidence-manifest",
        "manifest_sha256": "m" * 64,
        "parent_phase2g_aggregate_sha256": "a" * 64,
    }


def test_result_packager_is_deterministic_and_non_authorizing() -> None:
    a = package_phase2h_result(_diagnostics(), _manifest())
    b = package_phase2h_result(_diagnostics(), _manifest())
    assert a == b
    assert a["frozen"] is False
    assert a["supported_mechanisms"] is None
    assert a["execution_authorized_for_phase2i"] is False
    assert a["verdict"] == "phase2h_mechanism_verdict_not_yet_authorized"


def test_result_packager_rejects_parent_mismatch() -> None:
    manifest = _manifest()
    manifest["parent_phase2g_aggregate_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="parent mismatch"):
        package_phase2h_result(_diagnostics(), manifest)
