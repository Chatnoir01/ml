from __future__ import annotations

import ast
from pathlib import Path


SECURE_CORE_ROOT = Path("secure_core_mobile")
FORBIDDEN_PREFIXES = ("adversarial_sbox",)

PLATFORM_ISSUER = "_issue_android_avf_platform_verification"
PLATFORM_ISSUER_ALLOWED = Path("secure_core_mobile/avf_platform_verifier.py")

PVMFW_ISSUER = "_PVMFW_KEY_ISSUER_KEY"
PVMFW_ISSUER_ALLOWED = Path("secure_core_mobile/secretkeeper_dt.py")

PVMFW_TOKEN_CONSTRUCTOR = "PvmfwValidatedSecretkeeperKey"
PVMFW_CONSTRUCTOR_ALLOWED = Path("secure_core_mobile/secretkeeper_dt.py")

AVF_PIN_TOKEN_CONSTRUCTOR = "PreprovisionedAvfProfilePin"
AVF_PIN_CONSTRUCTOR_ALLOWED = Path("secure_core_mobile/avf_platform_verifier.py")
AVF_TEST_PIN_ISSUER = "_issue_preprovisioned_avf_profile_pin_for_test"


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(FORBIDDEN_PREFIXES):
                    violations.append(f"{path}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(FORBIDDEN_PREFIXES):
                violations.append(f"{path}:{node.lineno}: from {module} import ...")

    return violations


def _trust_token_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported = {alias.name for alias in node.names}
            if PLATFORM_ISSUER in imported and path != PLATFORM_ISSUER_ALLOWED:
                violations.append(
                    f"{path}:{node.lineno}: unauthorized platform-token issuer import"
                )
            if PVMFW_ISSUER in imported and path != PVMFW_ISSUER_ALLOWED:
                violations.append(
                    f"{path}:{node.lineno}: unauthorized pvmfw-token issuer import"
                )

        if isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if (
                name == PVMFW_TOKEN_CONSTRUCTOR
                and path != PVMFW_CONSTRUCTOR_ALLOWED
            ):
                violations.append(
                    f"{path}:{node.lineno}: pvmfw provenance token constructed outside reader"
                )
            if (
                name == AVF_PIN_TOKEN_CONSTRUCTOR
                and path != AVF_PIN_CONSTRUCTOR_ALLOWED
            ):
                violations.append(
                    f"{path}:{node.lineno}: AVF protected-pin token constructed outside verifier module"
                )
            if name == AVF_TEST_PIN_ISSUER:
                violations.append(
                    f"{path}:{node.lineno}: test-only AVF pin issuer used in production"
                )

    return violations


def _production_python_files() -> list[Path]:
    return sorted(SECURE_CORE_ROOT.rglob("*.py"))


def test_secure_core_has_no_gann_cross_project_imports() -> None:
    violations: list[str] = []
    for path in _production_python_files():
        violations.extend(_forbidden_imports(path))

    assert violations == [], "\n".join(violations)


def test_trust_tokens_have_single_production_issuers() -> None:
    violations: list[str] = []
    for path in _production_python_files():
        violations.extend(_trust_token_violations(path))

    assert violations == [], "\n".join(violations)
