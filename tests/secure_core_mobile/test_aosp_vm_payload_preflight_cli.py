from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from secure_core_mobile.aosp_vm_payload_contract import (
    VM_PAYLOAD_HEADER,
    VM_PAYLOAD_README,
)


SCRIPT = Path("scripts/secure_core_aosp_vm_payload_preflight.py")


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _eligible_tree(root: Path) -> None:
    _write(
        root,
        VM_PAYLOAD_HEADER,
        """
int AVmPayload_requestAttestation(...);
void AVmPayload_getVmInstanceSecret(...);
int AVmPayload_writeRollbackProtectedSecret(...);
int AVmPayload_readRollbackProtectedSecret(...);
bool AVmPayload_isNewInstance(...);
""",
    )
    _write(
        root,
        VM_PAYLOAD_README,
        """
A payload cannot connect to any binder server.
Use AVmPayload_runVsockRpcServer for Binder RPC.
""",
    )


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_emits_eligible_secret_free_receipt(tmp_path: Path) -> None:
    aosp = tmp_path / "aosp"
    aosp.mkdir()
    _eligible_tree(aosp)
    output = tmp_path / "receipt.json"

    result = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["eligible_for_secure_core_payload"] is True
    assert len(payload["header_sha256"]) == 64
    assert len(payload["readme_sha256"]) == 64
    assert len(payload["receipt_sha256"]) == 64


def test_cli_returns_two_for_ineligible_contract(tmp_path: Path) -> None:
    aosp = tmp_path / "aosp"
    aosp.mkdir()
    _eligible_tree(aosp)
    header = aosp / VM_PAYLOAD_HEADER
    header.write_text(
        header.read_text(encoding="utf-8").replace(
            "AVmPayload_readRollbackProtectedSecret",
            "REMOVED",
        ),
        encoding="utf-8",
    )
    output = tmp_path / "receipt.json"

    result = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(output),
    )

    assert result.returncode == 2
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["eligible_for_secure_core_payload"] is False
    assert "rollback-protected-read" in payload["reason"]
