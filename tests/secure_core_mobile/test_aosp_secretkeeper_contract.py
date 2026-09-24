from __future__ import annotations

from pathlib import Path

import pytest

from secure_core_mobile.aosp_secretkeeper_contract import (
    ISECRETKEEPER_AIDL,
    SECRETKEEPER_CLIENT,
    SECRETKEEPER_VTS_CLIENT,
    inspect_aosp_secretkeeper_contract,
)


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _eligible_tree(root: Path) -> None:
    _write(
        root,
        ISECRETKEEPER_AIDL,
        """
package android.hardware.security.secretkeeper;
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
    let session = SkSession::new(sk, &dice_artifacts, Some(expected_sk_key));
}
""",
    )


def test_eligible_aosp_contract_records_source_digests(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)

    receipt = inspect_aosp_secretkeeper_contract(tmp_path)

    assert receipt.eligible_for_secure_core_native_authgraph is True
    assert receipt.reason == "required-secretkeeper-authgraph-contract-present"
    assert len(receipt.aidl_sha256) == 64
    assert len(receipt.client_sha256) == 64
    assert len(receipt.vts_client_sha256) == 64
    assert len(receipt.receipt_sha256) == 64


def test_legacy_session_without_expected_identity_binding_is_rejected(
    tmp_path: Path,
) -> None:
    _eligible_tree(tmp_path)
    _write(
        tmp_path,
        SECRETKEEPER_CLIENT,
        """
pub struct OwnedDiceArtifactsWithExplicitKey {}
pub struct SkSession {}
impl SkSession {
  pub fn new(sk: Binder, dice: &OwnedDiceArtifactsWithExplicitKey) -> Self {
      todo!()
  }
}
""",
    )

    receipt = inspect_aosp_secretkeeper_contract(tmp_path)

    assert receipt.has_get_authgraph_ke is True
    assert receipt.has_process_secret_management_request is True
    assert receipt.has_explicit_dice_identity is True
    assert receipt.has_expected_secretkeeper_identity_binding is False
    assert receipt.eligible_for_secure_core_native_authgraph is False
    assert "expected-Secretkeeper-identity-binding" in receipt.reason


def test_missing_authgraph_binder_method_is_rejected(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    _write(
        tmp_path,
        ISECRETKEEPER_AIDL,
        """
interface ISecretkeeper {
  byte[] processSecretManagementRequest(in byte[] request);
}
""",
    )

    receipt = inspect_aosp_secretkeeper_contract(tmp_path)

    assert receipt.has_get_authgraph_ke is False
    assert receipt.eligible_for_secure_core_native_authgraph is False
    assert "getAuthGraphKe" in receipt.reason


def test_vts_must_exercise_expected_identity_path(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    _write(
        tmp_path,
        SECRETKEEPER_VTS_CLIENT,
        "fn smoke() { let session = SkSession::new(sk); }",
    )

    receipt = inspect_aosp_secretkeeper_contract(tmp_path)

    assert receipt.vts_exercises_expected_identity_binding is False
    assert receipt.eligible_for_secure_core_native_authgraph is False


def test_contract_source_symlink_is_rejected(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    real = tmp_path / "real-client.rs"
    real.write_text(
        (tmp_path / SECRETKEEPER_CLIENT).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / SECRETKEEPER_CLIENT).unlink()
    (tmp_path / SECRETKEEPER_CLIENT).symlink_to(real)

    with pytest.raises(ValueError, match="symlink"):
        inspect_aosp_secretkeeper_contract(tmp_path)
