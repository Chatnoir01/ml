from __future__ import annotations

import ast
from pathlib import Path


SECURE_CORE_ROOT = Path("secure_core_mobile")
FORBIDDEN_PREFIXES = ("adversarial_sbox",)


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


def test_secure_core_has_no_gann_cross_project_imports() -> None:
    violations: list[str] = []
    for path in sorted(SECURE_CORE_ROOT.rglob("*.py")):
        violations.extend(_forbidden_imports(path))

    assert violations == [], "\n".join(violations)
