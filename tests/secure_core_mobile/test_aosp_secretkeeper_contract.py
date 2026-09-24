from __future__ import annotations

from pathlib import Path

import pytest

from secure_core_mobile.aosp_secretkeeper_contract import (
    ISECRETKEEPER_AIDL,
    SECRETKEEPER_CLIENT,
    SECRETKEEPER_VTS_CLIENT,
    inspect_aosp_secretkeeper_contract,
    load_aosp_secretkeeper_contract_lock,
    lock_aosp_secretkeeper_contract,
    verify_aosp_secretkeeper_contract_lock,
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


def test_exact_contract_lock_accepts_unchanged_snapshot(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    receipt = inspect_aosp_secretkeeper_contract(tmp_path)
    lock = lock_aosp_secretkeeper_contract(receipt)

    verify_aosp_secretkeeper_contract_lock(receipt, lock)

    assert len(lock.lock_sha256) == 64


def test_contract_lock_rejects_source_drift_even_if_api_markers_remain(
    tmp_path: Path,
) -> None:
    _eligible_tree(tmp_path)
    original = inspect_aosp_secretkeeper_contract(tmp_path)
    lock = lock_aosp_secretkeeper_contract(original)

    client_path = tmp_path / SECRETKEEPER_CLIENT
    client_path.write_text(
        client_path.read_text(encoding="utf-8") + "\n// reviewed-source-drift\n",
        encoding="utf-8",
    )
    drifted = inspect_aosp_secretkeeper_contract(tmp_path)
    assert drifted.eligible_for_secure_core_native_authgraph is True

    with pytest.raises(ValueError, match="client lock mismatch"):
        verify_aosp_secretkeeper_contract_lock(drifted, lock)


def test_ineligible_contract_cannot_be_locked(tmp_path: Path) -> None:
    _eligible_tree(tmp_path)
    _write(
        tmp_path,
        SECRETKEEPER_CLIENT,
        "pub struct SkSession {}",
    )
    receipt = inspect_aosp_secretkeeper_contract(tmp_path)

    with pytest.raises(ValueError, match="ineligible"):
        lock_aosp_secretkeeper_contract(receipt)


def test_lock_loader_checks_self_digest(tmp_path: Path) -> None:
    import json
    from dataclasses import asdict

    _eligible_tree(tmp_path)
    receipt = inspect_aosp_secretkeeper_contract(tmp_path)
    lock = lock_aosp_secretkeeper_contract(receipt)
    lock_path = tmp_path / "contract-lock.json"

    payload = asdict(lock)
    payload["lock_sha256"] = lock.lock_sha256
    lock_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_aosp_secretkeeper_contract_lock(lock_path)
    assert loaded == lock

    payload["lock_sha256"] = "0" * 64
    lock_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="self-digest"):
        load_aosp_secretkeeper_contract_lock(lock_path)
