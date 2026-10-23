"""Deterministic PR fast-feedback selector; never replaces the full CI matrix.

Run only named regression suites. This tool neither trains cryptographic
models nor consumes frozen experimental evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from collections.abc import Callable, Iterable

CRYPTO_BASELINE = (
    "tests/test_cryptoshield.py",
    "tests/test_spn.py",
    "tests/test_provenance.py",
)
SELECTOR_TEST = "tests/test_fast_feedback_selector.py"
SECURE_CORE_GATES = (
    "tests/secure_core_mobile/test_cose_encrypt0.py",
    "tests/secure_core_mobile/test_secretkeeper_packet.py",
    "tests/secure_core_mobile/test_sk_session.py",
    "tests/secure_core_mobile/test_secretkeeper_sequence_hardening.py",
    "tests/secure_core_mobile/test_sk_session_invariants.py",
    "tests/secure_core_mobile/test_authgraph_identity_provenance.py",
)
PHASE2R_GATES = (
    "tests/test_phase2r_repro.py",
    "tests/test_phase2r_serialization.py",
    "tests/test_phase2r_fixture.py",
)


def choose_fast_tests(
    changed_files: Iterable[str],
    *,
    exists: Callable[[str], bool],
) -> tuple[str, ...]:
    """Select named smoke/regression suites without silently skipping changed lanes.

    Fast feedback is best-effort for *coverage depth*, never a replacement
    for mandatory full CI/secured scientific experiment approval.
    """
    changed = tuple(sorted(set(changed_files)))
    touched_selector = any(path in {
        "scripts/select_fast_tests.py",
        "tests/test_fast_feedback_selector.py",
        ".github/workflows/fast-feedback.yml",
        "pyproject.toml",
    } for path in changed)
    crypto = touched_selector or any(
        path.startswith(("src/adversarial_sbox/", "tests/test_")) for path in changed
    )
    secure = any(
        path.startswith(("secure_core_mobile/", "tests/secure_core_mobile/"))
        for path in changed
    )
    phase2r = any(
        path.startswith((
            "src/adversarial_sbox/phase2r_",
            "tests/test_phase2r_",
            "research/fixtures/phase2r-",
        ))
        for path in changed
    )
    chosen: list[str] = []

    def require(name: str) -> None:
        if not exists(name):
            raise ValueError(f"required fast regression test missing: {name}")
        if name not in chosen:
            chosen.append(name)

    if touched_selector:
        require(SELECTOR_TEST)
    if crypto or secure or phase2r:
        for name in CRYPTO_BASELINE:
            require(name)

    if secure:
        for name in SECURE_CORE_GATES:
            # Older Secure Core branches may lack the newest tests.
            # The existing general/secure CI is still required; flag missing
            # test files explicitly rather than fabricating a green run.
            if exists(name):
                require(name)
        if not any(name in chosen for name in SECURE_CORE_GATES):
            raise ValueError("Secure Core code changed without existing smoke tests")

    if phase2r:
        for name in PHASE2R_GATES:
            require(name)

    return tuple(chosen)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select and run bounded PR smoke tests")
    parser.add_argument("--changed-file-list", required=True, type=Path)
    args = parser.parse_args()
    paths = [
        line.strip()
        for line in args.changed_file_list.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    chosen = choose_fast_tests(paths, exists=lambda p: Path(p).is_file())
    print(f"Fast feedback: {len(paths)} changed paths, {len(chosen)} selected test files", flush=True)
    for test in chosen:
        print(f"  {test}", flush=True)
    if not chosen:
        print("No scoped Python/security research code changed.", flush=True)
        return 0
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *chosen],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
