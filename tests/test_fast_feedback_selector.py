"""No scientific execution: test deterministic fast-path selection only."""

from __future__ import annotations

import pytest

from scripts.select_fast_tests import (
    CRYPTO_BASELINE,
    PHASE2R_GATES,
    SECURE_CORE_GATES,
    SELECTOR_TEST,
    choose_fast_tests,
)


def _available(*additional: str):
    names = set(CRYPTO_BASELINE + PHASE2R_GATES + SECURE_CORE_GATES + (SELECTOR_TEST,))
    names.update(additional)
    return names.__contains__


def test_source_change_runs_crypto_reference_smoke() -> None:
    assert choose_fast_tests(
        ["src/adversarial_sbox/cryptoshield.py"], exists=_available()
    ) == CRYPTO_BASELINE


def test_secure_core_change_keeps_aes_and_negative_security_checks() -> None:
    result = choose_fast_tests(
        ["secure_core_mobile/sk_session.py"], exists=_available()
    )
    assert all(name in result for name in CRYPTO_BASELINE + SECURE_CORE_GATES)
    assert not any(name in result for name in PHASE2R_GATES)


def test_phase2r_change_selects_all_three_receipt_guards() -> None:
    result = choose_fast_tests(
        ["src/adversarial_sbox/phase2r_repro.py"], exists=_available()
    )
    assert all(name in result for name in CRYPTO_BASELINE + PHASE2R_GATES)
    assert not any(name in result for name in SECURE_CORE_GATES)


def test_scoped_changed_paths_are_order_independent() -> None:
    changes = [
        "src/adversarial_sbox/phase2r_fixture.py",
        "secure_core_mobile/secretkeeper_packet.py",
        "src/adversarial_sbox/phase2r_fixture.py",
    ]
    assert choose_fast_tests(changes, exists=_available()) == choose_fast_tests(
        reversed(changes), exists=_available()
    )


def test_unrelated_docs_do_not_claim_coverage() -> None:
    assert choose_fast_tests(["docs/README.md"], exists=_available()) == ()


def test_fast_workflow_changes_test_selection_itself() -> None:
    result = choose_fast_tests(
        [".github/workflows/fast-feedback.yml"], exists=_available()
    )
    assert result == (SELECTOR_TEST, *CRYPTO_BASELINE)


def test_missing_phase2r_evidence_test_cannot_be_silently_skipped() -> None:
    absent = PHASE2R_GATES[-1]
    with pytest.raises(ValueError, match="required fast regression test missing"):
        choose_fast_tests(
            ["research/fixtures/phase2r-synthetic-curriculum-v1.json"],
            exists=lambda p: _available()(p) and p != absent,
        )


def test_missing_secure_core_tests_fails_closed() -> None:
    with pytest.raises(ValueError, match="without existing smoke tests"):
        choose_fast_tests(
            ["secure_core_mobile/authorization.py"],
            exists=lambda p: p in CRYPTO_BASELINE,
        )


def test_secure_core_legacy_branch_without_latest_tests_uses_existing_gates() -> None:
    legacy = tuple(SECURE_CORE_GATES[:3])
    result = choose_fast_tests(
        ["secure_core_mobile/authorization.py"],
        exists=lambda p: p in set(CRYPTO_BASELINE + legacy),
    )
    assert result == (*CRYPTO_BASELINE, *legacy)
