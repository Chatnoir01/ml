from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from secure_core_mobile.aosp_secretkeeper_contract import (
    ISECRETKEEPER_AIDL,
    SECRETKEEPER_CLIENT,
    SECRETKEEPER_VTS_CLIENT,
)


SCRIPT = Path("scripts/secure_core_aosp_secretkeeper_preflight.py")


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _eligible_tree(root: Path) -> None:
    _write(
        root,
        ISECRETKEEPER_AIDL,
        """
interface ISecretkeeper {
  IAuthGraphKeyExchange getAuthGraphKe();
  byte[] processSecretManagementRequest(in byte[] request);
}
""",
    )
    _write(
        root,
        SECRETKEEPER_CLIENT,
        """
use coset::CoseKey;
pub struct SkSession {}
pub struct OwnedDiceArtifactsWithExplicitKey {}
impl SkSession {
  pub fn new(
    sk: Binder,
    dice: &OwnedDiceArtifactsWithExplicitKey,
    expected_sk_key: Option<CoseKey>,
  ) -> Result<Self, Error> { todo!() }
}
""",
    )
    _write(
        root,
        SECRETKEEPER_VTS_CLIENT,
        """
fn with_expected_sk_identity(expected_sk_key: CoseKey) {
  let _ = SkSession::new(sk, &dice_artifacts, Some(expected_sk_key));
}
""",
    )


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_can_create_and_require_exact_contract_lock(tmp_path: Path) -> None:
    aosp = tmp_path / "aosp"
    aosp.mkdir()
    _eligible_tree(aosp)

    receipt = tmp_path / "receipt.json"
    lock = tmp_path / "lock.json"

    created = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(receipt),
        "--lock-output",
        str(lock),
    )
    assert created.returncode == 0, created.stderr

    lock_payload = json.loads(lock.read_text(encoding="utf-8"))
    assert len(lock_payload["lock_sha256"]) == 64

    verified = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(tmp_path / "verified.json"),
        "--require-lock",
        str(lock),
    )
    assert verified.returncode == 0, verified.stderr

    client = aosp / SECRETKEEPER_CLIENT
    client.write_text(
        client.read_text(encoding="utf-8") + "\n// source drift\n",
        encoding="utf-8",
    )
    rejected = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(tmp_path / "drifted.json"),
        "--require-lock",
        str(lock),
    )
    assert rejected.returncode != 0
    assert "lock mismatch" in rejected.stderr


def test_cli_refuses_lock_creation_for_ineligible_contract(tmp_path: Path) -> None:
    aosp = tmp_path / "aosp"
    aosp.mkdir()
    _eligible_tree(aosp)
    _write(aosp, SECRETKEEPER_CLIENT, "pub struct SkSession {}")

    result = _run(
        "--aosp-root",
        str(aosp),
        "--output",
        str(tmp_path / "receipt.json"),
        "--lock-output",
        str(tmp_path / "lock.json"),
    )

    assert result.returncode != 0
    assert not (tmp_path / "lock.json").exists()
