from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import subprocess

import pytest

from secure_core_mobile.aosp_secretkeeper_contract import (
    ANDROID_SECURITY_17_R1,
    HARDWARE_INTERFACES_REPO,
    ISECRETKEEPER_AIDL,
    SECRETKEEPER_CLIENT,
    SECRETKEEPER_EXPLICIT_DICE,
    SECRETKEEPER_VTS_CLIENT,
    SYSTEM_SECRETKEEPER_REPO,
    inspect_aosp_secretkeeper_contract,
    lock_aosp_secretkeeper_contract,
)
from secure_core_mobile.aosp_verified_session_build import (
    VERIFIED_SESSION_MODULE,
    run_verified_session_soong_build,
)


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _eligible_contract_tree(root: Path) -> None:
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
use explicitkeydice::OwnedDiceArtifactsWithExplicitKey;
pub struct SkSession {}
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
        SECRETKEEPER_EXPLICIT_DICE,
        """
pub struct OwnedDiceArtifactsWithExplicitKey {}
impl OwnedDiceArtifactsWithExplicitKey {
  pub fn from_owned_artifacts(artifacts: OwnedDiceArtifacts) -> Result<Self, Error> {
    todo!()
  }
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


def _write_contract_lock(root: Path, path: Path) -> None:
    receipt = inspect_aosp_secretkeeper_contract(root)
    lock = lock_aosp_secretkeeper_contract(receipt)
    payload = asdict(lock)
    payload["lock_sha256"] = lock.lock_sha256
    path.write_text(json.dumps(payload), encoding="utf-8")


def _native_module(root: Path) -> Path:
    native = root / "external/secure_core/android_native"
    native.mkdir(parents=True, exist_ok=True)
    (native / "Android.bp").write_text(
        f"""
rust_library {{
    name: "{VERIFIED_SESSION_MODULE}",
    defaults: ["secretkeeper_use_latest_hal_aidl_rust"],
    rustlibs: [
        "android.hardware.security.secretkeeper-V1-rust",
        "libbinder_rs",
        "libcoset",
        "libexplicitkeydice",
        "libsecretkeeper_client",
    ],
}}
""",
        encoding="utf-8",
    )
    (native / "secretkeeper_verified_session.rs").write_text(
        """
use explicitkeydice::OwnedDiceArtifactsWithExplicitKey;
let expected_sk_key = CoseKey::from_slice(expected_sk_key_cbor)?;
let session = SkSession::new(sk, dice, Some(expected_sk_key))?;
""",
        encoding="utf-8",
    )
    return native


def _soong(root: Path) -> None:
    path = root / "build/soong/soong_ui.bash"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")


def _heads(root: Path):
    expected = {
        root / SYSTEM_SECRETKEEPER_REPO:
            ANDROID_SECURITY_17_R1.system_secretkeeper_commit,
        root / HARDWARE_INTERFACES_REPO:
            ANDROID_SECURITY_17_R1.hardware_interfaces_commit,
    }

    def read(path: Path) -> str:
        return expected[path]

    return read


def _prepared_tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "aosp"
    root.mkdir()
    _eligible_contract_tree(root)
    native = _native_module(root)
    _soong(root)
    lock = tmp_path / "secretkeeper-contract-lock.json"
    _write_contract_lock(root, lock)
    return root, native, lock


def test_locked_verified_session_soong_build_success(tmp_path: Path) -> None:
    root, native, lock = _prepared_tree(tmp_path)
    calls: list[tuple[list[str], Path, int]] = []

    def runner(command, *, cwd, timeout):
        calls.append((command, cwd, timeout))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="compiled verified session\n",
            stderr="",
        )

    receipt = run_verified_session_soong_build(
        aosp_root=root,
        secure_core_android_native_dir=native,
        contract_lock_path=lock,
        runner=runner,
        git_head_reader=_heads(root),
    )

    assert receipt.build_succeeded is True
    assert receipt.reason == "soong-build-succeeded"
    assert receipt.returncode == 0
    assert receipt.module_name == VERIFIED_SESSION_MODULE
    assert receipt.source_target == ANDROID_SECURITY_17_R1.name
    assert len(receipt.contract_lock_sha256) == 64
    assert len(receipt.android_bp_sha256) == 64
    assert len(receipt.rust_source_sha256) == 64
    assert len(receipt.stdout_sha256) == 64
    assert b"compiled verified session" not in receipt.canonical_bytes()
    assert calls[0][0][-1] == VERIFIED_SESSION_MODULE
    assert calls[0][1] == root


def test_soong_failure_is_receipted_not_promoted(tmp_path: Path) -> None:
    root, native, lock = _prepared_tree(tmp_path)

    def runner(command, *, cwd, timeout):
        return subprocess.CompletedProcess(
            command,
            7,
            stdout="",
            stderr="compiler error",
        )

    receipt = run_verified_session_soong_build(
        aosp_root=root,
        secure_core_android_native_dir=native,
        contract_lock_path=lock,
        runner=runner,
        git_head_reader=_heads(root),
    )

    assert receipt.build_succeeded is False
    assert receipt.reason == "soong-build-failed"
    assert receipt.returncode == 7
    assert b"compiler error" not in receipt.canonical_bytes()


def test_explicit_dice_drift_blocks_build_before_runner(tmp_path: Path) -> None:
    root, native, lock = _prepared_tree(tmp_path)
    dice = root / SECRETKEEPER_EXPLICIT_DICE
    dice.write_text(
        dice.read_text(encoding="utf-8") + "\n// drift\n",
        encoding="utf-8",
    )
    called = False

    def runner(command, *, cwd, timeout):
        nonlocal called
        called = True
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with pytest.raises(ValueError, match="explicit DICE client lock mismatch"):
        run_verified_session_soong_build(
            aosp_root=root,
            secure_core_android_native_dir=native,
            contract_lock_path=lock,
            runner=runner,
            git_head_reader=_heads(root),
        )
    assert called is False


def test_native_module_must_be_inside_aosp_tree(tmp_path: Path) -> None:
    root, _, lock = _prepared_tree(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "Android.bp").write_text("x", encoding="utf-8")
    (outside / "secretkeeper_verified_session.rs").write_text(
        "x", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="inside AOSP root"):
        run_verified_session_soong_build(
            aosp_root=root,
            secure_core_android_native_dir=outside,
            contract_lock_path=lock,
            git_head_reader=_heads(root),
        )


def test_missing_soong_dependency_marker_blocks_build(tmp_path: Path) -> None:
    root, native, lock = _prepared_tree(tmp_path)
    bp = native / "Android.bp"
    bp.write_text(
        bp.read_text(encoding="utf-8").replace(
            '"libexplicitkeydice",',
            "",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="libexplicitkeydice"):
        run_verified_session_soong_build(
            aosp_root=root,
            secure_core_android_native_dir=native,
            contract_lock_path=lock,
            git_head_reader=_heads(root),
        )
